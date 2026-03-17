#!/usr/bin/env python3
"""
RIDOS GPU Setup - Auto-detects GPU and installs the correct driver
Runs automatically after first boot on installed system
Also available as desktop shortcut: "Setup GPU Driver"
"""

import subprocess
import os
import sys
import re

def run(cmd, timeout=300):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return "", str(e), 1

def header(text):
    print("\n" + "═" * 58)
    print(f"  {text}")
    print("═" * 58)

def detect_gpu():
    """Detect all GPUs in the system."""
    out, _, _ = run("lspci | grep -iE 'vga|3d|display'")
    gpus = []
    for line in out.split("\n"):
        if not line.strip():
            continue
        line_lower = line.lower()
        if "nvidia" in line_lower:
            # Get NVIDIA PCI ID for driver matching
            match = re.search(r'\[(\w+):(\w+)\]', line)
            gpus.append({
                "type": "nvidia",
                "name": line.split(":")[-1].strip(),
                "pci_id": match.group(0) if match else ""
            })
        elif "amd" in line_lower or "radeon" in line_lower or "advanced micro" in line_lower:
            gpus.append({
                "type": "amd",
                "name": line.split(":")[-1].strip(),
                "pci_id": ""
            })
        elif "intel" in line_lower:
            gpus.append({
                "type": "intel",
                "name": line.split(":")[-1].strip(),
                "pci_id": ""
            })
        else:
            gpus.append({
                "type": "other",
                "name": line.split(":")[-1].strip(),
                "pci_id": ""
            })
    return gpus

def is_optimus(gpus):
    """Check if this is an Intel+NVIDIA Optimus system."""
    types = [g["type"] for g in gpus]
    return "intel" in types and "nvidia" in types

def get_installed_driver():
    """Check what GPU driver is currently active."""
    out, _, _ = run("lsmod | grep -E '^nvidia|^nouveau|^i915|^amdgpu|^radeon'")
    drivers = []
    for line in out.split("\n"):
        if line.strip():
            drivers.append(line.split()[0])
    return drivers

def install_intel_driver():
    """Install Intel GPU driver."""
    print("\n  Installing Intel GPU driver...")
    cmds = [
        "apt-get update -qq",
        "apt-get install -y xserver-xorg-video-intel intel-media-va-driver i965-va-driver libva-drm2",
    ]
    for cmd in cmds:
        print(f"  → {cmd}")
        out, err, rc = run(f"sudo {cmd}", timeout=300)
        if rc != 0:
            print(f"  ⚠️  {err[:100]}")
        else:
            print(f"  ✅ Done")

    # Enable i915 modeset
    run("sudo mkdir -p /etc/modprobe.d")
    run("echo 'options i915 modeset=1 enable_psr=0' | sudo tee /etc/modprobe.d/intel-gpu.conf")
    print("  ✅ Intel driver configured")

def install_amd_driver():
    """Install AMD GPU driver."""
    print("\n  Installing AMD GPU driver...")
    cmds = [
        "apt-get update -qq",
        "apt-get install -y xserver-xorg-video-amdgpu firmware-amd-graphics mesa-vulkan-drivers mesa-va-drivers libva-drm2",
    ]
    for cmd in cmds:
        print(f"  → {cmd}")
        out, err, rc = run(f"sudo {cmd}", timeout=300)
        if rc != 0:
            print(f"  ⚠️  {err[:100]}")
        else:
            print(f"  ✅ Done")

    # Enable amdgpu modeset
    run("sudo mkdir -p /etc/modprobe.d")
    run("echo 'options amdgpu modeset=1' | sudo tee /etc/modprobe.d/amd-gpu.conf")
    print("  ✅ AMD driver configured")

def install_nvidia_driver(optimus=False):
    """Install NVIDIA driver - proprietary."""
    print("\n  Installing NVIDIA driver...")
    print("  Checking available NVIDIA driver versions...")

    out, _, _ = run("apt-cache search nvidia-driver | grep '^nvidia-driver-' | sort -V")
    versions = re.findall(r'nvidia-driver-(\d+)', out)
    if versions:
        latest = max(versions, key=int)
        print(f"  Latest available: nvidia-driver-{latest}")
    else:
        latest = "525"  # fallback
        print(f"  Using default: nvidia-driver-{latest}")

    cmds = [
        "apt-get update -qq",
        f"apt-get install -y nvidia-driver-{latest} nvidia-settings",
    ]

    if optimus:
        cmds.append("apt-get install -y nvidia-prime bumblebee-nvidia primus")

    for cmd in cmds:
        print(f"  → {cmd}")
        out, err, rc = run(f"sudo {cmd}", timeout=600)
        if rc != 0:
            print(f"  ⚠️  {err[:100]}")
        else:
            print(f"  ✅ Done")

    # Remove nouveau blacklist (no longer needed with proper driver)
    run("sudo rm -f /etc/modprobe.d/blacklist-nvidia.conf")

    # Configure NVIDIA properly
    run("sudo mkdir -p /etc/modprobe.d")
    run("echo 'options nvidia-drm modeset=1' | sudo tee /etc/modprobe.d/nvidia-drm.conf")

    if optimus:
        print("\n  Configuring Optimus (Intel+NVIDIA) switching...")
        # Set Intel as default, NVIDIA on-demand
        run("sudo prime-select intel 2>/dev/null || true")
        print("  ✅ Optimus configured: Intel default, NVIDIA on-demand")
        print("  💡 Use 'sudo prime-select nvidia' to switch to NVIDIA")
        print("  💡 Use 'sudo prime-select intel' to switch back to Intel")
    else:
        print("  ✅ NVIDIA driver configured")

