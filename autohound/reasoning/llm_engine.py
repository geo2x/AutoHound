# AutoHound © 2026 Gordon Prescott

"""
LLM reasoning engine using Claude API.

Implements multi-pass reasoning: discovery pass to find paths, validation pass
to verify logic and generate commands.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from autohound.models import AttackPath, AttackStep, EdgeType

logger = logging.getLogger(__name__)


class LLMEngine:
    """LLM-powered attack path reasoning engine."""
    
    DISCOVERY_SYSTEM_PROMPT = """You are an expert red team operator analyzing Active Directory environments.

Your task is to identify novel, high-value attack paths from the BloodHound data provided.

FOCUS ON:
1. Multi-hop paths that combine unusual ACL misconfigurations
2. Paths through GPOs, OUs, and delegation that standard queries miss
3. Shadow admin chains (indirect control through Write permissions)
4. Kerberos delegation abuse opportunities
5. Cross-trust attack paths

PRIORITIZE:
- Impact: Paths leading to Domain Admin, Enterprise Admin, or DC compromise
- Stealth: Techniques less likely to trigger common detections
- Feasibility: Realistic paths an operator could execute

OUTPUT FORMAT:
Return a JSON array of attack paths. Each path must include:
{
  "path_id": "unique_id",
  "name": "Brief descriptive name",
  "description": "2-3 sentence explanation of the path",
  "start_node": "Starting object name",
  "end_node": "Target object name",
  "impact_score": 0-100,
  "stealth_score": 0-100,
  "complexity_score": 0-100,
  "steps": [
    {
      "sequence": 1,
      "source_node": "Source object",
      "target_node": "Target object",
      "technique": "What to do",
      "edge_type": "MemberOf|AdminTo|GenericAll|etc"
    }
  ]
}

Be creative. Look for paths that require 3-5 hops through unexpected objects."""
    
    VALIDATION_SYSTEM_PROMPT = """You are an expert red team operator validating and enriching attack paths.

Your task is to take the attack path and:
1. Verify the logical consistency of each step
2. Generate exact, executable commands for each step
3. Map each technique to MITRE ATT&CK
4. Provide detection guidance (Windows Event IDs, Sigma rules)
5. Suggest remediation

COMMAND GENERATION RULES:
- PowerView for AD enumeration
- Impacket for remote exploitation
- Rubeus for Kerberos attacks
- BloodHound custom Cypher queries
- Include expected output and failure conditions

DETECTION GUIDANCE:
- List specific Windows Event IDs
- Provide Sigma rule stub or reference
- Note SIEM query recommendations

REMEDIATION:
- ACL fixes
- Configuration hardening
- Monitoring recommendations

Return the enriched path in the same JSON format with added fields:
- commands: array of command strings per step
- attack_tactic, attack_technique_id, attack_technique_name per step
- event_ids, sigma_rule, detection_notes per step
- remediation per step"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize LLM engine.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
        
        self.model = model
        self.client = Anthropic(api_key=self.api_key)
        logger.info(f"Initialized LLM engine with model: {model}")
    
    def discover_paths(self, graph_description: str) -> List[AttackPath]:
        """
        Discovery pass: identify attack paths from graph description.
        
        Args:
            graph_description: Serialized graph text
        
        Returns:
            List of discovered attack paths
        """
        logger.info("Starting attack path discovery pass...")
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,  # Some creativity, but not too random
                system=self.DISCOVERY_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"Analyze this Active Directory environment and identify attack paths:\n\n{graph_description}"
                    }
                ]
            )
            
            # Extract JSON from response
            response_text = response.content[0].text
            logger.debug(f"LLM discovery response: {response_text[:500]}...")
            
            # Parse JSON
            paths_data = self._extract_json(response_text)
            
            if not paths_data:
                logger.warning("No attack paths discovered")
                return []
            
            # Convert to AttackPath objects
            paths = self._parse_attack_paths(paths_data)
            logger.info(f"Discovered {len(paths)} attack paths")
            
            return paths
            
        except Exception as e:
            logger.error(f"Error during discovery pass: {e}")
            raise
    
    def enrich_path(self, path: AttackPath, graph_description: str) -> AttackPath:
        """
        Validation/enrichment pass: add commands, ATT&CK mapping, detection.
        
        Args:
            path: Attack path from discovery
            graph_description: Original graph for context
        
        Returns:
            Enriched attack path with commands and defensive guidance
        """
        logger.info(f"Enriching path: {path.name}")
        
        # Serialize path to JSON for LLM
        path_json = self._path_to_json(path)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,  # No creativity, exact commands needed
                system=self.VALIDATION_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Enrich this attack path with commands, ATT&CK mapping, and detection guidance:

Attack Path:
{path_json}

