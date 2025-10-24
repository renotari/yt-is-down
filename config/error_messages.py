"""
Standardized error messages for YouTube Downloader.

This module contains all error message templates to ensure consistent
user communication throughout the application.
"""

class ErrorMessages:
    """Standardized error message templates."""
    
    # URL validation errors
    INVALID_URL_FORMAT = (
        "Please enter a valid YouTube URL.\n\n"
        "Supported formats:\n"
        "• https://www.youtube.com/watch?v=...\n"
        "• https://youtu.be/...\n"
        "• https://m.youtube.com/watch?v=..."
    )
    
    INVALID_URL_CONTENT = (
        "The clipboard contains a URL, but it's not a valid YouTube URL.\n\n"
        "Found: {url}\n\n"
        "Supported YouTube formats:\n"
        "• https://www.youtube.com/watch?v=...\n"
        "• https://youtu.be/...\n"
        "• https://m.youtube.com/watch?v=..."
    )
    
    # Network errors
    NETWORK_TIMEOUT = "Connection timed out after {timeout} seconds"
    NETWORK_TIMEOUT_DETAILED = (
        "Download timed out. Please check your internet connection and try again.\n\n"
        "Timeout: {timeout} seconds\n"
        "Details: {details}"
    )
    
    NETWORK_ERROR = "Network error: {error}"
    
    # Video availability errors
    VIDEO_UNAVAILABLE = (
        "The video is not available for download.\n\n"
        "Possible reasons:\n"
        "• Video is private or deleted\n"
        "• Geographic restrictions\n"
        "• Age restrictions\n\n"
        "Details: {details}"
    )
    
    VIDEO_PRIVATE = "Video is unavailable: {details}"
    
    # Playlist errors
    PLAYLIST_PRIVATE = (
        "Playlist is private or unavailable:\n\n"
        "{details}"
    )
    
    PLAYLIST_TOO_LARGE = (
        "Playlist contains {count} videos. "
        "For safety, we recommend downloading playlists with fewer than {threshold} videos. "
        "Large playlists may take several hours and risk IP blocking."
    )
    
    PLAYLIST_EMPTY = "Playlist appears to be empty or all videos are unavailable"
    
    PLAYLIST_NOT_FOUND = (
        "URL appears to be a playlist URL but yt-dlp detected it as: {type}.\n"
        "This might be a single video in a playlist or an invalid playlist URL."
    )
    
    PLAYLIST_SINGLE_VIDEO = (
        "URL does not point to a playlist - this appears to be a single video"
    )
    
    # Download errors
    DOWNLOAD_FAILED = "Download failed: {error}"
    
    HTTP_403_ERROR = (
        "YouTube blocked the download (HTTP 403 Forbidden).\n\n"
        "This can happen due to:\n"
        "• YouTube's anti-bot measures\n"
        "• Geographic restrictions\n"
        "• Rate limiting\n\n"
        "Solutions to try:\n"
        "1. Wait a few minutes and try again\n"
        "2. Try a different video quality\n"
        "3. Update yt-dlp: pip install --upgrade yt-dlp\n"
        "4. Use a VPN if geographically restricted\n\n"
        "Technical details: {details}"
    )
    
    AUDIO_DOWNLOAD_FAILED = (
        "All audio download strategies failed due to YouTube restrictions (HTTP 403).\n\n"
        "YouTube has become extremely aggressive with audio-only downloads. Try:\n"
        "1. Update yt-dlp: pip install --upgrade yt-dlp\n"
        "2. Wait 1-2 hours before trying again\n"
        "3. Try downloading as video first, then convert to MP3 locally\n"
        "4. Use a VPN to change your location\n"
        "5. Try downloading during off-peak hours (late night/early morning)\n"
        "6. Check if the video has copyright restrictions in your region\n\n"
        "💡 Alternative: Download as video (which works more reliably) then use a local tool to convert to MP3.\n\n"
        "Audio downloads are significantly more likely to be blocked than video downloads."
    )
    
    VIDEO_DOWNLOAD_FAILED = (
        "All download strategies failed due to YouTube restrictions (HTTP 403).\n\n"
        "YouTube frequently updates their anti-bot measures. Try:\n"
        "1. Update yt-dlp: pip install --upgrade yt-dlp\n"
        "2. Wait 10-15 minutes before trying again\n"
        "3. Try a different video quality\n"
        "4. Check if the video is available in your region"
    )
    
    # File system errors
    PERMISSION_DENIED = "Permission denied: Cannot create directory {path}"
    DISK_SPACE_ERROR = "Insufficient disk space for download"
    OUTPUT_DIR_ERROR = "Cannot create output directory: {error}"
    
    # FFmpeg errors
    FFMPEG_MISSING = (
        "Audio conversion failed. Please install FFmpeg:\n"
        "Windows: Download from https://ffmpeg.org/download.html\n"
        "Or install via chocolatey: choco install ffmpeg\n\n"
        "Error details: {error}"
    )
    
    # User interaction errors
    DOWNLOAD_CANCELLED = "Download cancelled by user"
    PLAYLIST_CANCELLED = "Playlist download cancelled by user"
    
    # Clipboard errors
    CLIPBOARD_EMPTY = (
        "Could not access clipboard content.\n\n"
        "Please make sure you have copied a YouTube URL to your clipboard."
    )
    
    CLIPBOARD_INVALID_CONTENT = (
        "Clipboard doesn't contain a valid YouTube URL.\n\n"
        "Found: {content}\n\n"
        "Please copy a YouTube URL to your clipboard first."
    )
    
    CLIPBOARD_ACCESS_ERROR = "An error occurred while accessing clipboard: {error}"
    
    # General errors
    UNEXPECTED_ERROR = (
        "An unexpected error occurred:\n{error}\n\n"
        "Please try again or contact support."
    )
    
    VALIDATION_ERROR = "Please specify an output directory"


