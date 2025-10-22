# YouTube Downloader

A simple YouTube video downloader with both GUI and command-line interfaces, built with Python and yt-dlp.

## Features

- Download YouTube videos in various qualities
- Audio-only downloads (MP3 format)
- Both graphical and command-line interfaces
- Smart clipboard integration with URL validation
- Progress tracking with detailed information
- Video information preview
- Custom output directory selection
- Comprehensive error handling and timeouts

## Installation

1. Install Python 3.7 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### GUI Interface

Run the graphical interface:
```bash
python gui.py
```

Features:
- **Smart Paste Button**: Automatically detects and validates YouTube URLs from clipboard
- **URL Validation**: Real-time validation with helpful error messages
- Get video information before downloading
- Select video quality from available formats
- Choose audio-only option (MP3 conversion)
- Set custom output directory
- Real-time progress tracking with speed and ETA
- **Keyboard Shortcuts**: Ctrl+Shift+V to paste and validate URLs

### Command Line Interface

Basic usage:
```bash
python cli.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Options:
- `-o, --output`: Output directory (default: downloads)
- `-q, --quality`: Video quality (best, worst, or specific like 720p)
- `-a, --audio-only`: Download audio only (MP3)
- `-i, --info`: Show video information only
- `-t, --timeout`: Network timeout in seconds (default: 30)

Examples:
```bash
# Download best quality video
python cli.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Download audio only
python cli.py -a "https://www.youtube.com/watch?v=VIDEO_ID"

# Download specific quality
python cli.py -q 720p "https://www.youtube.com/watch?v=VIDEO_ID"

# Custom output directory
python cli.py -o "C:\MyVideos" "https://www.youtube.com/watch?v=VIDEO_ID"

# Get video info only
python cli.py -i "https://www.youtube.com/watch?v=VIDEO_ID"

# Set custom timeout (60 seconds)
python cli.py -t 60 "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Requirements

- Python 3.7+
- yt-dlp
- tkinter (usually included with Python)

## Notes

- Downloads are saved to a "downloads" folder by default
- Audio files are converted to MP3 format
- The tool supports most YouTube video formats and qualities
- For audio extraction, FFmpeg may be required (yt-dlp will prompt if needed)

## Error Handling & Troubleshooting

The application includes comprehensive error handling for common issues:

### Network Issues
- **Timeout errors**: Increase timeout with `-t` option or check internet connection
- **Connection errors**: Verify network connectivity and try again

### Video Issues  
- **Invalid URL**: Ensure you're using a valid YouTube URL format
- **Video unavailable**: Video may be private, deleted, or geo-restricted
- **Age restrictions**: Some videos require authentication

### System Issues
- **Permission errors**: Check write permissions for output directory
- **Disk space**: Ensure sufficient storage space for downloads

### General Troubleshooting
1. Update yt-dlp: `pip install --upgrade yt-dlp`
2. Install FFmpeg for audio extraction
3. Try increasing timeout for slow connections
4. Check YouTube URL is valid and accessible
5. Verify output directory permissions