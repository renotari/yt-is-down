#!/usr/bin/env python3
import argparse
import sys
from downloader import YouTubeDownloader

def format_bytes(bytes_val):
    """Convert bytes to human readable format"""
    if bytes_val is None:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"

def progress_hook(d):
    """Progress callback for CLI"""
    if d['status'] == 'downloading':
        # Extract detailed progress information
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        speed = d.get('speed', 0)
        eta = d.get('eta', 0)
        
        # Calculate percentage
        if total > 0:
            percentage = (downloaded / total) * 100
            percent_str = f"{percentage:.1f}%"
        else:
            percent_str = "N/A"
        
        # Format sizes and speed
        downloaded_str = format_bytes(downloaded)
        total_str = format_bytes(total) if total > 0 else "Unknown"
        speed_str = format_bytes(speed) + "/s" if speed else "Unknown"
        eta_str = f"{eta}s" if eta else "Unknown"
        
        # Create progress bar
        if total > 0:
            bar_length = 30
            filled_length = int(bar_length * downloaded / total)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            progress_line = f"\r[{bar}] {percent_str} | {downloaded_str}/{total_str} | {speed_str} | ETA: {eta_str}"
        else:
            progress_line = f"\rDownloading... {downloaded_str} | {speed_str}"
        
        print(progress_line, end='', flush=True)
        
    elif d['status'] == 'finished':
        print(f"\n✅ Download completed: {d['filename']}")

def main():
    parser = argparse.ArgumentParser(description='YouTube Video Downloader')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('-o', '--output', default='downloads', 
                       help='Output directory (default: downloads)')
    parser.add_argument('-q', '--quality', default='best',
                       help='Video quality (best, worst, or specific like 720p)')
    parser.add_argument('-a', '--audio-only', action='store_true',
                       help='Download audio only (MP3)')
    parser.add_argument('-i', '--info', action='store_true',
                       help='Show video information only')
    
    args = parser.parse_args()
    
    try:
        downloader = YouTubeDownloader(args.output)
        
        if args.info:
            print("Getting video information...")
            info = downloader.get_video_info(args.url)
            print(f"\nTitle: {info['title']}")
            print(f"Uploader: {info['uploader']}")
            print(f"Duration: {info['duration']} seconds")
            print("Available formats:")
            for fmt in info['formats'][:10]:  # Show first 10 formats
                print(f"  - {fmt}")
        else:
            print(f"Starting download...")
            print(f"URL: {args.url}")
            print(f"Quality: {args.quality}")
            print(f"Audio only: {args.audio_only}")
            print(f"Output directory: {args.output}")
            print("-" * 50)
            
            success = downloader.download_video(
                args.url, 
                quality=args.quality,
                audio_only=args.audio_only,
                progress_callback=progress_hook
            )
            
            if success:
                print("\n✅ Download completed successfully!")
            else:
                print("\n❌ Download failed!")
                sys.exit(1)
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()