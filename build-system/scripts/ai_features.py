#!/usr/bin/env python3
"""
RIDOS OS - Advanced AI Features v2.0
Bilingual Arabic & English AI Tools for IT Professionals
Works with limited/poor internet - offline fallback included
"""

import os, sys, json, subprocess, socket, re
import psutil, time
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except:
    HAS_REQUESTS = False

# ─── Colors ───────────────────────────────────────────────────
PURPLE="\033[35m"; CYAN="\033[36m"; GREEN="\033[32m"
RED="\033[31m"; YELLOW="\033[33m"; WHITE="\033[37m"
BOLD="\033[1m"; RESET="\033[0m"

# ─── API Configuration ─────────────────────────────────────────
API_KEY_FILE = "/etc/ridos/api.key"
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"
MAX_RETRIES = 3
TIMEOUT = 20  # short timeout for poor connections

def load_api_key():
    try:
        with open(API_KEY_FILE,'r') as f: return f.read().strip()
    except: return os.environ.get("ANTHROPIC_API_KEY","")

def check_internet(timeout=5):
    """Quick internet check - tries multiple hosts"""
    for host, port in [("8.8.8.8",53),("1.1.1.1",53),("208.67.222.222",53)]:
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect((host,port))
            return True
        except: continue
    return False

def ask_claude(prompt, system_prompt="", max_tokens=800):
    """AI call with retry logic for poor connections"""
    if not HAS_REQUESTS:
        return offline_analysis(prompt)

    api_key = load_api_key()
    if not api_key:
        return "❌ API key missing at /etc/ridos/api.key\n❌ مفتاح API غير موجود في /etc/ridos/api.key"

    if not check_internet():
        return offline_analysis(prompt)

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    # Trim prompt for poor connections
    if len(prompt) > 2000:
        prompt = prompt[:2000] + "\n[truncated for bandwidth]"

    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role":"user","content": prompt}]
    }
    if system_prompt:
        body["system"] = system_prompt

    for attempt in range(MAX_RETRIES):
        try:
            print(f"  {YELLOW}Connecting to AI... (attempt {attempt+1}/{MAX_RETRIES}){RESET}")
            r = requests.post(API_URL, headers=headers, json=body,
                            timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()["content"][0]["text"]
        except requests.exceptions.Timeout:
            print(f"  {YELLOW}Timeout - retrying...{RESET}")
            time.sleep(2)
        except requests.exceptions.ConnectionError:
            print(f"  {RED}Connection failed - using offline mode{RESET}")
            return offline_analysis(prompt)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                return offline_analysis(prompt)
            time.sleep(2)
    return offline_analysis(prompt)

def offline_analysis(prompt):
    """Offline fallback - rule-based analysis when no internet"""
    result = []
    result.append(f"{YELLOW}⚡ OFFLINE MODE - No internet connection detected{RESET}")
    result.append(f"{YELLOW}⚡ وضع عدم الاتصال - لم يتم اكتشاف اتصال بالإنترنت{RESET}\n")

    p = prompt.lower()

    # CPU analysis
    if 'cpu' in p:
        cpu = psutil.cpu_percent()
        if cpu > 90:
            result.append(f"🔴 CPU CRITICAL ({cpu}%) | المعالج حرج - Close heavy applications")
        elif cpu > 70:
            result.append(f"🟡 CPU HIGH ({cpu}%) | المعالج مرتفع - Monitor usage")
        else:
            result.append(f"🟢 CPU OK ({cpu}%) | المعالج جيد")

    # Memory analysis
    if 'mem' in p or 'ram' in p:
        mem = psutil.virtual_memory()
        if mem.percent > 90:
            result.append(f"🔴 RAM CRITICAL ({mem.percent}%) | الذاكرة حرجة - Free memory immediately")
        elif mem.percent > 75:
            result.append(f"🟡 RAM HIGH ({mem.percent}%) | الذاكرة مرتفعة - Consider closing apps")
        else:
            result.append(f"🟢 RAM OK ({mem.percent}%) | الذاكرة جيدة")

    # Disk analysis
    if 'disk' in p or 'hdd' in p or 'ssd' in p:
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            result.append(f"🔴 DISK CRITICAL ({disk.percent}%) | القرص حرج - Free disk space now")
        elif disk.percent > 75:
            result.append(f"🟡 DISK HIGH ({disk.percent}%) | القرص مرتفع - Clean up files")
        else:
            result.append(f"🟢 DISK OK ({disk.percent}%) | القرص جيد")

    # Network analysis
    if 'network' in p or 'net' in p:
        result.append(f"🔴 Network offline | الشبكة غير متصلة")
        result.append(f"  → Check cable/WiFi connection | تحقق من الكابل/الواي فاي")
        result.append(f"  → Run: sudo systemctl restart NetworkManager")
        result.append(f"  → Run: ip addr show")

    if not result[2:]:
        result.append("📊 Local analysis complete. Connect to internet for AI insights.")
        result.append("📊 اكتمل التحليل المحلي. اتصل بالإنترنت للحصول على رؤى الذكاء الاصطناعي.")

    return '\n'.join(result)

def print_banner(en, ar):
    print(f"\n{BOLD}{PURPLE}{'='*62}{RESET}")
    print(f"{BOLD}{PURPLE}  {en}{RESET}")
    print(f"{BOLD}{PURPLE}  {ar}{RESET}")
    print(f"{BOLD}{PURPLE}{'='*62}{RESET}\n")

def print_section(en, ar=""):
    print(f"\n{BOLD}{CYAN}── {en}{' | '+ar if ar else ''} ──{RESET}")

def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                          text=True, timeout=timeout)
        return r.stdout + r.stderr
    except: return ""

