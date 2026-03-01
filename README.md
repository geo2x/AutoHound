# AutoHound

**Active Directory Attack Path Intelligence Engine**

![GitHub release](https://img.shields.io/github/v/release/geo2x/AutoHound)
![Downloads](https://img.shields.io/github/downloads/geo2x/AutoHound/total)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
![License](https://img.shields.io/badge/License-Proprietary-red.svg)
[![TLP:WHITE](https://img.shields.io/badge/TLP-WHITE-white.svg)](https://www.cisa.gov/tlp)

AutoHound feeds BloodHound data into Claude to surface attack paths standard queries miss.

**what it finds that BloodHound queries miss**
- multi-hop ACL chains across OU inheritance boundaries
- shadow admin paths via GPO delegation
- Kerberos delegation combinations
- cross-trust abuse chains

**authorized environments only**  
© 2026 Gordon Prescott — ACH Research Division

![AutoHound Workflow](docs/workflow.png)

## 🎯 Key Features

- **🔍 Novel Path Discovery** - Identifies multi-hop attack paths through unusual ACL combinations, GPO abuse, delegation chains, and cross-trust relationships that standard BloodHound queries don't surface
- **⚡ Command Generation** - Produces exact, copy-paste ready commands (PowerView, Impacket, Rubeus) for each attack step
- **🎖️ ATT&CK Mapping** - Automatically maps every technique to MITRE ATT&CK with tactic, technique ID, and sub-technique
- **🛡️ Defensive Guidance** - Provides Windows Event IDs, Sigma rules, and remediation recommendations for every offensive technique
- **📊 Prioritization** - Scores paths by Impact (40%), Stealth (35%), and Complexity (25%) to focus operator effort
- **📈 ATT&CK Navigator Integration** - Generates importable layer files for visualization at [MITRE ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/)

## ⚠️ Ethical Use & Legal Notice

**READ THIS BEFORE USING THIS TOOL**

AutoHound is designed **exclusively** for use in:

- ✅ Your own intentionally vulnerable Active Directory lab
- ✅ GOAD ([Game of Active Directory](https://github.com/Orange-Cyberdefense/GOAD)) or equivalent authorized test environments
- ✅ Client engagements with **explicit written authorization** (signed scope of work / rules of engagement)

**Never** use this tool against any system, network, or environment without written authorization. Unauthorized use may violate the **Computer Fraud and Abuse Act (CFAA)** and equivalent statutes.

### Hard Technical Controls

This tool:

- ❌ Does **NOT** perform live network enumeration
- ❌ Does **NOT** touch Active Directory infrastructure
- ❌ Does **NOT** execute commands automatically
- ❌ Does **NOT** exfiltrate data

It operates **exclusively** on pre-collected BloodHound JSON data or a local Neo4j instance. Input: BloodHound export. Output: local report file. Nothing else.

**Classification:** TLP:WHITE - Shareable within the security research community  
**Use Restriction:** Authorized lab and engagement environments only

## Download

**[AutoHound-v0.1.0-windows-x64.exe](#)** — Windows standalone, no install needed  
**[Source tarball](#)** — pip installable  
[View all releases →](https://github.com/geo2x/AutoHound/releases)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API key
- BloodHound JSON export

### Installation

```powershell
# Clone the repository
git clone https://github.com/geo2x/autohound.git
cd autohound

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .

# Or install from requirements.txt
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Basic Usage

```powershell
# Analyze BloodHound JSON export
autohound --input ./bloodhound_export.json --output ./reports

# Analyze from Neo4j database
autohound --neo4j-uri bolt://localhost:7687 --neo4j-password yourpass --output ./reports

# Use specific Claude model
autohound --input data.json --model claude-sonnet-4-20250514
```

### Example Output

```
╔══════════════════════════════════════════════════════════════╗
║              Active Directory Attack Path AI                 ║
║                       Version 0.1.0                          ║
║   TLP:WHITE - Authorized Research & Lab Use Only            ║
╚══════════════════════════════════════════════════════════════╝

[+] Discovered 3 attack path(s)

[+] Reports generated:
    - Markdown Report: ./reports/autohound_report.md
    - ATT&CK Navigator: ./reports/attack_navigator_layer.json

TOP ATTACK PATHS:

1. Shadow Admin via GPO Delegation (Score: 87.5/100)
   Low-privilege user has GenericAll on GPO that applies to Domain Controllers OU...

2. Kerberos Delegation Chain (Score: 82.3/100)
   Computer with unconstrained delegation can impersonate domain admin...

3. ACL Inheritance Abuse (Score: 76.8/100)
   WriteDacl on parent OU cascades to high-value group objects...
```

## 📚 Documentation

### Project Structure

```
autohound/
├── autohound/
│   ├── ingestor/          # Neo4j & JSON data ingestion
│   ├── serializer/        # Graph to LLM-optimized text
│   ├── reasoning/         # LLM reasoning engine
│   ├── reporting/         # Markdown & ATT&CK Navigator output
│   ├── utils/             # Shared utilities
│   └── cli.py             # Command-line interface
├── tests/                 # Test suite
├── docs/                  # Documentation
├── examples/              # Example outputs
└── requirements.txt       # Dependencies
```

### Architecture

1. **Ingestor** - Connects to Neo4j or parses BloodHound JSON exports
2. **Serializer** - Converts graph to chunked natural language descriptions optimized for LLM context windows
3. **Reasoning Engine** - Multi-pass LLM analysis (discovery → validation/enrichment)
4. **Report Generator** - Produces Markdown reports and ATT&CK Navigator layers

### Command Reference

```powershell
autohound [OPTIONS]

Options:
  -i, --input PATH              Path to BloodHound JSON export (required)
  -o, --output PATH             Output directory (default: ./reports)
  --neo4j-uri TEXT              Neo4j URI (alternative to JSON)
  --neo4j-user TEXT             Neo4j username (default: neo4j)
  --neo4j-password TEXT         Neo4j password
  --api-key TEXT                Anthropic API key
  --model TEXT                  Claude model (default: claude-sonnet-4-20250514)
  --skip-auth-check             Skip authorization verification
  --log-level [DEBUG|INFO|WARNING|ERROR]
  --version                     Show version
  --help                        Show help message
```

## 🧪 Testing

```powershell
# Run tests
pytest

# With coverage
pytest --cov=autohound --cov-report=html

# Run specific test
pytest tests/test_models.py -v
```

## 🏗️ Building a Test Lab

### Option 1: GOAD (Recommended)

Use [GOAD](https://github.com/Orange-Cyberdefense/GOAD) - a pre-built intentionally vulnerable AD lab:

```powershell
# Clone GOAD
git clone https://github.com/Orange-Cyberdefense/GOAD
cd GOAD

# Follow installation instructions in GOAD README
# Collect BloodHound data and analyze with AutoHound
```

### Option 2: Custom Lab

Build your own lab with intentional misconfigurations:

| VM | Role | Misconfigurations |
|----|------|-------------------|
| Windows Server 2019 | Domain Controller | Unconstrained delegation, weak password policy |
| Windows Server 2019 | Member Server | Kerberoastable SPNs, local admin reuse |
| Windows 10/11 (x2) | Workstations | Admin sessions, SMB signing disabled |
| Kali Linux | Attacker | BloodHound CE, Impacket, Rubeus installed |

## 🤝 Contributing

Contributions welcome! This is a research project for learning and portfolio building.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [SpecterOps](https://specterops.io/) for BloodHound Community Edition
- [MITRE](https://attack.mitre.org/) for the ATT&CK framework
- [Anthropic](https://www.anthropic.com/) for Claude API
- [Orange Cyberdefense](https://github.com/Orange-Cyberdefense) for GOAD
- The offensive security research community

## 📖 References

- [BloodHound Community Edition](https://github.com/SpecterOps/BloodHound)
- [MITRE ATT&CK Framework](https://attack.mitre.org)
- [GOAD Lab](https://github.com/Orange-Cyberdefense/GOAD)
- [Sigma Rules](https://github.com/SigmaHQ/sigma)
- [ADSecurity.org](https://adsecurity.org)

## 📧 Contact

**Author:** Gordon Prescott  
**Security Researcher** | Google Cybersecurity Certified | CompTIA CySA+ (In Progress)  
**GitHub:** [@geo2x](https://github.com/geo2x)

**Background:** Security researcher specializing in Active Directory attack automation and offensive tooling development.

---

**AutoHound** - Bringing LLM reasoning to Active Directory attack path analysis  
**TLP:WHITE** - Authorized Research Only

---

## 📜 Copyright & License

© 2026 Gordon Prescott — ACH Research Division. All rights reserved.

AutoHound is an original work by Gordon Prescott. This software is licensed 
under a custom restrictive license that permits personal and authorized research 
use only. Commercial use, redistribution, or modification without attribution 
requires written permission from Gordon Prescott.

**Unauthorized reproduction or redistribution is prohibited.**

For commercial licensing inquiries: gordon.j.prescott23@gmail.com

See [LICENSE](LICENSE) for full terms.
