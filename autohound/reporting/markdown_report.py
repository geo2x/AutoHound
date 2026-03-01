# AutoHound © 2026 Gordon Prescott

"""
Markdown report generator for AutoHound analysis results.

Generates professional, GitHub-compatible reports with attack paths,
commands, ATT&CK mappings, and defensive guidance.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List

from autohound.models import AttackPath, Graph

logger = logging.getLogger(__name__)


class MarkdownReportGenerator:
    """Generate Markdown reports from attack path analysis."""
    
    def __init__(self, graph: Graph, attack_paths: List[AttackPath]):
        """
        Initialize report generator.
        
        Args:
            graph: The analyzed AD graph
            attack_paths: Discovered attack paths
        """
        self.graph = graph
        self.attack_paths = attack_paths
    
    def generate(self, output_path: Path) -> None:
        """
        Generate complete Markdown report.
        
        Args:
            output_path: File path for the report
        """
        logger.info(f"Generating report: {output_path}")
        
        sections = [
            self._generate_header(),
            self._generate_executive_summary(),
            self._generate_environment_overview(),
            self._generate_attack_paths(),
            self._generate_recommendations(),
            self._generate_appendix(),
        ]
        
        report = "\n\n".join(sections)
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Report generated: {output_path}")
    
    def _generate_header(self) -> str:
        """Generate report header."""
        return f"""# AutoHound - Attack Path Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Tool:** AutoHound v0.1  
**Classification:** TLP:WHITE - Authorized Research Only

---

**USAGE NOTICE:** This report contains attack paths identified in an Active Directory environment.
Use only in authorized lab environments or engagements with explicit written permission.

---
"""
    
    def _generate_executive_summary(self) -> str:
        """Generate executive summary."""
        if not self.attack_paths:
            return """## Executive Summary

No exploitable attack paths were identified in this environment.
"""
        
        # Get top path
        top_path = self.attack_paths[0] if self.attack_paths else None
        
        critical_paths = [p for p in self.attack_paths if p.impact_score >= 80]
        high_paths = [p for p in self.attack_paths if 60 <= p.impact_score < 80]
        
        summary = f"""## Executive Summary

AutoHound identified **{len(self.attack_paths)} attack path(s)** in the analyzed Active Directory environment.

### Key Findings

- **Critical Severity Paths:** {len(critical_paths)} (Impact Score ≥ 80)
- **High Severity Paths:** {len(high_paths)} (Impact Score 60-79)
- **Total Paths to Domain Admin:** {len([p for p in self.attack_paths if 'Domain Admin' in str(p.end_node)])}

### Highest Priority Path

**{top_path.name}** (Overall Score: {top_path.overall_score:.1f}/100)
- Impact: {top_path.impact_score:.1f}/100
- Stealth: {top_path.stealth_score:.1f}/100
- Complexity: {top_path.complexity_score:.1f}/100

{top_path.description}

### Recommended Actions

1. Review and remediate the critical paths identified in Section 3
2. Implement detection rules provided in Section 4
3. Conduct ACL audit focusing on GenericAll, WriteDacl, and WriteOwner permissions
4. Review Kerberos delegation settings on all computers
"""
        return summary
    
    def _generate_environment_overview(self) -> str:
        """Generate environment statistics."""
        hvt = self.graph.get_high_value_nodes()
        
        return f"""## Environment Overview

### Object Counts

| Object Type | Count |
|-------------|-------|
| Total Nodes | {self.graph.node_count()} |
| Total Relationships | {self.graph.edge_count()} |
| High-Value Targets | {len(hvt)} |

### High-Value Targets

The following Tier 0 assets were identified:

{self._list_high_value_targets(hvt)}
"""
    
    def _list_high_value_targets(self, hvt: List) -> str:
        """List high-value targets."""
        if not hvt:
            return "- None identified"
        
        lines = []
        for node in hvt[:20]:  # Limit for report readability
            flags = []
            if node.is_domain_controller:
                flags.append("DC")
            if node.is_domain_admin:
                flags.append("Domain Admin")
            if node.is_enterprise_admin:
                flags.append("Enterprise Admin")
            
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            lines.append(f"- **{node.name}** ({node.node_type.value}){flag_str}")
        
        if len(hvt) > 20:
            lines.append(f"\n_... and {len(hvt) - 20} more high-value targets_")
        
        return "\n".join(lines)
    
    def _generate_attack_paths(self) -> str:
        """Generate detailed attack path documentation."""
        if not self.attack_paths:
            return "## Attack Paths\n\nNo attack paths identified."
        
        sections = ["## Attack Paths\n"]
        sections.append("The following attack paths were identified, ordered by priority:\n")
        
        # Table of contents
        sections.append("### Summary Table\n")
        sections.append("| # | Path Name | Impact | Stealth | Complexity | Overall |")
        sections.append("|---|-----------|--------|---------|------------|---------|")
        
        for i, path in enumerate(self.attack_paths, 1):
            sections.append(
                f"| {i} | [{path.name}](#{self._anchor(path.name)}) | "
                f"{path.impact_score:.0f} | {path.stealth_score:.0f} | "
                f"{path.complexity_score:.0f} | **{path.overall_score:.0f}** |"
            )
        
        sections.append("\n---\n")
        
        # Detailed path documentation
        for i, path in enumerate(self.attack_paths, 1):
            sections.append(self._generate_path_detail(i, path))
        
        return "\n".join(sections)
    
    def _generate_path_detail(self, number: int, path: AttackPath) -> str:
        """Generate detailed documentation for a single path."""
        sections = []
        
        # Header
        sections.append(f"### {number}. {path.name}\n")
        
        # Metadata
        sections.append(f"**Path ID:** `{path.path_id}`  ")
        sections.append(f"**Start:** {path.start_node}  ")
        sections.append(f"**Target:** {path.end_node}  ")
        sections.append(f"**Overall Score:** {path.overall_score:.1f}/100\n")
        
        # Scoring breakdown
        sections.append("**Scoring:**")
        sections.append(f"- Impact: {path.impact_score:.1f}/100")
        sections.append(f"- Stealth: {path.stealth_score:.1f}/100")
        sections.append(f"- Complexity: {path.complexity_score:.1f}/100\n")
        
        # Description
        sections.append(f"**Description:**\n\n{path.description}\n")
        
        # Prerequisites
        if path.prerequisites:
            sections.append("**Prerequisites:**\n")
            for prereq in path.prerequisites:
                sections.append(f"- {prereq}")
            sections.append("")
        
        # Steps
        sections.append("#### Attack Steps\n")
        
        for step in path.steps:
            sections.append(f"##### Step {step.sequence}: {step.technique}\n")
            sections.append(f"**Relationship:** `{step.source_node}` --[{step.edge_type.value}]--> `{step.target_node}`\n")
            
            # ATT&CK Mapping
            if step.attack_technique_id:
                sections.append(f"**MITRE ATT&CK:** [{step.attack_technique_id}](https://attack.mitre.org/techniques/{step.attack_technique_id}/) - {step.attack_technique_name}")
                if step.attack_tactic:
                    sections.append(f"  - Tactic: {step.attack_tactic}")
                sections.append("")
            
            # Commands
            if step.commands:
                sections.append("**Commands:**\n")
                for cmd in step.commands:
                    sections.append(f"```powershell\n{cmd}\n```\n")
            
            # Detection
            if step.event_ids or step.detection_notes:
                sections.append("**Detection:**\n")
                if step.event_ids:
                    sections.append(f"- Windows Event IDs: {', '.join(step.event_ids)}")
                if step.sigma_rule:
                    sections.append(f"- Sigma Rule: `{step.sigma_rule}`")
                if step.detection_notes:
                    sections.append(f"- Notes: {step.detection_notes}")
                sections.append("")
            
            # Remediation
            if step.remediation:
                sections.append(f"**Remediation:**\n\n{step.remediation}\n")
            
            sections.append("---\n")
        
        return "\n".join(sections)
    
    def _generate_recommendations(self) -> str:
        """Generate remediation recommendations."""
        return """## Recommendations

### Immediate Actions (Critical)

1. **Review ACL Misconfigurations**
   - Audit all GenericAll, WriteDacl, and WriteOwner permissions
   - Remove unnecessary ACL grants on high-value targets
   - Implement principle of least privilege

2. **Kerberos Hardening**
   - Disable unconstrained delegation where possible
   - Migrate to constrained delegation or resource-based constrained delegation
   - Implement Protected Users group for privileged accounts

3. **Session Management**
   - Prevent privileged account logons to untrusted workstations
   - Implement credential guard on all Tier 0 assets
   - Use LAPS for local admin password randomization

### Detection Implementation

Deploy the following detection rules to identify exploitation attempts:

- Enable advanced audit policy for privilege use and object access
- Monitor Event IDs: 4662 (object access), 4768/4769 (Kerberos), 4672 (privilege use)
- Implement Sigma rules provided in attack path details
- Deploy BloodHound Community Edition for continuous monitoring

### Long-Term Hardening

1. Implement Active Directory tiering model (Tier 0/1/2)
2. Regular BloodHound collection and analysis (monthly minimum)
3. Automated ACL auditing and alerting
4. Red team exercises to validate defenses
"""
    
    def _generate_appendix(self) -> str:
        """Generate appendix with references."""
        return """## Appendix

### References

- [MITRE ATT&CK Framework](https://attack.mitre.org)
- [BloodHound Community Edition](https://github.com/SpecterOps/BloodHound)
- [Active Directory Security (adsecurity.org)](https://adsecurity.org)
- [Harmj0y's Blog](https://blog.harmj0y.net)
- [Sigma Rules Repository](https://github.com/SigmaHQ/sigma)

### Tool Information

**AutoHound** is an open-source research tool for automated Active Directory attack path analysis.

- GitHub: [Your Repository URL]
- License: MIT
- Author: Gordon Prescott / ACH Research Division

### Disclaimer

This report was generated by an automated tool for authorized security testing purposes only.

**Classification:** TLP:WHITE - Authorized Research Only
"""
    
    def _anchor(self, text: str) -> str:
        """Convert text to GitHub markdown anchor."""
        return text.lower().replace(" ", "-").replace("(", "").replace(")", "")