# ════════════════════════════════════════════════════════════════
# 1. AI TERMINAL ASSISTANT
# ════════════════════════════════════════════════════════════════
def run_terminal_assistant():
    print_banner("RIDOS AI Terminal Assistant","مساعد طرفية ريدوس الذكي")
    print(f"{WHITE}Type commands - AI fixes errors automatically (Arabic & English){RESET}")
    print(f"{WHITE}اكتب الأوامر - يصلح الذكاء الاصطناعي الأخطاء تلقائياً{RESET}")
    print(f"{YELLOW}Type 'exit' to quit | اكتب 'exit' للخروج{RESET}\n")

    SYSTEM = """You are a bilingual Linux expert for RIDOS OS.
When given a failed command and error, respond concisely in BOTH English AND Arabic:

🔍 What happened | ماذا حدث: [1 line each language]
✅ Fix | الحل: [correct command]
💡 Tip | نصيحة: [1 line each language]

Keep it SHORT - user may have slow internet."""

    while True:
        try:
            cmd = input(f"{PURPLE}ridos@ai{RESET}:{CYAN}~{RESET}$ ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{YELLOW}Goodbye! مع السلامة!{RESET}"); break
        if cmd.lower() in ['exit','quit','خروج']:
            print(f"{YELLOW}Goodbye! مع السلامة!{RESET}"); break
        if not cmd: continue

        result = subprocess.run(cmd, shell=True, capture_output=True,
                               text=True, timeout=30)
        if result.stdout: print(result.stdout)
        if result.returncode != 0:
            print(f"{RED}✗ Error (code {result.returncode}): {result.stderr[:200]}{RESET}")
            print(f"\n{YELLOW}🤖 AI analyzing... يحلل...{RESET}")
            prompt = f"Command: {cmd}\nExit code: {result.returncode}\nError: {result.stderr[:300]}"
            print(f"{GREEN}{ask_claude(prompt, SYSTEM, 400)}{RESET}\n")
        else:
            print(f"{GREEN}✓ OK{RESET}")

