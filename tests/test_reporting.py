# AutoHound © 2026 Gordon Prescott

"""Tests for reporting functionality."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from autohound.reporting.markdown_report import MarkdownReportGenerator
from autohound.reporting.attack_navigator import AttackNavigatorGenerator
from autohound.models import Graph, Node, NodeType, AttackPath, AttackStep, EdgeType


@pytest.fixture
def sample_graph():
    """Create a sample graph for testing."""
    graph = Graph()
    
    # Add some nodes
    graph.add_node(Node(
        id="user1",
        name="testuser@domain.local",
        node_type=NodeType.USER,
        enabled=True
    ))
    
    graph.add_node(Node(
        id="da_group",
        name="Domain Admins@domain.local",
        node_type=NodeType.GROUP,
        is_domain_admin=True,
        is_tier_zero=True
    ))
    
    return graph


@pytest.fixture
def sample_paths():
    """Create sample attack paths for testing."""
    path = AttackPath(
        path_id="test_path_1",
        name="Test Attack Path",
        description="A test attack path for unit testing",
        start_node="testuser@domain.local",
        end_node="Domain Admins@domain.local",
        impact_score=85.0,
        stealth_score=60.0,
        complexity_score=40.0
    )
    
    step = AttackStep(
        sequence=1,
        source_node="testuser@domain.local",
        target_node="Domain Admins@domain.local",
        technique="Add user to privileged group",
        edge_type=EdgeType.ADD_MEMBER,
        commands=["net group 'Domain Admins' testuser /add /domain"],
        attack_technique_id="T1098",
        attack_technique_name="Account Manipulation",
        attack_tactic="Persistence",
        event_ids=["4728", "4732"],
        detection_notes="Monitor group membership changes"
    )
    
    path.steps.append(step)
    path.calculate_overall_score()
    
    return [path]


def test_markdown_report_generation(sample_graph, sample_paths):
    """Test that markdown report generates and contains expected sections."""
    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.md"
        
        generator = MarkdownReportGenerator(sample_graph, sample_paths)
        generator.generate(output_path)
        
        assert output_path.exists()
        
        content = output_path.read_text(encoding='utf-8')
        
        # Check for expected sections
        assert "# AutoHound - Attack Path Analysis Report" in content
        assert "## Executive Summary" in content
        assert "## Environment Overview" in content
        assert "## Attack Paths" in content
        assert "## Recommendations" in content
        
        # Check for path details
        assert "Test Attack Path" in content
        assert "T1098" in content


def test_markdown_report_no_paths(sample_graph):
    """Test markdown report generation with no paths."""
    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.md"
        
        generator = MarkdownReportGenerator(sample_graph, [])
        generator.generate(output_path)
        
        assert output_path.exists()
        
        content = output_path.read_text(encoding='utf-8')
        assert "No exploitable attack paths were identified" in content


def test_attack_navigator_generation(sample_paths):
    """Test ATT&CK Navigator layer generation."""
    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "navigator.json"
        
        generator = AttackNavigatorGenerator(sample_paths)
        generator.generate(output_path)
        
        assert output_path.exists()
        
        # Parse and validate JSON
        with open(output_path, 'r', encoding='utf-8') as f:
            layer = json.load(f)
        
        # Check structure
        assert "name" in layer
        assert "versions" in layer
        assert "domain" in layer
        assert "techniques" in layer
        
        # Check that our technique is present
        techniques = layer["techniques"]
        assert len(techniques) > 0
        assert any(t["techniqueID"] == "T1098" for t in techniques)


def test_attack_navigator_empty_paths():
    """Test ATT&CK Navigator with no paths."""
    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "navigator.json"
        
        generator = AttackNavigatorGenerator([])
        generator.generate(output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            layer = json.load(f)
        
        # Should still be valid JSON with structure
        assert "techniques" in layer
        assert len(layer["techniques"]) == 0
