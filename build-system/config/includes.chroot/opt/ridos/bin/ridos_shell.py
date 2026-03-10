"""
╔══════════════════════════════════════════════════════════════╗
║  RIDOS OS v1.1 — Interactive Shell                          ║
║  Copyright (C) 2026 RIDOS OS Project — GPL v3               ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio, json, os, subprocess, sys
from datetime import datetime

B = "\033[34m";  LB = "\033[94m"; G  = "\033[32m"
Y = "\033[33m";  R  = "\033[31m"; C  = "\033[36m"
W = "\033[97m";  D  = "\033[2m";  BD = "\033[1m"
X = "\033[0m"

VERSION   = "1.1.0"
CODENAME  = "Basra"
SOCKET    = "/run/ridos.sock"

BANNER = f"""
{LB}{BD}
  ██████╗ ██╗██████╗  ██████╗ ███████╗
  ██╔══██╗██║██╔══██╗██╔═══██╗██╔════╝
  ██████╔╝██║██║  ██║██║   ██║███████╗
  ██╔══██╗██║██║  ██║██║   ██║╚════██║
  ██║  ██║██║██████╔╝╚██████╔╝███████║
  ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝{X}
  {D}v{VERSION} "{CODENAME}"  |  Retro Intelligent Desktop OS{X}
  {D}Copyright (C) 2026 RIDOS OS Project — GPL v3{X}
"""

HELP = f"""
{Y}{BD}RIDOS OS — Available Commands{X}

  {LB}/help{X}       Show this help
  {LB}/status{X}     System information (CPU, RAM, disk, network)
  {LB}/clear{X}      Clear the screen
  {LB}/history{X}    Show recent conversation
  {LB}/reset{X}      Clear conversation history
  {LB}/tools{X}      List available IT tools
  {LB}/network{X}    Quick network status
  {LB}/version{X}    RIDOS OS version info
  {LB}/exit{X}       Exit RIDOS shell

  {C}$ command{X}    Run any shell command directly
  {C}search: ...{X}  Search the web

  {D}Ask anything — RIDOS AI understands IT, networking, code, and more.{X}
