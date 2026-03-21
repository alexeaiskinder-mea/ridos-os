#!/usr/bin/env python3
"""Install RIDOS core files, wallpaper, installer, and motd"""
import os, subprocess

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

def run(cmd):
    return subprocess.run(cmd, shell=True)

# Install SVG brand assets
import shutil, glob
os.makedirs('chroot/usr/share/ridos/icons', exist_ok=True)
os.makedirs('chroot/usr/share/pixmaps', exist_ok=True)

# Copy all brand SVGs to system
for svg in glob.glob('build-system/scripts/ridos-*.svg'):
    dst = f'chroot/usr/share/ridos/{os.path.basename(svg)}'
    shutil.copy2(svg, dst)
    print(f"Copied: {os.path.basename(svg)}")

# Copy icon pack
for svg in glob.glob('build-system/scripts/icon-*.svg'):
    dst = f'chroot/usr/share/ridos/icons/{os.path.basename(svg)}'
    shutil.copy2(svg, dst)

# Copy Plymouth script
if os.path.exists('build-system/scripts/ridos-plymouth.script'):
    shutil.copy2('build-system/scripts/ridos-plymouth.script',
                 'chroot/usr/share/plymouth/themes/ridos/ridos.script')
    print("Plymouth script installed")

# Install GRUB theme
os.makedirs('chroot/boot/grub/themes/ridos', exist_ok=True)
if os.path.exists('build-system/scripts/ridos-grub.svg'):
    shutil.copy2('build-system/scripts/ridos-grub.svg',
                 'chroot/boot/grub/themes/ridos/background.svg')
    print("GRUB theme installed")

# Generate wallpaper from SVG brand file
import shutil
wallpaper_dst = 'chroot/usr/share/ridos/ridos-wallpaper.png'
wallpaper_src_svg = 'build-system/scripts/ridos-wallpaper.svg'
wallpaper_src_png = 'build-system/scripts/ridos-wallpaper.png'

if os.path.exists(wallpaper_src_png) and os.path.getsize(wallpaper_src_png) > 10000:
    shutil.copy2(wallpaper_src_png, wallpaper_dst)
    print(f"Wallpaper copied from PNG: {os.path.getsize(wallpaper_dst)} bytes")
elif os.path.exists(wallpaper_src_svg):
    # Convert SVG to PNG using rsvg-convert or inkscape
    result = run(f'rsvg-convert -w 1920 -h 1080 {wallpaper_src_svg} -o {wallpaper_dst} 2>/dev/null')
    if not os.path.exists(wallpaper_dst) or os.path.getsize(wallpaper_dst) < 1000:
        run(f'inkscape --export-filename={wallpaper_dst} --export-width=1920 {wallpaper_src_svg} 2>/dev/null')
    if os.path.exists(wallpaper_dst) and os.path.getsize(wallpaper_dst) > 1000:
        print(f"Wallpaper converted from SVG: {os.path.getsize(wallpaper_dst)} bytes")
    else:
        # Fallback: generate with ImageMagick
        run(f'convert -size 1920x1080 gradient:"#0F0A1E-#2D1B69" '
            f'-fill "rgba(196,181,253,0.2)" -font DejaVu-Sans-Bold '
            f'-pointsize 100 -gravity center -annotate 0 "RIDOS OS" {wallpaper_dst} 2>/dev/null || true')
        print("Wallpaper generated with fallback")
else:
    run(f'convert -size 1920x1080 gradient:"#0F0A1E-#2D1B69" '
        f'-fill "rgba(196,181,253,0.2)" -font DejaVu-Sans-Bold '
        f'-pointsize 100 -gravity center -annotate 0 "RIDOS OS" {wallpaper_dst} 2>/dev/null || true')
    print("Wallpaper generated with ImageMagick")

# Generate icon from SVG
icon_dst = 'chroot/usr/share/ridos/ridos-icon.png'
icon_src_svg = 'build-system/scripts/ridos-icon.svg'
if os.path.exists(icon_src_svg):
    run(f'rsvg-convert -w 256 -h 256 {icon_src_svg} -o {icon_dst} 2>/dev/null')
    if not os.path.exists(icon_dst) or os.path.getsize(icon_dst) < 1000:
        run(f'convert -background none -size 256x256 {icon_src_svg} {icon_dst} 2>/dev/null')
    if os.path.exists(icon_dst):
        print(f"Icon generated: {os.path.getsize(icon_dst)} bytes")
    else:
        run(f'convert -size 256x256 gradient:"#6B21A8-#1E1B4B" '
            f'-fill white -gravity center -font DejaVu-Sans-Bold '
            f'-pointsize 80 -annotate 0 "R" {icon_dst} 2>/dev/null || true')
        print("Icon generated with fallback")

# Verify
if os.path.exists(wallpaper_dst):
    print(f"Wallpaper OK: {os.path.getsize(wallpaper_dst)} bytes")
else:
    print("WARNING: Wallpaper not created!")

