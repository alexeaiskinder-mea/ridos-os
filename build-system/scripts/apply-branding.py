#!/usr/bin/env python3
"""Apply RIDOS OS branding, theme, and desktop shortcuts"""
import os, subprocess, glob, shutil

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

def run(cmd):
    return subprocess.run(cmd, shell=True)

# XFCE config dirs
for d in [
    'chroot/home/ridos/.config/xfce4/xfconf/xfce-perchannel-xml',
    'chroot/home/ridos/.config/xfce4/terminal',
    'chroot/home/ridos/Desktop',
    'chroot/home/ridos/.config/autostart',
    'chroot/home/ridos/.config/neofetch',
    'chroot/usr/share/plymouth/themes/ridos',
]:
    os.makedirs(d, exist_ok=True)

# Dark purple XFCE theme
write('chroot/home/ridos/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<channel name="xsettings" version="1.0">
  <property name="Net" type="empty">
    <property name="ThemeName" type="string" value="Adwaita-dark"/>
    <property name="IconThemeName" type="string" value="Papirus-Dark"/>
  </property>
  <property name="Gtk" type="empty">
    <property name="FontName" type="string" value="Noto Sans 10"/>
    <property name="MonospaceFontName" type="string" value="Noto Mono 10"/>
    <property name="CursorThemeName" type="string" value="Adwaita"/>
  </property>
</channel>
''')

# Wallpaper - cover ALL possible monitor names
write('chroot/home/ridos/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-desktop" version="1.0">
  <property name="backdrop" type="empty">
    <property name="screen0" type="empty">
      <property name="monitorVirtual1" type="empty">
        <property name="workspace0" type="empty">
          <property name="color-style" type="int" value="0"/>
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="/usr/share/ridos/ridos-wallpaper.png"/>
        </property>
      </property>
      <property name="monitor0" type="empty">
        <property name="workspace0" type="empty">
          <property name="color-style" type="int" value="0"/>
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="/usr/share/ridos/ridos-wallpaper.png"/>
        </property>
      </property>
      <property name="monitorVGA-1" type="empty">
        <property name="workspace0" type="empty">
          <property name="color-style" type="int" value="0"/>
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="/usr/share/ridos/ridos-wallpaper.png"/>
        </property>
      </property>
      <property name="monitorHDMI-1" type="empty">
        <property name="workspace0" type="empty">
          <property name="color-style" type="int" value="0"/>
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="/usr/share/ridos/ridos-wallpaper.png"/>
        </property>
      </property>
      <property name="monitorScreen0" type="empty">
        <property name="workspace0" type="empty">
          <property name="color-style" type="int" value="0"/>
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="/usr/share/ridos/ridos-wallpaper.png"/>
        </property>
      </property>
    </property>
  </property>
</channel>
''')

