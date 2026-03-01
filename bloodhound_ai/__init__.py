"""
BloodHound AI - Active Directory Attack Path Intelligence Engine

An LLM-powered tool for analyzing BloodHound data to discover novel attack paths,
generate executable commands, and provide MITRE ATT&CK mapping with defensive guidance.

Classification: TLP:WHITE - Authorized Research Only
Use: Lab environments and authorized engagements only
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from bloodhound_ai import models

__all__ = ["models", "__version__"]
