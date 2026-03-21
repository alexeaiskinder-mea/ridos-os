#!/usr/bin/env python3
"""
RIDOS OS v1.1.0 Baghdad
Control Center v5 - Visual Intelligent Dashboard
AI-Powered System Management with Safe Auto-Fix
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, json, os, sys, threading, time, socket
from datetime import datetime

# ── Colors ────────────────────────────────────────────────────
BG       = "#0F0A1E"
BG2      = "#1E1B4B"
BG3      = "#2D1B69"
PURPLE   = "#6B21A8"
PURPLE2  = "#7C3AED"
PURPLE3  = "#A78BFA"
TEXT     = "#E9D5FF"
TEXT2    = "#C4B5FD"
GREEN    = "#10B981"
YELLOW   = "#F59E0B"
RED      = "#EF4444"
CYAN     = "#06B6D4"
WHITE    = "#FFFFFF"
GRAY     = "#374151"

# ── Safe Actions (AI can only trigger these) ──────────────────
SAFE_ACTIONS = {
    "clear_cache":       "sync; echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null",
    "system_clean":      "sudo apt-get autoremove -y && sudo apt-get autoclean -y",
    "update_system":     "sudo apt-get update -qq && sudo apt-get upgrade -y",
    "restart_network":   "sudo systemctl restart NetworkManager",
    "fix_dns":           "echo 'nameserver 1.1.1.1' | sudo tee /etc/resolv.conf > /dev/null",
    "enable_firewall":   "sudo ufw enable",
    "restart_display":   "sudo systemctl restart lightdm",
    "kill_zombies":      "sudo kill $(ps aux | awk '$8==\"Z\" {print $2}') 2>/dev/null || true",
    "fix_disk":          "sudo fsck -y /dev/sda 2>/dev/null || true",
    "check_temps":       "sensors 2>/dev/null || echo 'lm-sensors not installed'",
}

# ── API Configuration ─────────────────────────────────────────
API_KEY_FILE = "/etc/ridos/api.key"
API_URL      = "https://api.anthropic.com/v1/messages"
MODEL        = "claude-haiku-4-5-20251001"

def load_api_key():
    try:
        with open(API_KEY_FILE) as f:
            return f.read().strip()
    except:
        return os.environ.get("ANTHROPIC_API_KEY", "")

def check_internet():
    try:
        socket.setdefaulttimeout(3)
        socket.socket().connect(("8.8.8.8", 53))
        return True
    except:
        return False

def get_system_data():
    """Collect real system metrics"""
    import psutil
    cpu    = psutil.cpu_percent(interval=0.5)
    mem    = psutil.virtual_memory()
    disk   = psutil.disk_usage('/')
    net    = psutil.net_io_counters()
    uptime = int(time.time() - psutil.boot_time())
    procs  = sorted(psutil.process_iter(['pid','name','cpu_percent','memory_percent']),
                    key=lambda p: p.info['cpu_percent'] or 0, reverse=True)[:5]
    return {
        "cpu_percent":   round(cpu, 1),
        "cpu_count":     psutil.cpu_count(),
        "ram_percent":   round(mem.percent, 1),
        "ram_used_gb":   round(mem.used/1024**3, 1),
        "ram_total_gb":  round(mem.total/1024**3, 1),
        "disk_percent":  round(disk.percent, 1),
        "disk_used_gb":  round(disk.used/1024**3, 1),
        "disk_total_gb": round(disk.total/1024**3, 1),
        "uptime_h":      uptime // 3600,
        "uptime_m":      (uptime % 3600) // 60,
        "internet":      check_internet(),
        "api_ready":     bool(load_api_key()),
        "top_procs":     [{"name": p.info['name'], "cpu": p.info['cpu_percent']}
                          for p in procs],
    }

def ask_ai(data):
    """Ask Claude AI to analyze system and return JSON actions"""
    try:
        import urllib.request
        api_key = load_api_key()
        if not api_key or not check_internet():
            return local_analysis(data)

        prompt = f"""Analyze this Linux system data and return ONLY a JSON object.
