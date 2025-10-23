# 🔍 Critical Code Snippets for AI Review

## 1. Core Download Logic (downloader.py)

### Main Download Method
```python
def download_video(self, url: str, quality: str = 'best', audio_only: bool = False, 
                  progress_callback: Optional[Callable] = None) -> bool:
    """Download video with specified quality"""
    if not self._is_valid_url(url):
        raise InvalidURLError(ErrorMessages.INVALID_URL_FORMAT)
    
    # Ensure output_dir is a Path object
    if isinstance(self.output_dir, str):
        self.output_dir = Path(self.output_dir)
    
    # Validate output directory
    try:
        self.output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise YouTubeDownloaderError(ErrorMessages.PERMISSION_DENIED.format(path=self.output_dir))
    except OSError as e:
        raise YouTubeDownloaderError(ErrorMessages.OUTPUT_DIR_ERROR.format(error=str(e)))
    
    # Build yt-dlp options with timeouts and error handling
    base_opts = {
        'socket_timeout': self.timeout,
        'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
        'no_warnings': True,
        'ignoreerrors': False,
        'retries': DownloadConfig.EXTRACTOR_RETRIES,
        'fragment_retries': DownloadConfig.EXTRACTOR_RETRIES,
        'extractor_retries': DownloadConfig.EXTRACTOR_RETRIES,
        'sleep_interval': 2,
        'max_sleep_interval': 5,
        'http_headers': {
            'User-Agent': UserAgents.DESKTOP_CHROME
        },
    }
    
    if audio_only:
        ydl_opts = {
            **base_opts,
            'format': FormatSelectors.BEST_AUDIO,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': DownloadConfig.DEFAULT_AUDIO_QUALITY,
            }],
            'keepvideo': False,
        }
    else:
        # Format selection logic...
        ydl_opts = {**base_opts, 'format': format_selector}
    
    try:
        return self._try_download_with_fallbacks(ydl_opts, url, audio_only)
    except Exception as e:
        # Error handling...
```

**Questions for Review:**
- Is the error handling comprehensive?
- Are the yt-dlp options appropriate?
- Any security concerns with file path handling?

## 2. Fallback Strategy Logic

### Recently Refactored Fallback System
```python
def _try_download_with_fallbacks(self, ydl_opts: dict, url: str, audio_only: bool = False) -> bool:
    """Try download with different fallback strategies for 403 errors"""
    
    # Strategy 1: Normal download
    if self._try_normal_download(ydl_opts, url):
        return True

    # Enhanced strategies for audio downloads (YouTube is more restrictive with audio)
    if audio_only:
        if self._try_audio_format_fallback(ydl_opts, url):
            return True
        if self._try_mobile_client_fallback(ydl_opts, url):
            return True
        # ... more fallback strategies

    # If all strategies fail, provide specific guidance
    self._raise_fallback_error(audio_only)

def _try_normal_download(self, ydl_opts: dict, url: str) -> bool:
    """Try normal download strategy"""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return True
    except yt_dlp.DownloadError as e:
        if "403" not in str(e).lower() and "forbidden" not in str(e).lower():
            raise  # Re-raise if not a 403 error
        return False
```

**Questions for Review:**
- Is this fallback strategy approach sound?
- Are we handling YouTube restrictions appropriately?
- Any better ways to detect and handle different error types?

## 3. Rate Limiting Configuration

### Conservative Rate Limiting (config/download_config.py)
```python
class DownloadConfig:
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
```

**Questions for Review:**
- Are these rate limiting values appropriate?
- Too conservative or too aggressive?
- Any better approaches to avoid YouTube blocking?

## 4. Error Handling Pattern

### Standardized Error Messages (config/error_messages.py)
```python
class ErrorMessages:
    INVALID_URL_FORMAT = (
        "Please enter a valid YouTube URL.\n\n"
        "Supported formats:\n"
        "• https://www.youtube.com/watch?v=...\n"
        "• https://youtu.be/...\n"
        "• https://m.youtube.com/watch?v=..."
    )
    
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
```

**Questions for Review:**
- Are these error messages helpful to users?
- Any important error scenarios we're missing?
- Better ways to guide users through problems?

## 5. GUI Progress Tracking (gui.py)

### Progress Callback System
```python
def progress_hook(self, d):
    """Progress callback for GUI updates"""
    try:
        status = d.get('status', 'unknown')
        
        if status == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            
            if total > 0:
                percentage = (downloaded / total) * 100
                self.root.after(0, lambda p=percentage: self.progress_bar.config(value=p))
            
            # Check if this is part of a playlist download
            playlist_stats = d.get('playlist_stats')
            if playlist_stats:
                current_video = playlist_stats.get('downloaded', 0) + 1
                total_videos = playlist_stats.get('total_videos', 0)
                progress_text = f"📋 Playlist: Video {current_video}/{total_videos} • {percentage:.1f}%"
            else:
                progress_text = f"⬇️ Downloading {percentage:.1f}%"
            
            self.root.after(0, lambda pt=progress_text: self.progress_var.set(pt))
            
    except Exception as e:
        # Prevent progress callback errors from crashing the download
        print(f"Progress callback error: {e}")
        pass
```

**Questions for Review:**
- Is this thread-safe GUI updating approach correct?
- Any race conditions or potential issues?
- Better ways to handle progress updates?

---

## 🎯 Overall Architecture Questions

1. **Is the single-class approach in `downloader.py` appropriate, or should we split it further?**
2. **Are we properly separating concerns between GUI, CLI, and core logic?**
3. **Any obvious Python anti-patterns or code smells we missed?**
4. **How well does this handle edge cases and error recovery?**
5. **Any security vulnerabilities in how we handle user input or file operations?**

Please focus on practical improvements that maintain the simplicity of this desktop application.