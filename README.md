# YouTube Downloader

A simple YouTube video downloader with both GUI and command-line interfaces, built with Python and yt-dlp.

## Features

- Download YouTube videos in various qualities
- Audio-only downloads (MP3 format)
- Both graphical and command-line interfaces
- Progress tracking
- Video information preview
- Custom output directory selection

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
- Paste YouTube URL
- Get video information before downloading
- Select video quality
- Choose audio-only option
- Set custom output directory
- Real-time progress tracking

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

## Troubleshooting

If you encounter issues:
1. Make sure you have the latest version of yt-dlp: `pip install --upgrade yt-dlp`
2. For audio extraction issues, install FFmpeg
3. Check that the YouTube URL is valid and accessible