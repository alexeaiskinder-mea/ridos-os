"""
╔══════════════════════════════════════════════════════════════╗
║  RIDOS OS v1.1 — IT Tools Intent Parser                     ║
║  Copyright (C) 2026 RIDOS OS Project — GPL v3               ║
╚══════════════════════════════════════════════════════════════╝

Detects IT-related requests and executes tools directly,
instead of sending them to the AI API.
"""

import os, subprocess, socket, re
from typing import Tuple

class IntentParser:
    """
    Recognizes system and network commands and executes them directly.
    Returns (True, result_string) if handled, (False, "") if should go to AI.
    """

    INTENTS = {
        # System info
        "ram":          ["كم رام","ram usage","memory","how much ram","ذاكرة","show memory"],
        "cpu":          ["cpu usage","المعالج","processor","cpu percent","core"],
        "disk":         ["disk space","مساحة","قرص","storage","df "],
        "system":       ["system info","معلومات النظام","sysinfo","full status"],
        "processes":    ["processes","running procs","show processes","العمليات","ps aux"],
        "uptime":       ["uptime","how long running","since boot"],

        # Network
        "ip_addr":      ["my ip","show ip","ip address","عنوان ip","what is my ip"],
        "interfaces":   ["network interfaces","show interfaces","ip link","بطاقات الشبكة"],
        "wifi_status":  ["wifi","wireless","واي فاي","is wifi on"],
        "ping":         ["ping ","test connection to","check if .* is up"],
        "scan_network": ["scan network","scan lan","who is on my network","المتصلون بالشبكة","nmap local"],
        "open_ports":   ["open ports","listening ports","what ports","المنافذ المفتوحة"],
        "dns_lookup":   ["dns lookup","nslookup","dig ","resolve ","what is the ip of"],
        "traceroute":   ["traceroute","trace route to","tracepath"],
        "net_speed":    ["network speed","bandwidth test","iperf"],

        # Files
        "list_files":   ["list files","show files","ls ","اعرض الملفات","what is in"],
        "disk_usage":   ["disk usage","du ","folder size","حجم المجلد"],

        # Power
        "shutdown":     ["shutdown","power off","اغلق الجهاز","إيقاف التشغيل"],
        "reboot":       ["reboot","restart system","اعد التشغيل","إعادة التشغيل"],
    }

    def detect(self, msg: str) -> Tuple[str, dict]:
        """Returns (intent_name, args) or ('chat', {})"""
        m = msg.lower().strip()
        for intent, keywords in self.INTENTS.items():
            for kw in keywords:
                if re.search(kw, m):
                    args = self._extract_args(intent, msg)
                    return intent, args
        return "chat", {}

    def _extract_args(self, intent: str, msg: str) -> dict:
        args = {}
        if intent == "ping":
            match = re.search(r"ping\s+(\S+)", msg, re.I)
            if match:
                args["host"] = match.group(1)
        elif intent == "dns_lookup":
            match = re.search(r"(?:nslookup|dig|resolve|ip of)\s+(\S+)", msg, re.I)
            if match:
                args["host"] = match.group(1)
        elif intent == "traceroute":
            match = re.search(r"(?:traceroute|trace.*to)\s+(\S+)", msg, re.I)
            if match:
                args["host"] = match.group(1)
        elif intent in ("list_files", "disk_usage"):
            match = re.search(r"(?:in|of|for|في)\s+(\S+)", msg, re.I)
            args["path"] = match.group(1) if match else "."
        return args

    def execute(self, intent: str, args: dict) -> str:
        try:
            if intent == "ram":
                return self._ram()
            elif intent == "cpu":
                return self._cpu()
            elif intent == "disk":
                return self._disk()
            elif intent == "system":
                return "\n".join([self._ram(), self._cpu(), self._disk(), self._ip()])
            elif intent == "processes":
                return self._processes()
            elif intent == "uptime":
                return self._run_cmd(["uptime", "-p"])
            elif intent == "ip_addr":
                return self._ip()
            elif intent == "interfaces":
                return self._run_cmd(["ip", "addr", "show"])
            elif intent == "wifi_status":
                return self._run_cmd(["iwconfig"], timeout=5)
            elif intent == "ping":
                host = args.get("host", "8.8.8.8")
                result = self._run_cmd(["ping", "-c4", "-W2", host], timeout=12)
                return f"Ping to {host}:\n{result}"
            elif intent == "scan_network":
                return self._scan_local()
            elif intent == "open_ports":
                return self._run_cmd(["ss", "-tlnp"], timeout=5)
            elif intent == "dns_lookup":
                host = args.get("host", "google.com")
                return self._run_cmd(["nslookup", host], timeout=8)
            elif intent == "traceroute":
                host = args.get("host", "8.8.8.8")
                return self._run_cmd(["traceroute", "-m10", host], timeout=20)
            elif intent == "list_files":
                path = os.path.expanduser(args.get("path", "."))
                return self._run_cmd(["ls", "-lah", "--color=never", path], timeout=5)
            elif intent == "disk_usage":
                path = os.path.expanduser(args.get("path", "."))
                return self._run_cmd(["du", "-sh", path], timeout=10)
            elif intent in ("shutdown", "reboot"):
                action = "shutdown" if intent == "shutdown" else "reboot"
                return (f"⚠ Confirm {action}? Type 'yes' to proceed.\n"
                        f"  Or run: `sudo {action} now`")
        except Exception as e:
            return f"⚠ Error executing {intent}: {e}"
        return f"⚠ Unknown intent: {intent}"

    # ── System helpers ────────────────────────────────────────
    def _ram(self) -> str:
        try:
            import psutil
            m = psutil.virtual_memory()
            pct = m.percent
            bar = "█" * int(pct/5) + "░" * (20 - int(pct/5))
            return (f"RAM: [{bar}] {pct:.0f}%\n"
                    f"  Used: {m.used//1024**2} MB  |  "
                    f"Available: {m.available//1024**2} MB  |  "
                    f"Total: {m.total//1024**2} MB")
        except ImportError:
            r = self._run_cmd(["free", "-h"])
            return f"Memory:\n{r}"

    def _cpu(self) -> str:
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            bar = "█" * int(cpu/5) + "░" * (20 - int(cpu/5))
            freq = psutil.cpu_freq()
            freq_str = f"  {freq.current:.0f} MHz" if freq else ""
            return (f"CPU: [{bar}] {cpu:.0f}%{freq_str}\n"
                    f"  Cores: {psutil.cpu_count(logical=False)} physical, "
                    f"{psutil.cpu_count()} logical")
        except ImportError:
            return self._run_cmd(["top", "-bn1"])[:300]

    def _disk(self) -> str:
        try:
            import psutil
            d = psutil.disk_usage("/")
            pct = d.percent
            bar = "█" * int(pct/5) + "░" * (20 - int(pct/5))
            return (f"Disk /: [{bar}] {pct:.0f}%\n"
                    f"  Used: {d.used//1024**3} GB  |  "
                    f"Free: {d.free//1024**3} GB  |  "
                    f"Total: {d.total//1024**3} GB")
        except ImportError:
            return self._run_cmd(["df", "-h", "/"])

    def _ip(self) -> str:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "unknown"
        try:
            r = subprocess.run(["ip", "-4", "addr", "show"],
                               capture_output=True, text=True, timeout=3)
            return f"IP: {ip}\n{r.stdout[:400]}"
        except Exception:
            return f"IP: {ip}"

    def _processes(self) -> str:
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
                try:
                    procs.append(p.info)
                except Exception:
                    pass
            procs.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
            lines = ["Top Processes (by CPU):"]
            for p in procs[:12]:
                lines.append(
                    f"  {p['pid']:6d}  {p['name'][:22]:22s}  "
                    f"CPU:{p['cpu_percent']:5.1f}%  "
                    f"MEM:{p.get('memory_percent',0):4.1f}%"
                )
            return "\n".join(lines)
        except ImportError:
            return self._run_cmd(["ps", "aux", "--sort=-%cpu"])[:800]

    def _scan_local(self) -> str:
        try:
            # Get default gateway to determine local subnet
            r = subprocess.run(["ip", "route", "show", "default"],
                               capture_output=True, text=True, timeout=3)
            gw = re.search(r"via\s+(\S+)", r.stdout)
            if gw:
                subnet = re.sub(r"\.\d+$", ".0/24", gw.group(1))
            else:
                subnet = "192.168.1.0/24"

            result = subprocess.run(
                ["nmap", "-sn", "--open", subnet],
                capture_output=True, text=True, timeout=30
            )
            return f"LAN Scan ({subnet}):\n{result.stdout[:1000]}"
        except FileNotFoundError:
            return "⚠ nmap not found. Install with: sudo apt install nmap"
        except Exception as e:
            return f"⚠ Scan error: {e}"

    def _run_cmd(self, cmd: list, timeout: int = 8) -> str:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return (r.stdout or r.stderr).strip()[:1200]
        except FileNotFoundError:
            return f"⚠ Command not found: {cmd[0]}"
        except subprocess.TimeoutExpired:
            return f"⚠ Command timed out ({timeout}s)"
        except Exception as e:
            return f"⚠ Error: {e}"

    def handle(self, msg: str) -> Tuple[bool, str]:
        intent, args = self.detect(msg)
        if intent == "chat":
            return False, ""
        result = self.execute(intent, args)
        return True, result
