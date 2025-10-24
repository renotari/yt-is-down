# 🚀 GitHub Release Guide - Step by Step

## 📋 **Prerequisites**

Before creating a release, make sure you have:
- [ ] All code committed and pushed to GitHub
- [ ] Executables built and tested
- [ ] Release notes prepared
- [ ] Version number decided (e.g., v2.0.0)

## 🛠️ **Step 1: Build Your Executables**

### **Build for Your Platform**
```bash
# Create icon (optional but recommended)
python create_icon.py

# Build executables
python build_executable.py
```

This creates files in the `dist/` folder:
- `YouTube-Downloader-GUI.exe` (Windows)
- `YouTube-Downloader-CLI.exe` (Windows)
- Or equivalent for Mac/Linux

### **Test Your Executables**
```bash
cd dist
./YouTube-Downloader-GUI.exe    # Test GUI
./YouTube-Downloader-CLI.exe --help  # Test CLI
```

## 🏷️ **Step 2: Create a Git Tag**

### **Option A: Command Line (Recommended)**
```bash
# Create and push a tag
git tag -a v2.0.0 -m "YouTube Downloader v2.0.0 - Production Release"
git push origin v2.0.0
```

### **Option B: GitHub Web Interface**
We'll create the tag during the release process.

## 🌐 **Step 3: Create GitHub Release**

### **Navigate to Releases**
1. Go to your GitHub repository: `https://github.com/renotari/yt-is-down`
2. Click the **"Releases"** tab (or go to `/releases`)
3. Click **"Create a new release"**

### **Fill in Release Information**

#### **Tag Version**
- **Tag**: `v2.0.0`
- **Target**: `main` (or your default branch)

#### **Release Title**
```
YouTube Downloader v2.0.0 - Production Release 🎉
```

#### **Release Description**
```markdown
## 🎬 YouTube Downloader v2.0.0 - Production Release

A secure, user-friendly YouTube video downloader with both GUI and CLI interfaces.

### ✨ **New Features**
- 🖥️ **Modern GUI Interface** - Intuitive drag-and-drop style interface
- ⌨️ **Powerful CLI Interface** - Full command-line control for advanced users
- 🎵 **Audio Extraction** - Download as MP3 with high quality
- 📹 **Video Downloads** - Multiple quality options (best, worst, custom)
- 📋 **Playlist Support** - Download entire playlists with safety delays
- 🔒 **Security Hardened** - Input validation, safe file handling
- 📊 **Progress Tracking** - Real-time download progress and ETA

### 🛡️ **Security & Safety**
- ✅ **Rate Limited** - Respectful 15-25 second delays between downloads
- ✅ **Input Validation** - Prevents malicious URLs and directory traversal
- ✅ **Safe File Handling** - No overwriting of existing files
- ✅ **Error Recovery** - Comprehensive fallback strategies

### 📦 **Download Options**

#### **🖥️ For End Users (No Python Required)**
- **Windows**: Download `YouTube-Downloader-GUI.exe` 
- **Windows CLI**: Download `YouTube-Downloader-CLI.exe`
- **Mac/Linux**: Download `YouTube-Downloader-GUI` (coming soon)

#### **🐍 For Python Users**
```bash
pip install youtube-downloader-secure
```

### 🚀 **Quick Start**

#### **GUI Version**
1. Download `YouTube-Downloader-GUI.exe`
2. Double-click to run
3. Paste YouTube URL
4. Choose quality and format
5. Click Download!

#### **CLI Version**
```bash
# Download video
YouTube-Downloader-CLI.exe "https://youtube.com/watch?v=VIDEO_ID"

# Download audio only
YouTube-Downloader-CLI.exe -a "https://youtube.com/watch?v=VIDEO_ID"

