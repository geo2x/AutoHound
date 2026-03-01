"""
AutoHound � Attack Path Intelligence Engine
Copyright (c) 2026 Gordon Prescott. All rights reserved.

ACH Research Division
Unauthorized copying, distribution, or modification of this software
without explicit written permission from Gordon Prescott is prohibited.

This tool is intended exclusively for authorized security research 
and penetration testing engagements with written scope of work.
"""
"""Tests for data models."""

import pytest
from autohound.models import (
    Node, Edge, Graph, NodeType, EdgeType, AttackPath, AttackStep
)


def test_node_creation():
    """Test Node creation and properties."""
    node = Node(
        id="S-1-5-21-123",
        name="TestUser",
        node_type=NodeType.USER,
        enabled=True,
        domain="test.local"
    )
    
    assert node.id == "S-1-5-21-123"
    assert node.name == "TestUser"
    assert node.node_type == NodeType.USER
    assert node.enabled is True
    assert not node.is_domain_admin


def test_node_equality():
    """Test node equality based on ID."""
    node1 = Node(id="123", name="User1", node_type=NodeType.USER)
    node2 = Node(id="123", name="User2", node_type=NodeType.USER)
    node3 = Node(id="456", name="User1", node_type=NodeType.USER)
    
    assert node1 == node2  # Same ID
    assert node1 != node3  # Different ID


def test_graph_operations():
    """Test Graph add/get operations."""
    graph = Graph()
    
    node1 = Node(id="1", name="User1", node_type=NodeType.USER)
    node2 = Node(id="2", name="Computer1", node_type=NodeType.COMPUTER)
    
    graph.add_node(node1)
    graph.add_node(node2)
    
    assert graph.node_count() == 2
    assert graph.get_node("1") == node1
    
    edge = Edge(source_id="1", target_id="2", edge_type=EdgeType.ADMIN_TO)
    graph.add_edge(edge)
    
    assert graph.edge_count() == 1
    assert len(graph.get_outbound_edges("1")) == 1
    assert len(graph.get_inbound_edges("2")) == 1


def test_high_value_nodes():
    """Test high-value target identification."""
    graph = Graph()
    
    normal_user = Node(id="1", name="User1", node_type=NodeType.USER)
    da_user = Node(id="2", name="AdminUser", node_type=NodeType.USER)
    da_user.is_domain_admin = True
    da_user.is_tier_zero = True
    
    graph.add_node(normal_user)
    graph.add_node(da_user)
    
    hvt = graph.get_high_value_nodes()
    assert len(hvt) == 1
    assert hvt[0].id == "2"


def test_attack_path_scoring():
    """Test attack path score calculation."""
    path = AttackPath(
        path_id="test1",
        name="Test Path",
        description="Test",
        impact_score=80.0,
        stealth_score=60.0,
        complexity_score=40.0
    )
    
    path.calculate_overall_score()
    
    # Expected: 80*0.4 + 60*0.35 + 40*0.25 = 32 + 21 + 10 = 63
    assert abs(path.overall_score - 63.0) < 0.1


def test_attack_step_creation():
    """Test AttackStep creation."""
    step = AttackStep(
        sequence=1,
        source_node="User1",
        target_node="AdminGroup",
        technique="Add member to group",
        edge_type=EdgeType.ADD_MEMBER,
        commands=["Add-ADGroupMember -Identity AdminGroup -Members User1"],
        attack_technique_id="T1098"
    )
    
    assert step.sequence == 1
    assert step.edge_type == EdgeType.ADD_MEMBER
    assert len(step.commands) == 1
