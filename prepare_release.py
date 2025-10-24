#!/usr/bin/env python3
"""
Release preparation script for YouTube Downloader
Builds executables and packages them for GitHub release.
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path
from datetime import datetime

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

def clean_build_dirs():
    """Clean previous build directories."""
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    for dir_pattern in dirs_to_clean:
        for path in Path('.').glob(dir_pattern):
            if path.is_dir():
                print(f"🧹 Cleaning {path}")
                shutil.rmtree(path)
            elif path.is_file():
                print(f"🧹 Removing {path}")
                path.unlink()

def build_executables():
    """Build the executables."""
    print("\n🔨 Building executables...")
    
    # Check if we have an icon
    if not Path("icon.ico").exists():
        print("💡 No icon found. Creating one...")
        if not run_command("python create_icon.py", "Icon creation"):
            print("⚠️  Continuing without icon...")
    
    # Build executables
    return run_command("python build_executable.py", "Executable build")

def create_release_package(version):
    """Create a packaged release with all necessary files."""
    release_dir = f"YouTube-Downloader-{version}"
    
    # Create release directory
    if Path(release_dir).exists():
        shutil.rmtree(release_dir)
    Path(release_dir).mkdir()
    
    print(f"\n📦 Creating release package: {release_dir}")
    
    # Copy executables
    dist_dir = Path("dist")
    if dist_dir.exists():
        for exe_file in dist_dir.glob("YouTube-Downloader-*"):
            if exe_file.is_file():
                dest = Path(release_dir) / exe_file.name
                shutil.copy2(exe_file, dest)
                print(f"✅ Copied: {exe_file.name}")
    
    # Copy documentation
    docs_to_copy = [
        "README.md",
        "LICENSE", 
        "DISTRIBUTION_QUICKSTART.md",
        "ICON_SOLUTIONS.md"
    ]
    
    for doc in docs_to_copy:
        if Path(doc).exists():
            shutil.copy2(doc, Path(release_dir) / doc)
            print(f"✅ Copied: {doc}")
    
    # Copy icon if it exists
    if Path("icon.png").exists():
        shutil.copy2("icon.png", Path(release_dir) / "icon.png")
        print(f"✅ Copied: icon.png")
    
    # Create a simple installation guide
    install_guide = f"""# YouTube Downloader v{version} - Installation Guide

## 🚀 Quick Start

### For Windows Users:
1. Download `YouTube-Downloader-GUI.exe` for the graphical interface
2. Or download `YouTube-Downloader-CLI.exe` for command-line use
3. Double-click to run (no installation required!)

### For GUI Version:
1. Run `YouTube-Downloader-GUI.exe`
2. Paste a YouTube URL
3. Choose your preferred quality and format
4. Click Download!

### For CLI Version:
Open Command Prompt and run:
```
YouTube-Downloader-CLI.exe "https://youtube.com/watch?v=VIDEO_ID"
```

## 📋 What's Included:
- YouTube-Downloader-GUI.exe - Graphical interface
- YouTube-Downloader-CLI.exe - Command-line interface  
- README.md - Full documentation
- LICENSE - MIT License terms
- This installation guide

## 🔐 Security Note:
This software is for personal and educational use only. Please respect YouTube's Terms of Service.

## 🐛 Issues or Questions:
Visit: https://github.com/renotari/yt-is-down/issues

Enjoy downloading! 🎉
"""
    
    with open(Path(release_dir) / "INSTALL.md", "w") as f:
        f.write(install_guide)
    print("✅ Created: INSTALL.md")
    
    # Create ZIP file
    zip_filename = f"{release_dir}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in Path(release_dir).rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(".")
                zipf.write(file_path, arcname)
    
    print(f"✅ Created ZIP: {zip_filename}")
    return release_dir, zip_filename

def generate_release_notes(version):
    """Generate release notes template."""
    release_notes = f"""# YouTube Downloader v{version} - Release Notes

## 🎬 What's New

### ✨ Features
- 🖥️ Modern GUI interface with drag-and-drop functionality
- ⌨️ Powerful CLI for advanced users and automation
- 🎵 High-quality audio extraction (MP3)
- 📹 Multiple video quality options
- 📋 Full playlist support with safety delays
- 🔒 Security hardened with comprehensive input validation

### 🛡️ Security & Safety
- ✅ Rate limiting (15-25 second delays) to respect YouTube servers
- ✅ Input validation prevents malicious URLs
- ✅ Safe file handling prevents overwriting existing files
- ✅ Comprehensive error recovery with fallback strategies

### 🐛 Bug Fixes
- Fixed MP4 deletion when downloading MP3 of same video
- Improved error handling and user feedback
- Enhanced thread safety for concurrent operations
- Better progress tracking and ETA calculations

## 📦 Downloads

### 🖥️ For End Users (No Python Required)
- **Windows GUI**: `YouTube-Downloader-GUI.exe`
- **Windows CLI**: `YouTube-Downloader-CLI.exe`
- **Complete Package**: `YouTube-Downloader-{version}.zip`

### 🐍 For Python Users
```bash
pip install youtube-downloader-secure
```

## 🚀 Quick Start

1. Download the appropriate executable for your needs
2. Double-click to run (GUI) or use command line (CLI)
3. Paste YouTube URL and download!

## 📋 System Requirements
- Windows 7 or later
- 100MB RAM, 50MB storage
- Internet connection

## 🔐 Legal Notice
For personal and educational use only. Users must comply with YouTube's Terms of Service.

---
Built with ❤️ and attention to security and user experience.
"""
    
    with open(f"RELEASE_NOTES_v{version}.md", "w") as f:
        f.write(release_notes)
    
    print(f"✅ Created: RELEASE_NOTES_v{version}.md")
    return f"RELEASE_NOTES_v{version}.md"

def main():
    """Main release preparation process."""
    print("🚀 YouTube Downloader - Release Preparation")
    print("=" * 50)
    
    # Get version
    version = input("Enter version number (e.g., v2.0.0): ").strip()
    if not version:
        version = "v2.0.0"
    
    if not version.startswith('v'):
        version = f"v{version}"
    
    print(f"📋 Preparing release: {version}")
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build executables
    if not build_executables():
        print("❌ Failed to build executables")
        sys.exit(1)
    
    # Create release package
    release_dir, zip_file = create_release_package(version)
    
    # Generate release notes
    release_notes_file = generate_release_notes(version)
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Release preparation complete!")
    
    print(f"\n📁 Files ready for GitHub release:")
    
    # List executables
    dist_dir = Path("dist")
    if dist_dir.exists():
        for exe_file in dist_dir.glob("YouTube-Downloader-*"):
            if exe_file.is_file():
                size_mb = exe_file.stat().st_size / (1024 * 1024)
                print(f"   • {exe_file.name} ({size_mb:.1f} MB)")
    
    # List package
    if Path(zip_file).exists():
        size_mb = Path(zip_file).stat().st_size / (1024 * 1024)
        print(f"   • {zip_file} ({size_mb:.1f} MB)")
    
    print(f"   • {release_notes_file}")
    
    print(f"\n📋 Next steps:")
    print("1. Go to: https://github.com/renotari/yt-is-down/releases")
    print("2. Click 'Create a new release'")
    print(f"3. Tag: {version}")
    print(f"4. Title: YouTube Downloader {version} - Production Release")
    print(f"5. Copy content from: {release_notes_file}")
    print("6. Upload the files listed above")
    print("7. Click 'Publish release'")
    
    print(f"\n🎯 Or follow the detailed guide:")
    print("   See: docs/github-release-guide.md")

if __name__ == "__main__":
    main()