Graph Context (for reference):
{graph_description[:5000]}"""
                    }
                ]
            )
            
            response_text = response.content[0].text
            logger.debug(f"LLM enrichment response: {response_text[:500]}...")
            
            # Parse enriched path
            enriched_data = self._extract_json(response_text)
            
            if enriched_data:
                enriched_path = self._parse_attack_paths([enriched_data])[0]
                # Recalculate overall score
                enriched_path.calculate_overall_score()
                return enriched_path
            else:
                logger.warning("Failed to parse enriched path, returning original")
                return path
                
        except Exception as e:
            logger.error(f"Error during enrichment pass: {e}")
            return path  # Return original if enrichment fails
    
    def analyze(self, graph_description: str) -> List[AttackPath]:
        """
        Complete analysis: discovery + enrichment.
        
        Args:
            graph_description: Serialized graph text
        
        Returns:
            List of fully enriched attack paths
        """
        # Discovery pass
        discovered_paths = self.discover_paths(graph_description)
        
        if not discovered_paths:
            logger.warning("No paths discovered, analysis complete")
            return []
        
        # Enrichment pass for each path
        enriched_paths = []
        for path in discovered_paths:
            try:
                enriched = self.enrich_path(path, graph_description)
                enriched_paths.append(enriched)
            except Exception as e:
                logger.error(f"Failed to enrich path {path.name}: {e}")
                # Include original path even if enrichment fails
                enriched_paths.append(path)
        
        # Sort by overall score
        enriched_paths.sort(key=lambda p: p.overall_score, reverse=True)
        
        logger.info(f"Analysis complete: {len(enriched_paths)} paths identified and enriched")
        return enriched_paths
    
    def _extract_json(self, text: str) -> Optional[Any]:
        """Extract JSON from LLM response (handles markdown code blocks)."""
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Look for JSON in markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_text = text[start:end].strip()
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass
        
        # Look for JSON array or object
        for start_char in ['{', '[']:
            if start_char in text:
                start = text.find(start_char)
                # Find matching end
                try:
                    json_text = text[start:]
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass
        
        logger.error("Failed to extract JSON from LLM response")
        return None
    
    def _parse_attack_paths(self, paths_data: Any) -> List[AttackPath]:
        """Parse JSON data into AttackPath objects."""
        if isinstance(paths_data, dict):
            paths_data = [paths_data]
        
        if not isinstance(paths_data, list):
            logger.error(f"Expected list of paths, got {type(paths_data)}")
            return []
        
        paths = []
        for path_dict in paths_data:
            try:
                path = AttackPath(
                    path_id=path_dict.get("path_id", "unknown"),
                    name=path_dict.get("name", "Unnamed Path"),
                    description=path_dict.get("description", ""),
                    start_node=path_dict.get("start_node"),
                    end_node=path_dict.get("end_node"),
                    impact_score=float(path_dict.get("impact_score", 0)),
                    stealth_score=float(path_dict.get("stealth_score", 0)),
                    complexity_score=float(path_dict.get("complexity_score", 0)),
                    prerequisites=path_dict.get("prerequisites", []),
                    notes=path_dict.get("notes"),
                )
                
                # Parse steps
                for step_dict in path_dict.get("steps", []):
                    step = AttackStep(
                        sequence=step_dict.get("sequence", 0),
                        source_node=step_dict.get("source_node", ""),
                        target_node=step_dict.get("target_node", ""),
                        technique=step_dict.get("technique", ""),
                        edge_type=self._parse_edge_type(step_dict.get("edge_type", "")),
                        commands=step_dict.get("commands", []),
                        attack_tactic=step_dict.get("attack_tactic"),
                        attack_technique_id=step_dict.get("attack_technique_id"),
                        attack_technique_name=step_dict.get("attack_technique_name"),
                        event_ids=step_dict.get("event_ids", []),
                        sigma_rule=step_dict.get("sigma_rule"),
                        detection_notes=step_dict.get("detection_notes"),
                        remediation=step_dict.get("remediation"),
                    )
                    path.steps.append(step)
                
                path.calculate_overall_score()
                paths.append(path)
                
            except Exception as e:
                logger.error(f"Failed to parse attack path: {e}")
                continue
        
        return paths
    
    def _parse_edge_type(self, edge_str: str) -> EdgeType:
        """Parse edge type string to enum."""
        try:
            return EdgeType(edge_str)
        except ValueError:
            # Try to match by name
            for et in EdgeType:
                if et.value.lower() == edge_str.lower():
                    return et
            return EdgeType.UNKNOWN
    
    def _path_to_json(self, path: AttackPath) -> str:
        """Convert AttackPath to JSON string."""
        path_dict = {
            "path_id": path.path_id,
            "name": path.name,
            "description": path.description,
            "start_node": path.start_node,
            "end_node": path.end_node,
            "impact_score": path.impact_score,
            "stealth_score": path.stealth_score,
            "complexity_score": path.complexity_score,
            "steps": [
                {
                    "sequence": step.sequence,
                    "source_node": step.source_node,
                    "target_node": step.target_node,
                    "technique": step.technique,
                    "edge_type": step.edge_type.value,
                }
                for step in path.steps
            ]
        }
        return json.dumps(path_dict, indent=2)
