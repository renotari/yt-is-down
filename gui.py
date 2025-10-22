#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
from downloader import (
    YouTubeDownloader, YouTubeDownloaderError, NetworkTimeoutError,
    VideoUnavailableError, InvalidURLError
)
import os
from pathlib import Path

class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("600x500")
        
        self.downloader = YouTubeDownloader(timeout=30)
        self.video_info = None
        self.download_cancelled = False
        
        self.setup_ui()
        self.check_clipboard()  # Start clipboard monitoring
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # URL input
        url_label_frame = ttk.Frame(main_frame)
        url_label_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(url_label_frame, text="YouTube URL:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(url_label_frame, text="(Tip: Copy a YouTube URL and click Paste, or press Ctrl+Shift+V)", 
                 font=("TkDefaultFont", 8), foreground="gray").grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # URL input frame with entry and paste button
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Bind Ctrl+Shift+V to paste and validate (Ctrl+V is default paste)
        self.url_entry.bind('<Control-Shift-V>', lambda e: self.paste_from_clipboard())
        
        self.paste_btn = ttk.Button(url_frame, text="📋 Paste", command=self.paste_from_clipboard, width=8)
        self.paste_btn.grid(row=0, column=1)
        
        # Configure url_frame grid weights
        url_frame.columnconfigure(0, weight=1)
        
        # Get info button
        ttk.Button(main_frame, text="Get Video Info", 
                  command=self.get_video_info).grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        # Video info display
        info_frame = ttk.LabelFrame(main_frame, text="Video Information", padding="5")
        info_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, height=6, width=70, state=tk.DISABLED)
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        info_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Download options
        options_frame = ttk.LabelFrame(main_frame, text="Download Options", padding="5")
        options_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Quality selection
        ttk.Label(options_frame, text="Quality:").grid(row=0, column=0, sticky=tk.W)
        self.quality_var = tk.StringVar(value="best")
        self.quality_combo = ttk.Combobox(options_frame, textvariable=self.quality_var, 
                                         values=["best", "worst"], state="readonly", width=20)
        self.quality_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Audio only checkbox
        self.audio_only_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Audio Only (MP3)", 
                       variable=self.audio_only_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Output directory
        ttk.Label(options_frame, text="Output Directory:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.output_var = tk.StringVar(value="downloads")
        output_frame = ttk.Frame(options_frame)
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Entry(output_frame, textvariable=self.output_var, width=40).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(output_frame, text="Browse", 
                  command=self.browse_output_dir).grid(row=0, column=1, padx=(5, 0))
        
        # Progress information
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        
        # Detailed progress info
        self.detail_progress_var = tk.StringVar(value="")
        ttk.Label(main_frame, textvariable=self.detail_progress_var, font=("Consolas", 9)).grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        
        # Progress bar (determinate mode for actual percentage)
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate', maximum=100)
        self.progress_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Download/Cancel button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(0, 10))
        
        self.download_btn = ttk.Button(button_frame, text="Download", 
                                      command=self.start_download, style="Accent.TButton")
        self.download_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel", 
                                    command=self.cancel_download, state=tk.DISABLED)
        self.cancel_btn.grid(row=0, column=1)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        url_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
        output_frame.columnconfigure(0, weight=1)
        
    def get_video_info(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        def fetch_info():
            try:
                self.progress_var.set("Getting video information...")
                self.progress_bar.start()
                
                self.video_info = self.downloader.get_video_info(url)
                
                # Update UI in main thread
                self.root.after(0, self.display_video_info)
                
            except InvalidURLError as e:
                error_msg = "Please enter a valid YouTube URL.\n\nSupported formats:\n• https://www.youtube.com/watch?v=...\n• https://youtu.be/...\n• https://m.youtube.com/watch?v=..."
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Invalid URL", msg))
            except NetworkTimeoutError as e:
                error_msg = f"Connection timed out. Please check your internet connection and try again.\n\n{str(e)}"
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Network Timeout", msg))
            except VideoUnavailableError as e:
                error_msg = f"The video is not available for download.\n\nPossible reasons:\n• Video is private or deleted\n• Geographic restrictions\n• Age restrictions\n\n{str(e)}"
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Video Unavailable", msg))
            except YouTubeDownloaderError as e:
                error_msg = str(e)
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Download Error", msg))
            except Exception as e:
                error_msg = f"An unexpected error occurred:\n{str(e)}\n\nPlease try again or contact support."
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Unexpected Error", msg))
            finally:
                self.root.after(0, lambda: self.progress_bar.stop())
                self.root.after(0, lambda: self.progress_var.set("Ready"))
        
        threading.Thread(target=fetch_info, daemon=True).start()
    
    def display_video_info(self):
        if not self.video_info:
            return
            
        info_text = f"Title: {self.video_info['title']}\n"
        info_text += f"Uploader: {self.video_info['uploader']}\n"
        info_text += f"Duration: {self.video_info['duration']} seconds\n\n"
        info_text += "Available formats:\n"
        
        formats = ["best", "worst"] + self.video_info['formats'][:8]  # Limit to 8 formats
        for fmt in self.video_info['formats'][:8]:
            info_text += f"  - {fmt}\n"
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info_text)
        self.info_text.config(state=tk.DISABLED)
        
        # Update quality combobox
        self.quality_combo['values'] = formats
    
    def browse_output_dir(self):
        directory = filedialog.askdirectory(initialdir=self.output_var.get())
        if directory:
            self.output_var.set(directory)
    
    def paste_from_clipboard(self):
        """Paste URL from clipboard and validate it"""
        try:
            # Get clipboard content
            clipboard_content = self.root.clipboard_get().strip()
            
            if not clipboard_content:
                messagebox.showwarning("Empty Clipboard", "Clipboard is empty or contains no text.")
                return
            
            # Validate if it's a YouTube URL
            if self.downloader._is_valid_url(clipboard_content):
                self.url_var.set(clipboard_content)
                self.url_entry.focus()
                
                # Visual feedback - briefly change button color
                original_style = self.paste_btn.cget('style')
                self.paste_btn.configure(text="✅ Pasted")
                self.root.after(1500, lambda: self.paste_btn.configure(text="📋 Paste"))
                
                # Show success message in status
                self.progress_var.set("Valid YouTube URL pasted!")
                self.root.after(3000, lambda: self.progress_var.set("Ready"))
                
            else:
                # Check if it looks like a URL but not YouTube
                if any(protocol in clipboard_content.lower() for protocol in ['http://', 'https://', 'www.']):
                    messagebox.showerror("Invalid URL", 
                        f"The clipboard contains a URL, but it's not a valid YouTube URL.\n\n"
                        f"Found: {clipboard_content[:100]}{'...' if len(clipboard_content) > 100 else ''}\n\n"
                        f"Supported YouTube formats:\n"
                        f"• https://www.youtube.com/watch?v=...\n"
                        f"• https://youtu.be/...\n"
                        f"• https://m.youtube.com/watch?v=...")
                else:
                    messagebox.showerror("Invalid Content", 
                        f"Clipboard doesn't contain a valid YouTube URL.\n\n"
                        f"Found: {clipboard_content[:100]}{'...' if len(clipboard_content) > 100 else ''}\n\n"
                        f"Please copy a YouTube URL to your clipboard first.")
                
        except tk.TclError:
            # Clipboard is empty or contains non-text data
            messagebox.showwarning("Clipboard Error", 
                "Could not access clipboard content.\n\n"
                "Please make sure you have copied a YouTube URL to your clipboard.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while accessing clipboard:\n{str(e)}")
    
    def check_clipboard(self):
        """Monitor clipboard for YouTube URLs and update paste button accordingly"""
        try:
            clipboard_content = self.root.clipboard_get().strip()
            if clipboard_content and self.downloader._is_valid_url(clipboard_content):
                # Clipboard contains valid YouTube URL
                if self.paste_btn.cget('text') == '📋 Paste':
                    self.paste_btn.configure(text='📋 Paste URL', style='Accent.TButton')
            else:
                # No valid YouTube URL in clipboard
                if 'URL' in self.paste_btn.cget('text'):
                    self.paste_btn.configure(text='📋 Paste', style='')
        except (tk.TclError, Exception):
            # Clipboard error or empty - reset button
            if 'URL' in self.paste_btn.cget('text'):
                self.paste_btn.configure(text='📋 Paste', style='')
        
        # Check again in 2 seconds
        self.root.after(2000, self.check_clipboard)
    
    def format_bytes(self, bytes_val):
        """Convert bytes to human readable format"""
        if bytes_val is None:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} TB"
    
    def progress_hook(self, d):
        """Progress callback for GUI updates"""
        try:
            status = d.get('status', 'unknown')
            
            if status == 'downloading':
                # Extract progress information
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                # Calculate percentage
                if total > 0:
                    percentage = (downloaded / total) * 100
                    self.root.after(0, lambda p=percentage: self.progress_bar.config(value=p))
                else:
                    percentage = 0
                
                # Format progress text
                downloaded_str = self.format_bytes(downloaded)
                total_str = self.format_bytes(total) if total > 0 else "Unknown"
                speed_str = self.format_bytes(speed) + "/s" if speed else "Unknown"
                eta_str = f"{eta}s" if eta else "Unknown"
                
                progress_text = f"Downloading... {percentage:.1f}%"
                detail_text = f"{downloaded_str} / {total_str} | Speed: {speed_str} | ETA: {eta_str}"
                
                # Update UI in main thread
                self.root.after(0, lambda pt=progress_text: self.progress_var.set(pt))
                self.root.after(0, lambda dt=detail_text: self.detail_progress_var.set(dt))
                
            elif status == 'finished':
                filename = d.get('filename', 'file')
                if self.audio_only_var.get():
                    # For audio downloads, show conversion status
                    self.root.after(0, lambda: self.progress_var.set("Converting to MP3..."))
                    self.root.after(0, lambda: self.detail_progress_var.set("Converting audio format, please wait..."))
                else:
                    self.root.after(0, lambda: self.progress_var.set("Processing..."))
                    self.root.after(0, lambda: self.detail_progress_var.set("Finalizing download..."))
                self.root.after(0, lambda: self.progress_bar.config(value=100))
                
            elif status == 'error':
                error_msg = d.get('error', 'Unknown error occurred')
                self.root.after(0, lambda: self.progress_var.set("Error occurred"))
                self.root.after(0, lambda em=str(error_msg): self.detail_progress_var.set(f"Error: {em}"))
                
            # Handle post-processor events (for MP3 conversion)
            elif 'postprocessor' in d:
                postprocessor = d.get('postprocessor', '')
                if 'FFmpegExtractAudio' in postprocessor:
                    self.root.after(0, lambda: self.progress_var.set("Converting to MP3..."))
                    self.root.after(0, lambda: self.detail_progress_var.set("Extracting audio and converting to MP3..."))
                elif 'finished' in str(d).lower():
                    self.root.after(0, lambda: self.progress_var.set("Conversion complete"))
                    self.root.after(0, lambda: self.detail_progress_var.set("MP3 conversion finished"))
                
        except Exception as e:
            # Prevent progress callback errors from crashing the download
            print(f"Progress callback error: {e}")
            pass
    
    def cancel_download(self):
        """Cancel the current download"""
        self.download_cancelled = True
        self.progress_var.set("Cancelling...")
        self.detail_progress_var.set("Please wait while download is cancelled...")
    
    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        self.download_cancelled = False
            
        def download():
            try:
                # Reset progress and update UI
                self.root.after(0, lambda: self.progress_var.set("Initializing..."))
                self.root.after(0, lambda: self.detail_progress_var.set(""))
                self.root.after(0, lambda: self.progress_bar.config(value=0))
                self.root.after(0, lambda: self.download_btn.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.cancel_btn.config(state=tk.NORMAL))
                
                # Validate output directory
                output_path = self.output_var.get()
                if not output_path:
                    raise YouTubeDownloaderError("Please specify an output directory")
                
                # Update downloader output directory
                self.downloader.output_dir = Path(output_path)
                
                # Check if cancelled before starting
                if self.download_cancelled:
                    return
                
                success = self.downloader.download_video(
                    url,
                    quality=self.quality_var.get(),
                    audio_only=self.audio_only_var.get(),
                    progress_callback=self.progress_hook
                )
                
                # Small delay to ensure post-processing is complete
                if success and self.audio_only_var.get():
                    time.sleep(1)  # Give time for MP3 conversion to finish
                
                if self.download_cancelled:
                    self.root.after(0, lambda: self.progress_var.set("Cancelled"))
                    self.root.after(0, lambda: self.detail_progress_var.set("Download was cancelled"))
                elif success:
                    self.root.after(0, lambda: self.progress_var.set("Completed!"))
                    if self.audio_only_var.get():
                        self.root.after(0, lambda: self.detail_progress_var.set("MP3 download completed successfully"))
                        self.root.after(0, lambda: messagebox.showinfo("Success", 
                            f"Audio download completed!\n\nMP3 file saved to: {output_path}"))
                    else:
                        self.root.after(0, lambda: self.detail_progress_var.set("Video download completed successfully"))
                        self.root.after(0, lambda: messagebox.showinfo("Success", 
                            f"Video download completed!\n\nSaved to: {output_path}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Download failed!"))
                    
            except InvalidURLError as e:
                error_msg = "Please enter a valid YouTube URL.\n\nSupported formats:\n• https://www.youtube.com/watch?v=...\n• https://youtu.be/...\n• https://m.youtube.com/watch?v=..."
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Invalid URL", msg))
            except NetworkTimeoutError as e:
                error_msg = f"Download timed out. Please check your internet connection and try again.\n\n{str(e)}"
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Network Timeout", msg))
            except VideoUnavailableError as e:
                error_msg = f"The video is not available for download.\n\nPossible reasons:\n• Video is private or deleted\n• Geographic restrictions\n• Age restrictions\n\n{str(e)}"
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Video Unavailable", msg))
            except YouTubeDownloaderError as e:
                error_msg = str(e)
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Download Error", msg))
            except Exception as e:
                error_msg = f"An unexpected error occurred:\n{str(e)}\n\nPlease try again or contact support."
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Unexpected Error", msg))
            finally:
                self.root.after(0, lambda: self.progress_var.set("Ready"))
                self.root.after(0, lambda: self.detail_progress_var.set(""))
                self.root.after(0, lambda: self.progress_bar.config(value=0))
                self.root.after(0, lambda: self.download_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.cancel_btn.config(state=tk.DISABLED))
        
        threading.Thread(target=download, daemon=True).start()

def main():
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()