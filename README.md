# YouTube Downloader

A simple YouTube video downloader with both GUI and command-line interfaces, built with Python and yt-dlp.

## Features

- Download YouTube videos and playlists in various qualities
- Audio-only downloads (MP3 format)
- Both graphical and command-line interfaces
- Smart clipboard integration with URL validation
- **Safe playlist downloading** with 15-25 second delays between videos
- Progress tracking with detailed information
- Video and playlist information preview with time estimates
- Custom output directory selection
- Comprehensive error handling and timeouts
- Playlist range selection for partial downloads

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
- **Smart Paste Button**: Automatically detects YouTube videos and playlists from clipboard
- **Playlist Support**: Download entire playlists with safety delays (15-25 seconds between videos)
- **URL Validation**: Real-time validation with helpful error messages
- **Time Estimates**: Shows estimated download time for playlists
- Get video/playlist information before downloading
- Select video quality from available formats
- Choose audio-only option (MP3 conversion)
- Set custom output directory
- Real-time progress tracking with playlist progress and ETA
- **Safety First**: Built-in rate limiting to prevent IP blocking
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
- `--playlist-range`: Download only specific range of videos (e.g., 1:10)

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

# Download playlist (with safety delays)
python cli.py "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# Download first 10 videos of playlist
python cli.py --playlist-range 1:10 "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# Get playlist information only
python cli.py -i "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

## Playlist Downloads - Important Information

### Safety First Approach
This application prioritizes **safety over speed** when downloading playlists. We implement:

- **15-25 second delays** between video downloads
- **Conservative rate limiting** to respect YouTube's servers
- **Automatic error handling** to skip failed videos and continue

### Why the Delays?
- **Prevents IP blocking**: Aggressive downloading can result in temporary bans
- **Respects YouTube's infrastructure**: Reduces server load
- **Ensures reliability**: Lower chance of failed downloads
- **Sustainable operation**: Allows for large playlist downloads without interruption

### Time Expectations
- **Small playlist (10 videos)**: ~3-5 minutes
- **Medium playlist (50 videos)**: ~15-20 minutes  
- **Large playlist (100 videos)**: ~30-40 minutes
- **Very large playlist (200+ videos)**: 1+ hours

**This is normal and necessary for safe downloading!**

## Project Structure

```
youtube-downloader/
├── config/
│   ├── download_config.py    # Configuration constants
│   └── error_messages.py     # Standardized error messages
├── docs/
│   ├── refactoring-summary.md # Code improvement summary
│   └── old/                  # Archived overengineering docs
├── downloader.py             # Core download functionality
├── gui.py                    # Graphical user interface
├── cli.py                    # Command-line interface
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Requirements

- Python 3.7+
- yt-dlp
- tkinter (usually included with Python)

## Code Quality

This application has been refactored for better maintainability:
- **Centralized Configuration**: All timeouts, delays, and settings in `config/download_config.py`
- **Standardized Error Messages**: Consistent, helpful error messages in `config/error_messages.py`
- **Clean Code Organization**: Well-structured methods and clear separation of concerns
- **Easy Customization**: Modify behavior by changing constants rather than hunting through code

See `docs/refactoring-summary.md` for details on the improvements made.

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