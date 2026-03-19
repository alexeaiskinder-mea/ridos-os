#!/usr/bin/env python3
"""
RIDOS Control Center v5
Single entry point for all RIDOS OS functionality.
Architecture: UI → AI Analysis → Safe Action Whitelist → OS Execution
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import json
import os
import sys
import socket
import time

# ── Safe action whitelist (AI can ONLY trigger these) ───────────────────────
# Never allow AI to write arbitrary commands — only predefined safe actions
SAFE_ACTIONS = {
    "clear_cache":       ("sync; echo 3 > /proc/sys/vm/drop_caches",         "Free RAM cache"),
    "system_clean":      ("apt-get autoremove -y && apt-get clean",           "Remove unused packages"),
    "update_system":     ("apt-get update && apt-get upgrade -y",             "Update all packages"),
    "enable_firewall":   ("ufw --force enable",                               "Enable UFW firewall"),
    "restart_network":   ("systemctl restart NetworkManager",                  "Restart network"),
    "fix_dns":           ("echo 'nameserver 1.1.1.1' > /etc/resolv.conf && echo 'nameserver 8.8.8.8' >> /etc/resolv.conf", "Fix DNS"),
    "kill_heavy_cpu":    ("ps aux --sort=-%cpu | awk 'NR>2{print $2}' | head -3 | xargs -r kill -15", "Kill top CPU processes"),
    "restart_display":   ("systemctl restart lightdm",                         "Restart display manager"),
    "check_disk":        ("e2fsck -f -y $(df / | awk 'NR==2{print $1}') 2>/dev/null || true", "Check filesystem"),
    "sync_time":         ("timedatectl set-ntp true",                          "Sync system time"),
}

# ── RIDOS Dark Purple Theme ───────────────────────────────────────────────────
BG       = "#1a0a2e"
BG2      = "#2d1254"
BG3      = "#3d1a6e"
ACCENT   = "#6B21A8"
ACCENT2  = "#9333ea"
FG       = "#ffffff"
FG2      = "#c4b5fd"
FG3      = "#e9d5ff"
GREEN    = "#22c55e"
YELLOW   = "#eab308"
RED      = "#ef4444"
ORANGE   = "#f97316"
FONT     = ("Noto Sans", 10)
FONT_B   = ("Noto Sans", 10, "bold")
FONT_LG  = ("Noto Sans", 14, "bold")
FONT_XL  = ("Noto Sans", 18, "bold")
FONT_SM  = ("Noto Sans", 9)
FONT_C   = ("Noto Mono", 9)

TOOLS    = "/opt/ridos/bin"


def run_cmd(cmd, timeout=10):
    """Run shell command safely."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def run_safe_action(action_key):
    """Execute a whitelisted safe action via pkexec."""
    if action_key not in SAFE_ACTIONS:
        messagebox.showerror("Security Error", f"Action '{action_key}' is not in the safe whitelist.")
        return
    cmd, desc = SAFE_ACTIONS[action_key]
    if not messagebox.askyesno("Confirm Action", f"Run: {desc}?\n\nThis requires administrator privileges."):
        return
    full_cmd = f'pkexec bash -c "{cmd}"'
    subprocess.Popen(full_cmd, shell=True)


def collect_system_data():
    """Collect real system metrics."""
    data = {}

    # CPU
    cpu_raw = run_cmd("grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}'")
    try:
        data["cpu"] = float(cpu_raw)
    except Exception:
        data["cpu"] = 0.0

    # RAM
    mem_raw = run_cmd("free | awk 'NR==2{printf \"%.0f\", $3/$2*100}'")
    try:
        data["ram"] = float(mem_raw)
    except Exception:
        data["ram"] = 0.0

    data["ram_used"] = run_cmd("free -h | awk 'NR==2{print $3}'")
    data["ram_total"] = run_cmd("free -h | awk 'NR==2{print $2}'")

    # Disk
    disk_raw = run_cmd("df / | awk 'NR==2{print $5}' | tr -d '%'")
    try:
        data["disk"] = float(disk_raw)
    except Exception:
        data["disk"] = 0.0

    data["disk_used"] = run_cmd("df -h / | awk 'NR==2{print $3}'")
    data["disk_total"] = run_cmd("df -h / | awk 'NR==2{print $2}'")

    # CPU temp
    temp = run_cmd("sensors 2>/dev/null | grep 'Core 0' | awk '{print $3}' | head -1 | tr -d '+°C'")
    try:
        data["cpu_temp"] = float(temp)
    except Exception:
        data["cpu_temp"] = 0.0

    # Network
    try:
        socket.setdefaulttimeout(2)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        data["internet"] = True
    except Exception:
        data["internet"] = False

    data["ip"] = run_cmd("ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \\K\\S+'")

    # Failed services
    failed = run_cmd("systemctl --failed --no-legend 2>/dev/null | wc -l")
    try:
        data["failed_services"] = int(failed)
    except Exception:
        data["failed_services"] = 0

    # Uptime
    data["uptime"] = run_cmd("uptime -p").replace("up ", "")

    return data


