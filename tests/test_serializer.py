"""
AutoHound � Attack Path Intelligence Engine
Copyright (c) 2026 Gordon Prescott. All rights reserved.

ACH Research Division
Unauthorized copying, distribution, or modification of this software
without explicit written permission from Gordon Prescott is prohibited.

This tool is intended exclusively for authorized security research 
and penetration testing engagements with written scope of work.
"""
"""Tests for graph serializer."""

import pytest
from autohound.models import Graph, Node, Edge, NodeType, EdgeType
from autohound.serializer import GraphSerializer


@pytest.fixture
def sample_graph():
    """Create a sample graph for testing."""
    graph = Graph()
    
    # Create nodes
    da_group = Node(
        id="DA-001",
        name="Domain Admins@test.local",
        node_type=NodeType.GROUP
    )
    da_group.is_domain_admin = True
    da_group.is_tier_zero = True
    
    user = Node(
        id="USER-001",
        name="lowpriv@test.local",
        node_type=NodeType.USER,
        enabled=True
    )
    
    admin_user = Node(
        id="USER-002",
        name="admin@test.local",
        node_type=NodeType.USER,
        enabled=True
    )
    
    graph.add_node(da_group)
    graph.add_node(user)
    graph.add_node(admin_user)
    
    # Create edges
    edge1 = Edge(
        source_id="USER-002",
        target_id="DA-001",
        edge_type=EdgeType.MEMBER_OF
    )
    
    edge2 = Edge(
        source_id="USER-001",
        target_id="USER-002",
        edge_type=EdgeType.FORCE_CHANGE_PASSWORD
    )
    
    graph.add_edge(edge1)
    graph.add_edge(edge2)
    
    return graph


def test_serializer_summary(sample_graph):
    """Test summary generation."""
    serializer = GraphSerializer(sample_graph)
    text = serializer.serialize_to_text()
    
    assert "Active Directory Environment Summary" in text
    assert "3" in text  # Node count
    assert "High-Value Targets" in text
    assert "Domain Admins" in text


def test_serializer_json(sample_graph):
    """Test JSON serialization."""
    serializer = GraphSerializer(sample_graph)
    json_str = serializer.serialize_to_json()
    
    assert "nodes" in json_str
    assert "edges" in json_str
    assert "high_value_targets" in json_str
    assert "Domain Admins" in json_str


def test_chunking(sample_graph):
    """Test chunk creation."""
    serializer = GraphSerializer(sample_graph, max_chunk_size=500)
    chunks = serializer.create_chunks()
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)

def test_serializer_include_all_nodes():
    graph = Graph()
    for i in range(5):
        graph.add_node(Node(id=f"n{i}", name=f"Node{i}", node_type=NodeType.USER))
    
    serializer = GraphSerializer(graph)
    text = serializer.serialize_to_text(include_all_nodes=True)
    assert "All Nodes" in text


def test_serializer_no_hvt():
    graph = Graph()
    graph.add_node(Node(id="n1", name="NormalUser", node_type=NodeType.USER))
    
    serializer = GraphSerializer(graph)
    text = serializer.serialize_to_text()
    assert "No high-value targets identified" in text


def test_serializer_attack_surface():
    graph = Graph()
    comp = Node(id="c1", name="Server1", node_type=NodeType.COMPUTER, properties={"unconstrained_delegation": True})
    graph.add_node(comp)
    user = Node(id="u1", name="User1", node_type=NodeType.USER)
    graph.add_node(user)
    from autohound.models import Edge
    graph.add_edge(Edge(source_id="u1", target_id="c1", edge_type=EdgeType.HAS_SESSION))
    
    serializer = GraphSerializer(graph)
    text = serializer.serialize_to_text()
    assert "Unconstrained Delegation" in text or "Active Sessions" in text


def test_init_version():
    import autohound
    assert hasattr(autohound, '__version__')
    assert isinstance(autohound.__version__, str)
