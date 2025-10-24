#!/usr/bin/env python3
"""
Build script for creating standalone executables using PyInstaller.
Run this script to create distributable executables for your platform.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        return run_command("pip install pyinstaller", "PyInstaller installation")

def build_gui_executable():
    """Build GUI executable."""
    system = platform.system().lower()
    
    # Check if icon exists
    icon_param = ""
    if os.path.exists("icon.ico"):
        icon_param = " --icon=icon.ico"
        print("✅ Using custom icon: icon.ico")
    else:
        print("ℹ️  No custom icon found (icon.ico), using default")
    
    if system == "windows":
        cmd = f'pyinstaller --onefile --windowed --name "YouTube-Downloader-GUI"{icon_param} gui.py'
    elif system == "darwin":  # macOS
        cmd = f'pyinstaller --onefile --windowed --name "YouTube-Downloader-GUI"{icon_param} gui.py'
    else:  # Linux
        cmd = f'pyinstaller --onefile --name "YouTube-Downloader-GUI"{icon_param} gui.py'
    
    return run_command(cmd, "GUI executable build")

def build_cli_executable():
    """Build CLI executable."""
    system = platform.system().lower()
    
    if system == "windows":
        cmd = 'pyinstaller --onefile --name "YouTube-Downloader-CLI" cli.py'
    else:
        cmd = 'pyinstaller --onefile --name "YouTube-Downloader-CLI" cli.py'
    
    return run_command(cmd, "CLI executable build")

def create_spec_file():
    """Create a PyInstaller spec file for advanced configuration."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/', 'config/'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YouTube-Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
'''
    
    with open('youtube_downloader.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Created PyInstaller spec file: youtube_downloader.spec")

def main():
    """Main build process."""
    print("🚀 YouTube Downloader - Executable Builder")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version}")
    print(f"✅ Platform: {platform.system()} {platform.machine()}")
    
    # Check for icon
    if not os.path.exists("icon.ico"):
        print("\n💡 No icon found (icon.ico)")
        print("   Options:")
        print("   1. Run: python create_icon.py  (auto-generate)")
        print("   2. Download icon and save as icon.ico")
        print("   3. Continue without icon (uses default)")
        print("   4. See ICON_SOLUTIONS.md for detailed help")
        
        response = input("\n   Continue without icon? (y/n): ").lower().strip()
        if response not in ['y', 'yes', '']:
            print("   Please add an icon and run the script again.")
            sys.exit(0)
    
    # Install PyInstaller
    if not install_pyinstaller():
        print("❌ Failed to install PyInstaller")
        sys.exit(1)
    
    # Create spec file
    create_spec_file()
    
    # Build executables
    success = True
    
    print("\n" + "=" * 50)
    print("Building executables...")
    
    if not build_gui_executable():
        success = False
    
    if not build_cli_executable():
        success = False
    
    # Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 Build completed successfully!")
        print("\n📁 Executables created in 'dist/' directory:")
        
        dist_path = Path("dist")
        if dist_path.exists():
            for exe_file in dist_path.glob("*"):
                if exe_file.is_file():
                    size_mb = exe_file.stat().st_size / (1024 * 1024)
                    print(f"   • {exe_file.name} ({size_mb:.1f} MB)")
        
        print("\n📋 Next steps:")
        print("   1. Test the executables on your target platforms")
        print("   2. Create installers using NSIS (Windows) or create .app bundles (macOS)")
        print("   3. Consider code signing for distribution")
        print("   4. Upload to GitHub Releases or other distribution platforms")
        
    else:
        print("❌ Build failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()