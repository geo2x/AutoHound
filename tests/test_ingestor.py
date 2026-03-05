"""
AutoHound � Attack Path Intelligence Engine
Copyright (c) 2026 Gordon Prescott. All rights reserved.

ACH Research Division
Unauthorized copying, distribution, or modification of this software
without explicit written permission from Gordon Prescott is prohibited.

This tool is intended exclusively for authorized security research 
and penetration testing engagements with written scope of work.
"""
"""Tests for data ingestors."""

import pytest
from pathlib import Path
from autohound.ingestor import JsonIngestor
from autohound.ingestor.neo4j_ingestor import Neo4jIngestor
from autohound.models import NodeType


def test_json_ingestor():
    """Test JSON file ingestion."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_bloodhound_data.json"
    
    if not fixture_path.exists():
        pytest.skip("Sample fixture not found")
    
    ingestor = JsonIngestor(fixture_path)
    graph = ingestor.ingest()
    
    assert graph.node_count() > 0
    
    # Verify high-value targets are identified
    hvt = graph.get_high_value_nodes()
    assert len(hvt) > 0
    
    # Check for Domain Admins group
    da_nodes = [n for n in graph.nodes.values() if "DOMAIN ADMINS" in n.name.upper()]
    assert len(da_nodes) > 0
    assert da_nodes[0].is_tier_zero


def test_json_ingestor_invalid_path():
    """Test ingestion with invalid path."""
    with pytest.raises(FileNotFoundError):
        ingestor = JsonIngestor("/nonexistent/path.json")
        ingestor.ingest()


def test_json_ingestor_modern_format():
    """Test modern BloodHound CE format parsing."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_bloodhound_data.json"
    
    if not fixture_path.exists():
        pytest.skip("Sample fixture not found")
    
    ingestor = JsonIngestor(fixture_path)
    graph = ingestor.ingest()
    
    # Should have users, computers, groups
    users = [n for n in graph.nodes.values() if n.node_type == NodeType.USER]
    computers = [n for n in graph.nodes.values() if n.node_type == NodeType.COMPUTER]
    groups = [n for n in graph.nodes.values() if n.node_type == NodeType.GROUP]
    
    assert len(users) >= 2
    assert len(computers) >= 2
    assert len(groups) >= 2


def test_neo4j_sanitize_rel_type():
    """Test Neo4j relationship type sanitization."""
    ingestor = Neo4jIngestor("bolt://localhost:7687", "neo4j", "password")
    
    # Valid relationship types
    assert ingestor._sanitize_rel_type("MemberOf") == "MemberOf"
    assert ingestor._sanitize_rel_type("GenericAll") == "GenericAll"
    assert ingestor._sanitize_rel_type("Valid_Type123") == "Valid_Type123"
    
    # Invalid relationship types should raise
    with pytest.raises(ValueError):
        ingestor._sanitize_rel_type("'; DROP TABLE edges; --")
    
    with pytest.raises(ValueError):
        ingestor._sanitize_rel_type("Invalid Type")
    
    with pytest.raises(ValueError):
        ingestor._sanitize_rel_type("123Invalid")
