# AutoHound © 2026 Gordon Prescott

"""
Neo4j database ingestor for BloodHound data.

Connects to a local Neo4j instance populated by BloodHound CE and extracts
the complete AD graph through Cypher queries.
"""

import logging
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase, Driver, Session

from autohound.models import (
    Graph, Node, Edge, NodeType, EdgeType
)

logger = logging.getLogger(__name__)


class Neo4jIngestor:
    """Ingest BloodHound data from a Neo4j database."""
    
    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j connection URI (e.g., bolt://localhost:7687)
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[Driver] = None
    
    def connect(self) -> None:
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def ingest(self) -> Graph:
        """
        Ingest complete BloodHound graph from Neo4j.
        
        Returns:
            Graph object containing all nodes and edges
        """
        if not self.driver:
            self.connect()
        
        graph = Graph()
        
        with self.driver.session() as session:
            # Ingest nodes by type
            logger.info("Ingesting users...")
            self._ingest_users(session, graph)
            
            logger.info("Ingesting computers...")
            self._ingest_computers(session, graph)
            
            logger.info("Ingesting groups...")
            self._ingest_groups(session, graph)
            
            logger.info("Ingesting domains...")
            self._ingest_domains(session, graph)
            
            logger.info("Ingesting GPOs...")
            self._ingest_gpos(session, graph)
            
            logger.info("Ingesting OUs...")
            self._ingest_ous(session, graph)
            
            # Ingest relationships
            logger.info("Ingesting relationships...")
            self._ingest_relationships(session, graph)
        
        logger.info(f"Ingestion complete: {graph.node_count()} nodes, {graph.edge_count()} edges")
        return graph
    
    def _ingest_users(self, session: Session, graph: Graph) -> None:
        """Ingest User nodes."""
        query = """
        MATCH (u:User)
        RETURN u.objectid AS id,
               u.name AS name,
               u.enabled AS enabled,
               u.admincount AS admincount,
               u.domain AS domain,
               u.distinguishedname AS dn,
               labels(u) AS labels
        """
        result = session.run(query)
        
        for record in result:
            node = Node(
                id=record["id"],
                name=record["name"],
                node_type=NodeType.USER,
                enabled=record.get("enabled"),
                admin_count=record.get("admincount"),
                domain=record.get("domain"),
                distinguished_name=record.get("dn"),
            )
            
            # Check if high-value target
            labels = record.get("labels", [])
            if "Domain Admins" in str(record["name"]):
                node.is_domain_admin = True
                node.is_tier_zero = True
            
            graph.add_node(node)
    
    def _ingest_computers(self, session: Session, graph: Graph) -> None:
        """Ingest Computer nodes."""
        query = """
        MATCH (c:Computer)
        RETURN c.objectid AS id,
               c.name AS name,
               c.enabled AS enabled,
               c.domain AS domain,
               c.distinguishedname AS dn,
               c.unconstraineddelegation AS unconstrained,
               labels(c) AS labels
        """
        result = session.run(query)
        
        for record in result:
            node = Node(
                id=record["id"],
                name=record["name"],
                node_type=NodeType.COMPUTER,
                enabled=record.get("enabled"),
                domain=record.get("domain"),
                distinguished_name=record.get("dn"),
                properties={"unconstrained_delegation": record.get("unconstrained", False)}
            )
            
            # Check if Domain Controller
            name = record["name"].upper()
            if "DC" in name or "DOMAIN" in name:
                node.is_domain_controller = True
                node.is_tier_zero = True
            
            graph.add_node(node)
    
    def _ingest_groups(self, session: Session, graph: Graph) -> None:
        """Ingest Group nodes."""
        query = """
        MATCH (g:Group)
        RETURN g.objectid AS id,
               g.name AS name,
               g.admincount AS admincount,
               g.domain AS domain,
               g.distinguishedname AS dn
        """
        result = session.run(query)
        
        for record in result:
            node = Node(
                id=record["id"],
                name=record["name"],
                node_type=NodeType.GROUP,
                admin_count=record.get("admincount"),
                domain=record.get("domain"),
                distinguished_name=record.get("dn"),
            )
            
            # High-value groups
            name = record["name"].upper()
            if "DOMAIN ADMINS" in name:
                node.is_domain_admin = True
                node.is_tier_zero = True
            elif "ENTERPRISE ADMINS" in name:
                node.is_enterprise_admin = True
                node.is_tier_zero = True
            elif any(hvg in name for hvg in ["ADMINISTRATORS", "SCHEMA ADMINS", "ACCOUNT OPERATORS"]):
                node.is_tier_zero = True
            
            graph.add_node(node)
    
    def _ingest_domains(self, session: Session, graph: Graph) -> None:
        """Ingest Domain nodes."""
        query = """
        MATCH (d:Domain)
        RETURN d.objectid AS id,
               d.name AS name,
               d.distinguishedname AS dn
        """
        result = session.run(query)
        
        for record in result:
            node = Node(
                id=record["id"],
                name=record["name"],
                node_type=NodeType.DOMAIN,
                distinguished_name=record.get("dn"),
            )
            node.is_tier_zero = True
            graph.add_node(node)
    
    def _ingest_gpos(self, session: Session, graph: Graph) -> None:
        """Ingest GPO nodes."""
        query = """
        MATCH (g:GPO)
        RETURN g.objectid AS id,
               g.name AS name,
               g.domain AS domain,
               g.distinguishedname AS dn
        """
        result = session.run(query)
        
        for record in result:
            node = Node(
                id=record["id"],
                name=record["name"],
                node_type=NodeType.GPO,
                domain=record.get("domain"),
                distinguished_name=record.get("dn"),
            )
            graph.add_node(node)
    
    def _ingest_ous(self, session: Session, graph: Graph) -> None:
        """Ingest OU nodes."""
        query = """
        MATCH (o:OU)
        RETURN o.objectid AS id,
               o.name AS name,
               o.domain AS domain,
               o.distinguishedname AS dn
        """
        result = session.run(query)
        
        for record in result:
            node = Node(
                id=record["id"],
                name=record["name"],
                node_type=NodeType.OU,
                domain=record.get("domain"),
                distinguished_name=record.get("dn"),
            )
            graph.add_node(node)
    
    def _ingest_relationships(self, session: Session, graph: Graph) -> None:
        """Ingest all relationship types."""
        # Get all relationship types
        query = """
        MATCH ()-[r]->()
        RETURN DISTINCT type(r) AS rel_type
        """
        result = session.run(query)
        rel_types = [record["rel_type"] for record in result]
        
        logger.info(f"Found {len(rel_types)} relationship types: {rel_types}")
        
        # Ingest each relationship type
        for rel_type in rel_types:
            self._ingest_relationship_type(session, graph, rel_type)
    
    def _ingest_relationship_type(self, session: Session, graph: Graph, rel_type: str) -> None:
        """Ingest a specific relationship type."""
        query = f"""
        MATCH (source)-[r:{rel_type}]->(target)
        RETURN source.objectid AS source_id,
               target.objectid AS target_id,
               type(r) AS edge_type,
               properties(r) AS props
        LIMIT 10000
        """
        
        result = session.run(query)
        count = 0
        
        for record in result:
            # Map BloodHound edge type to our enum
            edge_type = self._map_edge_type(record["edge_type"])
            
            edge = Edge(
                source_id=record["source_id"],
                target_id=record["target_id"],
                edge_type=edge_type,
                properties=record.get("props", {})
            )
            graph.add_edge(edge)
            count += 1
        
        logger.debug(f"Ingested {count} {rel_type} edges")
    
    def _map_edge_type(self, neo4j_type: str) -> EdgeType:
        """Map Neo4j relationship type to EdgeType enum."""
        mapping = {
            "MemberOf": EdgeType.MEMBER_OF,
            "AdminTo": EdgeType.ADMIN_TO,
            "HasSession": EdgeType.HAS_SESSION,
            "CanRDP": EdgeType.CAN_RDP,
            "CanPSRemote": EdgeType.CAN_PS_REMOTE,
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
            "GpLink": EdgeType.GPO_APPLY,
            "AllowedToDelegate": EdgeType.ALLOWED_TO_DELEGATE,
            "AllowedToAct": EdgeType.ALLOWED_TO_ACT,
            "Contains": EdgeType.CONTAINS,
            "TrustedBy": EdgeType.TRUSTED_BY,
        }
        
        return mapping.get(neo4j_type, EdgeType.UNKNOWN)
    
    def __enter__(self) -> "Neo4jIngestor":
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