"""

# ── Helpers ───────────────────────────────────────────────────
def sys_info() -> str:
    lines = []
    try:
        import psutil
        mem  = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu  = psutil.cpu_percent(interval=0.5)
        def bar(p):
            filled = int(p / 5)
            return G + "█" * filled + D + "░" * (20 - filled) + X
        lines += [
            f"\n  {Y}━━━ RIDOS OS {VERSION} — System Status ━━━{X}",
            f"  CPU   {bar(cpu)} {cpu:.0f}%",
            f"  RAM   {bar(mem.percent)} {mem.used//1024//1024}/{mem.total//1024//1024} MB",
            f"  Disk  {bar(disk.percent)} {disk.used//1024**3}/{disk.total//1024**3} GB",
        ]
    except ImportError:
        lines.append(f"  {D}(psutil not available){X}")

    import socket as sk
    try:
        ip = sk.gethostbyname(sk.gethostname())
        lines.append(f"  IP    {C}{ip}{X}")
    except Exception:
        lines.append(f"  IP    {D}unknown{X}")

    import subprocess
    try:
        r = subprocess.run(["ping", "-c1", "-W2", "8.8.8.8"],
                           capture_output=True, timeout=4)
        net = f"{G}ONLINE{X}" if r.returncode == 0 else f"{Y}OFFLINE{X}"
    except Exception:
        net = f"{D}unknown{X}"
    lines.append(f"  Net   {net}")
    lines.append("")
    return "\n".join(lines)

def it_tools() -> str:
    tools = [
        ("nmap",       "Network scanner & port mapper"),
        ("wireshark",  "Packet capture & analysis (GUI)"),
        ("tcpdump",    "Packet capture (CLI)"),
        ("netcat",     "TCP/UDP Swiss army knife"),
        ("traceroute", "Trace network path"),
        ("iperf3",     "Network bandwidth tester"),
        ("ssh",        "Secure remote access"),
        ("remmina",    "RDP / VNC / SSH client (GUI)"),
        ("nmap",       "Host discovery & port scan"),
        ("arp-scan",   "LAN device discovery"),
        ("git",        "Version control"),
        ("python3",    "Python interpreter"),
        ("gcc",        "C/C++ compiler"),
    ]
    lines = [f"\n  {Y}━━━ RIDOS OS — IT Tools ━━━{X}"]
    for name, desc in tools:
        lines.append(f"  {LB}{name:<14}{X} {D}{desc}{X}")
    lines.append(f"\n  {D}Ask RIDOS AI to use any of these tools for you.{X}\n")
    return "\n".join(lines)

# ── Daemon communication ───────────────────────────────────────
async def ask_ai(prompt: str, history: list) -> tuple[str, str]:
    if not os.path.exists(SOCKET):
        return (f"{R}⚠ RIDOS AI daemon not running.{X}\n"
                f"  Start it: {C}sudo systemctl start ridos-daemon{X}"), "error"
    try:
        reader, writer = await asyncio.open_unix_connection(SOCKET)
        payload = json.dumps({"prompt": prompt, "context": history}, ensure_ascii=False)
        writer.write(payload.encode())
        writer.write_eof()
        await writer.drain()
        data = await asyncio.wait_for(reader.read(65536), timeout=45)
        writer.close()
        r = json.loads(data.decode())
        return r["response"], r.get("model", "?")
    except asyncio.TimeoutError:
        return f"{Y}⚠ Timeout — daemon may be busy.{X}", "error"
    except Exception as e:
        return f"{R}⚠ Connection error: {e}{X}", "error"

# ── Main REPL ─────────────────────────────────────────────────
async def main():
    os.system("clear")
    print(BANNER)
    print(sys_info())
    print(f"  {D}Type your question or /help for commands{X}\n")

    history = []

    while True:
        try:
            user = input(f"{LB}{BD}[RIDOS]{X}{BD}▸{X} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Y}Goodbye!{X}")
            break

        if not user:
            continue

        cmd = user.lower()

        # ── Built-in commands ──
        if cmd in ("/exit", "/quit", "exit", "quit"):
            print(f"{Y}Goodbye!{X}"); break

        elif cmd == "/help":
            print(HELP)

        elif cmd == "/clear":
            os.system("clear"); print(BANNER)

        elif cmd == "/status":
            print(sys_info())

        elif cmd == "/tools":
            print(it_tools())

        elif cmd == "/reset":
            history.clear()
            print(f"{G}✓ Conversation cleared.{X}")

        elif cmd == "/version":
            print(f"\n  {LB}RIDOS OS{X} v{VERSION} \"{CODENAME}\"")
            print(f"  {D}Copyright (C) 2026 RIDOS OS Project — GPL v3{X}")
            print(f"  {D}https://github.com/ridos-os/ridos-os{X}\n")

        elif cmd == "/network":
            print(f"{D}Running network diagnostics...{X}")
            cmds = [
                ("IP address",   ["ip", "addr", "show"]),
                ("Default route",["ip", "route", "show", "default"]),
                ("DNS servers",  ["cat", "/etc/resolv.conf"]),
            ]
            for label, c in cmds:
                try:
                    r = subprocess.run(c, capture_output=True, text=True, timeout=5)
                    print(f"\n  {Y}{label}:{X}")
                    for line in r.stdout.strip().split("\n")[:4]:
                        print(f"  {D}{line}{X}")
                except Exception:
                    pass

        elif cmd == "/history":
            if not history:
                print(f"  {D}No conversation history.{X}")
            else:
                for m in history[-12:]:
                    role = f"{LB}RIDOS{X}" if m["role"] == "assistant" else f"{W}You{X}"
                    print(f"  {role}: {m['content'][:90]}{'...' if len(m['content'])>90 else ''}")

        elif user.startswith("$"):
            # Shell passthrough
            cmd_str = user[1:].strip()
            try:
                result = subprocess.run(cmd_str, shell=True,
                                        capture_output=True, text=True, timeout=30)
                output = result.stdout or result.stderr
                if output:
                    print(f"{D}{output.rstrip()}{X}")
                else:
                    print(f"{D}(no output){X}")
            except subprocess.TimeoutExpired:
                print(f"{Y}⚠ Command timed out (30s){X}")
            except Exception as e:
                print(f"{R}Error: {e}{X}")

        else:
            # ── AI request ──
            print(f"{D}RIDOS is thinking...{X}", end="\r", flush=True)
            response, model = await ask_ai(user, history)

            badge = {
                "online":        f"{G}[AI·Online]{X}",
                "online+search": f"{G}[AI·Web]{X}",
                "offline":       f"{Y}[AI·Local]{X}",
                "system":        f"{C}[System]{X}",
                "error":         f"{R}[Error]{X}",
            }.get(model, f"{D}[{model}]{X}")

            ts = datetime.now().strftime("%H:%M")
            print(f"\r{LB}{BD}RIDOS{X} {badge} {D}{ts}{X}")
            print(f"  {response}\n")

            history.append({"role": "user",      "content": user})
            history.append({"role": "assistant",  "content": response})
            if len(history) > 24:
                history = history[-24:]

if __name__ == "__main__":
    asyncio.run(main())