# ════════════════════════════════════════════════════════════════
# 2. AI SYSTEM DOCTOR
# ════════════════════════════════════════════════════════════════
def run_system_doctor():
    print_banner("RIDOS AI System Doctor","طبيب نظام ريدوس الذكي")
    print(f"{YELLOW}Scanning... جاري الفحص...{RESET}\n")

    data = {}
    data['cpu_percent'] = psutil.cpu_percent(interval=2)
    data['cpu_count'] = psutil.cpu_count()
    mem = psutil.virtual_memory()
    data['mem_used_gb'] = round(mem.used/(1024**3),2)
    data['mem_total_gb'] = round(mem.total/(1024**3),2)
    data['mem_percent'] = mem.percent
    disk = psutil.disk_usage('/')
    data['disk_used_gb'] = round(disk.used/(1024**3),2)
    data['disk_total_gb'] = round(disk.total/(1024**3),2)
    data['disk_percent'] = disk.percent
    data['uptime_h'] = round((time.time()-psutil.boot_time())/3600,1)
    data['top_procs'] = [p.info for p in sorted(
        psutil.process_iter(['pid','name','cpu_percent','memory_percent']),
        key=lambda x: x.info['cpu_percent'] or 0, reverse=True)[:5]]

    print_section("System Status","حالة النظام")
    print(f"  🖥️  CPU:    {data['cpu_percent']}% ({data['cpu_count']} cores)")
    print(f"  🧠  RAM:    {data['mem_used_gb']}/{data['mem_total_gb']}GB ({data['mem_percent']}%)")
    print(f"  💾  Disk:   {data['disk_used_gb']}/{data['disk_total_gb']}GB ({data['disk_percent']}%)")
    print(f"  ⏱️  Uptime: {data['uptime_h']}h")
    print_section("Top Processes","أكثر العمليات استهلاكاً")
    for p in data['top_procs']:
        print(f"  [{p['pid']}] {p['name'][:18]:<18} CPU:{p['cpu_percent']}% RAM:{round(p['memory_percent'] or 0,1)}%")

    print(f"\n{YELLOW}🤖 AI analyzing... يحلل...{RESET}\n")
    SYSTEM = """Bilingual system health expert. Respond in English AND Arabic.
Format: Status [GOOD/WARNING/CRITICAL], key findings, top 3 recommendations. Keep SHORT."""
    prompt = f"System data: CPU={data['cpu_percent']}% RAM={data['mem_percent']}% Disk={data['disk_percent']}% Uptime={data['uptime_h']}h Top processes: {[p['name'] for p in data['top_procs']]}"
    print(f"{GREEN}{ask_claude(prompt, SYSTEM, 600)}{RESET}\n")

