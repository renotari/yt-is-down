#!/usr/bin/env python3
import argparse
import sys
import signal
from downloader import (
    YouTubeDownloader, YouTubeDownloaderError, NetworkTimeoutError,
    VideoUnavailableError, InvalidURLError, PlaylistError,
    PlaylistTooLargeError, PlaylistPrivateError
)

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

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n⚠️  Download cancelled by user")
    sys.exit(0)

def main():
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
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
    parser.add_argument('-t', '--timeout', type=int, default=30,
                       help='Network timeout in seconds (default: 30)')
    parser.add_argument('--playlist-range', type=str, metavar='START:END',
                       help='Download only videos in range (e.g., 1:10 for first 10 videos)')
    
    args = parser.parse_args()
    
    try:
        downloader = YouTubeDownloader(args.output, timeout=args.timeout)
        
        if args.info:
            print("🔍 Getting content information...")
            try:
                info = downloader.get_content_info(args.url)
                
                # Check if it's a playlist or single video
                if info.get('is_playlist') or 'video_count' in info:
                    print(f"\n📋 Playlist: {info['title']}")
                    print(f"👤 Uploader: {info['uploader']}")
                    print(f"📊 Videos: {info['video_count']} videos")
                    print(f"⏰ Estimated time: ~{info['estimated_time_minutes']} minutes")
                    print(f"\n⚠️  IMPORTANT: Downloads use 15-25 second delays for safety")
                    print(f"📝 First few videos:")
                    for i, entry in enumerate(info['entries'][:5], 1):
                        title = entry.get('title', 'Unknown Title')
                        if len(title) > 60:
                            title = title[:57] + "..."
                        print(f"   {i}. {title}")
                    if len(info['entries']) > 5:
                        print(f"   ... and {info['video_count'] - 5} more videos")
                else:
                    print(f"\n📹 Title: {info['title']}")
                    print(f"👤 Uploader: {info['uploader']}")
                    print(f"⏱️  Duration: {info['duration']} seconds")
                    print("\n📊 Available formats:")
                    for fmt in info['formats'][:10]:  # Show first 10 formats
                        print(f"   • {fmt}")
                    if len(info['formats']) > 10:
                        print(f"   ... and {len(info['formats']) - 10} more formats")
            except Exception as e:
                raise e
        else:
            # Parse playlist range if provided
            video_range = None
            if args.playlist_range:
                try:
                    start, end = map(int, args.playlist_range.split(':'))
                    video_range = (start, end)
                except ValueError:
                    print("❌ Invalid playlist range format. Use START:END (e.g., 1:10)")
                    sys.exit(1)
            
            # Check if it's a playlist or single video
            if downloader._is_playlist_url(args.url):
                print(f"🚀 Starting playlist download...")
                print(f"🔗 URL: {args.url}")
                print(f"🎯 Quality: {args.quality}")
                print(f"🎵 Audio only: {args.audio_only}")
                print(f"📁 Output directory: {args.output}")
                print(f"⏰ Timeout: {args.timeout}s")
                if video_range:
                    print(f"📊 Range: Videos {video_range[0]} to {video_range[1]}")
                print(f"⚠️  Using 15-25 second delays between downloads for safety")
                print("-" * 60)
                
                # Get playlist info first to pass to download method
                try:
                    playlist_info = downloader.get_content_info(args.url)
                    if not (playlist_info.get('is_playlist') or 'video_count' in playlist_info):
                        playlist_info = None
                except:
                    playlist_info = None
                
                result = downloader.download_playlist(
                    args.url,
                    quality=args.quality,
                    audio_only=args.audio_only,
                    progress_callback=progress_hook,
                    video_range=video_range,
                    playlist_info=playlist_info
                )
                
                if result['success']:
                    print(f"\n✅ Playlist download completed!")
                    print(f"📋 Playlist: {result['playlist_title']}")
                    print(f"📊 Downloaded: {result['downloaded']}/{result['total_videos']} videos")
                    if result['failed'] > 0:
                        print(f"⚠️  Failed: {result['failed']} videos")
                    print(f"⏱️  Total time: {result['total_time_seconds']} seconds")
                    print(f"📁 Files saved to: {args.output}")
                else:
                    print("\n❌ Playlist download failed!")
                    sys.exit(1)
            else:
                print(f"🚀 Starting download...")
                print(f"🔗 URL: {args.url}")
                print(f"🎯 Quality: {args.quality}")
                print(f"🎵 Audio only: {args.audio_only}")
                print(f"📁 Output directory: {args.output}")
                print(f"⏰ Timeout: {args.timeout}s")
                print("-" * 60)
                
                success = downloader.download_video(
                    args.url, 
                    quality=args.quality,
                    audio_only=args.audio_only,
                    progress_callback=progress_hook
                )
                
                if success:
                    print("\n✅ Download completed successfully!")
                    print(f"📁 Files saved to: {args.output}")
                else:
                    print("\n❌ Download failed!")
                    sys.exit(1)
                
    except InvalidURLError as e:
        print(f"\n❌ Invalid URL: {e}")
        print("\n💡 Supported URL formats:")
        print("   • https://www.youtube.com/watch?v=...")
        print("   • https://youtu.be/...")
        print("   • https://m.youtube.com/watch?v=...")
        sys.exit(1)
    except NetworkTimeoutError as e:
        print(f"\n⏰ Network Timeout: {e}")
        print(f"\n💡 Try increasing timeout with --timeout option (current: {args.timeout}s)")
        print("💡 Check your internet connection")
        sys.exit(1)
    except VideoUnavailableError as e:
        print(f"\n🚫 Video Unavailable: {e}")
        print("\n💡 Possible reasons:")
        print("   • Video is private or deleted")
        print("   • Geographic restrictions")
        print("   • Age restrictions")
        print("   • Copyright restrictions")
        sys.exit(1)
    except PlaylistTooLargeError as e:
        print(f"\n⚠️  Large Playlist Warning: {e}")
        print("\n💡 Recommendations:")
        print("   • Use --playlist-range to download in smaller batches")
        print("   • Example: --playlist-range 1:50 for first 50 videos")
        sys.exit(1)
    except PlaylistPrivateError as e:
        print(f"\n🚫 Playlist Unavailable: {e}")
        print("\n💡 Possible reasons:")
        print("   • Playlist is private or deleted")
        print("   • Geographic restrictions")
        print("   • Requires authentication")
        sys.exit(1)
    except PlaylistError as e:
        print(f"\n❌ Playlist Error: {e}")
        sys.exit(1)
    except YouTubeDownloaderError as e:
        error_msg = str(e)
        print(f"\n❌ Download Error: {e}")
        
        # Special handling for HTTP 403 errors
        if "403" in error_msg or "forbidden" in error_msg.lower():
            print("\n🔧 Quick fixes for HTTP 403 errors:")
            print("   1. pip install --upgrade yt-dlp")
            print("   2. Wait 10-15 minutes and try again")
            print("   3. Try different quality: --quality worst")
            print("   4. Check if video is region-locked")
        
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Download cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected Error: {e}")
        print("\n💡 Please try again or report this issue")
        sys.exit(1)

if __name__ == "__main__":
    main()