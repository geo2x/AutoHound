# AutoHound © 2026 Gordon Prescott

"""
JSON file ingestor for BloodHound export data.

Parses BloodHound JSON export files (computers.json, users.json, etc.) and
builds a Graph representation without requiring a Neo4j database.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from autohound.models import (
    Graph, Node, Edge, NodeType, EdgeType
)

logger = logging.getLogger(__name__)


class JsonIngestor:
    """Ingest BloodHound data from JSON export files."""
    
    def __init__(self, file_path: Union[str, Path]):
        """
        Initialize JSON ingestor.
        
        Args:
            file_path: Path to BloodHound JSON export file or directory containing exports
        """
        self.file_path = Path(file_path)
        self.graph = Graph()
    
    def ingest(self) -> Graph:
        """
        Ingest BloodHound JSON data.
        
        Returns:
            Graph object containing all nodes and edges
        """
        if self.file_path.is_file():
            # Single JSON file
            logger.info(f"Ingesting single file: {self.file_path}")
            self._ingest_file(self.file_path)
        elif self.file_path.is_dir():
            # Directory of JSON files
            logger.info(f"Ingesting directory: {self.file_path}")
            json_files = list(self.file_path.glob("*.json"))
            logger.info(f"Found {len(json_files)} JSON files")
            
            for json_file in json_files:
                self._ingest_file(json_file)
        else:
            raise FileNotFoundError(f"Path not found: {self.file_path}")
        
        logger.info(f"Ingestion complete: {self.graph.node_count()} nodes, {self.graph.edge_count()} edges")
        return self.graph
    
    def _ingest_file(self, file_path: Path) -> None:
        """Ingest a single JSON file."""
        logger.info(f"Processing {file_path.name}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # BloodHound JSON structure varies by version
            # Modern format: {"data": [...], "meta": {...}}
            # Legacy format: {...}
            
            if isinstance(data, dict):
                if "data" in data:
                    # Modern format
                    self._process_data_array(data["data"])
                    if "meta" in data:
                        self.graph.metadata.update(data["meta"])
                else:
                    # Legacy single object or custom format
                    self._process_data_array([data])
            elif isinstance(data, list):
                # Array of objects
                self._process_data_array(data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    def _process_data_array(self, data: List[Dict[str, Any]]) -> None:
        """Process array of BloodHound data objects."""
        for item in data:
            # Determine object type
            if "Properties" in item and "ObjectIdentifier" in item:
                # Modern BloodHound CE format
                self._process_modern_format(item)
            elif "objectid" in item or "ObjectID" in item:
                # Legacy format
                self._process_legacy_format(item)
    
    def _process_modern_format(self, item: Dict[str, Any]) -> None:
        """Process modern BloodHound CE JSON format."""
        props = item.get("Properties", {})
        object_id = item.get("ObjectIdentifier", "")
        kind = item.get("Kind", "")
        
        # Create node
        node = self._create_node_from_properties(object_id, kind, props)
        if node:
            self.graph.add_node(node)
        
        # Process relationships
        # BloodHound CE stores edges in "Aces" (ACEs), "SPNTargets", etc.
        aces = item.get("Aces", [])
        for ace in aces:
            edge = self._create_edge_from_ace(object_id, ace)
            if edge:
                self.graph.add_edge(edge)
        
        # Group memberships
        primary_group = props.get("primarygroupsid")
        if primary_group:
            edge = Edge(
                source_id=object_id,
                target_id=primary_group,
                edge_type=EdgeType.MEMBER_OF
            )
            self.graph.add_edge(edge)
        
        # Process group members (reverse: members -> group)
        members = item.get("Members", [])
        for member in members:
            member_id = member.get("ObjectIdentifier") if isinstance(member, dict) else member
            if member_id:
                edge = Edge(
                    source_id=member_id,
                    target_id=object_id,
                    edge_type=EdgeType.MEMBER_OF
                )
                self.graph.add_edge(edge)
        
        # Process local admins (admin -> computer)
        local_admins = item.get("LocalAdmins", [])
        for admin in local_admins:
            admin_id = admin.get("ObjectIdentifier") if isinstance(admin, dict) else admin
            if admin_id:
                edge = Edge(
                    source_id=admin_id,
                    target_id=object_id,
                    edge_type=EdgeType.ADMIN_TO
                )
                self.graph.add_edge(edge)
        
        # Process sessions (user has session on computer)
        sessions = item.get("Sessions", [])
        for session in sessions:
            user_id = session.get("ObjectIdentifier") if isinstance(session, dict) else session
            if user_id:
                edge = Edge(
                    source_id=object_id,
                    target_id=user_id,
                    edge_type=EdgeType.HAS_SESSION
                )
                self.graph.add_edge(edge)
        
        # Process other relationship arrays
        for rel_key in ["AllowedToDelegate", "HasSIDHistory", "TrustedBy"]:
            rel_array = item.get(rel_key, [])
            for target in rel_array:
                edge_type = self._map_relationship_key(rel_key)
                target_id = target.get("ObjectIdentifier") if isinstance(target, dict) else target
                edge = Edge(
                    source_id=object_id,
                    target_id=target_id,
                    edge_type=edge_type
                )
                self.graph.add_edge(edge)
    
    def _process_legacy_format(self, item: Dict[str, Any]) -> None:
        """Process legacy BloodHound JSON format."""
        object_id = item.get("objectid") or item.get("ObjectID", "")
        node_type = item.get("type", "").lower()
        
        # Determine NodeType
        if node_type == "user":
            nt = NodeType.USER
        elif node_type == "computer":
            nt = NodeType.COMPUTER
        elif node_type == "group":
            nt = NodeType.GROUP
        elif node_type == "domain":
            nt = NodeType.DOMAIN
        elif node_type == "gpo":
            nt = NodeType.GPO
        elif node_type == "ou":
            nt = NodeType.OU
        else:
            nt = NodeType.UNKNOWN
        
        # Create node
        node = Node(
            id=object_id,
            name=item.get("name", "Unknown"),
            node_type=nt,
            enabled=item.get("enabled"),
            admin_count=item.get("admincount"),
            domain=item.get("domain"),
            distinguished_name=item.get("distinguishedname"),
            properties=item
        )
        
        # Mark high-value targets
        self._mark_high_value(node)
        self.graph.add_node(node)
        
        # Process relationships from legacy format
        # These are typically in arrays like "AdminTo", "MemberOf", etc.
        for key, value in item.items():
            if isinstance(value, list) and key != "properties":
                edge_type = self._map_relationship_key(key)
                if edge_type != EdgeType.UNKNOWN:
                    for target_id in value:
                        if isinstance(target_id, str):
                            edge = Edge(
                                source_id=object_id,
                                target_id=target_id,
                                edge_type=edge_type
                            )
                            self.graph.add_edge(edge)
    
    def _create_node_from_properties(self, object_id: str, kind: str, props: Dict[str, Any]) -> Optional[Node]:
        """Create a Node from modern format properties."""
        # Map kind to NodeType
        kind_lower = kind.lower()
        node_type_map = {
            "user": NodeType.USER,
            "computer": NodeType.COMPUTER,
            "group": NodeType.GROUP,
            "domain": NodeType.DOMAIN,
            "gpo": NodeType.GPO,
            "ou": NodeType.OU,
            "container": NodeType.CONTAINER,
        }
        
        node_type = node_type_map.get(kind_lower, NodeType.UNKNOWN)
        
        node = Node(
            id=object_id,
            name=props.get("name", props.get("displayname", "Unknown")),
            node_type=node_type,
            enabled=props.get("enabled"),
            admin_count=props.get("admincount"),
            domain=props.get("domain"),
            distinguished_name=props.get("distinguishedname"),
            properties=props
        )
        
        # Mark high-value
        self._mark_high_value(node)
        
        return node
    
    def _create_edge_from_ace(self, source_id: str, ace: Dict[str, Any]) -> Optional[Edge]:
        """Create an Edge from an ACE (Access Control Entry)."""
        principal_sid = ace.get("PrincipalSID")
        right_name = ace.get("RightName", "")
        
        if not principal_sid:
            return None
        
        # Map ACE right to EdgeType
        edge_type = self._map_ace_right(right_name)
        
        # ACEs describe permissions FROM principal TO object
        # So source is principal, target is the object
        edge = Edge(
            source_id=principal_sid,
            target_id=source_id,
            edge_type=edge_type,
            properties=ace
        )
        
        return edge
    
    def _map_ace_right(self, right_name: str) -> EdgeType:
        """Map ACE right name to EdgeType."""
        mapping = {
            "GenericAll": EdgeType.GENERIC_ALL,
            "GenericWrite": EdgeType.GENERIC_WRITE,
            "WriteOwner": EdgeType.WRITE_OWNER,
            "WriteDacl": EdgeType.WRITE_DACL,
            "AddMember": EdgeType.ADD_MEMBER,
            "ForceChangePassword": EdgeType.FORCE_CHANGE_PASSWORD,
            "AddAllowedToAct": EdgeType.ADD_ALLOWED_TO_ACT,
            "DCSync": EdgeType.DCSYNC,
            "GetChanges": EdgeType.GET_CHANGES,
            "GetChangesAll": EdgeType.GET_CHANGES_ALL,
        }
        return mapping.get(right_name, EdgeType.UNKNOWN)
    
    def _map_relationship_key(self, key: str) -> EdgeType:
        """Map JSON key to EdgeType."""
        mapping = {
            "MemberOf": EdgeType.MEMBER_OF,
            "AdminTo": EdgeType.ADMIN_TO,
            "HasSession": EdgeType.HAS_SESSION,
            "CanRDP": EdgeType.CAN_RDP,
            "CanPSRemote": EdgeType.CAN_PS_REMOTE,
            "AllowedToDelegate": EdgeType.ALLOWED_TO_DELEGATE,
            "AllowedToAct": EdgeType.ALLOWED_TO_ACT,
            "TrustedBy": EdgeType.TRUSTED_BY,
            "Contains": EdgeType.CONTAINS,
        }
        return mapping.get(key, EdgeType.UNKNOWN)
    
    def _mark_high_value(self, node: Node) -> None:
        """Mark high-value targets based on name and properties."""
        name_upper = node.name.upper()
        
        # Domain Controllers
        if node.node_type == NodeType.COMPUTER:
            if any(dc in name_upper for dc in ["DC01", "DC02", "DOMAIN CONTROLLER", "DC-"]):
                node.is_domain_controller = True
                node.is_tier_zero = True
        
        # High-value groups and users
        if "DOMAIN ADMIN" in name_upper:
            node.is_domain_admin = True
            node.is_tier_zero = True
        
        if "ENTERPRISE ADMIN" in name_upper:
            node.is_enterprise_admin = True
            node.is_tier_zero = True
        
        if node.node_type == NodeType.GROUP:
            hvgs = [
                "ADMINISTRATORS",
                "SCHEMA ADMINS",
                "ACCOUNT OPERATORS",
                "BACKUP OPERATORS",
                "SERVER OPERATORS",
                "PRINT OPERATORS"
            ]
            if any(hvg in name_upper for hvg in hvgs):
                node.is_tier_zero = True
        
        # Admin count flag
        if node.admin_count:
            node.is_tier_zero = True