def ai_analyze(system_data):
    """
    AI analysis returning structured JSON with action keys (not raw commands).
    Falls back to local rule engine if offline.
    """

    def local_rules(data):
        """Offline rule-based AI — safe, predictable."""
        issues = []
        if data["cpu"] > 85:
            issues.append({"problem": f"High CPU usage ({data['cpu']:.0f}%)", "action": "kill_heavy_cpu", "severity": "high"})
        if data["ram"] > 80:
            issues.append({"problem": f"High RAM usage ({data['ram']:.0f}%  {data['ram_used']}/{data['ram_total']})", "action": "clear_cache", "severity": "high"})
        if data["disk"] > 85:
            issues.append({"problem": f"Low disk space ({data['disk']:.0f}% used — {data['disk_used']}/{data['disk_total']})", "action": "system_clean", "severity": "high"})
        if not data["internet"]:
            issues.append({"problem": "No internet connection", "action": "restart_network", "severity": "medium"})
        if data["failed_services"] > 0:
            issues.append({"problem": f"{data['failed_services']} failed system service(s)", "action": None, "severity": "medium"})
        if data["cpu_temp"] > 85:
            issues.append({"problem": f"CPU temperature high ({data['cpu_temp']:.0f}°C)", "action": None, "severity": "high"})
        return {"issues": issues, "summary": "Offline analysis", "mode": "offline"}

    # Try online AI
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            import urllib.request
            prompt = f"""Analyze this Linux system and return ONLY valid JSON.
System: CPU={system_data['cpu']:.1f}% RAM={system_data['ram']:.1f}% Disk={system_data['disk']:.1f}% Internet={'yes' if system_data['internet'] else 'no'} Failed_services={system_data['failed_services']}

Return this exact format:
{{"issues": [{{"problem": "description", "action": "action_key", "severity": "high|medium|low"}}], "summary": "one line summary"}}

Available action keys: {list(SAFE_ACTIONS.keys())}
Use null for action if no automated fix exists.
Return ONLY JSON, no other text."""

            payload = json.dumps({
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 512,
                "messages": [{"role": "user", "content": prompt}]
            }).encode()

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                text = data["content"][0]["text"].strip()
                # Clean JSON
                if "```" in text:
                    text = text.split("```")[1].replace("json", "").strip()
                result = json.loads(text)
                result["mode"] = "online"
                # Safety: validate all action keys
                for issue in result.get("issues", []):
                    if issue.get("action") and issue["action"] not in SAFE_ACTIONS:
                        issue["action"] = None
                return result
        except Exception:
            pass

    return local_rules(system_data)


def launch_tool(script):
    """Launch an AI tool in terminal."""
    subprocess.Popen(
        f'xfce4-terminal --title="RIDOS {script}" -e "python3 {TOOLS}/{script}"',
        shell=True
    )


