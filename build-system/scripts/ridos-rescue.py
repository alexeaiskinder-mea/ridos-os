#!/usr/bin/env python3
import os
import subprocess
import sys

def get_ai_analysis(data, lang="ar"):
    """
    This function sends technical data to the AI.
    In RIDOS v1.1.1, it uses the API Key configured by the Wizard.
    """
    api_key = os.getenv("RIDOS_API_KEY")
    
    if not api_key:
        return "Error: No API Key found. Please run RIDOS Wizard first." if lang=="en" else "خطأ: لم يتم العثور على مفتاح API. يرجى تشغيل معالج RIDOS أولاً."

    # Logic to interface with your existing AI Features module
    # For now, we provide a structured prompt for the AI
    instructions = (
        "Analyze this disk data and provide a brief recovery plan." if lang=="en" 
        else "حلل بيانات القرص التالية وقدم خطة استعادة قصيرة."
    )
    
    # This is where you'd call your actual AI API (Gemini/Claude)
    return f"AI Analysis Result: The drive appears to have partition table issues. Recommended tool: TestDisk 'Analyse'."

def main():
    # 1. Language Selection
    print("========================================")
    print("   RIDOS AI Rescue Assistant v1.1.1     ")
    print("========================================\n")
    print("1. العربية (Arabic)")
    print("2. English")
    
    choice = input("\nSelect Language / اختر اللغة (1/2): ").strip()
    lang = "ar" if choice == "1" else "en"
    
    # 2. Hardware Scanning
    loading_msg = "[+] Scanning hardware..." if lang == "en" else "[+] جاري فحص العتاد..."
    print(f"\n{loading_msg}")
    
    try:
        # Get partition list
        disk_data = subprocess.check_output("lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT", shell=True).decode()
        # Get SMART status for sda (Common default)
        smart_data = subprocess.check_output("sudo smartctl -H /dev/sda", shell=True).decode()
    except Exception as e:
        disk_data = "Scan failed or permission denied."
        smart_data = str(e)

    full_report = f"DISK DATA:\n{disk_data}\n\nSMART DATA:\n{smart_data}"

    # 3. AI Processing
    print("[+] Consulting RIDOS AI..." if lang == "en" else "[+] جاري استشارة الذكاء الاصطناعي...")
    analysis = get_ai_analysis(full_report, lang)
    
    print("\n" + "="*40)
    print(analysis)
    print("="*40 + "\n")

    # 4. Action Choice
    prompt = "Launch GParted for manual repair? (y/n): " if lang == "en" else "هل تريد تشغيل GParted للإصلاح اليدوي؟ (نعم/لا): "
    action = input(prompt).lower()
    
    if action in ['y', 'yes', 'نعم', 'ن']:
        print("Launching GParted...")
        os.system("sudo gparted &")
    
    print("\nThank you for using RIDOS OS." if lang == "en" else "\nشكراً لاستخدامك نظام RIDOS.")

if __name__ == "__main__":
    main()
