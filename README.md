# RIDOS OS
### Retro Intelligent Desktop Operating System — v1.1.0 "Baghdad"

[![Build ISO](https://github.com/ridos-os/ridos-os/actions/workflows/build-iso.yml/badge.svg)](https://github.com/ridos-os/ridos-os/actions)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Platform: x86_64](https://img.shields.io/badge/Platform-x86__64-lightgrey)]()

> **A professional Linux distribution for IT specialists, network engineers, and developers — with a built-in Claude AI assistant.**

---

## What is RIDOS OS?

RIDOS OS is a bootable Linux ISO based on Debian. Insert a USB stick and boot directly — no installation needed. It includes professional IT tools and a conversational AI assistant (powered by Anthropic Claude) that understands Linux, networking, and code.

**Key difference from Kali Linux:** RIDOS integrates AI into every IT task. Ask "scan my local network" → RIDOS runs `nmap` and explains the results in plain language.

---

## Features

| Category | Tools |
|---|---|
| **Network Analysis** | Nmap, Wireshark, tcpdump, Netcat, iperf3, arp-scan |
| **Remote Access** | OpenSSH, Remmina (RDP/VNC), tmux, screen |
| **Security** | UFW, iptables, ClamAV, Lynis, fail2ban |
| **Development** | Python 3, GCC/G++, Git, Neovim |
| **AI Assistant** | Claude API (online) with IT tool integration |
| **Desktop** | XFCE (lightweight, works on 512MB RAM) |

---

## System Requirements

| | Minimum | Recommended |
|---|---|---|
| **CPU** | x86_64 (1 GHz) | x86_64 (2+ GHz) |
| **RAM** | 512 MB | 2 GB |
| **Storage** | USB 2GB+ | USB 8GB+ |
| **Network** | Optional | Required for AI |

---

## Quick Start

### 1. Download ISO
Download from [GitHub Releases](https://github.com/ridos-os/ridos-os/releases) or build from source.

### 2. Flash to USB
```bash
# Linux
sudo dd if=ridos-os-1.1.0-x86_64.iso of=/dev/sdX bs=4M status=progress

# Windows / Mac — use Balena Etcher (free)
```

### 3. Boot
Insert USB → restart → press F12/F2/Del → select USB → RIDOS OS boots.

### 4. First Run — Setup Wizard
RIDOS will ask for your **Anthropic API key** (free at [console.anthropic.com](https://console.anthropic.com)).

---

## Building from Source

### Requirements
- Ubuntu 22.04 or Debian 12 machine (or VM)
- 10 GB free disk space
- Root access

### Method 1 — Local Build
```bash
git clone https://github.com/ridos-os/ridos-os.git
cd ridos-os

# Install live-build
sudo apt install live-build debootstrap squashfs-tools xorriso

# Configure + Build
cd build-system
sudo bash scripts/lb_config.sh
sudo lb build

# Output: live-image-amd64.hybrid.iso
```

### Method 2 — GitHub Actions (No Linux required)
1. Fork this repo on GitHub
2. Go to **Actions** tab → **Build RIDOS OS ISO** → **Run workflow**
3. Download the ISO from Artifacts when complete

---

## Project Structure

```
ridos-os/
├── .github/workflows/
│   └── build-iso.yml          # CI/CD — auto-builds ISO on push
├── build-system/
│   ├── scripts/
│   │   └── lb_config.sh       # live-build configuration
│   └── config/
│       ├── package-lists/
│       │   └── ridos.list.chroot   # all packages to install
│       ├── hooks/
│       │   └── 0100-ridos-setup.hook.chroot  # post-install config
│       └── includes.binary/
│           └── boot/grub/     # custom GRUB theme
├── ridos-core/
│   ├── ai_daemon.py           # Claude API backend (Unix socket)
│   ├── ridos_shell.py         # terminal chat interface
│   ├── intent_parser.py       # IT tools automation
│   ├── web_search.py          # DuckDuckGo integration
│   └── setup_wizard.py        # first-boot setup
├── legal/
│   ├── LICENSE.txt            # GPL v3
│   ├── COPYRIGHT              # project copyright
│   └── CONTRIBUTORS.md        # contributors list
└── README.md
```

---

## RIDOS Shell Commands

| Command | Description |
|---|---|
| `/help` | Show all commands |
| `/status` | CPU, RAM, disk, network |
| `/tools` | List available IT tools |
| `/network` | Network diagnostics |
| `/version` | Version information |
| `/clear` | Clear screen |
| `/reset` | Clear AI conversation |
| `$ command` | Run any shell command |
| `search: ...` | Web search |

---

## Contributing

Contributions are welcome! See [CONTRIBUTORS.md](legal/CONTRIBUTORS.md).

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add: description"`
4. Push and open a Pull Request

---

## Copyright & License

```
RIDOS OS — Retro Intelligent Desktop Operating System
Copyright (C) 2026  RIDOS OS Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License.
```

See [legal/LICENSE.txt](legal/LICENSE.txt) for the full text.

**Third-party components** (Linux kernel, Debian, Python, GRUB, etc.) are governed by their own respective licenses. See [legal/LICENSE.txt](legal/LICENSE.txt) for details.

**Anthropic Claude API** — Each user provides their own API key. RIDOS OS does not include any API keys and is not affiliated with Anthropic.

---

*RIDOS OS — Built on open source. Powered by AI. Made for IT professionals.*
