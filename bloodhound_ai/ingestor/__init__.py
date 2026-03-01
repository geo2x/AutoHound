"""
BloodHound data ingestion layer.

Supports both Neo4j database queries and direct JSON export parsing.
"""

from bloodhound_ai.ingestor.neo4j_ingestor import Neo4jIngestor
from bloodhound_ai.ingestor.json_ingestor import JsonIngestor

__all__ = ["Neo4jIngestor", "JsonIngestor"]
