"""
BloodHound data ingestion layer.

Supports both Neo4j database queries and direct JSON export parsing.
"""

from autohound.ingestor.json_ingestor import JsonIngestor
from autohound.ingestor.neo4j_ingestor import Neo4jIngestor

__all__ = ["Neo4jIngestor", "JsonIngestor"]