class InfoMessages:
    """Informational message templates."""
    
    # Video in playlist messages
    VIDEO_IN_PLAYLIST_DETECTED = (
        "🎵 Video in Playlist Detected!\n\n"
        "📹 Current Video: {video_title}\n"
        "📋 Playlist: {playlist_title} ({playlist_count} videos)\n\n"
        "What would you like to download?\n\n"
        "• Click 'Yes' to download just this video\n"
        "• Click 'No' to download the entire playlist\n"
        "• Click 'Cancel' to choose different options"
    )
    
    VIDEO_IN_PLAYLIST_CLI_INFO = (
        "🎵 Video in Playlist Detected!\n"
        "📹 Current Video: {video_title}\n"
        "📋 Playlist: {playlist_title} ({playlist_count} videos)\n\n"
        "💡 Options:\n"
        "   • Add --video-only to download just the current video\n"
        "   • Remove --video-only to download the entire playlist"
    )
    
    # Success messages
    DOWNLOAD_COMPLETE = "🎉 Download Complete!"
    AUDIO_DOWNLOAD_COMPLETE = "🎵 Audio download completed!\n\n📁 MP3 file saved to:\n{path}"
    VIDEO_DOWNLOAD_COMPLETE = "🎬 Video download completed!\n\n📁 File saved to:\n{path}"
    
    PLAYLIST_DOWNLOAD_COMPLETE = (
        "✅ Playlist download completed!\n"
        "📋 Playlist: {title}\n"
        "📊 Downloaded: {downloaded}/{total} videos\n"
        "⚠️  Failed: {failed} videos\n"
        "⏱️  Total time: {time} seconds\n"
        "📁 Files saved to: {path}"
    )
    
    # Progress messages
    GETTING_INFO = "🔍 Getting information..."
    INITIALIZING_DOWNLOAD = "🚀 Initializing download..."
    PREPARING_DOWNLOAD = "🔄 Preparing to download..."
    CONVERTING_AUDIO = "🎵 Converting to MP3..."
    PROCESSING = "🔄 Processing..."
    
    # Playlist messages
    PLAYLIST_DETECTED = "📋 YouTube Playlist detected!"
    PLAYLIST_STARTING = "📋 Starting playlist download with safety delays (15-25 seconds between videos)"
    
    # Status messages
    READY_TO_DOWNLOAD = "✨ Ready to download"
    CANCELLING = "⏹️ Cancelling..."
    CANCELLED = "⏹️ Cancelled"
    
    # Confirmation messages
    PLAYLIST_DOWNLOAD_CONFIRMATION = (
        "You are about to download a playlist with {count} videos.\n\n"
        "⏰ Estimated time: ~{time} minutes\n"
        "⚠️  This will use 15-25 second delays between downloads for safety.\n"
        "{audio_warning}"
        "\nDo you want to continue?"
    )
    
    PLAYLIST_DOWNLOAD_CONFIRMATION_NO_INFO = (
        "You are about to download a YouTube playlist.\n\n"
        "⚠️  IMPORTANT: Playlist downloads use 15-25 second delays between videos for safety.\n"
        "⏰ This may take considerable time depending on playlist size.\n\n"
        "{audio_warning}"
        "💡 Tip: Click 'Get Video Info' first to see playlist details and time estimates.\n\n"
        "Do you want to continue?"
    )
    
    AUDIO_DOWNLOAD_WARNING = (
        "🎵 AUDIO-ONLY DOWNLOAD:\n"
        "   • YouTube is more restrictive with audio downloads\n"
        "   • Uses even longer delays (20-35 seconds) for safety\n"
        "   • Higher chance of temporary blocks\n"
    )


