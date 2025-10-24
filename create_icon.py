#!/usr/bin/env python3
"""
Simple icon creator for YouTube Downloader
Creates a basic icon using PIL (Pillow) if available, or provides alternatives.
"""

import os
import sys
from pathlib import Path

def create_simple_icon():
    """Create a simple icon using PIL/Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        print("✅ PIL/Pillow found, creating icon...")
    except ImportError:
        print("❌ PIL/Pillow not found. Install with: pip install Pillow")
        return False
    
    # Create a 256x256 image with transparent background
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # YouTube-inspired colors
    youtube_red = (255, 0, 0)
    white = (255, 255, 255)
    dark_gray = (33, 33, 33)
    
    # Draw background circle (YouTube red)
    margin = 20
    circle_bbox = [margin, margin, size - margin, size - margin]
    draw.ellipse(circle_bbox, fill=youtube_red)
    
    # Draw play button (white triangle)
    center_x, center_y = size // 2, size // 2
    triangle_size = 60
    
    # Triangle points (play button)
    triangle = [
        (center_x - triangle_size//2, center_y - triangle_size//2),
        (center_x - triangle_size//2, center_y + triangle_size//2),
        (center_x + triangle_size//2, center_y)
    ]
    draw.polygon(triangle, fill=white)
    
    # Draw download arrow below
    arrow_y = center_y + 40
    arrow_size = 25
    
    # Downward arrow
    arrow_points = [
        (center_x - arrow_size, arrow_y - arrow_size//2),
        (center_x + arrow_size, arrow_y - arrow_size//2),
        (center_x + arrow_size//2, arrow_y - arrow_size//2),
        (center_x + arrow_size//2, arrow_y + arrow_size//2),
        (center_x - arrow_size//2, arrow_y + arrow_size//2),
        (center_x - arrow_size//2, arrow_y - arrow_size//2),
    ]
    draw.polygon(arrow_points, fill=white)
    
    # Save as ICO file (Windows icon format)
    try:
        img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print("✅ Icon created successfully: icon.ico")
        
        # Also save as PNG for other uses
        img.save('icon.png', format='PNG')
        print("✅ PNG version created: icon.png")
        
        return True
    except Exception as e:
        print(f"❌ Error saving icon: {e}")
        return False

def download_icon_from_web():
    """Provide instructions for downloading a professional icon."""
    print("\n🎨 Professional Icon Options:")
    print("\n1. 📥 Free Icon Websites:")
    print("   • Icons8: https://icons8.com/icons/set/youtube-download")
    print("   • Flaticon: https://www.flaticon.com/search?word=youtube%20download")
    print("   • Feather Icons: https://feathericons.com/ (search 'download')")
    print("   • Heroicons: https://heroicons.com/ (search 'arrow-down')")
    
    print("\n2. 🎯 Search Terms to Use:")
    print("   • 'youtube downloader icon'")
    print("   • 'video download icon'")
    print("   • 'media downloader icon'")
    print("   • 'play button download'")
    
    print("\n3. 📐 Icon Requirements:")
    print("   • Format: .ico (Windows) or .png (cross-platform)")
    print("   • Size: 256x256 pixels minimum")
    print("   • Multiple sizes in ICO: 16x16, 32x32, 64x64, 128x128, 256x256")
    print("   • Transparent background preferred")
    
    print("\n4. 🛠️ Icon Conversion Tools:")
    print("   • Online: https://convertio.co/png-ico/")
    print("   • Online: https://www.icoconverter.com/")
    print("   • Software: GIMP (free), Photoshop, or any image editor")

def create_ascii_icon():
    """Create a simple ASCII-based icon description."""
    ascii_icon = """
    ╭─────────────────╮
    │  🎬 YouTube     │
    │     Downloader  │
    │                 │
    │      ▶️ ⬇️       │
    │                 │
    │   [Video] [MP3] │
    ╰─────────────────╯
    """
    
    print("\n🎨 ASCII Icon Concept:")
    print(ascii_icon)
    print("This represents the app concept - you can use this as inspiration for a graphic designer!")

def main():
    """Main icon creation process."""
    print("🎨 YouTube Downloader - Icon Creator")
    print("=" * 40)
    
    # Try to create a simple icon
    if create_simple_icon():
        print("\n🎉 Success! Icon created and ready to use.")
        print("📁 Files created:")
        print("   • icon.ico (for Windows executables)")
        print("   • icon.png (for general use)")
        
        # Test the build script
        print("\n🔧 You can now run the build script:")
        print("   python build_executable.py")
        
    else:
        print("\n💡 Alternative Options:")
        download_icon_from_web()
        create_ascii_icon()
        
        print("\n📋 Quick Fix:")
        print("1. Download any YouTube/download icon from the web")
        print("2. Save it as 'icon.ico' in this directory")
        print("3. Run: python build_executable.py")
        
        print("\n🚀 Or build without icon:")
        print("The build script will now work without an icon (uses default)")

if __name__ == "__main__":
    main()