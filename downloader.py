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

class PlaylistError(YouTubeDownloaderError):
    """Base exception for playlist-related errors"""
    pass

class PlaylistTooLargeError(PlaylistError):
    """Raised when playlist exceeds safe download limits"""
    pass

class PlaylistPrivateError(PlaylistError):
    """Raised when playlist is private or unavailable"""
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
    
    def get_playlist_info(self, url: str) -> Dict[str, Any]:
        """Get playlist information without downloading"""
        if not self._is_valid_url(url):
            raise InvalidURLError("Invalid YouTube URL format")
        
        # Use gentle scraping options for metadata extraction
        ydl_opts = {
            'quiet': True,
            'socket_timeout': self.timeout,
            'no_warnings': True,
            'sleep_interval_requests': 3,      # 3 seconds between requests
            'extract_flat': True,              # Don't extract individual video info yet
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise PlaylistPrivateError("Could not extract information - content may be private or unavailable")
                
                # Check if it's actually a playlist
                if info.get('_type') != 'playlist':
                    # If it's not a playlist but we expected one, provide helpful error
                    if self._is_playlist_url(url):
                        raise PlaylistError(
                            f"URL appears to be a playlist URL but yt-dlp detected it as: {info.get('_type', 'unknown')}.\n"
                            f"This might be a single video in a playlist or an invalid playlist URL."
                        )
                    else:
                        raise InvalidURLError("URL does not point to a playlist - this appears to be a single video")
                
                entries = info.get('entries', [])
                video_count = len(entries)
                
                # Handle empty playlists
                if video_count == 0:
                    raise PlaylistError("Playlist appears to be empty or all videos are unavailable")
                
                # Safety check - warn about large playlists
                if video_count > 200:
                    raise PlaylistTooLargeError(
                        f"Playlist contains {video_count} videos. "
                        f"For safety, we recommend downloading playlists with fewer than 200 videos. "
                        f"Large playlists may take several hours and risk IP blocking."
                    )
                
                # Calculate estimated download time (conservative estimate)
                avg_delay = 20  # Average of 15-25 second range
                estimated_minutes = (video_count * avg_delay) / 60
                
                return {
                    'title': info.get('title', 'Unknown Playlist'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'description': info.get('description', ''),
                    'video_count': video_count,
                    'estimated_time_minutes': int(estimated_minutes),
                    'entries': entries[:10],  # First 10 videos for preview
                    'url': url,
                    'id': info.get('id', ''),
                }
                
        except socket.timeout:
            raise NetworkTimeoutError(f"Connection timed out after {self.timeout} seconds")
        except urllib.error.URLError as e:
            if "timed out" in str(e).lower():
                raise NetworkTimeoutError(f"Network timeout: {str(e)}")
            raise YouTubeDownloaderError(f"Network error: {str(e)}")
        except yt_dlp.DownloadError as e:
            error_msg = str(e).lower()
            if "private" in error_msg or "unavailable" in error_msg:
                raise PlaylistPrivateError(f"Playlist is unavailable: {str(e)}")
            elif "timeout" in error_msg:
                raise NetworkTimeoutError(f"Playlist extraction timeout: {str(e)}")
            else:
                raise PlaylistError(f"Playlist extraction failed: {str(e)}")
        except Exception as e:
            raise PlaylistError(f"Unexpected error getting playlist info: {str(e)}")
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL"""
        youtube_domains = [
            'youtube.com', 'www.youtube.com', 'youtu.be', 
            'm.youtube.com', 'music.youtube.com'
        ]
        return any(domain in url.lower() for domain in youtube_domains)
    
    def _is_playlist_url(self, url: str) -> bool:
        """Check if URL is a YouTube playlist"""
        if not self._is_valid_url(url):
            return False
        
        url_lower = url.lower()
        # Check for various playlist URL patterns
        playlist_indicators = [
            'list=',           # Standard playlist parameter
            '/playlist?',      # Direct playlist URL
            '&list=',          # Playlist parameter in video URL
            'playlist/',       # Alternative playlist format
        ]
        
        return any(indicator in url_lower for indicator in playlist_indicators)
    
    def get_content_info(self, url: str) -> Dict[str, Any]:
        """
        Intelligently detect and get information for either video or playlist
        This method tries to determine the content type automatically
        """
        if not self._is_valid_url(url):
            raise InvalidURLError("Invalid YouTube URL format")
        
        # First, try to extract basic info to determine content type
        ydl_opts = {
            'quiet': True,
            'socket_timeout': self.timeout,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise YouTubeDownloaderError("Could not extract content information")
                
                content_type = info.get('_type', 'video')
                
                if content_type == 'playlist':
                    # It's a playlist, get full playlist info
                    return self.get_playlist_info(url)
                else:
                    # It's a single video, get video info
                    video_info = self.get_video_info(url)
                    video_info['is_playlist'] = False
                    return video_info
                    
        except Exception as e:
            # If extraction fails, fall back to URL-based detection
            if self._is_playlist_url(url):
                return self.get_playlist_info(url)
            else:
                return self.get_video_info(url)
    
    def _get_gentle_scraping_opts(self, audio_only: bool = False) -> Dict[str, Any]:
        """Get conservative yt-dlp options for gentle scraping"""
        base_opts = {
            # Essential rate limiting - prioritize safety over speed
            'sleep_interval': 15,              # 15 seconds between downloads (conservative)
            'max_sleep_interval': 25,          # Random variation up to 25 seconds  
            'sleep_interval_requests': 3,      # 3 seconds between metadata requests
            'sleep_interval_subtitles': 5,     # 5 seconds for subtitle requests
            
            # Speed control to avoid detection
            'ratelimit': 150000,               # 150KB/s download speed limit
            'concurrent_fragment_downloads': 1, # Single connection only
            
            # Enhanced error handling
            'retries': 5,
            'fragment_retries': 5,
            'extractor_retries': 3,
            
            # Anti-detection measures
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            
            # Error tolerance for playlists
            'ignoreerrors': True,              # Skip failed videos, continue with rest
            'no_warnings': False,              # Show warnings for transparency
        }
        
        # Extra conservative settings for audio downloads (YouTube is more restrictive)
        if audio_only:
            base_opts.update({
                'sleep_interval': 25,          # Even longer delays for audio
                'max_sleep_interval': 45,      # More variation
                'sleep_interval_requests': 8,  # Longer delays between requests
                'ratelimit': 75000,            # Even slower download speed (75KB/s)
                'retries': 2,                  # Fewer retries to avoid triggering detection
                'fragment_retries': 2,
                'extractor_retries': 2,
                # Try to use mobile client which is often less restricted for audio
                'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
                # Additional headers to appear more like a real mobile browser
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                },
            })
        
        return base_opts
    
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
        
        # Enhanced strategies for audio downloads (YouTube is more restrictive with audio)
        if audio_only:
            # Strategy 2a: Try with different audio format and no post-processing
            try:
                fallback_opts = ydl_opts.copy()
                fallback_opts['format'] = 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio'
                # Remove post-processors temporarily to see if that helps
                fallback_opts.pop('postprocessors', None)
                fallback_opts['keepvideo'] = True  # Keep original file
                with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                    ydl.download([url])
                    return True
            except yt_dlp.DownloadError:
                pass
            
            # Strategy 2b: Try downloading as video then extract audio manually
            try:
                video_opts = ydl_opts.copy()
                video_opts['format'] = 'worst[height<=480]/worst'  # Low quality video
                video_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128',  # Lower quality to be less suspicious
                }]
                video_opts.update({
                    'sleep_interval': 5,  # More conservative
                    'max_sleep_interval': 15,
                })
                with yt_dlp.YoutubeDL(video_opts) as ydl:
                    ydl.download([url])
                    return True
            except yt_dlp.DownloadError:
                pass
            
            # Strategy 2c: Try with mobile client (often less restricted)
            try:
                mobile_opts = ydl_opts.copy()
                mobile_opts['format'] = 'bestaudio'
                mobile_opts.update({
                    'extractor_args': {'youtube': {'player_client': ['android']}},
                    'sleep_interval': 8,
                    'max_sleep_interval': 20,
                })
                with yt_dlp.YoutubeDL(mobile_opts) as ydl:
                    ydl.download([url])
                    return True
            except yt_dlp.DownloadError:
                pass
            
            # Strategy 2d: Try iOS client (sometimes works when Android fails)
            try:
                ios_opts = ydl_opts.copy()
                ios_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
                ios_opts.update({
                    'extractor_args': {'youtube': {'player_client': ['ios']}},
                    'sleep_interval': 12,
                    'max_sleep_interval': 25,
                    'http_headers': {
                        'User-Agent': 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)'
                    },
                })
                with yt_dlp.YoutubeDL(ios_opts) as ydl:
                    ydl.download([url])
                    return True
            except yt_dlp.DownloadError:
                pass
            
            # Strategy 2e: Try web client with cookies simulation
            try:
                web_opts = ydl_opts.copy()
                web_opts['format'] = 'bestaudio[filesize<50M]/bestaudio'  # Prefer smaller files
                web_opts.update({
                    'extractor_args': {'youtube': {'player_client': ['web']}},
                    'sleep_interval': 15,
                    'max_sleep_interval': 30,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    },
                })
                with yt_dlp.YoutubeDL(web_opts) as ydl:
                    ydl.download([url])
                    return True
            except yt_dlp.DownloadError:
                pass
            
            # Strategy 2f: Try with TV client (often bypasses restrictions)
            try:
                tv_opts = ydl_opts.copy()
                tv_opts['format'] = 'bestaudio/worst[height<=360]'  # Very conservative format
                tv_opts.update({
                    'extractor_args': {'youtube': {'player_client': ['tv_embedded']}},
                    'sleep_interval': 20,
                    'max_sleep_interval': 40,
                    'retries': 1,
                    'fragment_retries': 1,
                })
                with yt_dlp.YoutubeDL(tv_opts) as ydl:
                    ydl.download([url])
                    return True
            except yt_dlp.DownloadError:
                pass
        
        # Strategy 3: Try with more conservative settings (for both video and audio)
        try:
            conservative_opts = ydl_opts.copy()
            conservative_opts.update({
                'sleep_interval': 10,      # Much longer delays
                'max_sleep_interval': 25,
                'retries': 1,
                'fragment_retries': 1,
                'extractor_retries': 1,
                # Use different user agent
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Android 10; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0'
                },
            })
            with yt_dlp.YoutubeDL(conservative_opts) as ydl:
                ydl.download([url])
                return True
        except yt_dlp.DownloadError:
            pass
        
        # Strategy 4: Try with different extractor args (bypass some restrictions)
        if audio_only:
            try:
                bypass_opts = ydl_opts.copy()
                bypass_opts.update({
                    'format': 'worstaudio/worst[height<=240]',  # Very low quality
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'web'],
                            'skip': ['hls', 'dash'],  # Skip certain formats that might be blocked
                        }
                    },
                    'sleep_interval': 25,
                    'max_sleep_interval': 45,
                    'retries': 1,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '64',  # Very low quality
                    }] if audio_only else [],
                })
                with yt_dlp.YoutubeDL(bypass_opts) as ydl:
                    ydl.download([url])
                    return True
            except yt_dlp.DownloadError:
                pass
        
        # Strategy 5: Last resort - try with minimal options and different approach
        try:
            minimal_opts = {
                'socket_timeout': self.timeout,
                'outtmpl': ydl_opts['outtmpl'],
                'format': 'worst' if not audio_only else 'worstaudio/worst[height<=144]',
                'sleep_interval': 30,
                'max_sleep_interval': 60,
                'retries': 1,
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {'youtube': {'player_client': ['android']}},
            }
            if audio_only:
                minimal_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64',  # Lowest quality possible
                }]
            
            with yt_dlp.YoutubeDL(minimal_opts) as ydl:
                ydl.download([url])
                return True
        except yt_dlp.DownloadError:
            pass
        
        # If all strategies fail, provide specific guidance for audio downloads
        if audio_only:
            raise yt_dlp.DownloadError(
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
        else:
            raise yt_dlp.DownloadError(
                "All download strategies failed due to YouTube restrictions (HTTP 403).\n\n"
                "YouTube frequently updates their anti-bot measures. Try:\n"
                "1. Update yt-dlp: pip install --upgrade yt-dlp\n"
                "2. Wait 10-15 minutes before trying again\n"
                "3. Try a different video quality\n"
                "4. Check if the video is available in your region"
            )

    def suggest_mp3_alternatives(self, url: str) -> str:
        """Provide helpful suggestions when MP3 download fails"""
        return (
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
            f"📋 Original URL: {url}"
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
            'sleep_interval': 2,               # Moderate delay for single videos
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
    
    def download_playlist(self, url: str, quality: str = 'best', audio_only: bool = False,
                         progress_callback: Optional[Callable] = None,
                         video_range: Optional[tuple] = None,
                         playlist_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Download YouTube playlist with gentle scraping practices
        
        Args:
            url: Playlist URL
            quality: Video quality preference
            audio_only: Whether to download audio only
            progress_callback: Callback for progress updates
            video_range: Optional tuple (start, end) for partial download
            playlist_info: Optional pre-fetched playlist info to avoid re-extraction
            
        Returns:
            Dict with download results and statistics
        """
        if not self._is_valid_url(url):
            raise InvalidURLError("Invalid YouTube URL format")
        
        # Ensure output directory exists
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise YouTubeDownloaderError(f"Permission denied: Cannot create directory {self.output_dir}")
        except OSError as e:
            raise YouTubeDownloaderError(f"Cannot create output directory: {str(e)}")
        
        # Get playlist info if not provided, but handle errors gracefully
        if playlist_info is None:
            try:
                # Try to get playlist info, but don't fail if it doesn't work
                playlist_info = self.get_content_info(url)
                
                # If it's not a playlist, we'll handle it in the yt-dlp download section
                if not (playlist_info.get('is_playlist') or 'video_count' in playlist_info):
                    # This might be a single video, let yt-dlp handle it
                    playlist_info = {
                        'title': 'Unknown Playlist',
                        'video_count': 1,  # Assume at least 1 video
                        'estimated_time_minutes': 1
                    }
            except Exception as e:
                # If we can't get playlist info, create minimal info and let yt-dlp handle it
                playlist_info = {
                    'title': 'Unknown Playlist', 
                    'video_count': 1,  # Assume at least 1 video
                    'estimated_time_minutes': 1
                }
        
        total_videos = playlist_info['video_count']
        
        # Apply video range if specified
        start_idx = 0
        end_idx = total_videos
        if video_range:
            start_idx = max(0, video_range[0] - 1)  # Convert to 0-based index
            end_idx = min(total_videos, video_range[1])
            if start_idx >= end_idx:
                raise PlaylistError("Invalid video range specified")
        
        # Build yt-dlp options with gentle scraping
        base_opts = {
            'socket_timeout': self.timeout,
            'outtmpl': str(self.output_dir / '%(playlist_title)s/%(title)s.%(ext)s'),
            **self._get_gentle_scraping_opts(audio_only=audio_only),
            # Force playlist extraction even if URL seems ambiguous
            'extract_flat': False,  # Extract full info for each video
            'yes_playlist': True,   # Always treat as playlist if possible
        }
        
        # Apply video range selection
        if video_range:
            base_opts['playlist_start'] = start_idx + 1  # yt-dlp uses 1-based indexing
            base_opts['playlist_end'] = end_idx
        
        if audio_only:
            ydl_opts = {
                **base_opts,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'keepvideo': False,
            }
        else:
            if quality == 'best':
                format_selector = 'best'
            elif quality == 'worst':
                format_selector = 'worst'
            else:
                try:
                    height = quality.split('p')[0] if 'p' in quality else quality
                    int(height)
                    format_selector = f'best[height<={height}]'
                except (ValueError, IndexError):
                    format_selector = 'best'
            
            ydl_opts = {
                **base_opts,
                'format': format_selector,
            }
        
        # Enhanced progress tracking for playlists
        download_stats = {
            'total_videos': end_idx - start_idx,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'errors': []
        }
        
        def playlist_progress_hook(d):
            """Enhanced progress hook for playlist downloads"""
            if progress_callback:
                # Add playlist context to progress data
                d['playlist_stats'] = download_stats
                d['playlist_info'] = playlist_info
                progress_callback(d)
            
            # Track download statistics
            if d.get('status') == 'finished':
                download_stats['downloaded'] += 1
            elif d.get('status') == 'error':
                download_stats['failed'] += 1
                error_msg = d.get('error', 'Unknown error')
                download_stats['errors'].append(error_msg)
        
        if progress_callback:
            ydl_opts['progress_hooks'] = [playlist_progress_hook]
            def post_processor_hook(d):
                if progress_callback:
                    d['playlist_stats'] = download_stats
                    d['playlist_info'] = playlist_info
                    progress_callback(d)
            ydl_opts['postprocessor_hooks'] = [post_processor_hook]
        
        # Record start time
        import time
        download_stats['start_time'] = time.time()
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Notify about gentle scraping
                if progress_callback:
                    progress_callback({
                        'status': 'playlist_starting',
                        'playlist_info': playlist_info,
                        'playlist_stats': download_stats,
                        'message': f"Starting playlist download with safety delays (15-25 seconds between videos)"
                    })
                
                # Try to download as playlist
                try:
                    ydl.download([url])
                except yt_dlp.DownloadError as e:
                    error_msg = str(e).lower()
                    if "not a playlist" in error_msg or "single video" in error_msg:
                        # If yt-dlp says it's not a playlist, try without playlist-specific options
                        fallback_opts = ydl_opts.copy()
                        fallback_opts.pop('yes_playlist', None)
                        fallback_opts['outtmpl'] = str(self.output_dir / '%(title)s.%(ext)s')
                        
                        with yt_dlp.YoutubeDL(fallback_opts) as fallback_ydl:
                            fallback_ydl.download([url])
                    else:
                        raise  # Re-raise other errors
                
            # Calculate final statistics
            end_time = time.time()
            total_time = end_time - download_stats['start_time']
            
            return {
                'success': True,
                'playlist_title': playlist_info['title'],
                'total_videos': download_stats['total_videos'],
                'downloaded': download_stats['downloaded'],
                'failed': download_stats['failed'],
                'skipped': download_stats['skipped'],
                'total_time_seconds': int(total_time),
                'errors': download_stats['errors']
            }
            
        except KeyboardInterrupt:
            raise YouTubeDownloaderError("Playlist download cancelled by user")
        except yt_dlp.DownloadError as e:
            error_msg = str(e).lower()
            if "403" in error_msg or "forbidden" in error_msg:
                raise YouTubeDownloaderError(
                    "Playlist download blocked by YouTube (HTTP 403).\n\n"
                    "This suggests our rate limiting wasn't sufficient. Try:\n"
                    "1. Wait 30-60 minutes before trying again\n"
                    "2. Download smaller portions of the playlist\n"
                    "3. Update yt-dlp: pip install --upgrade yt-dlp\n\n"
                    f"Technical details: {str(e)}"
                )
            elif "not a playlist" in error_msg or "single video" in error_msg:
                # This URL might be a single video in playlist context
                raise PlaylistError(
                    "The URL appears to be a single video rather than a playlist.\n\n"
                    "💡 Try downloading it as a single video instead:\n"
                    "1. Make sure the URL is a playlist URL (contains 'list=' parameter)\n"
                    "2. Or try downloading as a single video\n\n"
                    f"Technical details: {str(e)}"
                )
            else:
                raise PlaylistError(f"Playlist download failed: {str(e)}")
        except Exception as e:
            raise PlaylistError(f"Unexpected error during playlist download: {str(e)}")