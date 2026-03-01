"""
Command-line interface for BloodHound AI.

Main entry point for the tool.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

from bloodhound_ai import __version__
from bloodhound_ai.ingestor import Neo4jIngestor, JsonIngestor
from bloodhound_ai.serializer import GraphSerializer
from bloodhound_ai.reasoning import LLMEngine
from bloodhound_ai.reporting import MarkdownReportGenerator, AttackNavigatorGenerator
from bloodhound_ai.utils import setup_logging

logger = logging.getLogger(__name__)


BANNER = f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗ ██╗      ██████╗  ██████╗ ██████╗ ██╗  ██╗       ║
║   ██╔══██╗██║     ██╔═══██╗██╔═══██╗██╔══██╗██║  ██║       ║
║   ██████╔╝██║     ██║   ██║██║   ██║██║  ██║███████║       ║
║   ██╔══██╗██║     ██║   ██║██║   ██║██║  ██║██╔══██║       ║
║   ██████╔╝███████╗╚██████╔╝╚██████╔╝██████╔╝██║  ██║       ║
║   ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝  ╚═╝       ║
║                                                              ║
║              Active Directory Attack Path AI                 ║
║                       Version {__version__}                        ║
║                                                              ║
║   TLP:WHITE - Authorized Research & Lab Use Only            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def verify_authorization() -> bool:
    """Prompt user to confirm authorized use."""
    print("\n" + "="*70)
    print("AUTHORIZATION VERIFICATION")
    print("="*70)
    print("\nThis tool is designed for use ONLY in:")
    print("  1. Your own intentionally vulnerable AD lab")
    print("  2. GOAD or equivalent authorized test environments")
    print("  3. Client engagements with explicit written authorization")
    print("\nUnauthorized use may violate the Computer Fraud and Abuse Act (CFAA)")
    print("and equivalent laws.")
    print("\n" + "="*70)
    
    response = input("\nI confirm I am authorized to analyze this environment (yes/no): ")
    return response.lower() in ['yes', 'y']


@click.command()
@click.option('--input', '-i', 'input_path', required=True, 
              type=click.Path(exists=True),
              help='Path to BloodHound JSON export file or directory')
@click.option('--output', '-o', 'output_dir', 
              type=click.Path(),
              default='./reports',
              help='Output directory for reports (default: ./reports)')
@click.option('--neo4j-uri', 
              help='Neo4j URI (e.g., bolt://localhost:7687) - alternative to JSON')
@click.option('--neo4j-user', 
              default='neo4j',
              help='Neo4j username')
@click.option('--neo4j-password', 
              help='Neo4j password')
@click.option('--api-key',
              help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')
@click.option('--model',
              default='claude-sonnet-4-20250514',
              help='Claude model to use')
@click.option('--skip-auth-check',
              is_flag=True,
              help='Skip authorization verification (USE WITH CAUTION)')
@click.option('--log-level',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
              default='INFO',
              help='Logging level')
@click.version_option(version=__version__)
def main(
    input_path: str,
    output_dir: str,
    neo4j_uri: Optional[str],
    neo4j_user: str,
    neo4j_password: Optional[str],
    api_key: Optional[str],
    model: str,
    skip_auth_check: bool,
    log_level: str
) -> None:
    """
    BloodHound AI - Active Directory Attack Path Intelligence Engine
    
    Analyze BloodHound data to discover novel attack paths with LLM reasoning.
    
    Examples:
    
        # Analyze BloodHound JSON export
        bloodhound-ai --input ./bloodhound_export.json --output ./reports
        
        # Analyze from Neo4j database
        bloodhound-ai --neo4j-uri bolt://localhost:7687 --neo4j-password pass --output ./reports
        
        # Use specific Claude model
        bloodhound-ai --input data.json --model claude-sonnet-4-20250514
    """
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging(log_level)
    
    # Print banner
    print(BANNER)
    
    # Authorization check
    if not skip_auth_check:
        if not verify_authorization():
            print("\n[!] Authorization not confirmed. Exiting.")
            sys.exit(1)
        print("\n[+] Authorization confirmed. Proceeding...\n")
    else:
        logger.warning("Authorization check skipped - ensure you have proper authorization!")
    
    try:
        # Step 1: Ingest data
        logger.info("Step 1/5: Ingesting BloodHound data...")
        
        if neo4j_uri:
            if not neo4j_password:
                neo4j_password = click.prompt("Neo4j password", hide_input=True)
            
            with Neo4jIngestor(neo4j_uri, neo4j_user, neo4j_password) as ingestor:
                graph = ingestor.ingest()
        else:
            ingestor = JsonIngestor(input_path)
            graph = ingestor.ingest()
        
        logger.info(f"Loaded {graph.node_count()} nodes and {graph.edge_count()} edges")
        
        # Step 2: Serialize graph
        logger.info("Step 2/5: Serializing graph for LLM analysis...")
        serializer = GraphSerializer(graph)
        graph_text = serializer.serialize_to_text()
        logger.info(f"Generated graph description ({len(graph_text)} characters)")
        
        # Step 3: LLM analysis
        logger.info("Step 3/5: Analyzing attack paths with LLM...")
        engine = LLMEngine(api_key=api_key, model=model)
        attack_paths = engine.analyze(graph_text)
        
        if not attack_paths:
            logger.warning("No attack paths discovered!")
            print("\n[!] No attack paths found in this environment.")
            print("[i] This could mean:")
            print("    - The environment is well-hardened")
            print("    - BloodHound data is incomplete")
            print("    - The LLM needs more context (try --log-level DEBUG)")
            return
        
        logger.info(f"Discovered {len(attack_paths)} attack paths")
        
        # Step 4: Generate reports
        logger.info("Step 4/5: Generating reports...")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Markdown report
        report_file = output_path / "bloodhound_ai_report.md"
        report_gen = MarkdownReportGenerator(graph, attack_paths)
        report_gen.generate(report_file)
        
        # ATT&CK Navigator layer
        navigator_file = output_path / "attack_navigator_layer.json"
        navigator_gen = AttackNavigatorGenerator(attack_paths)
        navigator_gen.generate(navigator_file)
        
        # Step 5: Summary
        logger.info("Step 5/5: Analysis complete!")
        
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)
        print(f"\n[+] Discovered {len(attack_paths)} attack path(s)")
        print(f"\n[+] Reports generated:")
        print(f"    - Markdown Report: {report_file}")
        print(f"    - ATT&CK Navigator: {navigator_file}")
        print(f"\n[i] Import {navigator_file} at https://mitre-attack.github.io/attack-navigator/")
        print("\n" + "="*70)
        
        # Show top 3 paths
        if attack_paths:
            print("\nTOP ATTACK PATHS:\n")
            for i, path in enumerate(attack_paths[:3], 1):
                print(f"{i}. {path.name} (Score: {path.overall_score:.1f}/100)")
                print(f"   {path.description[:100]}...")
                print()
        
    except KeyboardInterrupt:
        print("\n\n[!] Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n[!] Error: {e}")
        print("[i] Run with --log-level DEBUG for detailed error information")
        sys.exit(1)


if __name__ == '__main__':
    main()