# ════════════════════════════════════════════════════════════════
# 3. AI NETWORK ANALYZER (Advanced)
# ════════════════════════════════════════════════════════════════
def run_network_analyzer():
    print_banner("RIDOS AI Network Analyzer","Advanced Network Diagnostics")

    net_data = {}

    # Interfaces
    print_section("Network Interfaces","")
    try:
        iface_output = run_cmd("ip addr show") or "N/A"
        net_data['interfaces'] = iface_output[:800]
        for line in iface_output.split('\n'):
            if line.strip() and ('inet ' in line or ('state UP' in line)):
                print(f"  {CYAN}{line.strip()}{RESET}")
    except Exception as e:
        print(f"  {YELLOW}Skipped: {e}{RESET}")
        net_data['interfaces'] = 'N/A'

    # Routing
    print_section("Default Gateway","")
    try:
        route_out = run_cmd("ip route show default") or "N/A"
        net_data['routing'] = route_out[:300]
        print(f"  {CYAN}{route_out[:200]}{RESET}")
    except Exception as e:
        print(f"  {YELLOW}Skipped: {e}{RESET}")
        net_data['routing'] = 'N/A'

    # DNS
    print_section("DNS Servers","")
    try:
        dns_out = run_cmd("cat /etc/resolv.conf 2>/dev/null") or "N/A"
        net_data['dns'] = dns_out[:200]
        for line in dns_out.split('\n'):
            if 'nameserver' in line:
                print(f"  {CYAN}{line}{RESET}")
    except Exception as e:
        print(f"  {YELLOW}Skipped: {e}{RESET}")
        net_data['dns'] = 'N/A'

    # Connectivity
    print_section("Connectivity Tests","")
    targets = [("8.8.8.8","Google DNS"),("1.1.1.1","Cloudflare"),("deb.debian.org","Debian")]
    net_data['connectivity'] = {}
    for host, name in targets:
        try:
            out = run_cmd(f"ping -c 2 -W 3 {host} 2>/dev/null")
            if out and 'time=' in out:
                import re
                m = re.search(r'time=(\S+)', out)
                lat = m.group(1) if m else '?'
                net_data['connectivity'][name] = f"OK ({lat}ms)"
                print(f"  {GREEN}✅ {name}: {lat}ms{RESET}")
            else:
                net_data['connectivity'][name] = "Unreachable"
                print(f"  {RED}❌ {name}: Unreachable{RESET}")
        except Exception as e:
            net_data['connectivity'][name] = "Error"
            print(f"  {YELLOW}⚠️  {name}: {e}{RESET}")

    # Open ports
    print_section("Listening Ports","")
    try:
        ports_out = run_cmd("ss -tuln 2>/dev/null | head -20") or "N/A"
        net_data['ports'] = ports_out[:600]
        print(f"{CYAN}{ports_out[:400]}{RESET}")
    except Exception as e:
        print(f"  {YELLOW}Skipped: {e}{RESET}")
        net_data['ports'] = 'N/A'

    # Optional target scan
    print(f"\n{WHITE}Enter IP to scan (or press Enter to skip){RESET}")
    try:
        target = input(f"{PURPLE}Target: {RESET}").strip()
        if target:
            print(f"{YELLOW}Scanning {target}...{RESET}")
            nmap_out = run_cmd(f"nmap -F -T4 {target} 2>/dev/null", timeout=60) or "N/A"
            net_data['scan'] = nmap_out[:800]
            print(f"{CYAN}{nmap_out[:600]}{RESET}")
    except (KeyboardInterrupt, EOFError):
        pass

    print(f"\n{YELLOW}AI analyzing... {RESET}\n")
    SYSTEM = """Network expert. Analyze network data concisely.
Format:
CONNECTIVITY: [status]
ISSUES: [list any problems]
RECOMMENDATIONS: [actionable steps]
Keep response short and practical."""

    prompt = f"""Network scan:
Routing: {net_data.get('routing','N/A')[:150]}
DNS: {net_data.get('dns','N/A')[:100]}
Connectivity: {json.dumps(net_data.get('connectivity',{}))}
Ports: {net_data.get('ports','N/A')[:200]}"""

    print(f"{GREEN}{ask_claude(prompt, SYSTEM, 600)}{RESET}\n")

