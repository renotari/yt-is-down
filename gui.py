#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from downloader import YouTubeDownloader
import os
from pathlib import Path

class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("600x500")
        
        self.downloader = YouTubeDownloader()
        self.video_info = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # URL input
        ttk.Label(main_frame, text="YouTube URL:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        
        # Download button
        self.download_btn = ttk.Button(main_frame, text="Download", 
                                      command=self.start_download, style="Accent.TButton")
        self.download_btn.grid(row=8, column=0, columnspan=2, pady=(0, 10))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
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
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
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
        if d['status'] == 'downloading':
            # Extract progress information
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            
            # Calculate percentage
            if total > 0:
                percentage = (downloaded / total) * 100
                self.root.after(0, lambda: self.progress_bar.config(value=percentage))
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
            self.root.after(0, lambda: self.progress_var.set(progress_text))
            self.root.after(0, lambda: self.detail_progress_var.set(detail_text))
            
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.progress_var.set("Processing..."))
            self.root.after(0, lambda: self.detail_progress_var.set("Finalizing download..."))
            self.root.after(0, lambda: self.progress_bar.config(value=100))
    
    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        def download():
            try:
                # Reset progress
                self.root.after(0, lambda: self.progress_var.set("Initializing..."))
                self.root.after(0, lambda: self.detail_progress_var.set(""))
                self.root.after(0, lambda: self.progress_bar.config(value=0))
                self.download_btn.config(state=tk.DISABLED)
                
                # Update downloader output directory
                output_path = self.output_var.get()
                self.downloader.output_dir = Path(output_path)
                self.downloader.output_dir.mkdir(parents=True, exist_ok=True)
                
                success = self.downloader.download_video(
                    url,
                    quality=self.quality_var.get(),
                    audio_only=self.audio_only_var.get(),
                    progress_callback=self.progress_hook
                )
                
                if success:
                    self.root.after(0, lambda: self.progress_var.set("Completed!"))
                    self.root.after(0, lambda: self.detail_progress_var.set("Download finished successfully"))
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Download completed!"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Download failed!"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, lambda: self.progress_var.set("Ready"))
                self.root.after(0, lambda: self.detail_progress_var.set(""))
                self.root.after(0, lambda: self.progress_bar.config(value=0))
                self.root.after(0, lambda: self.download_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=download, daemon=True).start()

def main():
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()