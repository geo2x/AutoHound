# AutoHound © 2026 Gordon Prescott

"""Tests for LLM engine functionality."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from autohound.reasoning.llm_engine import LLMEngine
from autohound.models import AttackPath, AttackStep, EdgeType


class TestLLMEngine:
    """Test LLM engine functionality."""
    
    @pytest.fixture
    def mock_anthropic(self):
        """Mock Anthropic client."""
        with patch('autohound.reasoning.llm_engine.Anthropic') as mock:
            client = Mock()
            mock.return_value = client
            
            # Mock model detection
            models_data = Mock()
            models_data.data = [Mock(id='claude-3-5-sonnet-20241022')]
            client.models.list.return_value = models_data
            
            yield client
    
    def test_extract_json_raw(self, mock_anthropic):
        """Test extracting raw JSON."""
        engine = LLMEngine(api_key="test-key")
        
        raw_json = '{"path_id": "test", "name": "Test Path"}'
        result = engine._extract_json(raw_json)
        
        assert result is not None
        assert result["path_id"] == "test"
        assert result["name"] == "Test Path"
    
    def test_extract_json_code_block(self, mock_anthropic):
        """Test extracting JSON from markdown code block."""
        engine = LLMEngine(api_key="test-key")
        
        text = '''Here is the result:
```json
{"path_id": "test", "name": "Test Path"}
```
'''
        result = engine._extract_json(text)
        
        assert result is not None
        assert result["path_id"] == "test"
    
    def test_extract_json_embedded(self, mock_anthropic):
        """Test extracting JSON embedded in prose."""
        engine = LLMEngine(api_key="test-key")
        
        text = 'The analysis shows: {"path_id": "test", "name": "Test Path"} as the result.'
        result = engine._extract_json(text)
        
        assert result is not None
        assert result["path_id"] == "test"
    
    def test_extract_json_garbage(self, mock_anthropic):
        """Test handling garbage text with no JSON."""
        engine = LLMEngine(api_key="test-key")
        
        text = "This is just plain text with no JSON at all."
        result = engine._extract_json(text)
        
        assert result is None
    
    def test_parse_edge_type_valid(self, mock_anthropic):
        """Test parsing valid edge type."""
        engine = LLMEngine(api_key="test-key")
        
        assert engine._parse_edge_type("MemberOf") == EdgeType.MEMBER_OF
        assert engine._parse_edge_type("GenericAll") == EdgeType.GENERIC_ALL
    
    def test_parse_edge_type_invalid(self, mock_anthropic):
        """Test parsing invalid edge type."""
        engine = LLMEngine(api_key="test-key")
        
        result = engine._parse_edge_type("InvalidType")
        assert result == EdgeType.UNKNOWN
    
    def test_discover_paths_with_response(self, mock_anthropic):
        """Test discover_paths with valid LLM response."""
        engine = LLMEngine(api_key="test-key")
        
        # Mock LLM response
        response = Mock()
        response.content = [Mock(text=json.dumps([{
            "path_id": "path1",
            "name": "Test Attack Path",
            "description": "A test path",
            "start_node": "User1",
            "end_node": "Domain Admins",
            "impact_score": 90,
            "stealth_score": 70,
            "complexity_score": 50,
            "steps": [{
                "sequence": 1,
                "source_node": "User1",
                "target_node": "Domain Admins",
                "technique": "Add to group",
                "edge_type": "AddMember"
            }]
        }]))]
        
        mock_anthropic.messages.create.return_value = response
        
        paths = engine.discover_paths("Test graph description")
        
        assert len(paths) == 1
        assert paths[0].path_id == "path1"
        assert paths[0].name == "Test Attack Path"
        assert len(paths[0].steps) == 1
    
    def test_discover_paths_malformed_json(self, mock_anthropic):
        """Test discover_paths with malformed JSON."""
        engine = LLMEngine(api_key="test-key")
        
        # Mock LLM response with garbage
        response = Mock()
        response.content = [Mock(text="This is not JSON at all")]
        
        mock_anthropic.messages.create.return_value = response
        
        with pytest.raises(ValueError, match="LLM response did not contain valid JSON"):
            engine.discover_paths("Test graph description")
    
    def test_enrich_path(self, mock_anthropic):
        """Test enrich_path with valid enrichment."""
        engine = LLMEngine(api_key="test-key")
        
        # Create a basic path
        path = AttackPath(
            path_id="test1",
            name="Test Path",
            description="Test",
            steps=[AttackStep(
                sequence=1,
                source_node="User1",
                target_node="Admin",
                technique="Test",
                edge_type=EdgeType.MEMBER_OF
            )]
        )
        
        # Mock enrichment response
        enriched_data = {
            "path_id": "test1",
            "name": "Test Path",
            "description": "Test",
            "steps": [{
                "sequence": 1,
                "source_node": "User1",
                "target_node": "Admin",
                "technique": "Test",
                "edge_type": "MemberOf",
                "commands": ["net group 'Domain Admins' User1 /add"],
                "attack_technique_id": "T1098",
                "attack_technique_name": "Account Manipulation"
            }]
        }
        
        response = Mock()
        response.content = [Mock(text=json.dumps(enriched_data))]
        mock_anthropic.messages.create.return_value = response
        
        enriched = engine.enrich_path(path, "Graph context")
        
        assert len(enriched.steps[0].commands) == 1
        assert enriched.steps[0].attack_technique_id == "T1098"
    
    def test_truncate_context(self, mock_anthropic):
        """Test context truncation at newline boundary."""
        engine = LLMEngine(api_key="test-key")
        
        text = "Line 1\nLine 2\nLine 3\nLine 4"
        truncated = engine._truncate_context(text, 15)
        
        # Should truncate at newline before char 15
        assert truncated == "Line 1\nLine 2"
        assert len(truncated) < 15