# ══# ════════════════════════════════════════════════════════════════
# 4. AI HARDWARE FIXER (HDD/SSD/NVMe/RAM)
# ════════════════════════════════════════════════════════════════
def run_hardware_fixer():
    print_banner(
        "RIDOS AI Hardware Fixer - HDD/SSD/NVMe/RAM",
        "إصلاح العتاد الذكي - أقراص صلبة وذاكرة"
    )

    hw_data = {}

    # ── Detect all storage devices ──
    print_section("Storage Devices Detected","أجهزة التخزين المكتشفة")
    lsblk_out = run_cmd("lsblk -o NAME,SIZE,TYPE,ROTA,TRAN,MODEL,SERIAL 2>/dev/null")
    hw_data['storage_devices'] = lsblk_out
    print(f"{CYAN}{lsblk_out[:800]}{RESET}")

    # ── SMART health for all drives ──
    print_section("Drive Health (SMART)","صحة الأقراص (SMART)")
    drives = re.findall(r'(sd[a-z]|nvme\d+n\d+|hd[a-z])', lsblk_out)
    drives = list(set(drives))
    smart_results = {}

    for drive in drives:
        dev = f"/dev/{drive}"
        print(f"\n  {YELLOW}Checking {dev}...{RESET}")

        # SMART overall health
        health = run_cmd(f"sudo smartctl -H {dev} 2>/dev/null")
        status_line = [l for l in health.split('\n') if 'SMART overall' in l or 'PASSED' in l or 'FAILED' in l]
        status = status_line[0].strip() if status_line else "Unknown"
        print(f"  📊 {dev}: {GREEN if 'PASSED' in status else RED}{status}{RESET}")

        # Key SMART attributes
        attrs = run_cmd(f"sudo smartctl -A {dev} 2>/dev/null")
        critical = {}
        for line in attrs.split('\n'):
            parts = line.split()
            if len(parts) >= 10:
                attr_name = parts[1] if len(parts) > 1 else ""
                raw_val = parts[-1] if parts else "0"
                if attr_name in ['Reallocated_Sector_Ct','Current_Pending_Sector',
                                  'Offline_Uncorrectable','Spin_Retry_Count',
                                  'Power_On_Hours','Temperature_Celsius',
                                  'Wear_Leveling_Count','Available_Reservd_Space']:
                    critical[attr_name] = raw_val
                    if attr_name == 'Reallocated_Sector_Ct' and int(raw_val or 0) > 0:
                        print(f"  {RED}⚠️  Bad sectors found: {raw_val}{RESET}")
                    if attr_name == 'Temperature_Celsius':
                        temp = int(raw_val or 0)
                        color = RED if temp > 55 else YELLOW if temp > 45 else GREEN
                        print(f"  {color}🌡️  Temperature: {temp}°C{RESET}")
                    if attr_name == 'Power_On_Hours':
                        hours = int(raw_val or 0)
                        years = round(hours/8760, 1)
                        print(f"  ⏱️  Power-on: {hours}h ({years} years)")

        # NVMe specific
        if 'nvme' in drive:
            nvme_out = run_cmd(f"sudo nvme smart-log {dev} 2>/dev/null")
            if nvme_out:
                for line in nvme_out.split('\n'):
                    if any(k in line for k in ['temperature','available_spare',
                                               'percentage_used','media_errors']):
                        print(f"  {CYAN}{line.strip()}{RESET}")
                critical['nvme_log'] = nvme_out[:500]

        smart_results[drive] = {
            'health': status,
            'attributes': critical,
            'device': dev
        }

        # Disk filesystem check
        df_out = run_cmd(f"df -h {dev}* 2>/dev/null | head -5")
        if df_out.strip():
            print(f"  📁 Filesystem:\n{CYAN}{df_out}{RESET}")

        hw_data['smart'] = smart_results

    # ── RAM Analysis ──
    print_section("RAM Memory Analysis","تحليل ذاكرة RAM")
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    print(f"  🧠 Total RAM:  {round(mem.total/1024**3,2)} GB")
    print(f"  ✅ Available:  {round(mem.available/1024**3,2)} GB")
    print(f"  📊 Used:       {mem.percent}%")
    print(f"  💾 Swap Total: {round(swap.total/1024**3,2)} GB")
    print(f"  💾 Swap Used:  {swap.percent}%")

    # DMI memory info
    dmi_out = run_cmd("sudo dmidecode -t memory 2>/dev/null | grep -E 'Size:|Type:|Speed:|Manufacturer:|Part Number:|Form Factor:|Locator:' | head -40")
    if dmi_out.strip():
        print_section("RAM Modules Detected","وحدات RAM المكتشفة")
        print(f"{CYAN}{dmi_out}{RESET}")
        hw_data['ram_modules'] = dmi_out

    # Memory errors
    memtest_hint = ""
    edac_out = run_cmd("sudo cat /sys/devices/system/edac/mc/mc*/ue_count 2>/dev/null")
    if edac_out.strip() and any(int(x.strip()) > 0 for x in edac_out.split() if x.strip().isdigit()):
        print(f"  {RED}⚠️  Memory errors detected! Run memtest86+{RESET}")
        memtest_hint = "CRITICAL: Memory errors found"
    else:
        print(f"  {GREEN}✅ No memory errors detected{RESET}")

    hw_data['ram'] = {
        'total_gb': round(mem.total/1024**3, 2),
        'used_percent': mem.percent,
        'swap_percent': swap.percent,
        'memtest': memtest_hint
    }

    # ── CPU & Motherboard Info ──
    print_section("CPU & Motherboard","المعالج واللوحة الأم")
    cpu_info = run_cmd("lscpu | grep -E 'Model name|Architecture|CPU MHz|Cache|Vendor'")
    print(f"{CYAN}{cpu_info[:400]}{RESET}")
    mb_info = run_cmd("sudo dmidecode -t baseboard 2>/dev/null | grep -E 'Manufacturer|Product Name|Version|Serial'")
    if mb_info.strip():
        print(f"{CYAN}{mb_info[:300]}{RESET}")
    hw_data['cpu'] = cpu_info[:300]
    hw_data['motherboard'] = mb_info[:200]

    # ── PCI Devices ──
    print_section("PCI Hardware","أجهزة PCI")
    pci_out = run_cmd("lspci 2>/dev/null | grep -E 'VGA|Audio|Network|Storage|NVME|SATA' | head -15")
    print(f"{CYAN}{pci_out}{RESET}")
    hw_data['pci'] = pci_out

    # ── Repair Options ──
    print_section("Quick Repair Tools","أدوات الإصلاح السريع")
    print(f"  {WHITE}[1] Check & repair filesystem errors | فحص وإصلاح أخطاء نظام الملفات{RESET}")
    print(f"  {WHITE}[2] Run disk bad sector scan | فحص القطاعات التالفة{RESET}")
    print(f"  {WHITE}[3] Check RAM with memtest | فحص الذاكرة{RESET}")
    print(f"  {WHITE}[4] Get AI diagnosis report | تقرير تشخيص الذكاء الاصطناعي{RESET}")
    print(f"  {WHITE}[5] Skip to AI report | تخطي إلى تقرير الذكاء الاصطناعي{RESET}\n")

    choice = input(f"{PURPLE}Select | اختر [1-5]: {RESET}").strip()

    if choice == '1':
        print(f"\n{YELLOW}Available partitions:{RESET}")
        print(run_cmd("lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINT | head -20"))
        part = input(f"{PURPLE}Enter partition (e.g. sda1, nvme0n1p1): {RESET}").strip()
        if part:
            print(f"{YELLOW}Running fsck on /dev/{part}...{RESET}")
            out = run_cmd(f"sudo fsck -y /dev/{part} 2>&1", timeout=120)
            print(f"{CYAN}{out[:1000]}{RESET}")
            hw_data['fsck_result'] = out[:500]

    elif choice == '2':
        print(f"\n{YELLOW}Available drives:{RESET}")
        for d in drives: print(f"  /dev/{d}")
        drv = input(f"{PURPLE}Enter drive (e.g. sda, nvme0n1): {RESET}").strip()
        if drv:
            print(f"{YELLOW}Running bad sector scan on /dev/{drv} (this may take a while)...{RESET}")
            out = run_cmd(f"sudo badblocks -v /dev/{drv} 2>&1 | head -50", timeout=300)
            print(f"{CYAN}{out[:1000]}{RESET}")
            hw_data['badblocks'] = out[:500]

    elif choice == '3':
        print(f"\n{GREEN}To run memtest86+:{RESET}")
        print(f"  1. Reboot your computer | أعد تشغيل الحاسوب")
        print(f"  2. At GRUB menu, select 'memtest86+' | اختر 'memtest86+' من قائمة GRUB")
        print(f"  3. Let it run at least 2 passes | دعه يعمل مرورين على الأقل")
        print(f"  {YELLOW}Install memtest: sudo apt-get install memtest86+{RESET}")
        input(f"\n{PURPLE}Press Enter to continue...{RESET}")

    # AI Analysis
    print(f"\n{YELLOW}🤖 AI analyzing hardware... يحلل العتاد...{RESET}\n")

    SYSTEM = """You are a bilingual hardware diagnostics expert for IT engineers.
Analyze hardware data and respond in BOTH English AND Arabic.

Format:
## 🔧 Hardware Diagnosis | تشخيص العتاد

**Storage Health | صحة التخزين:**
[English analysis of each drive]
[Arabic analysis]

**RAM Status | حالة الذاكرة:**
[English] [Arabic]

**Issues Found | المشكلات المكتشفة:**
[List with severity: CRITICAL/WARNING/OK]

**Repair Steps | خطوات الإصلاح:**
[Numbered steps in English]
[Arabic steps]

Be specific for IT engineers."""

    prompt = f"""Hardware scan results:
Drives: {json.dumps(list(smart_results.keys()))}
SMART status: {json.dumps({k: v['health'] for k,v in smart_results.items()})}
RAM: {json.dumps(hw_data['ram'])}
RAM modules: {hw_data.get('ram_modules','N/A')[:200]}
CPU: {hw_data['cpu'][:150]}
PCI devices: {hw_data['pci'][:200]}
{('Filesystem check: '+hw_data.get('fsck_result','N/A')[:200]) if hw_data.get('fsck_result') else ''}
{('Bad sectors: '+hw_data.get('badblocks','N/A')[:200]) if hw_data.get('badblocks') else ''}"""

    print(f"{GREEN}{ask_claude(prompt, SYSTEM, 1000)}{RESET}\n")

    # Save report
    report = f"/home/ridos/hardware-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    try:
        with open(report, 'w') as f:
            f.write(f"RIDOS OS Hardware Report | {datetime.now()}\n{'='*60}\n")
            f.write(json.dumps(hw_data, indent=2, default=str))
        print(f"{GREEN}📄 Report saved: {report} | تم حفظ التقرير{RESET}")
    except: pass

