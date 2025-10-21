import yt_dlp
import os
from pathlib import Path

class YouTubeDownloader:
    def __init__(self, output_dir="downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def get_video_info(self, url):
        """Get video information without downloading"""
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'formats': self._get_available_formats(info)
                }
            except Exception as e:
                raise Exception(f"Error getting video info: {str(e)}")
    
    def _get_available_formats(self, info):
        """Extract available video formats"""
        formats = []
        for f in info.get('formats', []):
            if f.get('vcodec') != 'none':  # Video formats only
                quality = f.get('height', 'Unknown')
                ext = f.get('ext', 'Unknown')
                formats.append(f"{quality}p - {ext}")
        return list(set(formats))  # Remove duplicates
    
    def download_video(self, url, quality='best', audio_only=False, progress_callback=None):
        """Download video with specified quality"""
        # Ensure output_dir is a Path object
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        
        if audio_only:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            if quality == 'best':
                format_selector = 'best'
            elif quality == 'worst':
                format_selector = 'worst'
            else:
                # Extract height from quality string like "720p - mp4"
                height = quality.split('p')[0] if 'p' in quality else quality
                format_selector = f'best[height<={height}]'
            
            ydl_opts = {
                'format': format_selector,
                'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            }
        
        if progress_callback:
            ydl_opts['progress_hooks'] = [progress_callback]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
                return True
            except Exception as e:
                raise Exception(f"Download failed: {str(e)}")