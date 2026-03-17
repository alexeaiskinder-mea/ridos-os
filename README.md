# ⚡ RIDOS OS v1.1.0 "Baghdad"
### AI-Powered Linux for IT Professionals

<p align="center">
  <img src="https://img.shields.io/badge/Base-Debian%20Bookworm-purple?style=for-the-badge&logo=debian"/>
  <img src="https://img.shields.io/badge/Desktop-XFCE-blueviolet?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/AI-Offline--First-green?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Boot-Rufus%20Compatible-blue?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-GPL%20v3-orange?style=for-the-badge"/>
</p>

---

## 🌟 What is RIDOS OS?

RIDOS OS is a Debian-based live Linux distribution built for **IT professionals, field engineers, and system administrators**. It fills the gap between Kali (offensive security) and Ubuntu (general use) — RIDOS is built for **diagnosing, repairing, and securing systems in the field**.

The defining feature is **built-in AI tools that work fully offline** — no internet required.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🤖 **AI System Doctor** | Diagnoses system problems and suggests exact fixes |
| 🌐 **AI Network Analyzer** | Advanced network scanning, port analysis, connectivity diagnosis |
| 💾 **AI Hardware Fixer** | HDD/SSD/NVMe health via SMART, RAM diagnostics |
| 🔒 **AI Security Scanner** | Rootkit detection, firewall audit, vulnerability assessment |
| 📴 **Offline-First AI** | All tools work without internet using local rule engine |
| 💿 **GUI HDD Installer** | Clean wizard to install RIDOS permanently to disk |
| ⚡ **Fast Shutdown** | 5-second shutdown via systemd tuning |
| 🛠️ **Diagnostic Tools** | smartmontools, memtest86+, wireshark, nmap, lynis, rkhunter |
| 🖥️ **XFCE Desktop** | Dark purple theme, all tools as desktop shortcuts |
| 🌍 **Baghdad/Iraq Locale** | Arabic + English, Asia/Baghdad timezone |
| 🔌 **Rufus Compatible** | ISO hybrid works with Rufus in DD and ISO mode |

---

## 📥 Download & Boot

### Requirements
- USB drive: **4 GB minimum**
- RAM: **2 GB minimum** (4 GB recommended)
- Architecture: **x86_64**

### Flash with Rufus (Windows)
1. Download the latest ISO from [Releases](../../releases)
2. Open Rufus → Select the ISO
3. Partition scheme: **MBR** (for most systems)
4. Click **Start** → Select **Write in ISO Image mode**
5. Boot from USB → Select **RIDOS OS** from the menu

### Flash with `dd` (Linux/Mac)
```bash
sudo dd if=ridos-os-1.1.0-Baghdad-x86_64.iso of=/dev/sdX bs=4M status=progress
sudo sync
```

---

## 🔐 Login

| | |
|---|---|
| **Username** | `ridos` |
| **Password** | `ridos` |
| **Root password** | `ridos` |

---

## 🤖 AI Tools

All AI tools are in `/opt/ridos/bin/` and have desktop shortcuts.

### Online Mode (Anthropic API)
Set your API key for full AI responses:
```bash
export ANTHROPIC_API_KEY="your-key-here"
python3 /opt/ridos/bin/ridos_shell.py
```

### Offline Mode (No internet needed)
All tools automatically fall back to a local rule-based AI engine when offline:
```bash
python3 /opt/ridos/bin/ridos_shell.py        # AI Shell
python3 /opt/ridos/bin/system_doctor.py      # System Doctor
python3 /opt/ridos/bin/network_analyzer.py   # Network Analyzer
python3 /opt/ridos/bin/hardware_fixer.py     # Hardware Fixer
python3 /opt/ridos/bin/security_scanner.py   # Security Scanner
```

---

## 💿 Install to HDD

Launch the **"Install RIDOS OS to HDD"** shortcut on the desktop, or run:
```bash
sudo python3 /opt/ridos/bin/ridos_installer_gui.py
```

The GUI installer will guide you through disk selection, formatting, and GRUB setup.

---

## 🛠️ Built-in Tools

### Diagnostics
- `smartmontools` — HDD/SSD/NVMe SMART health
- `memtest86+` — RAM testing (from boot menu)
- `lshw`, `dmidecode` — hardware inventory
- `nvme-cli`, `hdparm` — advanced disk tools

### Network
- `nmap`, `wireshark`, `tshark` — network scanning and capture
- `net-tools`, `traceroute`, `iftop`, `nethogs` — traffic analysis
- `openssh-client/server` — SSH

### Security
- `lynis` — system security audit
- `rkhunter`, `chkrootkit` — rootkit detection
- `fail2ban`, `ufw` — intrusion prevention
- `wireshark` — packet analysis

---

## 🏗️ Build from Source

RIDOS OS is built entirely by GitHub Actions — no manual build needed.

```bash
# Fork the repo, then push to main to trigger a build
git clone https://github.com/alexeaiskinder-mea/ridos-os
cd ridos-os
# Make your changes
git push origin main
# Check Actions tab for build progress (~60-90 min)
```

### Tag a release
```bash
git tag v1.1.0
git push origin v1.1.0
# GitHub Actions will build the ISO and create a Release automatically
```

---

## 🗂️ Repository Structure

```
ridos-os/
├── .github/workflows/
│   └── build-iso.yml        # Full CI/CD build pipeline
├── ridos-core/
│   ├── ai_engine.py         # Shared offline-first AI engine
│   ├── ridos_shell.py       # Interactive AI shell
│   ├── system_doctor.py     # AI system diagnostics
│   ├── network_analyzer.py  # AI network analysis
│   ├── hardware_fixer.py    # AI hardware diagnostics
│   ├── security_scanner.py  # AI security audit
│   └── ridos_installer_gui.py  # GUI HDD installer
├── legal/
│   ├── LICENSE.txt          # GPL v3
│   ├── COPYRIGHT            # Copyright notice
│   └── CONTRIBUTORS.md      # Contributors
└── README.md
```

---

## 🆚 RIDOS vs Kali vs Ubuntu

| | RIDOS OS | Kali Linux | Ubuntu |
|---|---|---|---|
| **Purpose** | IT repair & diagnosis | Penetration testing | General use |
| **AI tools** | ✅ Built-in offline | ❌ None | ❌ None |
| **Hardware diagnostics** | ✅ Full | ⚠️ Basic | ⚠️ Basic |
| **Security tools** | ✅ Defense-focused | ✅ Offense-focused | ❌ Minimal |
| **Rufus compatible** | ✅ | ✅ | ✅ |
| **Offline usable** | ✅ Fully | ✅ | ⚠️ Partial |
| **Arabic locale** | ✅ Built-in | ❌ | ⚠️ Manual |
| **ISO size** | ~500 MB | ~4 GB | ~5 GB |
| **CI/CD build** | ✅ GitHub Actions | ❌ | ❌ |

---

## 🤝 Contributing

Pull requests welcome. Open an issue first for major changes.

---

## 📄 License

GPL v3 — see [legal/LICENSE.txt](legal/LICENSE.txt)

---

<p align="center">Built in Baghdad 🇮🇶 | Powered by Debian | GPL v3</p>
