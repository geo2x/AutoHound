# AutoHound © 2026 Gordon Prescott

"""
Constants and configuration values for AutoHound.

All magic numbers and hardcoded limits are centralized here for easy tuning.
"""

# Serializer limits
MAX_PRIORITY_NODES = 50
MAX_ALL_NODES = 200
MAX_EDGE_DESCRIPTIONS = 100
MAX_INBOUND_EDGES_DISPLAY = 10
DEFAULT_MAX_CHUNK_SIZE = 100_000

# Neo4j limits
NEO4J_EDGE_BATCH_LIMIT = 10_000

# LLM limits
LLM_MAX_TOKENS = 4096
LLM_MAX_CONTEXT_CHARS = 80_000
LLM_GRAPH_CONTEXT_TRUNCATION = 5000

# Report limits
MAX_HVT_IN_REPORT = 20
MAX_PATHS_IN_SUMMARY = 3
