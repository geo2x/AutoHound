<p align="center">
  <img src="assets/autohound_small.png" width="150" alt="AutoHound">
</p>

<h1 align="center">AutoHound</h1>
<p align="center">
  <b>AI-Powered Active Directory Attack Path Analysis</b><br>
  <i>by ACH Research Division</i>
</p>

<p align="center">
  <a href="https://github.com/geo2x/AutoHound/releases/latest">
    <img src="https://img.shields.io/github/v/release/geo2x/AutoHound?style=for-the-badge&color=6a0dad&labelColor=0a0a0a" alt="Latest Release">
  </a>
  <img src="https://img.shields.io/badge/platform-windows-6a0dad?style=for-the-badge&labelColor=0a0a0a" alt="Platform">
  <img src="https://img.shields.io/badge/powered%20by-claude%20AI-c77dff?style=for-the-badge&labelColor=0a0a0a" alt="Claude AI">
</p>

---

## What is AutoHound?

AutoHound connects to your BloodHound CE instance, reads the Active Directory graph, and uses Claude AI to automatically find attack paths that lead to Domain Admin. It scores each path, maps it to MITRE ATT&CK, generates exploitation commands, and produces a full markdown report.

BloodHound shows you the map. AutoHound tells you the route.

---

## Download

| File | Description |
|------|-------------|
| [AutoHound_Setup.exe](https://github.com/geo2x/AutoHound/releases/latest) | Full GUI installer — recommended |
| [AutoHound.exe](https://github.com/geo2x/AutoHound/releases/latest) | CLI standalone |

---

## Quick Start

### GUI Installer
1. Download and run `AutoHound_Setup.exe`
2. The installer detects Docker, Python, and BloodHound CE automatically
3. Enter your Anthropic API key when prompted
4. Done — start analyzing

### CLI
```bash
autohound --input ./bloodhound_data/ --output ./reports/
```

---

## Requirements

- Windows 10/11 x64
- Docker Desktop
- Anthropic API key — [get one here](https://console.anthropic.com)
- BloodHound CE (GUI installer handles this)

---

## Output

AutoHound produces:
- `autohound_report.md` — full attack path report with exploitation steps
- `attack_navigator_layer.json` — MITRE ATT&CK Navigator layer

---

## Legal

For authorized penetration testing and red team engagements only.
Use only on systems you own or have explicit written permission to test.
The authors accept no liability for unauthorized use.

---

<p align="center">
  © 2026 Gordon Prescott — ACH Research Division. All rights reserved.
</p>
