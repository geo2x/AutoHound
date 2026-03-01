# AutoHound © 2026 Gordon Prescott

"""
Graph serializer - converts AD graph to LLM-optimized text representation.

Implements intelligent chunking to prioritize high-value nodes and keep within
LLM context windows while preserving critical attack path information.
"""

import json
import logging
from typing import Dict, List, Set

from autohound.models import Graph, Node, Edge, NodeType, EdgeType

logger = logging.getLogger(__name__)


class GraphSerializer:
    """Serialize AD graph into LLM-readable format with intelligent chunking."""
    
    def __init__(self, graph: Graph, max_chunk_size: int = 100000):
        """
        Initialize serializer.
        
        Args:
            graph: The AD graph to serialize
            max_chunk_size: Maximum characters per chunk (consider LLM context limits)
        """
        self.graph = graph
        self.max_chunk_size = max_chunk_size
    
    def serialize_to_text(self, include_all_nodes: bool = False) -> str:
        """
        Serialize graph to natural language description.
        
        Args:
            include_all_nodes: If False, prioritize high-value nodes and paths
        
        Returns:
            Human-readable text description of the AD environment
        """
        sections = []
        
        # Executive summary
        sections.append(self._generate_summary())
        
        # High-value targets (always included)
        sections.append(self._describe_high_value_targets())
        
        # Node descriptions
        if include_all_nodes:
            sections.append(self._describe_all_nodes())
        else:
            sections.append(self._describe_prioritized_nodes())
        
        # Relationship descriptions
        sections.append(self._describe_relationships())
        
        # Attack surface indicators
        sections.append(self._describe_attack_surface())
        
        return "\n\n".join(sections)
    
    def serialize_to_json(self) -> str:
        """
        Serialize graph to structured JSON for LLM consumption.
        
        Returns:
            JSON string with nodes, edges, and metadata
        """
        data = {
            "metadata": {
                "node_count": self.graph.node_count(),
                "edge_count": self.graph.edge_count(),
                "high_value_targets": len(self.graph.get_high_value_nodes()),
            },
            "nodes": [self._node_to_dict(node) for node in self.graph.nodes.values()],
            "edges": [self._edge_to_dict(edge) for edge in self.graph.edges],
            "high_value_targets": [
                self._node_to_dict(node) for node in self.graph.get_high_value_nodes()
            ],
        }
        
        return json.dumps(data, indent=2)
    
    def create_chunks(self) -> List[str]:
        """
        Create multiple chunks if graph is too large for single context window.
        
        Returns:
            List of text chunks, each under max_chunk_size
        """
        chunks = []
        
        # Always include summary in first chunk
        summary = self._generate_summary()
        hvt_desc = self._describe_high_value_targets()
        
        chunk_1 = f"{summary}\n\n{hvt_desc}"
        chunks.append(chunk_1)
        
        # Chunk relationships by high-value node proximity
        hvt_nodes = self.graph.get_high_value_nodes()
        hvt_ids = {node.id for node in hvt_nodes}
        
        # Get all edges connected to high-value targets
        priority_edges = [
            e for e in self.graph.edges
            if e.source_id in hvt_ids or e.target_id in hvt_ids
        ]
        
        # Describe priority edges
        priority_desc = self._describe_edge_list(priority_edges, "High-Value Target Relationships")
        
        if len(chunk_1) + len(priority_desc) < self.max_chunk_size:
            chunks[0] = f"{chunk_1}\n\n{priority_desc}"
        else:
            chunks.append(priority_desc)
        
        # Add remaining edges if space permits
        remaining_edges = [e for e in self.graph.edges if e not in priority_edges]
        if remaining_edges:
            remaining_desc = self._describe_edge_list(remaining_edges, "Additional Relationships")
            chunks.append(remaining_desc)
        
        logger.info(f"Created {len(chunks)} chunks for LLM processing")
        return chunks
    
    def _generate_summary(self) -> str:
        """Generate executive summary of the AD environment."""
        hvt = self.graph.get_high_value_nodes()
        
        # Count by type
        users = sum(1 for n in self.graph.nodes.values() if n.node_type == NodeType.USER)
        computers = sum(1 for n in self.graph.nodes.values() if n.node_type == NodeType.COMPUTER)
        groups = sum(1 for n in self.graph.nodes.values() if n.node_type == NodeType.GROUP)
        
        dcs = sum(1 for n in hvt if n.is_domain_controller)
        das = sum(1 for n in hvt if n.is_domain_admin)
        
        summary = f"""# Active Directory Environment Summary

**Total Objects:** {self.graph.node_count()} nodes, {self.graph.edge_count()} relationships

**Breakdown:**
- Users: {users}
- Computers: {computers}
- Groups: {groups}
- High-Value Targets: {len(hvt)}
  - Domain Controllers: {dcs}
  - Domain Admins: {das}

**Analysis Objective:** Identify novel attack paths from low-privilege starting points to Domain Admin or equivalent compromise.
"""
        return summary
    
    def _describe_high_value_targets(self) -> str:
        """Describe all high-value targets in detail."""
        hvt = self.graph.get_high_value_nodes()
        
        if not hvt:
            return "# High-Value Targets\n\nNo high-value targets identified."
        
        desc = ["# High-Value Targets\n"]
        desc.append("These are Tier 0 assets - compromise of any grants significant or complete domain control.\n")
        
        for node in hvt:
            desc.append(f"\n## {node.name}")
            desc.append(f"- Type: {node.node_type.value}")
            desc.append(f"- Object ID: {node.id}")
            
            if node.is_domain_controller:
                desc.append("- **Role: Domain Controller**")
            if node.is_domain_admin:
                desc.append("- **Role: Domain Admin**")
            if node.is_enterprise_admin:
                desc.append("- **Role: Enterprise Admin**")
            
            # Show direct paths TO this target
            inbound = self.graph.get_inbound_edges(node.id)
            if inbound:
                desc.append(f"\n**Inbound Relationships ({len(inbound)}):**")
                for edge in inbound[:10]:  # Limit to 10 for readability
                    source = self.graph.get_node(edge.source_id)
                    if source:
                        desc.append(f"  - {source.name} --[{edge.edge_type.value}]--> {node.name}")
        
        return "\n".join(desc)
    
    def _describe_prioritized_nodes(self) -> str:
        """Describe nodes prioritized by attack path relevance."""
        # Priority: HVT, then nodes with edges to HVT, then privileged users/computers
        hvt_ids = {node.id for node in self.graph.get_high_value_nodes()}
        
        # Find nodes one hop from HVT
        one_hop_ids: Set[str] = set()
        for edge in self.graph.edges:
            if edge.target_id in hvt_ids:
                one_hop_ids.add(edge.source_id)
        
        # Collect priority nodes
        priority_nodes = [
            self.graph.get_node(nid) for nid in one_hop_ids
            if nid not in hvt_ids and self.graph.get_node(nid) is not None
        ]
        
        desc = ["# Priority Nodes (Direct Paths to High-Value Targets)\n"]
        
        for node in priority_nodes[:50]:  # Limit for context
            desc.append(f"\n## {node.name}")
            desc.append(f"- Type: {node.node_type.value}")
            desc.append(f"- Enabled: {node.enabled if node.enabled is not None else 'Unknown'}")
            
            # Show what HVTs this node can reach
            outbound_to_hvt = [
                e for e in self.graph.get_outbound_edges(node.id)
                if e.target_id in hvt_ids
            ]
            
            if outbound_to_hvt:
                desc.append(f"\n**Can reach {len(outbound_to_hvt)} high-value target(s):**")
                for edge in outbound_to_hvt:
                    target = self.graph.get_node(edge.target_id)
                    if target:
                        desc.append(f"  - {edge.edge_type.value} --> {target.name}")
        
        return "\n".join(desc)
    
    def _describe_all_nodes(self) -> str:
        """Describe all nodes (use with caution - can be very large)."""
        desc = ["# All Nodes\n"]
        
        for node in list(self.graph.nodes.values())[:200]:  # Hard limit
            desc.append(f"\n- {node.name} ({node.node_type.value})")
        
        if self.graph.node_count() > 200:
            desc.append(f"\n... and {self.graph.node_count() - 200} more nodes")
        
        return "\n".join(desc)
    
    def _describe_relationships(self) -> str:
        """Describe key relationship patterns."""
        desc = ["# Key Relationships\n"]
        
        # Group edges by type
        edge_counts: Dict[EdgeType, int] = {}
        for edge in self.graph.edges:
            edge_counts[edge.edge_type] = edge_counts.get(edge.edge_type, 0) + 1
        
        desc.append("**Relationship Type Distribution:**\n")
        for edge_type, count in sorted(edge_counts.items(), key=lambda x: x[1], reverse=True):
            desc.append(f"- {edge_type.value}: {count}")
        
        # Highlight dangerous relationships
        dangerous_types = {
            EdgeType.GENERIC_ALL, EdgeType.WRITE_DACL, EdgeType.WRITE_OWNER,
            EdgeType.DCSYNC, EdgeType.GET_CHANGES_ALL, EdgeType.FORCE_CHANGE_PASSWORD
        }
        
        dangerous_edges = [e for e in self.graph.edges if e.edge_type in dangerous_types]
        
        if dangerous_edges:
            desc.append(f"\n**High-Risk ACL Misconfigurations ({len(dangerous_edges)}):**\n")
            for edge in dangerous_edges[:20]:
                source = self.graph.get_node(edge.source_id)
                target = self.graph.get_node(edge.target_id)
                if source and target:
                    desc.append(f"- {source.name} --[{edge.edge_type.value}]--> {target.name}")
        
        return "\n".join(desc)
    
    def _describe_attack_surface(self) -> str:
        """Describe attack surface indicators."""
        desc = ["# Attack Surface Indicators\n"]
        
        # Kerberoastable (users with SPNs)
        # Unconstrained delegation
        # Computers with admin sessions
        
        unconstrained_computers = [
            node for node in self.graph.nodes.values()
            if node.node_type == NodeType.COMPUTER
            and node.properties.get("unconstrained_delegation", False)
        ]
        
        if unconstrained_computers:
            desc.append(f"\n**Unconstrained Delegation Enabled ({len(unconstrained_computers)}):**")
            for comp in unconstrained_computers[:10]:
                desc.append(f"- {comp.name}")
        
        # Sessions on computers
        session_edges = [e for e in self.graph.edges if e.edge_type == EdgeType.HAS_SESSION]
        if session_edges:
            desc.append(f"\n**Active Sessions Detected: {len(session_edges)}**")
            desc.append("(May enable credential theft or lateral movement)")
        
        return "\n".join(desc)
    
    def _describe_edge_list(self, edges: List[Edge], title: str) -> str:
        """Describe a list of edges."""
        desc = [f"# {title}\n"]
        
        for edge in edges[:100]:  # Limit
            source = self.graph.get_node(edge.source_id)
            target = self.graph.get_node(edge.target_id)
            
            if source and target:
                desc.append(f"- {source.name} --[{edge.edge_type.value}]--> {target.name}")
        
        if len(edges) > 100:
            desc.append(f"\n... and {len(edges) - 100} more relationships")
        
        return "\n".join(desc)
    
    def _node_to_dict(self, node: Node) -> Dict:
        """Convert Node to dictionary for JSON serialization."""
        return {
            "id": node.id,
            "name": node.name,
            "type": node.node_type.value,
            "enabled": node.enabled,
            "domain": node.domain,
            "is_high_value": node.is_tier_zero,
            "is_domain_controller": node.is_domain_controller,
            "is_domain_admin": node.is_domain_admin,
        }
    
    def _edge_to_dict(self, edge: Edge) -> Dict:
        """Convert Edge to dictionary for JSON serialization."""
        return {
            "source": edge.source_id,
            "target": edge.target_id,
            "type": edge.edge_type.value,
        }