def launch_software_center():
    subprocess.Popen(f"python3 {TOOLS}/ridos_software_center.py", shell=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTROL CENTER
# ─────────────────────────────────────────────────────────────────────────────

class RIDOSControlCenter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RIDOS Control Center")
        self.geometry("750x620")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._system_data = {}
        self._analysis = {}
        self._build_ui()
        self._auto_refresh()

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=ACCENT, height=70)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚡  RIDOS Control Center",
                 font=FONT_XL, bg=ACCENT, fg=FG).pack(side=tk.LEFT, padx=20, pady=14)
        self.mode_lbl = tk.Label(hdr, text="● Offline", font=FONT_SM, bg=ACCENT, fg=YELLOW)
        self.mode_lbl.pack(side=tk.RIGHT, padx=20)
        tk.Label(hdr, text="Field Engineer OS", font=FONT_SM, bg=ACCENT, fg=FG2).pack(side=tk.RIGHT)

        # ── Body ─────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # Left: status + issues
        left = tk.Frame(body, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # ── Live Status Panel ────────────────────────────────────────────────
        status_hdr = tk.Frame(left, bg=BG2, pady=6)
        status_hdr.pack(fill=tk.X)
        tk.Label(status_hdr, text="  🖥️  Live System Status",
                 font=FONT_B, bg=BG2, fg=FG2).pack(anchor="w")

        self.status_frame = tk.Frame(left, bg=BG2, padx=12, pady=8)
        self.status_frame.pack(fill=tk.X, pady=(0, 8))

        self.cpu_bar  = self._metric_row(self.status_frame, "CPU")
        self.ram_bar  = self._metric_row(self.status_frame, "RAM")
        self.disk_bar = self._metric_row(self.status_frame, "Disk")

        # Extra info row
        self.info_frame = tk.Frame(left, bg=BG2, padx=12, pady=4)
        self.info_frame.pack(fill=tk.X, pady=(0, 8))
        self.net_lbl    = tk.Label(self.info_frame, text="Net: --", font=FONT_SM, bg=BG2, fg=FG2)
        self.net_lbl.pack(side=tk.LEFT, padx=(0, 16))
        self.uptime_lbl = tk.Label(self.info_frame, text="Up: --", font=FONT_SM, bg=BG2, fg=FG2)
        self.uptime_lbl.pack(side=tk.LEFT)

        # ── AI Issues Panel ───────────────────────────────────────────────────
        issues_hdr = tk.Frame(left, bg=BG2, pady=6)
        issues_hdr.pack(fill=tk.X)
        tk.Label(issues_hdr, text="  🤖  AI Analysis",
                 font=FONT_B, bg=BG2, fg=FG2).pack(anchor="w", side=tk.LEFT)
        self.ai_mode_lbl = tk.Label(issues_hdr, text="", font=FONT_SM, bg=BG2, fg=FG2)
        self.ai_mode_lbl.pack(side=tk.RIGHT, padx=8)

        self.issues_canvas_frame = tk.Frame(left, bg=BG2)
        self.issues_canvas_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.issues_canvas_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.issues_canvas = tk.Canvas(self.issues_canvas_frame, bg=BG2,
                                        highlightthickness=0,
                                        yscrollcommand=scrollbar.set)
        self.issues_canvas.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.issues_canvas.yview)

        self.issues_inner = tk.Frame(self.issues_canvas, bg=BG2)
        self.issues_canvas.create_window((0, 0), window=self.issues_inner, anchor="nw")
        self.issues_inner.bind("<Configure>", lambda e: self.issues_canvas.configure(
            scrollregion=self.issues_canvas.bbox("all")))

        # Analyze button
        self.analyze_btn = tk.Button(left, text="🔍  Analyze Now",
                                      font=FONT_B, bg=ACCENT, fg=FG, bd=0,
                                      padx=10, pady=8, cursor="hand2",
                                      command=self._run_analysis,
                                      activebackground=ACCENT2, activeforeground=FG)
        self.analyze_btn.pack(fill=tk.X, pady=(8, 0))

        # ── Right panel: Quick Actions ────────────────────────────────────────
        right = tk.Frame(body, bg=BG2, width=200, padx=10, pady=10)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        tk.Label(right, text="Quick Actions", font=FONT_B, bg=BG2, fg=FG2).pack(pady=(0, 8))

        actions = [
            ("🤖 AI Terminal",      lambda: launch_tool("ridos_shell.py")),
            ("🏥 System Doctor",    lambda: launch_tool("system_doctor.py")),
            ("🌐 Network Analyzer", lambda: launch_tool("network_analyzer.py")),
            ("💾 Hardware Fixer",   lambda: launch_tool("hardware_fixer.py")),
            ("🔒 Security Scan",    lambda: launch_tool("security_scanner.py")),
            ("📦 Software Center",  launch_software_center),
            ("📋 Health Report",    lambda: launch_tool("health_report.py --full")),
        ]

        for label, cmd in actions:
            btn = tk.Button(right, text=label, font=FONT_SM,
                            bg=BG3, fg=FG, bd=0, anchor="w",
                            padx=8, pady=7, cursor="hand2",
                            command=cmd,
                            activebackground=ACCENT, activeforeground=FG)
            btn.pack(fill=tk.X, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=ACCENT))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG3))

        # Separator
        tk.Frame(right, bg=ACCENT, height=1).pack(fill=tk.X, pady=10)
        tk.Label(right, text="Safe Fixes", font=FONT_B, bg=BG2, fg=FG2).pack(pady=(0, 6))

        safe_btns = [
            ("🧹 Clear RAM Cache",  "clear_cache"),
            ("🗑️ Clean System",     "system_clean"),
            ("🔄 Restart Network",  "restart_network"),
            ("🔥 Enable Firewall",  "enable_firewall"),
            ("⏰ Sync Time",        "sync_time"),
        ]
        for label, action in safe_btns:
            btn = tk.Button(right, text=label, font=FONT_SM,
                            bg=BG3, fg=FG2, bd=0, anchor="w",
                            padx=8, pady=6, cursor="hand2",
                            command=lambda a=action: run_safe_action(a),
                            activebackground=ACCENT, activeforeground=FG)
            btn.pack(fill=tk.X, pady=1)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=ACCENT))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG3))

        # ── Footer ────────────────────────────────────────────────────────────
        footer = tk.Frame(self, bg=BG2, height=30)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        self.footer_lbl = tk.Label(footer,
                                    text="RIDOS OS v1.1.0 Baghdad  •  Auto-refreshing every 10s",
                                    font=FONT_SM, bg=BG2, fg=FG2)
        self.footer_lbl.pack(pady=6)

    def _metric_row(self, parent, label):
        """Create a labeled progress bar metric row."""
        row = tk.Frame(parent, bg=BG2)
        row.pack(fill=tk.X, pady=3)

        tk.Label(row, text=f"{label}:", font=FONT_SM, bg=BG2,
                 fg=FG2, width=6, anchor="w").pack(side=tk.LEFT)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(f"{label}.Horizontal.TProgressbar",
                        background=GREEN, troughcolor=BG3, thickness=14)
        bar = ttk.Progressbar(row, length=150, mode="determinate",
                               style=f"{label}.Horizontal.TProgressbar")
        bar.pack(side=tk.LEFT, padx=(4, 8))

        val_lbl = tk.Label(row, text="--", font=FONT_C, bg=BG2, fg=FG, width=14, anchor="w")
        val_lbl.pack(side=tk.LEFT)

        return bar, val_lbl

    def _update_metric(self, bar_tuple, value, detail=""):
        """Update a metric bar with color coding."""
        bar, lbl = bar_tuple
        value = min(100, max(0, value))
        bar["value"] = value

        color = GREEN if value < 60 else (YELLOW if value < 80 else RED)
        style_name = bar.cget("style").split(".")[0]
        ttk.Style().configure(f"{style_name}.Horizontal.TProgressbar", background=color)

        lbl.config(text=f"{value:.0f}%  {detail}")

    def _update_status_display(self, data):
        """Update all status labels from collected data."""
        self._update_metric(self.cpu_bar, data["cpu"],
                            f"{'🌡️ ' + str(int(data['cpu_temp'])) + '°C' if data['cpu_temp'] > 0 else ''}")
        self._update_metric(self.ram_bar, data["ram"],
                            f"{data['ram_used']}/{data['ram_total']}")
        self._update_metric(self.disk_bar, data["disk"],
                            f"{data['disk_used']}/{data['disk_total']}")

        net_text = f"🌐 {data['ip'] or 'no IP'}" if data["internet"] else "📴 Offline"
        net_color = GREEN if data["internet"] else RED
        self.net_lbl.config(text=net_text, fg=net_color)
        self.uptime_lbl.config(text=f"⏱️ {data['uptime']}")

        mode_text = "● Online" if data["internet"] else "● Offline"
        mode_color = GREEN if data["internet"] else YELLOW
        self.mode_lbl.config(text=mode_text, fg=mode_color)

    def _update_issues_display(self, analysis):
        """Render AI analysis results in the issues panel."""
        for w in self.issues_inner.winfo_children():
            w.destroy()

        mode = analysis.get("mode", "offline")
        ai_tag = "🌐 Claude AI" if mode == "online" else "📴 Local Rules"
        self.ai_mode_lbl.config(text=ai_tag)

        summary = analysis.get("summary", "")
        if summary:
            tk.Label(self.issues_inner, text=summary, font=FONT_SM,
                     bg=BG2, fg=FG2, wraplength=340, justify="left").pack(
                anchor="w", padx=8, pady=(6, 4))

        issues = analysis.get("issues", [])
        if not issues:
            tk.Label(self.issues_inner, text="✅  System is healthy — no issues detected",
                     font=FONT_B, bg=BG2, fg=GREEN).pack(pady=12, padx=8)
            return

        sev_colors = {"high": RED, "medium": YELLOW, "low": FG2}
        sev_icons  = {"high": "🔴", "medium": "🟡", "low": "🔵"}

        for issue in issues:
            problem  = issue.get("problem", "Unknown issue")
            action   = issue.get("action")
            severity = issue.get("severity", "medium")

            card = tk.Frame(self.issues_inner, bg=BG3, padx=10, pady=8)
            card.pack(fill=tk.X, padx=6, pady=3)

            icon  = sev_icons.get(severity, "⚪")
            color = sev_colors.get(severity, FG2)

            tk.Label(card, text=f"{icon}  {problem}", font=FONT_SM,
                     bg=BG3, fg=color, wraplength=300, justify="left",
                     anchor="w").pack(anchor="w")

            if action and action in SAFE_ACTIONS:
                _, desc = SAFE_ACTIONS[action]
                fix_btn = tk.Button(card, text=f"⚡ Fix: {desc}",
                                    font=FONT_SM, bg=ACCENT, fg=FG, bd=0,
                                    padx=8, pady=4, cursor="hand2",
                                    command=lambda a=action: run_safe_action(a),
                                    activebackground=ACCENT2, activeforeground=FG)
                fix_btn.pack(anchor="w", pady=(4, 0))

    def _run_analysis(self):
        """Collect data and run AI analysis in background thread."""
        self.analyze_btn.config(text="⏳ Analyzing...", state=tk.DISABLED)
        self.footer_lbl.config(text="Collecting system data...")

        def worker():
            data     = collect_system_data()
            analysis = ai_analyze(data)
            self._system_data = data
            self._analysis    = analysis
            # Update UI on main thread
            self.after(0, lambda: self._update_status_display(data))
            self.after(0, lambda: self._update_issues_display(analysis))
            self.after(0, lambda: self.analyze_btn.config(
                text="🔍  Analyze Now", state=tk.NORMAL))
            self.after(0, lambda: self.footer_lbl.config(
                text=f"RIDOS OS v1.1.0 Baghdad  •  Last updated: {time.strftime('%H:%M:%S')}  •  Auto-refresh every 10s"))

        threading.Thread(target=worker, daemon=True).start()

    def _auto_refresh(self):
        """Auto-refresh every 10 seconds — makes it feel alive."""
        self._run_analysis()
        self.after(10000, self._auto_refresh)


