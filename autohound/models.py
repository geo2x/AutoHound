# AutoHound © 2026 Gordon Prescott

"""
Data models for AutoHound graph representation.

These models represent Active Directory objects and relationships extracted from BloodHound.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class NodeType(StrEnum):
    """Active Directory object types."""
    USER = "User"
    COMPUTER = "Computer"
    GROUP = "Group"
    DOMAIN = "Domain"
    GPO = "GPO"
    OU = "OU"
    CONTAINER = "Container"
    UNKNOWN = "Unknown"


class EdgeType(StrEnum):
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
    properties: dict[str, Any] = field(default_factory=dict)

    # Common properties that may be extracted
    enabled: bool | None = None
    admin_count: bool | None = None
    domain: str | None = None
    distinguished_name: str | None = None

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
    properties: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.source_id, self.target_id, self.edge_type))


@dataclass
class Graph:
    """Represents a complete Active Directory graph."""

    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Adjacency indices — populated on add_edge
    _outbound: dict[str, list[Edge]] = field(default_factory=lambda: defaultdict(list), repr=False)
    _inbound: dict[str, list[Edge]] = field(default_factory=lambda: defaultdict(list), repr=False)

    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
        self._outbound[edge.source_id].append(edge)
        self._inbound[edge.target_id].append(edge)

    def get_node(self, node_id: str) -> Node | None:
        """Retrieve a node by ID."""
        return self.nodes.get(node_id)

    def get_outbound_edges(self, node_id: str) -> list[Edge]:
        """Get all edges where this node is the source."""
        return self._outbound.get(node_id, [])

    def get_inbound_edges(self, node_id: str) -> list[Edge]:
        """Get all edges where this node is the target."""
        return self._inbound.get(node_id, [])

    def get_high_value_nodes(self) -> list[Node]:
        """Get all high-value target nodes."""
        return [
            n for n in self.nodes.values()
            if n.is_tier_zero or n.is_domain_admin or n.is_enterprise_admin
            or n.is_domain_controller
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
    commands: list[str] = field(default_factory=list)

    # ATT&CK Mapping
    attack_tactic: str | None = None
    attack_technique_id: str | None = None
    attack_technique_name: str | None = None

    # Detection
    event_ids: list[str] = field(default_factory=list)
    sigma_rule: str | None = None
    detection_notes: str | None = None

    # Remediation
    remediation: str | None = None


@dataclass
class AttackPath:
    """Represents a complete attack path from start to compromise."""

    path_id: str
    name: str
    description: str
    steps: list[AttackStep] = field(default_factory=list)

    # Scoring
    impact_score: float = 0.0  # 0-100
    stealth_score: float = 0.0  # 0-100
    complexity_score: float = 0.0  # 0-100
    overall_score: float = 0.0  # Weighted composite

    # Metadata
    start_node: str | None = None
    end_node: str | None = None
    prerequisites: list[str] = field(default_factory=list)
    notes: str | None = None

    def calculate_overall_score(self) -> None:
        """Calculate weighted composite score."""
        self.overall_score = (
            self.impact_score * 0.4 +
            self.stealth_score * 0.35 +
            self.complexity_score * 0.25
        )
