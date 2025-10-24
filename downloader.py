import yt_dlp
import os
import socket
import urllib.error
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from config.download_config import (
    DownloadConfig, UserAgents, YouTubeClients, FormatSelectors, 
    HTTPHeaders, ValidationConfig
)
from config.error_messages import ErrorMessages, InfoMessages, TroubleshootingMessages

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
    def __init__(self, output_dir="downloads", timeout=DownloadConfig.DEFAULT_TIMEOUT):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Note: We don't set global socket timeout to avoid affecting other libraries
        # Instead, we pass socket_timeout to each yt-dlp call
    
    def _error_contains(self, exc: Exception, *tokens: str) -> bool:
        """Check if exception message contains any of the given tokens"""
        error_msg = str(exc).lower()
        return any(token.lower() in error_msg for token in tokens)
    
    def _is_http_403_error(self, exc: Exception) -> bool:
        """Check if exception indicates HTTP 403 error"""
        return self._error_contains(exc, "403", "forbidden")
    
    def _is_timeout_error(self, exc: Exception) -> bool:
        """Check if exception indicates timeout"""
        return self._error_contains(exc, "timeout", "timed out")
    
    def _is_private_video_error(self, exc: Exception) -> bool:
        """Check if exception indicates private/unavailable video"""
        return self._error_contains(exc, "private video", "unavailable")
    
    def _is_disk_space_error(self, exc: Exception) -> bool:
        """Check if exception indicates insufficient disk space"""
        return self._error_contains(exc, "no space left")
    
    def _is_ffmpeg_error(self, exc: Exception) -> bool:
        """Check if exception indicates FFmpeg-related error"""
        return self._error_contains(exc, "ffmpeg")
    
    def _validate_url(self, url: str) -> None:
        """Validate URL format and length"""
        if not url or not url.strip():
            raise InvalidURLError("URL cannot be empty")
        
        if len(url) > ValidationConfig.MAX_URL_LENGTH:
            raise InvalidURLError(f"URL too long (max {ValidationConfig.MAX_URL_LENGTH} characters)")
        
        if not self._is_valid_url(url):
            raise InvalidURLError(ErrorMessages.INVALID_URL_FORMAT)
        
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """Get video information without downloading"""
        self._validate_url(url)
        
        ydl_opts = {
            'quiet': True,
            'socket_timeout': self.timeout,
            'no_warnings': True,
            'restrictfilenames': True,  # Prevent directory traversal attacks
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
            raise NetworkTimeoutError(ErrorMessages.NETWORK_TIMEOUT.format(timeout=self.timeout))
        except urllib.error.URLError as e:
            if "timed out" in str(e).lower():
                raise NetworkTimeoutError(ErrorMessages.NETWORK_ERROR.format(error=str(e)))
            raise YouTubeDownloaderError(ErrorMessages.NETWORK_ERROR.format(error=str(e)))
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
        self._validate_url(url)
        
        # Use gentle scraping options for metadata extraction
        ydl_opts = {
            'quiet': True,
            'socket_timeout': self.timeout,
            'no_warnings': True,
            'sleep_interval_requests': DownloadConfig.DEFAULT_REQUEST_DELAY,
            'extract_flat': True,              # Don't extract individual video info yet
            'restrictfilenames': True,         # Prevent directory traversal attacks
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
                if video_count > DownloadConfig.PLAYLIST_SIZE_WARNING_THRESHOLD:
                    raise PlaylistTooLargeError(
                        ErrorMessages.PLAYLIST_TOO_LARGE.format(
                            count=video_count,
                            threshold=DownloadConfig.PLAYLIST_SIZE_WARNING_THRESHOLD
                        )
                    )
                
                # Calculate estimated download time (conservative estimate)
                avg_delay = (DownloadConfig.DEFAULT_SLEEP_INTERVAL + DownloadConfig.MAX_SLEEP_INTERVAL) // 2
                estimated_minutes = (video_count * avg_delay) / 60
                
                return {
                    'title': info.get('title', 'Unknown Playlist'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'description': info.get('description', ''),
                    'video_count': video_count,
                    'estimated_time_minutes': int(estimated_minutes),
                    'entries': entries[:DownloadConfig.PLAYLIST_PREVIEW_COUNT],  # First videos for preview
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
        return any(domain in url.lower() for domain in ValidationConfig.YOUTUBE_DOMAINS)
    
    def _is_playlist_url(self, url: str) -> bool:
        """Check if URL is a YouTube playlist"""
        if not self._is_valid_url(url):
            return False
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in ValidationConfig.PLAYLIST_INDICATORS)
    
    def _is_video_in_playlist_url(self, url: str) -> bool:
        """Check if URL is a video within a playlist (has both video ID and playlist ID)"""
        if not self._is_valid_url(url):
            return False
        
        url_lower = url.lower()
        has_video_id = 'watch?v=' in url_lower or 'youtu.be/' in url_lower
        has_playlist_id = any(indicator in url_lower for indicator in ValidationConfig.PLAYLIST_INDICATORS)
        
        return has_video_id and has_playlist_id
    
    def _extract_video_url_from_playlist(self, url: str) -> str:
        """Extract just the video URL from a playlist URL"""
        import urllib.parse as urlparse
        
        parsed = urlparse.urlparse(url)
        query_params = urlparse.parse_qs(parsed.query)
        
        # Get video ID
        video_id = query_params.get('v', [None])[0]
        if not video_id:
            return url  # Return original if we can't extract video ID
        
        # Create clean video URL
        if 'youtube.com' in parsed.netloc:
            return f"https://www.youtube.com/watch?v={video_id}"
        elif 'youtu.be' in parsed.netloc:
            return f"https://youtu.be/{video_id}"
        
        return url  # Fallback to original URL
    
    def get_video_and_playlist_info(self, url: str) -> Dict[str, Any]:
        """
        Get information for both video and playlist when URL contains both
        Used when user is watching a specific video in a playlist
        """
        self._validate_url(url)
        
        try:
            # Get video info (just the current video)
            video_url = self._extract_video_url_from_playlist(url)
            video_info = self.get_video_info(video_url)
            
            # Get playlist info
            playlist_info = self.get_playlist_info(url)
            
            return {
                'is_video_in_playlist': True,
                'video_info': video_info,
                'playlist_info': playlist_info,
                'video_url': video_url,
                'playlist_url': url,
                'video_title': video_info.get('title', 'Unknown'),
                'playlist_title': playlist_info.get('title', 'Unknown Playlist'),
                'playlist_video_count': playlist_info.get('video_count', 0)
            }
            
        except Exception as e:
            self.logger.exception("Failed to get video and playlist info")
            raise YouTubeDownloaderError(f"Could not extract video and playlist information: {str(e)}")

    def get_content_info(self, url: str) -> Dict[str, Any]:
        """
        Intelligently detect and get information for either video or playlist
        This method tries to determine the content type automatically
        """
        self._validate_url(url)
        
        # Check if this is a video within a playlist
        if self._is_video_in_playlist_url(url):
            return self.get_video_and_playlist_info(url)
        
        # First, try to extract basic info to determine content type
        ydl_opts = {
            'quiet': True,
            'socket_timeout': self.timeout,
            'no_warnings': True,
            'extract_flat': True,
            'restrictfilenames': True,  # Prevent directory traversal attacks
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
            'sleep_interval': DownloadConfig.DEFAULT_SLEEP_INTERVAL,
            'max_sleep_interval': DownloadConfig.MAX_SLEEP_INTERVAL,
            'sleep_interval_requests': DownloadConfig.DEFAULT_REQUEST_DELAY,
            'sleep_interval_subtitles': DownloadConfig.SUBTITLE_REQUEST_DELAY,
            
            # Speed control to avoid detection
            'ratelimit': DownloadConfig.DEFAULT_RATE_LIMIT,
            'concurrent_fragment_downloads': 1, # Single connection only
            
            # Enhanced error handling
            'retries': DownloadConfig.DEFAULT_RETRIES,
            'fragment_retries': DownloadConfig.FRAGMENT_RETRIES,
            'extractor_retries': DownloadConfig.EXTRACTOR_RETRIES,
            
            # Anti-detection measures
            'http_headers': {
                'User-Agent': UserAgents.DESKTOP_CHROME
            },
            
            # Error tolerance for playlists
            'ignoreerrors': True,              # Skip failed videos, continue with rest
            'no_warnings': False,              # Show warnings for transparency
        }
        
        # Extra conservative settings for audio downloads (YouTube is more restrictive)
        if audio_only:
            base_opts.update({
                'sleep_interval': DownloadConfig.CONSERVATIVE_SLEEP_INTERVAL,
                'max_sleep_interval': DownloadConfig.CONSERVATIVE_MAX_SLEEP_INTERVAL,
                'sleep_interval_requests': DownloadConfig.AUDIO_REQUEST_DELAY,
                'ratelimit': DownloadConfig.CONSERVATIVE_RATE_LIMIT,
                'retries': DownloadConfig.CONSERVATIVE_RETRIES,
                'fragment_retries': DownloadConfig.CONSERVATIVE_RETRIES,
                'extractor_retries': DownloadConfig.CONSERVATIVE_RETRIES,
                # Try to use mobile client which is often less restricted for audio
                'extractor_args': {'youtube': {'player_client': [YouTubeClients.ANDROID, YouTubeClients.IOS]}},
                # Additional headers to appear more like a real mobile browser
                'http_headers': HTTPHeaders.MOBILE_HEADERS,
            })
        
        return base_opts
    
    def _get_available_formats(self, info: Dict[str, Any]) -> list:
        """Extract available video formats"""
        formats = []
        try:
            for f in info.get('formats', []) or []:
                if f and f.get('vcodec') != 'none':  # Video formats only
                    quality = f.get('height')
                    ext = f.get('ext')
                    if quality and ext:
                        formats.append(f"{quality}p - {ext}")
        except Exception as e:
            self.logger.exception("Failed to extract video formats")
            # Return empty list instead of crashing
        # Preserve order while removing duplicates
        return list(dict.fromkeys(formats))
    
    def _try_normal_download(self, ydl_opts: dict, url: str) -> bool:
        """Try normal download strategy"""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                return True
        except yt_dlp.DownloadError as e:
            if not self._is_http_403_error(e):
                raise  # Re-raise if not a 403 error
            self.logger.debug(f"Normal download failed with 403: {str(e)}")
            return False

    def _try_audio_format_fallback(self, ydl_opts: dict, url: str) -> bool:
        """Try with different audio format and no post-processing"""
        try:
            fallback_opts = ydl_opts.copy()
            fallback_opts['format'] = FormatSelectors.AUDIO_M4A
            # Remove post-processors temporarily to see if that helps
            fallback_opts.pop('postprocessors', None)
            fallback_opts['keepvideo'] = True  # Keep original file
            with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                ydl.download([url])
                return True
        except yt_dlp.DownloadError as e:
            self.logger.debug(f"Audio format fallback failed: {str(e)}")
            return False

    def _try_mobile_client_fallback(self, ydl_opts: dict, url: str) -> bool:
        """Try with mobile client (often less restricted)"""
        try:
            mobile_opts = ydl_opts.copy()
            mobile_opts['format'] = FormatSelectors.BEST_AUDIO
            mobile_opts.update({
                'extractor_args': {'youtube': {'player_client': [YouTubeClients.ANDROID]}},
                'sleep_interval': DownloadConfig.AUDIO_REQUEST_DELAY,
                'max_sleep_interval': DownloadConfig.DEFAULT_SLEEP_INTERVAL + 5,
            })
            with yt_dlp.YoutubeDL(mobile_opts) as ydl:
                ydl.download([url])
                return True
        except yt_dlp.DownloadError as e:
            self.logger.debug(f"Mobile client fallback failed: {str(e)}")
            return False

    def _try_download_with_fallbacks(self, ydl_opts: dict, url: str, audio_only: bool = False) -> bool:
        """Try download with different fallback strategies for 403 errors"""
        
        # Strategy 1: Normal download
        if self._try_normal_download(ydl_opts, url):
            return True
        
        # Enhanced strategies for audio downloads (YouTube is more restrictive with audio)
        if audio_only:
            if self._try_audio_format_fallback(ydl_opts, url):
                return True
            
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
            
            if self._try_mobile_client_fallback(ydl_opts, url):
                return True
            
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
        
        # If all strategies fail, provide specific guidance
        self._raise_fallback_error(audio_only)

    def _raise_fallback_error(self, audio_only: bool) -> None:
        """Raise appropriate error when all fallback strategies fail"""
        if audio_only:
            raise yt_dlp.DownloadError(ErrorMessages.AUDIO_DOWNLOAD_FAILED)
        else:
            raise yt_dlp.DownloadError(ErrorMessages.VIDEO_DOWNLOAD_FAILED)

    def suggest_mp3_alternatives(self, url: str) -> str:
        """Provide helpful suggestions when MP3 download fails"""
        return TroubleshootingMessages.MP3_ALTERNATIVES.format(url=url)

    def download_video(self, url: str, quality: str = 'best', audio_only: bool = False, 
                      progress_callback: Optional[Callable] = None) -> bool:
        """Download video with specified quality"""
        self._validate_url(url)
        
        # Use local copy to avoid mutating instance state (thread safety)
        output_dir = Path(self.output_dir)
        
        # Validate output directory
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise YouTubeDownloaderError(ErrorMessages.PERMISSION_DENIED.format(path=output_dir))
        except OSError as e:
            raise YouTubeDownloaderError(ErrorMessages.OUTPUT_DIR_ERROR.format(error=str(e)))
        
        # Build yt-dlp options with timeouts and error handling
        base_opts = {
            'socket_timeout': self.timeout,
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'no_warnings': True,
            'ignoreerrors': False,
            'restrictfilenames': True,         # Prevent directory traversal attacks
            'retries': DownloadConfig.EXTRACTOR_RETRIES,
            'fragment_retries': DownloadConfig.EXTRACTOR_RETRIES,
            # Add options to handle YouTube restrictions
            'extractor_retries': DownloadConfig.EXTRACTOR_RETRIES,
            'sleep_interval': 2,               # Moderate delay for single videos
            'max_sleep_interval': 5,
            # Use cookies and headers to appear more like a browser
            'http_headers': {
                'User-Agent': UserAgents.DESKTOP_CHROME
            },
        }
        
        if audio_only:
            # Use different output template for audio to avoid overwriting existing video files
            audio_opts = base_opts.copy()
            audio_opts['outtmpl'] = str(output_dir / '%(title)s [audio].%(ext)s')
            ydl_opts = {
                **audio_opts,
                'format': FormatSelectors.BEST_AUDIO,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': DownloadConfig.DEFAULT_AUDIO_QUALITY,
                }],
                'keepvideo': False,  # Safe to remove intermediate file (different name)
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
            raise NetworkTimeoutError(ErrorMessages.NETWORK_TIMEOUT.format(timeout=self.timeout))
        except urllib.error.URLError as e:
            if "timed out" in str(e).lower():
                raise NetworkTimeoutError(ErrorMessages.NETWORK_ERROR.format(error=str(e)))
            raise YouTubeDownloaderError(ErrorMessages.NETWORK_ERROR.format(error=str(e)))
        except yt_dlp.DownloadError as e:
            if self._is_private_video_error(e):
                raise VideoUnavailableError(ErrorMessages.VIDEO_PRIVATE.format(details=str(e)))
            elif self._is_timeout_error(e):
                raise NetworkTimeoutError(ErrorMessages.NETWORK_ERROR.format(error=str(e)))
            elif self._is_http_403_error(e):
                raise YouTubeDownloaderError(ErrorMessages.HTTP_403_ERROR.format(details=str(e)))
            elif self._is_disk_space_error(e):
                raise YouTubeDownloaderError(ErrorMessages.DISK_SPACE_ERROR)
            elif self._is_ffmpeg_error(e) and audio_only:
                raise YouTubeDownloaderError(ErrorMessages.FFMPEG_MISSING.format(error=str(e)))
            else:
                self.logger.exception("Unexpected yt-dlp download error")
                raise YouTubeDownloaderError(ErrorMessages.DOWNLOAD_FAILED.format(error=str(e)))
        except KeyboardInterrupt:
            raise YouTubeDownloaderError(ErrorMessages.DOWNLOAD_CANCELLED)
        except Exception as e:
            raise YouTubeDownloaderError(ErrorMessages.UNEXPECTED_ERROR.format(error=str(e)))
    
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
        self._validate_url(url)
        
        # Use local copy to avoid mutating instance state (thread safety)
        output_dir = Path(self.output_dir)
        
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise YouTubeDownloaderError(ErrorMessages.PERMISSION_DENIED.format(path=output_dir))
        except OSError as e:
            raise YouTubeDownloaderError(ErrorMessages.OUTPUT_DIR_ERROR.format(error=str(e)))
        
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
            'outtmpl': str(output_dir / '%(playlist_title)s/%(title)s.%(ext)s'),
            'restrictfilenames': True,         # Prevent directory traversal attacks
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
            # Use different output template for audio to avoid overwriting existing video files
            audio_opts = base_opts.copy()
            audio_opts['outtmpl'] = str(output_dir / '%(playlist_title)s/%(title)s [audio].%(ext)s')
            ydl_opts = {
                **audio_opts,
                'format': FormatSelectors.BEST_AUDIO,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': DownloadConfig.DEFAULT_AUDIO_QUALITY,
                }],
                'keepvideo': False,  # Safe to remove intermediate file (different name)
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
                        fallback_opts['outtmpl'] = str(output_dir / '%(title)s.%(ext)s')
                        
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
            raise YouTubeDownloaderError(ErrorMessages.PLAYLIST_CANCELLED)
        except yt_dlp.DownloadError as e:
            error_msg = str(e).lower()
            if "403" in error_msg or "forbidden" in error_msg:
                raise YouTubeDownloaderError(ErrorMessages.HTTP_403_ERROR.format(details=str(e)))
            elif "not a playlist" in error_msg or "single video" in error_msg:
                # This URL might be a single video in playlist context
                raise PlaylistError(ErrorMessages.PLAYLIST_SINGLE_VIDEO)
            else:
                raise PlaylistError(ErrorMessages.DOWNLOAD_FAILED.format(error=str(e)))
        except Exception as e:
            raise PlaylistError(ErrorMessages.UNEXPECTED_ERROR.format(error=str(e)))