# ─────────────────────────────────────────────────────────────────────────────
# FIRST BOOT WELCOME (replaces neofetch terminal)
# ─────────────────────────────────────────────────────────────────────────────

class WelcomeScreen(tk.Toplevel):
    """Simple welcome dialog shown on first boot."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Welcome to RIDOS OS")
        self.geometry("480x320")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 480) // 2
        y = (self.winfo_screenheight() - 320) // 2
        self.geometry(f"+{x}+{y}")

        # Header
        hdr = tk.Frame(self, bg=ACCENT, height=60)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚡  Welcome to RIDOS OS v1.1.0 Baghdad",
                 font=FONT_B, bg=ACCENT, fg=FG).pack(pady=16)

        # Message
        tk.Label(self, text="Field Engineer OS  •  AI-Powered Linux",
                 font=FONT_SM, bg=BG, fg=FG2).pack(pady=(12, 4))
        tk.Label(self, text="Username: ridos  |  Password: ridos",
                 font=FONT_SM, bg=BG, fg=FG2).pack(pady=4)

        # Action buttons
        btn_frame = tk.Frame(self, bg=BG, pady=20)
        btn_frame.pack()

        self._make_btn(btn_frame, "🖥️  Open Control Center", self.destroy, ACCENT)
        self._make_btn(btn_frame, "🔍  Run Full Diagnosis",
                       lambda: [self.destroy(), parent.after(500, parent._run_analysis)], BG3)
        self._make_btn(btn_frame, "📦  Open Software Center",
                       lambda: [self.destroy(), launch_software_center()], BG3)

        tk.Label(self, text="This screen only appears once",
                 font=FONT_SM, bg=BG, fg=BG3).pack(side=tk.BOTTOM, pady=8)

    def _make_btn(self, parent, text, cmd, bg):
        tk.Button(parent, text=text, font=FONT_B, bg=bg, fg=FG, bd=0,
                  padx=16, pady=10, cursor="hand2", width=28,
                  command=cmd,
                  activebackground=ACCENT2, activeforeground=FG).pack(pady=4)


def main():
    app = RIDOSControlCenter()

    # Show welcome screen on first boot
    flag = os.path.expanduser("~/.ridos-welcome-shown")
    if not os.path.exists(flag):
        WelcomeScreen(app)
        open(flag, "w").close()

    app.mainloop()


if __name__ == "__main__":
    main()