class TroubleshootingMessages:
    """Troubleshooting and help message templates."""
    
    MP3_ALTERNATIVES = (
        "🎵 MP3 Download Failed - Try These Alternatives:\n\n"
        "🔄 IMMEDIATE OPTIONS:\n"
        "1. Download as VIDEO first (more reliable), then convert locally\n"
        "2. Try again in 1-2 hours (YouTube restrictions are temporary)\n"
        "3. Update yt-dlp: pip install --upgrade yt-dlp\n\n"
        "🌐 BYPASS OPTIONS:\n"
        "4. Use a VPN to change your location\n"
        "5. Try during off-peak hours (late night/early morning)\n"
        "6. Check if the video is region-restricted\n\n"
        "💡 WHY THIS HAPPENS:\n"
        "YouTube aggressively blocks audio-only downloads because:\n"
        "• Audio files are easier to distribute (copyright concerns)\n"
        "• Audio extraction indicates automated scraping\n"
        "• Video downloads appear more 'legitimate' to YouTube\n\n"
        "🎯 RECOMMENDED APPROACH:\n"
        "Download as video (which usually works) → Convert to MP3 locally using:\n"
        "• FFmpeg: ffmpeg -i video.mp4 -q:a 0 -map a audio.mp3\n"
        "• VLC Media Player (free converter)\n"
        "• Online converters (for small files)\n\n"
        "📋 Original URL: {url}"
    )
    
    HTTP_403_FIXES = (
        "🔧 Quick fixes for HTTP 403 errors:\n"
        "   1. pip install --upgrade yt-dlp\n"
        "   2. Wait 10-15 minutes and try again\n"
        "   3. Try different quality: --quality worst\n"
        "   4. Check if video is region-locked"
    )
    
    PLAYLIST_LARGE_WARNING = (
        "💡 Recommendations:\n"
        "   • Use --playlist-range to download in smaller batches\n"
        "   • Example: --playlist-range 1:50 for first 50 videos"
    )
    
    KEYBOARD_SHORTCUTS = (
        "🎹 Keyboard Shortcuts:\n\n"
        "⌨️ Ctrl+Shift+V - Paste and validate URL\n"
        "⌨️ Enter (in URL field) - Get video info\n"
        "⌨️ Ctrl+Q - Quit application\n\n"
        "💡 Tips:\n"
        "• Copy any YouTube URL and the paste button will highlight\n"
        "• Press Enter after pasting a URL to quickly get video info\n"
        "• Use the Browse button to select a custom download folder"
    )
    
    ABOUT_TEXT = (
        "🎬 YouTube Downloader v2.0\n\n"
        "A modern, user-friendly YouTube video downloader built with Python.\n\n"
        "✨ Features:\n"
        "• Download videos in multiple qualities\n"
        "• Extract audio as MP3 files\n"
        "• Smart clipboard integration\n"
        "• Real-time progress tracking\n"
        "• Comprehensive error handling\n\n"
        "🛠️ Built with:\n"
        "• Python 3.7+\n"
        "• tkinter (GUI)\n"
        "• yt-dlp (Download engine)\n\n"
        "💝 Open Source\n"
        "This software is free and open source.\n\n"
        "🎯 Made for easy YouTube downloading!"
    )