# ════════════════════════════════════════════════════════════════
# 5. AI CYBERSECURITY SCANNER
# ════════════════════════════════════════════════════════════════
def run_security_scanner():
    print_banner("RIDOS AI Cybersecurity Scanner","الماسح الأمني الذكي لريدوس")
    print(f"{YELLOW}⚠️  Only scan systems you own! افحص فقط ما تملكه!{RESET}\n")

    target = input(f"{PURPLE}Target IP/hostname | الهدف: {RESET}").strip()
    if not target: return

    results = {}
    try:
        results['ip'] = socket.gethostbyname(target)
        print(f"  ✅ Resolved: {results['ip']}")
    except:
        results['ip'] = target

    print(f"{YELLOW}[1/4] Port scan...{RESET}")
    results['ports'] = run_cmd(
        f"nmap -sV --open -T4 -p 21,22,23,25,53,80,110,143,443,445,3306,3389,5432,8080 {target}",
        timeout=120)
    print(f"{CYAN}{results['ports'][:1000]}{RESET}")

    print(f"{YELLOW}[2/4] OS detection...{RESET}")
    results['os'] = run_cmd(f"nmap -O --osscan-guess -T4 {target}", timeout=60)

    print(f"{YELLOW}[3/4] HTTP headers...{RESET}")
    if HAS_REQUESTS:
        for scheme in ['https','http']:
            try:
                import urllib3; urllib3.disable_warnings()
                r = requests.get(f"{scheme}://{target}", timeout=5,
                               verify=False, allow_redirects=True)
                results['http'] = {
                    'status': r.status_code,
                    'server': r.headers.get('Server','?'),
                    'missing_headers': [h for h in
                        ['X-Frame-Options','Content-Security-Policy',
                         'Strict-Transport-Security','X-Content-Type-Options']
                        if h not in r.headers]
                }
                print(f"  HTTP {r.status_code} | Server: {results['http']['server']}")
                if results['http']['missing_headers']:
                    print(f"  {YELLOW}Missing: {', '.join(results['http']['missing_headers'])}{RESET}")
                break
            except: continue

    print(f"{YELLOW}[4/4] AI security analysis...{RESET}\n")
    SYSTEM = """Bilingual cybersecurity expert. Analyze scan and respond in English AND Arabic.
Include: Risk level, open ports analysis, vulnerabilities, hardening steps. Be concise."""
    prompt = f"Target: {target}\nPorts:\n{results['ports'][:800]}\nHTTP: {json.dumps(results.get('http',{}))}"
    response = ask_claude(prompt, SYSTEM, 800)
    print(f"{GREEN}{response}{RESET}\n")

    report = f"/home/ridos/security-{target.replace('.','_')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    try:
        with open(report,'w') as f:
            f.write(f"RIDOS Security Report | Target: {target} | {datetime.now()}\n")
            f.write(response)
        print(f"{GREEN}📄 Saved: {report}{RESET}")
    except: pass