# Generate icon
run('convert -size 256x256 gradient:"#6B21A8-#1E1B4B" '
    '-font DejaVu-Sans-Bold -pointsize 48 '
    '-fill white -gravity center -annotate 0 "RIDOS" '
    'chroot/usr/share/ridos/ridos-icon.png 2>/dev/null || true')

# Dashboard service
write('chroot/etc/systemd/system/ridos-dashboard.service',
    '[Unit]\n'
    'Description=RIDOS Dashboard Stats Server\n'
    'After=network.target\n\n'
    '[Service]\n'
    'Type=simple\n'
    'User=ridos\n'
    'ExecStart=/usr/bin/python3 /opt/ridos/bin/dashboard_server.py\n'
    'Restart=always\n'
    'RestartSec=3\n\n'
    '[Install]\n'
    'WantedBy=multi-user.target\n')

# MOTD banner
write('chroot/etc/motd', '''
  \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557
  \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d
  \u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557
  \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u255a\u2550\u2550\u2550\u2550\u2588\u2588\u2551
  \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551
  \u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u255d  \u255a\u2550\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d

  RIDOS OS v1.1.0 "Baghdad"
  AI-Powered Linux for IT Professionals
  Username: ridos  |  Password: ridos
  AI Shell: python3 /opt/ridos/bin/ridos_shell.py

''')

# HDD bash installer
write('chroot/opt/ridos/bin/ridos-install.sh', '''#!/bin/bash
clear
echo "============================================"
echo "   RIDOS OS v1.1.0 Baghdad - HDD Installer"
echo "============================================"
echo ""
echo "Available disks:"
lsblk -d -o NAME,SIZE,MODEL | grep -v loop
echo ""
read -p "Enter disk to install to (e.g. sda, sdb): " DISK
DISK="/dev/$DISK"
if [ ! -b "$DISK" ]; then
  echo "ERROR: Disk $DISK not found!"
  read -p "Press Enter to exit..."; exit 1
fi
echo ""; echo "Selected: $DISK"; lsblk "$DISK"; echo ""
read -p "ARE YOU SURE? All data will be ERASED! Type YES: " CONFIRM
if [ "$CONFIRM" != "YES" ]; then
  echo "Cancelled."; read -p "Press Enter..."; exit 0
fi
echo "Partitioning..."
parted -s "$DISK" mklabel msdos
parted -s "$DISK" mkpart primary ext4 1MiB 100%
parted -s "$DISK" set 1 boot on
PARTITION="${DISK}1"; sleep 2
echo "Formatting..."; mkfs.ext4 -F "$PARTITION"
mkdir -p /mnt/ridos-install
mount "$PARTITION" /mnt/ridos-install
echo "Copying files (10-20 minutes)..."
rsync -ax --exclude=/proc --exclude=/sys --exclude=/dev \\
  --exclude=/run --exclude=/mnt --exclude=/media \\
  / /mnt/ridos-install/
mkdir -p /mnt/ridos-install/{proc,sys,dev,run,mnt,media}
echo "Installing GRUB..."
mount --bind /dev  /mnt/ridos-install/dev
mount --bind /proc /mnt/ridos-install/proc
mount --bind /sys  /mnt/ridos-install/sys
UUID=$(blkid -s UUID -o value "$PARTITION")
echo "UUID=$UUID / ext4 errors=remount-ro 0 1" > /mnt/ridos-install/etc/fstab
chroot /mnt/ridos-install apt-get remove -y live-boot live-boot-initramfs-tools 2>/dev/null || true
chroot /mnt/ridos-install update-initramfs -u 2>/dev/null || true
chroot /mnt/ridos-install grub-install "$DISK"
chroot /mnt/ridos-install update-grub
sed -i "s/boot=live //" /mnt/ridos-install/boot/grub/grub.cfg 2>/dev/null || true
umount /mnt/ridos-install/sys /mnt/ridos-install/proc /mnt/ridos-install/dev
umount /mnt/ridos-install
echo ""
echo "RIDOS OS installed! Remove USB and reboot."
read -p "Press Enter to exit..."
''')
run('chmod +x chroot/opt/ridos/bin/ridos-install.sh')
run('chroot chroot chown -R ridos:ridos /home/ridos 2>/dev/null || true')

# Install GRUB helper to live system
import shutil, stat
shutil.copy2('build-system/scripts/ridos-grub-install.sh',
             'chroot/usr/local/bin/ridos-grub-install')
os.chmod('chroot/usr/local/bin/ridos-grub-install', 0o755)
print("✅ ridos-grub-install installed to live system")

# Install unattended-upgrades (Pro Team Recommendation)
run('chroot chroot apt-get install -y unattended-upgrades 2>/dev/null || true')

# Create ridos-update script
with open('chroot/usr/local/bin/ridos-update', 'w') as f:
    f.write('''#!/bin/bash
echo "================================"
echo "  RIDOS OS System Update"
echo "================================"
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y
echo "================================"
echo "  Update complete!"
echo "================================"
''')
run('chmod +x chroot/usr/local/bin/ridos-update')
print("RIDOS files installed successfully")
