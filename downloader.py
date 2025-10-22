import yt_dlp
import os
import socket
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, Callable

class YouTubeDownloaderError(Exception):
    """Base exception for YouTube downloader errors"""
    pass

class NetworkTimeoutError(YouTubeDownloaderError):
    """Raised when network operations timeout"""
    pass

class VideoUnavailableError(YouTubeDownloaderError):
    """Raised when video is unavailable or private"""
    pass

class InvalidURLError(YouTubeDownloaderError):
    """Raised when URL is invalid"""
    pass

class YouTubeDownloader:
    def __init__(self, output_dir="downloads", timeout=30):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timeout = timeout
        
        # Set default socket timeout
        socket.setdefaulttimeout(self.timeout)
        
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """Get video information without downloading"""
        if not self._is_valid_url(url):
            raise InvalidURLError("Invalid YouTube URL format")
        
        ydl_opts = {
            'quiet': True,
            'socket_timeout': self.timeout,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise VideoUnavailableError("Could not extract video information")
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'formats': self._get_available_formats(info)
                }
                
        except socket.timeout:
            raise NetworkTimeoutError(f"Connection timed out after {self.timeout} seconds")
        except urllib.error.URLError as e:
            if "timed out" in str(e).lower():
                raise NetworkTimeoutError(f"Network timeout: {str(e)}")
            raise YouTubeDownloaderError(f"Network error: {str(e)}")
        except yt_dlp.DownloadError as e:
            error_msg = str(e).lower()
            if "private video" in error_msg or "unavailable" in error_msg:
                raise VideoUnavailableError(f"Video is unavailable: {str(e)}")
            elif "timeout" in error_msg:
                raise NetworkTimeoutError(f"Download timeout: {str(e)}")
            else:
                raise YouTubeDownloaderError(f"Download error: {str(e)}")
        except Exception as e:
            raise YouTubeDownloaderError(f"Unexpected error getting video info: {str(e)}")
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL"""
        youtube_domains = [
            'youtube.com', 'www.youtube.com', 'youtu.be', 
            'm.youtube.com', 'music.youtube.com'
        ]
        return any(domain in url.lower() for domain in youtube_domains)
    
    def _get_available_formats(self, info: Dict[str, Any]) -> list:
        """Extract available video formats"""
        formats = []
        try:
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none':  # Video formats only
                    quality = f.get('height', 'Unknown')
                    ext = f.get('ext', 'Unknown')
                    if quality != 'Unknown' and ext != 'Unknown':
                        formats.append(f"{quality}p - {ext}")
        except Exception:
            # If format extraction fails, return empty list
            pass
        return list(set(formats))  # Remove duplicates
    
    def _try_download_with_fallbacks(self, ydl_opts: dict, url: str, audio_only: bool = False) -> bool:
        """Try download with different fallback strategies for 403 errors"""
        
        # Strategy 1: Normal download
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                return True
        except yt_dlp.DownloadError as e:
            if "403" not in str(e).lower() and "forbidden" not in str(e).lower():
                raise  # Re-raise if not a 403 error
        
        # Strategy 2: Try with different format for audio
        if audio_only:
            try:
                fallback_opts = ydl_opts.copy()
                fallback_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
                with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                    ydl.download([url])
                    return True
            except yt_dlp.DownloadError:
                pass
        
        # Strategy 3: Try with more conservative settings
        try:
            conservative_opts = ydl_opts.copy()
            conservative_opts.update({
                'sleep_interval': 2,
                'max_sleep_interval': 10,
                'retries': 1,
                'fragment_retries': 1,
            })
            with yt_dlp.YoutubeDL(conservative_opts) as ydl:
                ydl.download([url])
                return True
        except yt_dlp.DownloadError:
            pass
        
        # If all strategies fail, raise a helpful error
        raise yt_dlp.DownloadError(
            "All download strategies failed due to YouTube restrictions (HTTP 403).\n\n"
            "YouTube frequently updates their anti-bot measures. Try:\n"
            "1. Update yt-dlp: pip install --upgrade yt-dlp\n"
            "2. Wait 10-15 minutes before trying again\n"
            "3. Try a different video quality\n"
            "4. Check if the video is available in your region"
        )

    def download_video(self, url: str, quality: str = 'best', audio_only: bool = False, 
                      progress_callback: Optional[Callable] = None) -> bool:
        """Download video with specified quality"""
        if not self._is_valid_url(url):
            raise InvalidURLError("Invalid YouTube URL format")
        
        # Ensure output_dir is a Path object
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        
        # Validate output directory
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise YouTubeDownloaderError(f"Permission denied: Cannot create directory {self.output_dir}")
        except OSError as e:
            raise YouTubeDownloaderError(f"Cannot create output directory: {str(e)}")
        
        # Build yt-dlp options with timeouts and error handling
        base_opts = {
            'socket_timeout': self.timeout,
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'no_warnings': True,
            'ignoreerrors': False,
            'retries': 3,
            'fragment_retries': 3,
            # Add options to handle YouTube restrictions
            'extractor_retries': 3,
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            # Use cookies and headers to appear more like a browser
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
        }
        
        if audio_only:
            ydl_opts = {
                **base_opts,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'keepvideo': False,  # Remove original video file after conversion
            }
        else:
            if quality == 'best':
                format_selector = 'best'
            elif quality == 'worst':
                format_selector = 'worst'
            else:
                # Extract height from quality string like "720p - mp4"
                try:
                    height = quality.split('p')[0] if 'p' in quality else quality
                    # Validate height is numeric
                    int(height)
                    format_selector = f'best[height<={height}]'
                except (ValueError, IndexError):
                    format_selector = 'best'  # Fallback to best quality
            
            ydl_opts = {
                **base_opts,
                'format': format_selector,
            }
        
        if progress_callback:
            ydl_opts['progress_hooks'] = [progress_callback]
            # Add post-processor hook for audio conversion progress
            def post_processor_hook(d):
                if progress_callback:
                    progress_callback(d)
            ydl_opts['postprocessor_hooks'] = [post_processor_hook]
        
        try:
            return self._try_download_with_fallbacks(ydl_opts, url, audio_only)
                
        except socket.timeout:
            raise NetworkTimeoutError(f"Download timed out after {self.timeout} seconds")
        except urllib.error.URLError as e:
            if "timed out" in str(e).lower():
                raise NetworkTimeoutError(f"Network timeout during download: {str(e)}")
            raise YouTubeDownloaderError(f"Network error during download: {str(e)}")
        except yt_dlp.DownloadError as e:
            error_msg = str(e).lower()
            if "private video" in error_msg or "unavailable" in error_msg:
                raise VideoUnavailableError(f"Video is unavailable: {str(e)}")
            elif "timeout" in error_msg:
                raise NetworkTimeoutError(f"Download timeout: {str(e)}")
            elif "403" in error_msg or "forbidden" in error_msg:
                raise YouTubeDownloaderError(
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
                    f"Technical details: {str(e)}"
                )
            elif "no space left" in error_msg:
                raise YouTubeDownloaderError("Insufficient disk space for download")
            elif "ffmpeg" in error_msg and audio_only:
                raise YouTubeDownloaderError(
                    "Audio conversion failed. Please install FFmpeg:\n"
                    "Windows: Download from https://ffmpeg.org/download.html\n"
                    "Or install via chocolatey: choco install ffmpeg\n\n"
                    f"Error details: {str(e)}"
                )
            else:
                raise YouTubeDownloaderError(f"Download failed: {str(e)}")
        except KeyboardInterrupt:
            raise YouTubeDownloaderError("Download cancelled by user")
        except Exception as e:
            raise YouTubeDownloaderError(f"Unexpected error during download: {str(e)}")