# ════════════════════════════════════════════════════════════════
# MAIN MENU
# ════════════════════════════════════════════════════════════════
def main():
    while True:
        print(f"\n{BOLD}{PURPLE}")
        print("  ██████╗ ██╗██████╗  ██████╗ ███████╗")
        print("  ██╔══██╗██║██╔══██╗██╔═══██╗██╔════╝")
        print("  ██████╔╝██║██║  ██║██║   ██║███████╗")
        print("  ██╔══██╗██║██║  ██║██║   ██║╚════██║")
        print("  ██║  ██║██║██████╔╝╚██████╔╝███████║")
        print("  ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝")
        print(f"{RESET}{BOLD}{WHITE}  RIDOS OS v1.1.0 Baghdad — AI Tools{RESET}")
        print(f"{BOLD}{WHITE}  أدوات الذكاء الاصطناعي — ريدوس أو إس{RESET}\n")

        online = check_internet()
        status = f"{GREEN}🌐 Online{RESET}" if online else f"{YELLOW}⚡ Offline Mode{RESET}"
        print(f"  Internet: {status}\n")

        print(f"{CYAN}  [1] 🖥️  AI Terminal Assistant  | مساعد الطرفية الذكي{RESET}")
        print(f"{CYAN}  [2] 🏥  AI System Doctor        | طبيب النظام الذكي{RESET}")
        print(f"{CYAN}  [3] 🌐  AI Network Analyzer     | محلل الشبكة المتقدم{RESET}")
        print(f"{CYAN}  [4] 🔧  AI Hardware Fixer       | إصلاح العتاد (HDD/SSD/NVMe/RAM){RESET}")
        print(f"{CYAN}  [5] 🔒  AI Security Scanner     | الماسح الأمني الذكي{RESET}")
        print(f"{YELLOW}  [0] Exit                       | خروج{RESET}\n")

        choice = input(f"{PURPLE}Select | اختر [0-5]: {RESET}").strip()

        if   choice=='1': run_terminal_assistant()
        elif choice=='2': run_system_doctor()
        elif choice=='3': run_network_analyzer()
        elif choice=='4': run_hardware_fixer()
        elif choice=='5': run_security_scanner()
        elif choice=='0':
            print(f"\n{PURPLE}Goodbye! مع السلامة! 🌟{RESET}\n"); sys.exit(0)
        else:
            print(f"{RED}Invalid choice | اختيار غير صحيح{RESET}")

if __name__ == "__main__":
    # Support direct launch with argument: python3 ai_features.py 2
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if   choice=='1': run_terminal_assistant()
        elif choice=='2': run_system_doctor()
        elif choice=='3': run_network_analyzer()
        elif choice=='4': run_hardware_fixer()
        elif choice=='5': run_security_scanner()
        else: main()
    else:
        main()
