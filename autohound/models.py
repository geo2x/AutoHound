# AutoHound © 2026 Gordon Prescott

"""
Data models for AutoHound graph representation.

These models represent Active Directory objects and relationships extracted from BloodHound.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(str, Enum):
    """Active Directory object types."""
    USER = "User"
    COMPUTER = "Computer"
    GROUP = "Group"
    DOMAIN = "Domain"
    GPO = "GPO"
    OU = "OU"
    CONTAINER = "Container"
    UNKNOWN = "Unknown"


class EdgeType(str, Enum):
    """Active Directory relationship types."""
    # Group Membership
    MEMBER_OF = "MemberOf"
    
    # Local Admin Rights
    ADMIN_TO = "AdminTo"
    
    # Session Information
    HAS_SESSION = "HasSession"
    
    # RDP Rights
    CAN_RDP = "CanRDP"
    
    # PS Remoting
    CAN_PS_REMOTE = "CanPSRemote"
    
    # ACL-based edges
    GENERIC_ALL = "GenericAll"
    GENERIC_WRITE = "GenericWrite"
    WRITE_OWNER = "WriteOwner"
    WRITE_DACL = "WriteDacl"
    ADD_MEMBER = "AddMember"
    FORCE_CHANGE_PASSWORD = "ForceChangePassword"
    ADD_ALLOWED_TO_ACT = "AddAllowedToAct"
    
    # DCSync
    DCSYNC = "DCSync"
    GET_CHANGES = "GetChanges"
    GET_CHANGES_ALL = "GetChangesAll"
    
    # GPO
    GPO_APPLY = "GPOApply"
    
    # Kerberos
    ALLOWED_TO_DELEGATE = "AllowedToDelegate"
    ALLOWED_TO_ACT = "AllowedToAct"
    
    # Other
    CONTAINS = "Contains"
    TRUSTED_BY = "TrustedBy"
    UNKNOWN = "Unknown"


@dataclass
class Node:
    """Represents an Active Directory object."""
    
    id: str  # ObjectID or unique identifier
    name: str  # Display name
    node_type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Common properties that may be extracted
    enabled: Optional[bool] = None
    admin_count: Optional[bool] = None
    domain: Optional[str] = None
    distinguished_name: Optional[str] = None
    
    # High-value target markers
    is_domain_admin: bool = False
    is_enterprise_admin: bool = False
    is_domain_controller: bool = False
    is_tier_zero: bool = False
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return False
        return self.id == other.id


@dataclass
class Edge:
    """Represents a relationship between two AD objects."""
    
    source_id: str  # Source node ID
    target_id: str  # Target node ID
    edge_type: EdgeType
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        return hash((self.source_id, self.target_id, self.edge_type))


@dataclass
class Graph:
    """Represents a complete Active Directory graph."""
    
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
    
    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Retrieve a node by ID."""
        return self.nodes.get(node_id)
    
    def get_outbound_edges(self, node_id: str) -> List[Edge]:
        """Get all edges where this node is the source."""
        return [e for e in self.edges if e.source_id == node_id]
    
    def get_inbound_edges(self, node_id: str) -> List[Edge]:
        """Get all edges where this node is the target."""
        return [e for e in self.edges if e.target_id == node_id]
    
    def get_high_value_nodes(self) -> List[Node]:
        """Get all high-value target nodes."""
        return [
            n for n in self.nodes.values()
            if n.is_tier_zero or n.is_domain_admin or n.is_enterprise_admin or n.is_domain_controller
        ]
    
    def node_count(self) -> int:
        """Total number of nodes."""
        return len(self.nodes)
    
    def edge_count(self) -> int:
        """Total number of edges."""
        return len(self.edges)


@dataclass
class AttackStep:
    """Represents a single step in an attack path."""
    
    sequence: int  # Step number
    source_node: str  # Node name
    target_node: str  # Node name
    technique: str  # Attack technique description
    edge_type: EdgeType
    
    # Commands
    commands: List[str] = field(default_factory=list)
    
    # ATT&CK Mapping
    attack_tactic: Optional[str] = None
    attack_technique_id: Optional[str] = None
    attack_technique_name: Optional[str] = None
    
    # Detection
    event_ids: List[str] = field(default_factory=list)
    sigma_rule: Optional[str] = None
    detection_notes: Optional[str] = None
    
    # Remediation
    remediation: Optional[str] = None


@dataclass
class AttackPath:
    """Represents a complete attack path from start to compromise."""
    
    path_id: str
    name: str
    description: str
    steps: List[AttackStep] = field(default_factory=list)
    
    # Scoring
    impact_score: float = 0.0  # 0-100
    stealth_score: float = 0.0  # 0-100
    complexity_score: float = 0.0  # 0-100
    overall_score: float = 0.0  # Weighted composite
    
    # Metadata
    start_node: Optional[str] = None
    end_node: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def calculate_overall_score(self) -> None:
        """Calculate weighted composite score."""
        self.overall_score = (
            self.impact_score * 0.4 +
            self.stealth_score * 0.35 +
            self.complexity_score * 0.25
        )