def configure_grub_after_install(gpus):
    """Update GRUB for installed system with correct GPU params."""
    print("\n  Updating GRUB configuration...")

    has_nvidia = any(g["type"] == "nvidia" for g in gpus)
    has_amd    = any(g["type"] == "amd"    for g in gpus)
    has_intel  = any(g["type"] == "intel"  for g in gpus)
    optimus    = is_optimus(gpus)

    # Build optimized GRUB_CMDLINE
    params = ["quiet", "splash"]

    if optimus:
        params += ["nvidia-drm.modeset=1", "i915.modeset=1"]
    elif has_nvidia:
        params += ["nvidia-drm.modeset=1"]
    elif has_amd:
        params += ["amdgpu.modeset=1"]
    elif has_intel:
        params += ["i915.modeset=1", "i915.enable_psr=0"]

    cmdline = " ".join(params)

    # Write /etc/default/grub
    grub_default = f"""# RIDOS OS GRUB Configuration
# Auto-generated by ridos-gpu-setup.py
GRUB_DEFAULT=0
GRUB_TIMEOUT=5
GRUB_DISTRIBUTOR="RIDOS OS v1.1.0 Baghdad"
GRUB_CMDLINE_LINUX_DEFAULT="{cmdline}"
GRUB_CMDLINE_LINUX=""
"""
    try:
        with open('/tmp/grub_ridos', 'w') as f:
            f.write(grub_default)
        run("sudo cp /tmp/grub_ridos /etc/default/grub")
        run("sudo update-grub")
        print(f"  ✅ GRUB updated with params: {cmdline}")
    except Exception as e:
        print(f"  ⚠️  Could not update GRUB: {e}")

def update_initramfs():
    """Rebuild initramfs to include new drivers."""
    print("\n  Rebuilding initramfs (may take 1-2 min)...")
    out, err, rc = run("sudo update-initramfs -u -k all", timeout=300)
    if rc == 0:
        print("  ✅ initramfs rebuilt")
    else:
        print(f"  ⚠️  initramfs rebuild issue: {err[:100]}")

def main():
    os.system("clear")
    header("RIDOS GPU Setup v1.1.0 Baghdad")

    # Must run as root
    if os.geteuid() != 0:
        print("\n  ⚠️  This script requires root. Re-launching with sudo...\n")
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

    # Detect GPUs
    print("\n  Detecting GPU hardware...")
    gpus = detect_gpu()

    if not gpus:
        print("  ❌ No GPU detected. Cannot continue.")
        sys.exit(1)

    print("\n  Detected GPUs:")
    for g in gpus:
        icons = {"nvidia": "🟩", "amd": "🟥", "intel": "🔵", "other": "⚪"}
        print(f"  {icons.get(g['type'],'⚪')} [{g['type'].upper()}] {g['name']}")

    optimus = is_optimus(gpus)
    if optimus:
        print("\n  🔀 Optimus system detected (Intel + NVIDIA)")

    # Show current drivers
    active = get_installed_driver()
    print(f"\n  Currently loaded drivers: {', '.join(active) or 'none'}")

    # Determine what to install
    print("\n  Recommended driver plan:")
    has_nvidia = any(g["type"] == "nvidia" for g in gpus)
    has_amd    = any(g["type"] == "amd"    for g in gpus)
    has_intel  = any(g["type"] == "intel"  for g in gpus)

    if optimus:
        print("  → Intel i915 driver (primary display)")
        print("  → NVIDIA proprietary driver (on-demand via prime-select)")
        print("  → nvidia-prime for GPU switching")
    elif has_nvidia:
        print("  → NVIDIA proprietary driver (latest)")
    elif has_amd:
        print("  → AMDGPU open source driver")
        print("  → Mesa Vulkan + VA-API acceleration")
    elif has_intel:
        print("  → Intel i915 driver")
        print("  → Intel VA-API media driver")
    else:
        print("  → Standard VESA/fbdev (generic fallback)")

    print()
    confirm = input("  Proceed with driver installation? [Y/n]: ").strip().lower()
    if confirm == 'n':
        print("\n  Cancelled. System will continue using current driver.\n")
        sys.exit(0)

    print("\n  Starting installation...\n")

    # Install drivers
    if optimus:
        install_intel_driver()
        install_nvidia_driver(optimus=True)
    elif has_nvidia:
        install_nvidia_driver(optimus=False)
    elif has_amd:
        install_amd_driver()
        install_intel_driver() if has_intel else None
    elif has_intel:
        install_intel_driver()

    # Update GRUB and initramfs
    configure_grub_after_install(gpus)
    update_initramfs()

    print("\n" + "═" * 58)
    print("  ✅ GPU driver setup complete!")
    print()
    if optimus:
        print("  Intel+NVIDIA Optimus configured:")
        print("  • Default: Intel GPU (battery saving)")
        print("  • Switch to NVIDIA: sudo prime-select nvidia")
        print("  • Switch to Intel:  sudo prime-select intel")
    elif has_nvidia:
        print("  NVIDIA driver installed and configured.")
    elif has_amd:
        print("  AMD driver installed with Vulkan/VA-API support.")
    elif has_intel:
        print("  Intel driver installed and configured.")
    print()
    print("  ⚠️  Please REBOOT to activate the new driver.")
    print("═" * 58)

    reboot = input("\n  Reboot now? [Y/n]: ").strip().lower()
    if reboot != 'n':
        run("sudo reboot")

if __name__ == "__main__":
    main()
