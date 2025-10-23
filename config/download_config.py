"""
Download configuration constants for YouTube Downloader.

This module contains all configuration constants used throughout the application
to replace magic numbers and provide centralized configuration management.
"""

class DownloadConfig:
    """Configuration constants for download operations."""
    
    # Network and timeout settings
    DEFAULT_TIMEOUT = 30
    DEFAULT_SOCKET_TIMEOUT = 30
    
    # Rate limiting and delays (in seconds)
    DEFAULT_SLEEP_INTERVAL = 15
    MAX_SLEEP_INTERVAL = 25
    CONSERVATIVE_SLEEP_INTERVAL = 25
    CONSERVATIVE_MAX_SLEEP_INTERVAL = 45
    
    # Request delays (in seconds)
    DEFAULT_REQUEST_DELAY = 3
    SUBTITLE_REQUEST_DELAY = 5
    AUDIO_REQUEST_DELAY = 8
    
    # Download speed limits (bytes per second)
    DEFAULT_RATE_LIMIT = 150000  # 150KB/s
    CONSERVATIVE_RATE_LIMIT = 75000  # 75KB/s for audio downloads
    
    # Retry settings
    DEFAULT_RETRIES = 5
    FRAGMENT_RETRIES = 5
    EXTRACTOR_RETRIES = 3
    CONSERVATIVE_RETRIES = 2
    MINIMAL_RETRIES = 1
    
    # Playlist settings
    PLAYLIST_SIZE_WARNING_THRESHOLD = 200
    PLAYLIST_PREVIEW_COUNT = 10  # Number of videos to show in preview
    PLAYLIST_INFO_PREVIEW_COUNT = 5  # Number of videos to show in info
    
    # Audio download settings
    DEFAULT_AUDIO_QUALITY = '192'
    CONSERVATIVE_AUDIO_QUALITY = '128'
    MINIMAL_AUDIO_QUALITY = '64'
    
    # Progress and UI settings
    PROGRESS_BAR_LENGTH = 30
    CLIPBOARD_CHECK_INTERVAL = 2000  # milliseconds
    
    # File size limits
    AUDIO_FILE_SIZE_PREFERENCE = 50 * 1024 * 1024  # 50MB for audio files


class UserAgents:
    """User agent strings for different client types."""
    
    DESKTOP_CHROME = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    MOBILE_ANDROID = 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
    MOBILE_FIREFOX = 'Mozilla/5.0 (Android 10; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0'
    DESKTOP_CHROME_LATEST = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    IOS_YOUTUBE = 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)'


class YouTubeClients:
    """YouTube client configurations for different extraction strategies."""
    
    ANDROID = 'android'
    IOS = 'ios'
    WEB = 'web'
    TV_EMBEDDED = 'tv_embedded'
    
    # Client priority order for fallbacks
    FALLBACK_ORDER = [ANDROID, IOS, WEB, TV_EMBEDDED]


class FormatSelectors:
    """Format selector strings for different quality preferences."""
    
    BEST_VIDEO = 'best'
    WORST_VIDEO = 'worst'
    BEST_AUDIO = 'bestaudio/best'
    WORST_AUDIO = 'worstaudio/worst'
    
    # Audio-specific formats
    AUDIO_M4A = 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio'
    AUDIO_WEBM = 'bestaudio[ext=webm]/bestaudio'
    
    # Conservative formats for fallbacks
    LOW_QUALITY_VIDEO = 'worst[height<=480]/worst'
    VERY_LOW_QUALITY_VIDEO = 'worst[height<=360]/worst'
    MINIMAL_QUALITY_VIDEO = 'worst[height<=240]/worst'
    ULTRA_LOW_QUALITY_VIDEO = 'worst[height<=144]/worst'
    
    # Size-limited formats
    SMALL_AUDIO_FILE = 'bestaudio[filesize<50M]/bestaudio'


class HTTPHeaders:
    """Standard HTTP headers for different request types."""
    
    STANDARD_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    MOBILE_HEADERS = {
        **STANDARD_HEADERS,
        'User-Agent': UserAgents.MOBILE_ANDROID
    }
    
    DESKTOP_HEADERS = {
        **STANDARD_HEADERS,
        'User-Agent': UserAgents.DESKTOP_CHROME
    }


class ValidationConfig:
    """Configuration for URL and input validation."""
    
    YOUTUBE_DOMAINS = [
        'youtube.com',
        'www.youtube.com', 
        'youtu.be',
        'm.youtube.com',
        'music.youtube.com'
    ]
    
    PLAYLIST_INDICATORS = [
        'list=',           # Standard playlist parameter
        '/playlist?',      # Direct playlist URL
        '&list=',          # Playlist parameter in video URL
        'playlist/',       # Alternative playlist format
    ]
    
    # URL validation patterns
    MAX_URL_LENGTH = 2048
    MIN_VIDEO_ID_LENGTH = 11