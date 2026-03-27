#!/usr/bin/env python3
"""Configure Calamares installer for RIDOS OS"""
import os, subprocess

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"Written: {path}")

def run(cmd):
    return subprocess.run(cmd, shell=True)

os.makedirs('chroot/etc/calamares/branding/ridos', exist_ok=True)
os.makedirs('chroot/etc/calamares/modules', exist_ok=True)

# Main settings
write('chroot/etc/calamares/settings.conf', '''---
modules-search: [ local, /usr/lib/calamares/modules ]

sequence:
  - show:
      - welcome
      - locale
      - keyboard
      - partition
      - users
      - summary
  - exec:
      - partition
      - mount
      - unpackfs
      - machineid
      - fstab
      - locale
      - keyboard
      - users
      - displaymanager
      - packages
      - grubcfg
      - shellprocess
      - bootloader
      - finished

branding: ridos
prompt-install: false
dont-chroot: false
''')

# Branding
write('chroot/etc/calamares/branding/ridos/branding.desc', '''---
componentName: ridos
welcomeStyleCalamares: true
strings:
  productName: RIDOS OS
  shortProductName: RIDOS
  version: "1.1.0"
  shortVersion: "1.1"
  versionedName: "RIDOS OS 1.1.0"
  shortVersionedName: "RIDOS 1.1"
  bootloaderEntryName: RIDOS
  productUrl: "https://github.com/alexeaiskinder-mea/ridos-os"
  supportUrl: "https://github.com/alexeaiskinder-mea/ridos-os/issues"
  releaseNotesUrl: "https://github.com/alexeaiskinder-mea/ridos-os"
images:
  productLogo: "logo.png"
  productIcon: "logo.png"
  productWelcome: "languages.png"
slideshow: "show.qml"
style:
  sidebarBackground: "#1E1B4B"
  sidebarText: "#FFFFFF"
  sidebarTextSelect: "#6B21A8"
''')

# Welcome slide
write('chroot/etc/calamares/branding/ridos/show.qml', '''import QtQuick 2.0
Rectangle {
    color: "#1E1B4B"
    width: 800
    height: 500
    Column {
        anchors.centerIn: parent
        spacing: 20
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "RIDOS OS"
            color: "#C4B5FD"
            font.pointSize: 36
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "v1.1.0 Baghdad"
            color: "#E9D5FF"
            font.pointSize: 16
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "AI-Powered Linux for IT Professionals"
            color: "#DDD6FE"
            font.pointSize: 14
        }
    }
}
''')

# Partition config
write('chroot/etc/calamares/modules/partition.conf', '''---
efiSystemPartition: "/boot/efi"
defaultPartitionTableType: gpt
availableFileSystemTypes: [ ext4, btrfs, xfs ]
initialPartitioningChoice: erase
initialSwapChoice: small
''')

# Users config
write('chroot/etc/calamares/modules/users.conf', '''---
defaultGroups:
  - sudo
  - audio
  - video
  - netdev
  - plugdev
  - bluetooth
  - storage
autologinGroup: autologin
doAutologin: false
sudoersGroup: sudo
setRootPassword: true
passwordRequirements:
  minLength: 6
''')

# Unpackfs - squashfs location
write('chroot/etc/calamares/modules/unpackfs.conf', '''---
unpack:
  - source: "/run/live/medium/live/filesystem.squashfs"
    sourcefs: "squashfs"
    destination: ""
''')

# Display manager
write('chroot/etc/calamares/modules/displaymanager.conf', '''---
displaymanagers:
  - lightdm
defaultDesktopEnvironment:
  executable: "startxfce4"
  desktopFile: "xfce.desktop"
basicSetup: false
''')

# CRITICAL: fstab - fixes "No mountOptions" error
write('chroot/etc/calamares/modules/fstab.conf', '''---
mountOptions:
  default: defaults
  btrfs: defaults,noatime,autodefrag
  ext4: defaults,noatime
  fat32: defaults,umask=0077
  vfat: defaults,umask=0077
ssdExtraMountOptions:
  ext4: discard
  btrfs: discard,ssd
efiMountOptions: umask=0077
ensureSuspendToDisk: true
neverCheckSuspendToDisk: false
''')

# locale config
write('chroot/etc/calamares/modules/locale.conf', '''---
region: "Asia"
zone: "Baghdad"
useSystemTimezone: false
''')

# keyboard config
write('chroot/etc/calamares/modules/keyboard.conf', '''---
writeEtcDefaultKeyboard: true
''')

# networkcfg
write('chroot/etc/calamares/modules/networkcfg.conf', '''---
explicitNMconfig: true
''')

# CRITICAL FIX: packages.conf
# This installs grub-pc ON THE TARGET SYSTEM during installation
# Without this, grub-install and update-grub don't exist after install
write('chroot/etc/calamares/modules/packages.conf', '''---
backend: apt
update_db: false
operations:
  - remove:
      - live-boot
      - live-boot-initramfs-tools
      - calamares
      - calamares-settings-debian
''')

# bootloader config - allow skip since shellprocess handles it
write('chroot/etc/calamares/modules/bootloader.conf', '''---
efiBootLoader: "grub"
grubInstall: "grub-install"
grubMkconfig: "update-grub"
grubCfg: "/boot/grub/grub.cfg"
grubProbe: "grub-probe"
efiInstallerPath: "/usr/bin/efibootmgr"
installEFIFallback: false
canBeSkipped: true
''')

# CRITICAL: shellprocess - runs ridos-grub-install from LIVE system
write('chroot/etc/calamares/modules/shellprocess.conf', '''---
dontChroot: true
timeout: 300
verbose: true

script:
  - command: "/usr/local/bin/ridos-grub-install"
    timeout: 300
''')

# GRUB branding
write('chroot/etc/default/grub',
    'GRUB_DEFAULT=0\n'
    'GRUB_TIMEOUT=5\n'
    'GRUB_DISTRIBUTOR="RIDOS OS"\n'
    'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"\n'
    'GRUB_CMDLINE_LINUX=""\n')

# Generate logo
run('convert -size 200x200 gradient:"#6B21A8-#1E1B4B" '
    '-font DejaVu-Sans-Bold -pointsize 32 '
    '-fill white -gravity center -annotate 0 "RIDOS" '
    'chroot/etc/calamares/branding/ridos/logo.png 2>/dev/null || '
    'convert -size 200x200 xc:"#6B21A8" '
    '-fill white -gravity center -annotate 0 "RIDOS" '
    'chroot/etc/calamares/branding/ridos/logo.png 2>/dev/null || true')

run('cp chroot/etc/calamares/branding/ridos/logo.png '
    'chroot/etc/calamares/branding/ridos/languages.png 2>/dev/null || true')

# Remove calamares-settings-debian which overrides our config
run('chroot chroot apt-get remove -y calamares-settings-debian 2>/dev/null || true')

if os.path.exists('chroot/usr/bin/calamares'):
    print("Calamares installed and configured successfully")
else:
    print("WARNING: Calamares binary not found")