System: CPU={data['cpu_percent']}% RAM={data['ram_percent']}% Disk={data['disk_percent']}%
Uptime={data['uptime_h']}h Internet={'Yes' if data['internet'] else 'No'}
Top processes: {[p['name'] for p in data['top_procs']]}

Return ONLY this JSON format (no other text):
{{"status": "healthy|warning|critical", "message": "brief status in English and Arabic", "issues": [{{"problem": "description", "action": "safe_action_key"}}]}}

Available actions: clear_cache, system_clean, update_system, restart_network, fix_dns, enable_firewall, kill_zombies
Only include issues that actually need fixing."""

        payload = json.dumps({
            "model": MODEL,
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()

        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            text = resp["content"][0]["text"].strip()
            # Extract JSON from response
            start = text.find('{')
            end   = text.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
    except Exception as e:
        pass
    return local_analysis(data)

def local_analysis(data):
    """Offline fallback analysis"""
    issues  = []
    status  = "healthy"
    message = "System is running normally "

    if data['cpu_percent'] > 85:
        status = "critical"
        issues.append({"problem": "⚠️ Critical CPU usage detected ", "action": "kill_zombies"})
    elif data['cpu_percent'] > 70:
        status = "warning"
        issues.append({"problem": "⚠️ High CPU usage ", "action": None})

    if data['ram_percent'] > 85:
        status = "critical"
        issues.append({"problem": "⚠️ Critical RAM usage ", "action": "clear_cache"})
    elif data['ram_percent'] > 75:
        status = "warning"
        issues.append({"problem": "⚠️ High RAM usage ", "action": "clear_cache"})

    if data['disk_percent'] > 90:
        status = "critical"
        issues.append({"problem": "⚠️ Disk almost full ", "action": "system_clean"})
    elif data['disk_percent'] > 80:
        status = "warning"
        issues.append({"problem": "⚠️ Disk usage high ", "action": "system_clean"})

    if not data['internet']:
        issues.append({"problem": "⚠️ No internet connection ", "action": "restart_network"})

    if status != "healthy":
        message = f"Issues detected: {len(issues)}  issues found: {len(issues)}"

    return {"status": status, "message": message, "issues": issues}


# ════════════════════════════════════════════════════════════════
# MAIN UI
# ════════════════════════════════════════════════════════════════
class RIDOSControlCenter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RIDOS Control Center")
        self.root.geometry("720x600")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.data     = {}
        self.decision = {}
        self.running  = True

        self._build_ui()
        self._start_auto_refresh()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=PURPLE, pady=8)
        hdr.pack(fill='x')
        tk.Label(hdr, text="  RIDOS OS", font=("DejaVu Sans", 20, "bold"),
                 bg=PURPLE, fg=WHITE).pack(side='left', padx=10)
        tk.Label(hdr, text="Control Center",
                 font=("Arial", 12), bg=PURPLE, fg=TEXT2).pack(side='left')
        self.status_dot = tk.Label(hdr, text="●", font=("Arial", 16),
                                    bg=PURPLE, fg=YELLOW)
        self.status_dot.pack(side='right', padx=15)
        self.time_label = tk.Label(hdr, text="", font=("Arial", 10),
                                    bg=PURPLE, fg=TEXT2)
        self.time_label.pack(side='right', padx=5)

        # ── System Status Row ─────────────────────────────────
        status_row = tk.Frame(self.root, bg=BG2, pady=10)
        status_row.pack(fill='x', padx=10, pady=(8,0))

        self.cpu_card  = self._stat_card(status_row, "CPU",  "--", "cores")
        self.ram_card  = self._stat_card(status_row, "RAM",  "--", "GB")
        self.disk_card = self._stat_card(status_row, "DISK", "--", "GB")
        self.net_card  = self._stat_card(status_row, "NET",  "--", "")

        for card in [self.cpu_card, self.ram_card, self.disk_card, self.net_card]:
            card['frame'].pack(side='left', expand=True, fill='both', padx=5)

        # ── AI Status Message ─────────────────────────────────
        self.ai_msg = tk.Label(self.root, text="🤖 Analyzing system...",
                                font=("Arial", 11), bg=BG, fg=PURPLE3)
        self.ai_msg.pack(pady=(10,0))

        # ── Issues Panel ──────────────────────────────────────
        issues_lbl = tk.Frame(self.root, bg=BG)
        issues_lbl.pack(fill='x', padx=10, pady=(5,0))
        tk.Label(issues_lbl, text="⚠  Detected Issues",
                 font=("Arial", 11, "bold"), bg=BG, fg=TEXT2).pack(side='left')

        self.issues_frame = tk.Frame(self.root, bg=BG2, padx=10, pady=8)
        self.issues_frame.pack(fill='both', expand=True, padx=10, pady=5)
        tk.Label(self.issues_frame, text="Scanning...", bg=BG2, fg=GRAY,
                 font=("Arial", 10)).pack()

        # ── Action Buttons ────────────────────────────────────
        btn_row = tk.Frame(self.root, bg=BG, pady=8)
        btn_row.pack(fill='x', padx=10)

        buttons = [
            ("🔄 Refresh & Analyze", self._refresh, PURPLE),
            ("🛠️  AI Terminal",       self._open_ai_terminal, BG3),
            ("📦 Software Center",   self._open_software, BG3),
            ("🌐 Network Scan",      self._run_network, BG3),
            ("🔒 Security Scan",     self._run_security, BG3),
        ]
        for text, cmd, color in buttons:
            tk.Button(btn_row, text=text, command=cmd,
                      bg=color, fg=WHITE, font=("Arial", 10, "bold"),
                      relief='flat', padx=8, pady=6,
                      cursor='hand2').pack(side='left', padx=3, expand=True)

        # ── Footer ────────────────────────────────────────────
        footer = tk.Frame(self.root, bg=BG, pady=4)
        footer.pack(fill='x')
        self.footer_msg = tk.Label(footer,
            text="RIDOS OS v1.1.0 Baghdad  |  AI-Powered Linux  |  GPL v3",
            font=("Arial", 9), bg=BG, fg=GRAY)
        self.footer_msg.pack()

    def _stat_card(self, parent, title, value, unit):
        frame = tk.Frame(parent, bg=BG3, padx=8, pady=8)
        tk.Label(frame, text=title, font=("Arial", 9), bg=BG3, fg=PURPLE3).pack()
        val_lbl = tk.Label(frame, text=value, font=("DejaVu Sans", 18, "bold"),
                           bg=BG3, fg=WHITE)
        val_lbl.pack()
        bar = ttk.Progressbar(frame, length=80, mode='determinate')
        bar.pack(pady=2)
        sub_lbl = tk.Label(frame, text=unit, font=("Arial", 8),
                           bg=BG3, fg=GRAY)
        sub_lbl.pack()
        return {'frame': frame, 'val': val_lbl, 'bar': bar, 'sub': sub_lbl}

    def _update_card(self, card, value, percent, sub_text):
        color = GREEN if percent < 60 else YELLOW if percent < 80 else RED
        card['val'].config(text=str(value), fg=color)
        card['bar']['value'] = min(percent, 100)
        card['sub'].config(text=sub_text)

    def _refresh(self):
        self.ai_msg.config(text="🤖 Analyzing system...", fg=YELLOW)
        self.root.update()
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _do_refresh(self):
        try:
            self.data     = get_system_data()
            self.decision = ask_ai(self.data)
            self.root.after(0, self._update_ui)
        except Exception as e:
            self.root.after(0, lambda: self.ai_msg.config(
                text=f"⚠️ Error: {str(e)[:50]}", fg=RED))

    def _update_ui(self):
        d  = self.data
        dc = self.decision

        # Update cards
        self._update_card(self.cpu_card,
            f"{d['cpu_percent']}%", d['cpu_percent'],
            f"{d['cpu_count']} cores")
        self._update_card(self.ram_card,
            f"{d['ram_percent']}%", d['ram_percent'],
            f"{d['ram_used_gb']}/{d['ram_total_gb']}GB")
        self._update_card(self.disk_card,
            f"{d['disk_percent']}%", d['disk_percent'],
            f"{d['disk_used_gb']}/{d['disk_total_gb']}GB")

        net_color = GREEN if d['internet'] else RED
        net_text  = "Online" if d['internet'] else "Offline"
        self.net_card['val'].config(text=net_text, fg=net_color)
        self.net_card['bar']['value'] = 100 if d['internet'] else 0
        self.net_card['sub'].config(text="Internet")

        # Status dot
        status = dc.get('status', 'healthy')
        dot_color = {
            'healthy': GREEN, 'warning': YELLOW, 'critical': RED
        }.get(status, YELLOW)
        self.status_dot.config(fg=dot_color)

        # AI message
        api_status = "🌐 🌐 Online" if (d['internet'] and d['api_ready']) else "⚡ Offline"
        self.ai_msg.config(
            text=f"{api_status}  —  {dc.get('message', 'Analyzing...')}",
            fg=PURPLE3)

        # Issues
        for w in self.issues_frame.winfo_children():
            w.destroy()

        issues = dc.get('issues', [])
        if not issues:
            tk.Label(self.issues_frame,
                text="✅  System Healthy — No issues detected | النظام بصحة جيدة",
                font=("Arial", 11), bg=BG2, fg=GREEN).pack(pady=10)
        else:
            for issue in issues:
                row = tk.Frame(self.issues_frame, bg=BG2)
                row.pack(fill='x', pady=3)
                # Extract English only to avoid Arabic rendering issues
                problem_text = issue.get('problem', '')
                if '|' in problem_text:
                    problem_text = problem_text.split('|')[0].strip()
                tk.Label(row, text=problem_text,
                         font=("Arial", 10), bg=BG2, fg=TEXT,
                         wraplength=500, justify='left').pack(side='left', expand=True, anchor='w')
                action = issue.get('action')
                if action and action in SAFE_ACTIONS:
                    tk.Button(row, text="Fix Now",
                              command=lambda a=action: self._run_action(a),
                              bg=PURPLE, fg=WHITE, font=("Arial", 9, "bold"),
                              relief='flat', padx=8, pady=3,
                              cursor='hand2').pack(side='right', padx=5)

        # Uptime in footer
        self.footer_msg.config(
            text=f"RIDOS OS v1.1.0 Baghdad  |  Uptime: {d['uptime_h']}h {d['uptime_m']}m  |  GPL v3")

        # Time
        self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))

    def _run_action(self, action_key):
        if action_key not in SAFE_ACTIONS:
            messagebox.showerror("Error", f"Unknown action: {action_key}")
            return
        cmd = SAFE_ACTIONS[action_key]
        if messagebox.askyesno("Confirm Action",
            f"Run safe action: {action_key}?\n\nCommand: {cmd}"):
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=30)
                msg = f"✅ Action completed!\n\n{result.stdout[:300]}"
                if result.returncode != 0:
                    msg += f"\n\nWarning: {result.stderr[:200]}"
                messagebox.showinfo("Done", msg)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _open_ai_terminal(self):
        subprocess.Popen([
            "xfce4-terminal", "--title=RIDOS AI Terminal",
            "-e", "python3 /opt/ridos/bin/ai_features.py"
        ])

    def _open_software(self):
        subprocess.Popen([
            "firefox-esr",
            "/opt/ridos/bin/ridos-dashboard.html"
        ])

    def _run_network(self):
        subprocess.Popen([
            "xfce4-terminal", "--title=AI Network Analyzer",
            "-e", "bash -c 'python3 /opt/ridos/bin/ai_features.py 3; read'"
        ])

    def _run_security(self):
        subprocess.Popen([
            "xfce4-terminal", "--title=AI Security Scanner",
            "-e", "bash -c 'python3 /opt/ridos/bin/ai_features.py 5; read'"
        ])

    def _start_auto_refresh(self):
        self._refresh()
        # Auto-refresh every 10 seconds
        def auto():
            while self.running:
                time.sleep(10)
                if self.running:
                    self.root.after(0, self._refresh)
        threading.Thread(target=auto, daemon=True).start()

    def _on_close(self):
        self.running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        subprocess.run(["pip3", "install", "psutil", "--break-system-packages", "-q"])
        import psutil

    app = RIDOSControlCenter()
    app.run()