# Download playlist
YouTube-Downloader-CLI.exe "https://youtube.com/playlist?list=PLAYLIST_ID"
```

### 📋 **System Requirements**
- **Windows**: Windows 7 or later
- **Memory**: 100MB RAM
- **Storage**: 50MB free space
- **Network**: Internet connection required

### 🔐 **Legal & Ethics**
- ✅ **Personal Use Only** - For educational and personal use
- ✅ **Respects YouTube** - Conservative rate limiting
- ⚠️ **User Responsibility** - Users must comply with YouTube ToS
- 📄 **Open Source** - MIT License

### 🐛 **Bug Fixes**
- Fixed MP4 deletion when downloading MP3 of same video
- Improved error handling and user feedback
- Enhanced security with input validation
- Better thread safety for concurrent operations

### 🙏 **Credits**
Built with:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Powerful YouTube extraction
- Python & tkinter - Cross-platform GUI
- Love and attention to detail ❤️

### 📞 **Support**
- 🐛 **Bug Reports**: [Open an Issue](https://github.com/renotari/yt-is-down/issues)
- 💡 **Feature Requests**: [Discussions](https://github.com/renotari/yt-is-down/discussions)
- 📖 **Documentation**: [README](https://github.com/renotari/yt-is-down/blob/main/README.md)

---

**⚠️ Disclaimer**: This software is for educational and personal use only. Users are responsible for complying with YouTube's Terms of Service and applicable copyright laws.
```

## 📎 **Step 4: Upload Release Assets**

### **Drag and Drop Files**
In the release creation page, drag these files to the "Attach binaries" area:

#### **Required Files**:
- `YouTube-Downloader-GUI.exe` (or your platform's GUI executable)
- `YouTube-Downloader-CLI.exe` (or your platform's CLI executable)

#### **Optional Files**:
- `YouTube-Downloader-v2.0.0.zip` (packaged version with README, LICENSE)
- `icon.png` (for users who want the icon)
- `CHANGELOG.md` (if you have one)

### **Create a Release Package** (Optional but Professional)
```bash
# Create a release folder
mkdir YouTube-Downloader-v2.0.0
cp dist/YouTube-Downloader-* YouTube-Downloader-v2.0.0/
cp README.md LICENSE YouTube-Downloader-v2.0.0/
cp DISTRIBUTION_QUICKSTART.md YouTube-Downloader-v2.0.0/

# Create ZIP
zip -r YouTube-Downloader-v2.0.0.zip YouTube-Downloader-v2.0.0/
```

## ✅ **Step 5: Publish Release**

### **Release Options**
- [ ] **Set as the latest release** ✅ (recommended)
- [ ] **Set as a pre-release** (only if it's beta/alpha)
- [ ] **Create a discussion for this release** ✅ (recommended)

### **Click "Publish Release"**

## 📊 **Step 6: Verify Your Release**

### **Check Release Page**
Your release should be visible at:
`https://github.com/renotari/yt-is-down/releases/tag/v2.0.0`

### **Test Downloads**
1. Download your own executables from the release page
2. Test them on a clean machine (if possible)
3. Verify they work without Python installed

## 🎯 **Step 7: Promote Your Release**

### **Update Repository**
- Update README.md with download links
- Add a "Latest Release" badge
- Update documentation

### **Share Your Release**
- Social media (if appropriate)
- Relevant communities (Reddit, Discord, forums)
- Friends and colleagues for feedback

## 🔄 **Future Releases**

### **For Updates**
1. Make your changes
2. Commit and push
3. Build new executables
4. Create new tag (e.g., v2.0.1, v2.1.0)
5. Create new release
6. Upload new executables

### **Version Numbering**
- **Major**: v2.0.0 → v3.0.0 (breaking changes)
- **Minor**: v2.0.0 → v2.1.0 (new features)
- **Patch**: v2.0.0 → v2.0.1 (bug fixes)

## 🎉 **Success!**

Once published, users can:
- Download your executables directly
- See professional release notes
- Track download statistics
- Report issues and provide feedback
- Star your repository for updates

Your YouTube Downloader is now professionally distributed! 🚀

## 📋 **Quick Checklist**

Before publishing:
- [ ] Code is tested and working
- [ ] Executables built and tested
- [ ] Version number chosen
- [ ] Release notes written
- [ ] Files ready to upload
- [ ] Legal disclaimer included

After publishing:
- [ ] Test download links work
- [ ] Executables run on clean machine
- [ ] Update repository documentation
- [ ] Monitor for user feedback