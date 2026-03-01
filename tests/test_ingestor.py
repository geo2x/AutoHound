"""Tests for data ingestors."""

import pytest
from pathlib import Path
from bloodhound_ai.ingestor import JsonIngestor
from bloodhound_ai.models import NodeType


def test_json_ingestor():
    """Test JSON file ingestion."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_bloodhound.json"
    
    if not fixture_path.exists():
        pytest.skip("Sample fixture not found")
    
    ingestor = JsonIngestor(fixture_path)
    graph = ingestor.ingest()
    
    assert graph.node_count() > 0
    assert graph.edge_count() >= 0
    
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