# Window manager
write('chroot/home/ridos/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <property name="theme" type="string" value="Default-dark"/>
    <property name="title_font" type="string" value="Noto Sans Bold 10"/>
  </property>
</channel>
''')

# Terminal purple theme
write('chroot/home/ridos/.config/xfce4/terminal/terminalrc',
    '[Configuration]\n'
    'ColorForeground=#E9D5FF\n'
    'ColorBackground=#0F0A1E\n'
    'ColorCursor=#7C3AED\n'
    'FontName=Noto Mono 11\n')

write('chroot/home/ridos/.config/xfce4/helpers.rc', 'TerminalEmulator=xfce4-terminal\n')

# ── CLEAN DESKTOP ─────────────────────────────────────────────
# Remove ALL existing desktop files
for f in glob.glob('chroot/home/ridos/Desktop/*.desktop'):
    os.remove(f)
    print(f"Removed: {os.path.basename(f)}")

# Remove system calamares desktop if exists
for f in [
    'chroot/usr/share/applications/calamares.desktop',
    'chroot/usr/share/applications/install-debian.desktop',
]:
    if os.path.exists(f):
        os.remove(f)

# ── 7 CLEAN DESKTOP ICONS ────────────────────────────────────
# 1. RIDOS Control Center
write('chroot/home/ridos/Desktop/01-control-center.desktop',
    '[Desktop Entry]\n'
    'Version=1.0\n'
    'Type=Application\n'
    'Name=RIDOS Control Center\n'
    'Comment=AI System Management\n'
    'Exec=xfce4-terminal --title="RIDOS Control Center" -e "python3 /opt/ridos/bin/control_center.py"\n'
    'Icon=/usr/share/ridos/ridos-icon.png\n'
    'Terminal=false\n'
    'Categories=System;\n')

# 2. AI Terminal
write('chroot/home/ridos/Desktop/02-ai-terminal.desktop',
    '[Desktop Entry]\n'
    'Version=1.0\n'
    'Type=Application\n'
    'Name=AI Terminal\n'
    'Comment=Intelligent Command Assistant\n'
    'Exec=xfce4-terminal --title="RIDOS AI Terminal" -e "python3 /opt/ridos/bin/ai_features.py 1"\n'
    'Icon=utilities-terminal\n'
    'Terminal=false\n'
    'Categories=System;\n')

# 3. RIDOS AI Shell
write('chroot/home/ridos/Desktop/03-ai-shell.desktop',
    '[Desktop Entry]\n'
    'Version=1.0\n'
    'Type=Application\n'
    'Name=RIDOS AI Shell\n'
    'Comment=AI Assistant Shell\n'
    'Exec=xfce4-terminal --title="RIDOS AI Shell" -e "python3 /opt/ridos/bin/ridos_shell.py"\n'
    'Icon=utilities-terminal\n'
    'Terminal=false\n'
    'Categories=System;\n')

# 4. Firefox Browser
write('chroot/home/ridos/Desktop/04-firefox.desktop',
    '[Desktop Entry]\n'
    'Version=1.0\n'
    'Type=Application\n'
    'Name=Firefox Browser\n'
    'Exec=firefox-esr %u\n'
    'Icon=firefox-esr\n'
    'Terminal=false\n'
    'Categories=Network;WebBrowser;\n')

# 5. File Manager
write('chroot/home/ridos/Desktop/05-files.desktop',
    '[Desktop Entry]\n'
    'Version=1.0\n'
    'Type=Application\n'
    'Name=File Manager\n'
    'Exec=thunar\n'
    'Icon=system-file-manager\n'
    'Terminal=false\n'
    'Categories=System;FileManager;\n')

# 6. Install RIDOS OS
write('chroot/home/ridos/Desktop/06-install-ridos.desktop',
    '[Desktop Entry]\n'
    'Version=1.0\n'
    'Type=Application\n'
    'Name=Install RIDOS OS\n'
    'Comment=Install to hard drive\n'
    'Exec=bash -c "if [ -f /usr/bin/calamares ]; then pkexec /usr/bin/calamares; else xfce4-terminal --title=\'RIDOS Installer\' -e \'sudo /opt/ridos/bin/ridos-install.sh\'; fi"\n'
    'Icon=drive-harddisk\n'
    'Terminal=false\n'
    'Categories=System;\n')

# 7. AI Tools (all tools menu)
write('chroot/home/ridos/Desktop/07-ai-tools.desktop',
    '[Desktop Entry]\n'
    'Version=1.0\n'
    'Type=Application\n'
    'Name=RIDOS AI Tools\n'
    'Comment=Network, Hardware, Security, System\n'
    'Exec=xfce4-terminal --title="RIDOS AI Tools" -e "python3 /opt/ridos/bin/ai_features.py"\n'
    'Icon=utilities-system-monitor\n'
    'Terminal=false\n'
    'Categories=System;Network;\n')

# Make all executable
for f in glob.glob('chroot/home/ridos/Desktop/*.desktop'):
    os.chmod(f, 0o755)
    print(f"Created: {os.path.basename(f)}")

# Autostart Control Center on login
write('chroot/home/ridos/.config/autostart/ridos-welcome.desktop',
    '[Desktop Entry]\n'
    'Type=Application\n'
    'Name=RIDOS Welcome\n'
    'Exec=xfce4-terminal --title="RIDOS OS v1.1.0 Baghdad" -e "bash -c \'cat /etc/motd; echo; bash\'"\n'
    'Hidden=false\n'
    'NoDisplay=false\n'
    'X-GNOME-Autostart-enabled=true\n')

# Neofetch config
write('chroot/home/ridos/.config/neofetch/config.conf',
    'print_info() {\n'
    '    info title\n'
    '    info "OS" distro\n'
    '    info "Kernel" kernel\n'
    '    info "Uptime" uptime\n'
    '    info "DE" de\n'
    '    info "CPU" cpu\n'
    '    info "Memory" memory\n'
    '}\n'
    'ascii_distro="auto"\n')

# Plymouth
write('chroot/usr/share/plymouth/themes/ridos/ridos.plymouth',
    '[Plymouth Theme]\n'
    'Name=RIDOS OS\n'
    'Description=RIDOS OS Boot Splash\n'
    'ModuleName=script\n\n'
    '[script]\n'
    'ImageDir=/usr/share/plymouth/themes/ridos\n'
    'ScriptFile=/usr/share/plymouth/themes/ridos/ridos.script\n')

write('chroot/usr/share/plymouth/themes/ridos/ridos.script',
    'Window.SetBackgroundTopColor(0.42, 0.13, 0.66);\n'
    'Window.SetBackgroundBottomColor(0.12, 0.07, 0.27);\n'
    'message_sprite = Sprite();\n'
    'message_sprite.SetPosition(Window.GetWidth()/2 - 150, Window.GetHeight()/2 - 20, 10000);\n'
    'fun refresh_callback() {\n'
    '  message_image = Image.Text("RIDOS OS v1.1.0 Baghdad", 1.0, 1.0, 1.0);\n'
    '  message_sprite.SetImage(message_image);\n'
    '}\n'
    'Plymouth.SetRefreshFunction(refresh_callback);\n')

run('chroot chroot chown -R ridos:ridos /home/ridos')
print("Branding applied - 7 clean desktop icons")
