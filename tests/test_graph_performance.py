# AutoHound © 2026 Gordon Prescott

"""Performance tests for Graph adjacency index."""

import time
import pytest

from autohound.models import Graph, Node, Edge, NodeType, EdgeType


def test_graph_adjacency_performance():
    """Test that adjacency index makes lookups fast."""
    graph = Graph()
    
    # Create 1000 nodes
    for i in range(1000):
        graph.add_node(Node(
            id=f"node_{i}",
            name=f"Node {i}",
            node_type=NodeType.USER
        ))
    
    # Create 10,000 edges (average 10 edges per node)
    for i in range(10000):
        source_id = f"node_{i % 1000}"
        target_id = f"node_{(i + 1) % 1000}"
        
        graph.add_edge(Edge(
            source_id=source_id,
            target_id=target_id,
            edge_type=EdgeType.MEMBER_OF
        ))
    
    # Test outbound edge lookup performance
    start = time.perf_counter()
    
    for i in range(100):
        node_id = f"node_{i}"
        outbound = graph.get_outbound_edges(node_id)
        assert isinstance(outbound, list)
    
    elapsed = time.perf_counter() - start
    avg_time_ms = (elapsed / 100) * 1000
    
    # Should complete in under 10ms per lookup on average
    assert avg_time_ms < 10, f"Lookup too slow: {avg_time_ms:.2f}ms"
    
    # Test inbound edge lookup performance
    start = time.perf_counter()
    
    for i in range(100):
        node_id = f"node_{i}"
        inbound = graph.get_inbound_edges(node_id)
        assert isinstance(inbound, list)
    
    elapsed = time.perf_counter() - start
    avg_time_ms = (elapsed / 100) * 1000
    
    assert avg_time_ms < 10, f"Lookup too slow: {avg_time_ms:.2f}ms"


def test_graph_adjacency_correctness():
    """Test that adjacency index returns correct results."""
    graph = Graph()
    
    # Create nodes
    for i in range(5):
        graph.add_node(Node(
            id=f"node_{i}",
            name=f"Node {i}",
            node_type=NodeType.USER
        ))
    
    # Create specific edges
    # node_0 -> node_1, node_2
    # node_1 -> node_2, node_3
    # node_2 -> node_3, node_4
    
    graph.add_edge(Edge("node_0", "node_1", EdgeType.MEMBER_OF))
    graph.add_edge(Edge("node_0", "node_2", EdgeType.MEMBER_OF))
    graph.add_edge(Edge("node_1", "node_2", EdgeType.ADMIN_TO))
    graph.add_edge(Edge("node_1", "node_3", EdgeType.ADMIN_TO))
    graph.add_edge(Edge("node_2", "node_3", EdgeType.HAS_SESSION))
    graph.add_edge(Edge("node_2", "node_4", EdgeType.HAS_SESSION))
    
    # Test outbound from node_0
    outbound_0 = graph.get_outbound_edges("node_0")
    assert len(outbound_0) == 2
    assert all(e.source_id == "node_0" for e in outbound_0)
    assert set(e.target_id for e in outbound_0) == {"node_1", "node_2"}
    
    # Test inbound to node_3
    inbound_3 = graph.get_inbound_edges("node_3")
    assert len(inbound_3) == 2
    assert all(e.target_id == "node_3" for e in inbound_3)
    assert set(e.source_id for e in inbound_3) == {"node_1", "node_2"}
    
    # Test node with no edges
    outbound_4 = graph.get_outbound_edges("node_4")
    assert len(outbound_4) == 0
    
    inbound_0 = graph.get_inbound_edges("node_0")
    assert len(inbound_0) == 0
