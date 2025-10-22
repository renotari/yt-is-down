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
        self.root.title("🎬 YouTube Downloader")
        self.root.geometry("700x700")
        self.root.minsize(650, 650)
        
        # Set modern colors and styling
        self.colors = {
            'bg': '#f0f0f0',
            'primary': '#ff0000',  # YouTube red
            'primary_dark': '#cc0000',
            'secondary': '#065fd4',  # YouTube blue
            'success': '#00c851',
            'warning': '#ffbb33',
            'danger': '#ff4444',
            'dark': '#212529',
            'light': '#ffffff',
            'muted': '#6c757d'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Try to set a nice icon (will fail gracefully if not available)
        try:
            self.root.iconbitmap(default='youtube.ico')
        except:
            pass
        
        self.downloader = YouTubeDownloader(timeout=30)
        self.video_info = None
        self.download_cancelled = False
        
        self.setup_styles()
        self.setup_menu()
        self.setup_ui()
        self.check_clipboard()  # Start clipboard monitoring
    
    def setup_styles(self):
        """Configure modern ttk styles"""
        style = ttk.Style()
        
        # Use a theme that works better with custom colors
        try:
            style.theme_use('clam')  # More customizable than default
        except:
            pass
        
        # Configure modern button styles with better contrast
        style.configure('Primary.TButton',
                       background=self.colors['primary'],
                       foreground='white',
                       borderwidth=1,
                       relief='solid',
                       focuscolor='none',
                       padding=(20, 10),
                       font=('Segoe UI', 10, 'bold'))
        style.map('Primary.TButton',
                 background=[('active', self.colors['primary_dark']),
                           ('pressed', self.colors['primary_dark'])],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        style.configure('Secondary.TButton',
                       background=self.colors['secondary'],
                       foreground='white',
                       borderwidth=1,
                       relief='solid',
                       focuscolor='none',
                       padding=(15, 8),
                       font=('Segoe UI', 9, 'bold'))
        style.map('Secondary.TButton',
                 background=[('active', '#0056b3'), ('pressed', '#004085')],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       borderwidth=1,
                       relief='solid',
                       focuscolor='none',
                       padding=(15, 8),
                       font=('Segoe UI', 9, 'bold'))
        style.map('Success.TButton',
                 background=[('active', '#00a041'), ('pressed', '#007c32')],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground='white',
                       borderwidth=1,
                       relief='solid',
                       focuscolor='none',
                       padding=(15, 8),
                       font=('Segoe UI', 9, 'bold'))
        style.map('Danger.TButton',
                 background=[('active', '#e53e3e'), ('pressed', '#c53030')],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        # Configure entry styles
        style.configure('Modern.TEntry',
                       fieldbackground='white',
                       foreground='black',
                       borderwidth=2,
                       relief='solid',
                       insertcolor='black',
                       padding=(10, 8),
                       font=('Segoe UI', 10))
        
        # Configure frame styles
        style.configure('Card.TFrame',
                       background='white',
                       relief='solid',
                       borderwidth=1)
        
        # Configure label styles
        style.configure('Title.TLabel',
                       background='white',
                       foreground=self.colors['dark'],
                       font=('Segoe UI', 12, 'bold'))
        
        style.configure('Subtitle.TLabel',
                       background='white',
                       foreground=self.colors['muted'],
                       font=('Segoe UI', 9))
        
        style.configure('Status.TLabel',
                       background='white',
                       foreground=self.colors['dark'],
                       font=('Segoe UI', 10, 'bold'))
        
        # Configure checkbox styles for better visibility
        style.configure('Modern.TCheckbutton',
                       background='white',
                       foreground=self.colors['dark'],
                       focuscolor='none',
                       font=('Segoe UI', 10))
        style.map('Modern.TCheckbutton',
                 background=[('active', 'white')],
                 foreground=[('active', self.colors['dark'])])
        
        # Configure combobox styles
        style.configure('Modern.TCombobox',
                       fieldbackground='white',
                       background='white',
                       foreground='black',
                       borderwidth=2,
                       relief='solid',
                       font=('Segoe UI', 10))
        
        # Configure progress bar
        style.configure('Modern.Horizontal.TProgressbar',
                       background=self.colors['primary'],
                       troughcolor='#e9ecef',
                       borderwidth=0,
                       lightcolor=self.colors['primary'],
                       darkcolor=self.colors['primary'])
    
    def setup_menu(self):
        """Setup application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Clear URL", command=lambda: self.url_var.set(""))
        file_menu.add_command(label="Open Downloads Folder", command=self.open_downloads_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_command(label="About", command=self.show_about)
    
    def open_downloads_folder(self):
        """Open the downloads folder in file explorer"""
        import subprocess
        import platform
        
        folder_path = self.output_var.get()
        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{str(e)}")
    
    def show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        shortcuts_text = """🎹 Keyboard Shortcuts:

⌨️ Ctrl+Shift+V - Paste and validate URL
⌨️ Enter (in URL field) - Get video info
⌨️ Ctrl+Q - Quit application

💡 Tips:
• Copy any YouTube URL and the paste button will highlight
• Press Enter after pasting a URL to quickly get video info
• Use the Browse button to select a custom download folder"""
        
        messagebox.showinfo("🎹 Keyboard Shortcuts", shortcuts_text)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """🎬 YouTube Downloader v2.0

A modern, user-friendly YouTube video downloader built with Python.

✨ Features:
• Download videos in multiple qualities
• Extract audio as MP3 files
• Smart clipboard integration
• Real-time progress tracking
• Comprehensive error handling

🛠️ Built with:
• Python 3.7+
• tkinter (GUI)
• yt-dlp (Download engine)

💝 Open Source
This software is free and open source.

🎯 Made for easy YouTube downloading!"""
        
        messagebox.showinfo("🎬 About YouTube Downloader", about_text)
        
    def setup_ui(self):
        # Main container with minimal padding
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        
        # Header section
        header_frame = tk.Frame(main_container, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 6))
        
        # App title with icon
        title_label = tk.Label(header_frame, 
                              text="🎬 YouTube Downloader", 
                              font=('Segoe UI', 14, 'bold'),
                              fg=self.colors['dark'],
                              bg=self.colors['bg'])
        title_label.pack(side=tk.LEFT)
        
        # Version label
        version_label = tk.Label(header_frame,
                               text="v2.0",
                               font=('Segoe UI', 10),
                               fg=self.colors['muted'],
                               bg=self.colors['bg'])
        version_label.pack(side=tk.RIGHT, pady=(5, 0))
        
        # URL Input Card
        url_card = ttk.Frame(main_container, style='Card.TFrame', padding=8)
        url_card.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(url_card, text="📎 Video URL", style='Title.TLabel').pack(anchor=tk.W)
        ttk.Label(url_card, text="Paste your YouTube video URL here", style='Subtitle.TLabel').pack(anchor=tk.W, pady=(0, 4))
        
        # URL input with paste button
        url_input_frame = tk.Frame(url_card, bg='white')
        url_input_frame.pack(fill=tk.X, pady=(0, 4))
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_input_frame, textvariable=self.url_var, 
                                  style='Modern.TEntry', font=('Segoe UI', 11))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.paste_btn = tk.Button(url_input_frame, 
                                  text="📋 Paste", 
                                  command=self.paste_from_clipboard,
                                  bg='#065fd4',  # Explicit blue color
                                  fg='white',
                                  font=('Segoe UI', 10, 'bold'),
                                  relief='raised',
                                  borderwidth=2,
                                  padx=15,
                                  pady=8,
                                  cursor='hand2',
                                  activebackground='#0056b3',
                                  activeforeground='white',
                                  highlightthickness=0)
        self.paste_btn.pack(side=tk.RIGHT)
        
        # Bind keyboard shortcuts
        self.url_entry.bind('<Control-Shift-V>', lambda e: self.paste_from_clipboard())
        self.url_entry.bind('<Return>', lambda e: self.get_video_info())
        
        # Global keyboard shortcuts
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<F1>', lambda e: self.show_shortcuts())
        
        # Action buttons frame
        action_frame = tk.Frame(url_card, bg='white')
        action_frame.pack(fill=tk.X)
        
        self.info_btn = tk.Button(action_frame, 
                                 text="🔍 Get Video Info", 
                                 command=self.get_video_info,
                                 bg='#065fd4',  # Explicit blue color
                                 fg='white',
                                 font=('Segoe UI', 10, 'bold'),
                                 relief='raised',
                                 borderwidth=2,
                                 padx=15,
                                 pady=8,
                                 cursor='hand2',
                                 activebackground='#0056b3',
                                 activeforeground='white',
                                 highlightthickness=0)
        self.info_btn.pack(side=tk.LEFT)
        
        # Tip label
        tip_label = ttk.Label(url_card, 
                             text="💡 Tip: Copy a YouTube URL and the paste button will light up automatically!",
                             style='Subtitle.TLabel')
        tip_label.pack(anchor=tk.W, pady=(4, 0))
        
        # Video Info Card
        self.info_card = ttk.Frame(main_container, style='Card.TFrame', padding=8)
        self.info_card.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        ttk.Label(self.info_card, text="📹 Video Information", style='Title.TLabel').pack(anchor=tk.W)
        
        # Info display with modern styling
        info_display_frame = tk.Frame(self.info_card, bg='white')
        info_display_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        
        self.info_text = tk.Text(info_display_frame, 
                                height=4, 
                                font=('Segoe UI', 10),
                                bg='#f8f9fa',
                                fg=self.colors['dark'],
                                border=0,
                                padx=15,
                                pady=15,
                                state=tk.DISABLED,
                                wrap=tk.WORD)
        
        info_scrollbar = ttk.Scrollbar(info_display_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Download Options Card
        options_card = ttk.Frame(main_container, style='Card.TFrame', padding=8)
        options_card.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(options_card, text="⚙️ Download Options", style='Title.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        # Options grid
        options_grid = tk.Frame(options_card, bg='white')
        options_grid.pack(fill=tk.X)
        
        # Quality and Audio options on same line
        quality_audio_frame = tk.Frame(options_grid, bg='white')
        quality_audio_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Quality selection (left side)
        ttk.Label(quality_audio_frame, text="🎯 Quality:", font=('Segoe UI', 10, 'bold'), background='white').pack(side=tk.LEFT)
        self.quality_var = tk.StringVar(value="best")
        self.quality_combo = ttk.Combobox(quality_audio_frame, textvariable=self.quality_var, 
                                         values=["best", "worst"], state="readonly", 
                                         style='Modern.TCombobox', width=20)
        self.quality_combo.pack(side=tk.LEFT, padx=(8, 20))
        
        # Audio only option (right side)
        self.audio_only_var = tk.BooleanVar()
        audio_check = tk.Checkbutton(quality_audio_frame, 
                                    text="🎵 Audio Only (MP3)", 
                                    variable=self.audio_only_var,
                                    bg='white',
                                    fg=self.colors['dark'],
                                    font=('Segoe UI', 10),
                                    activebackground='white',
                                    activeforeground=self.colors['dark'],
                                    selectcolor='white',
                                    relief='flat',
                                    borderwidth=0)
        audio_check.pack(side=tk.LEFT)
        
        # Output directory
        output_frame = tk.Frame(options_grid, bg='white')
        output_frame.pack(fill=tk.X)
        
        ttk.Label(output_frame, text="📁 Save to:", font=('Segoe UI', 10, 'bold'), background='white').pack(anchor=tk.W)
        
        output_input_frame = tk.Frame(output_frame, bg='white')
        output_input_frame.pack(fill=tk.X, pady=(2, 0))
        
        self.output_var = tk.StringVar(value="downloads")
        output_entry = ttk.Entry(output_input_frame, textvariable=self.output_var, 
                               style='Modern.TEntry', font=('Segoe UI', 10))
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(output_input_frame, 
                              text="📂 Browse", 
                              command=self.browse_output_dir,
                              bg='#065fd4',  # Explicit blue color
                              fg='white',
                              font=('Segoe UI', 10, 'bold'),
                              relief='raised',
                              borderwidth=2,
                              padx=15,
                              pady=8,
                              cursor='hand2',
                              activebackground='#0056b3',
                              activeforeground='white',
                              highlightthickness=0)
        browse_btn.pack(side=tk.RIGHT)
        
        # Progress Card
        progress_card = ttk.Frame(main_container, style='Card.TFrame', padding=8)
        progress_card.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(progress_card, text="📊 Progress", style='Title.TLabel').pack(anchor=tk.W)
        
        # Status labels
        self.progress_var = tk.StringVar(value="Ready to download")
        status_label = ttk.Label(progress_card, textvariable=self.progress_var, style='Status.TLabel')
        status_label.pack(anchor=tk.W, pady=(4, 2))
        
        self.detail_progress_var = tk.StringVar(value="")
        detail_label = ttk.Label(progress_card, textvariable=self.detail_progress_var, 
                               font=('Consolas', 8), background='white', foreground=self.colors['muted'])
        detail_label.pack(anchor=tk.W, pady=(0, 4))
        
        # Modern progress bar
        self.progress_bar = ttk.Progressbar(progress_card, mode='determinate', maximum=100,
                                          style='Modern.Horizontal.TProgressbar', length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 6))
        
        # Action buttons with fallback styling
        button_frame = tk.Frame(progress_card, bg='white')
        button_frame.pack(fill=tk.X)
        
        # Use tk.Button with consistent blue theme
        self.download_btn = tk.Button(button_frame, 
                                     text="⬇️ Download", 
                                     command=self.start_download,
                                     bg='#065fd4',  # Blue color to match other buttons
                                     fg='white',
                                     font=('Segoe UI', 10, 'bold'),
                                     relief='raised',
                                     borderwidth=2,
                                     padx=18,
                                     pady=6,
                                     cursor='hand2',
                                     activebackground='#0056b3',
                                     activeforeground='white',
                                     highlightthickness=0)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.cancel_btn = tk.Button(button_frame, 
                                   text="❌ Cancel", 
                                   command=self.cancel_download,
                                   bg='#6c757d',  # Gray color for cancel
                                   fg='white',
                                   font=('Segoe UI', 9, 'bold'),
                                   relief='raised',
                                   borderwidth=2,
                                   padx=12,
                                   pady=5,
                                   cursor='hand2',
                                   state=tk.DISABLED,
                                   activebackground='#5a6268',
                                   activeforeground='white',
                                   highlightthickness=0)
        self.cancel_btn.pack(side=tk.LEFT)
        
        # Status bar at bottom
        status_bar = tk.Frame(self.root, bg=self.colors['muted'], height=25)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready • Press F1 for shortcuts")
        status_label = tk.Label(status_bar, textvariable=self.status_var, 
                               bg=self.colors['muted'], fg='white', 
                               font=('Segoe UI', 9), anchor=tk.W)
        status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # Version info on right side of status bar
        version_status = tk.Label(status_bar, text="v2.0", 
                                 bg=self.colors['muted'], fg='white', 
                                 font=('Segoe UI', 9))
        version_status.pack(side=tk.RIGHT, padx=10, pady=2)
        
        # Configure grid weights for responsiveness
        main_container.columnconfigure(0, weight=1)
        url_input_frame.columnconfigure(0, weight=1)
        output_input_frame.columnconfigure(0, weight=1)
        
    def get_video_info(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        def fetch_info():
            try:
                self.progress_var.set("🔍 Getting video information...")
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
                self.root.after(0, lambda: self.progress_var.set("✨ Ready to download"))
        
        threading.Thread(target=fetch_info, daemon=True).start()
    
    def display_video_info(self):
        if not self.video_info:
            return
        
        # Format duration nicely
        duration = self.video_info['duration']
        if duration > 0:
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes:02d}:{seconds:02d}"
        else:
            duration_str = "Unknown"
        
        # Create nicely formatted info text
        info_text = f"🎬 Title: {self.video_info['title']}\n\n"
        info_text += f"👤 Uploader: {self.video_info['uploader']}\n\n"
        info_text += f"⏱️ Duration: {duration_str}\n\n"
        
        if self.video_info['formats']:
            info_text += "📊 Available Quality Options:\n"
            formats = ["best", "worst"] + self.video_info['formats'][:8]  # Limit to 8 formats
            for i, fmt in enumerate(self.video_info['formats'][:8], 1):
                info_text += f"   {i}. {fmt}\n"
            
            if len(self.video_info['formats']) > 8:
                info_text += f"   ... and {len(self.video_info['formats']) - 8} more options\n"
        else:
            info_text += "📊 Quality: Standard formats available\n"
            formats = ["best", "worst"]
        
        info_text += "\n✅ Video information loaded successfully!"
        
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
                self.paste_btn.configure(text="✅ Pasted", bg='#00c851')  # Green
                self.root.after(1500, lambda: self.paste_btn.configure(text="📋 Paste", bg='#065fd4'))  # Blue
                
                # Show success message in status
                self.progress_var.set("✅ Valid YouTube URL pasted!")
                self.status_var.set("✅ Valid YouTube URL detected and pasted")
                self.root.after(3000, lambda: self.progress_var.set("✨ Ready to download"))
                self.root.after(3000, lambda: self.status_var.set("Ready • Press F1 for shortcuts"))
                
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
                    self.paste_btn.configure(text='📋 Paste URL', bg='#00c851')  # Green
            else:
                # No valid YouTube URL in clipboard
                if 'URL' in self.paste_btn.cget('text'):
                    self.paste_btn.configure(text='📋 Paste', bg='#065fd4')  # Blue
        except (tk.TclError, Exception):
            # Clipboard error or empty - reset button
            if 'URL' in self.paste_btn.cget('text'):
                self.paste_btn.configure(text='📋 Paste', bg='#065fd4')  # Blue
        
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
                
                progress_text = f"⬇️ Downloading {percentage:.1f}%"
                detail_text = f"📦 {downloaded_str} of {total_str} • 🚀 {speed_str} • ⏱️ {eta_str} remaining"
                
                # Update UI in main thread
                self.root.after(0, lambda pt=progress_text: self.progress_var.set(pt))
                self.root.after(0, lambda dt=detail_text: self.detail_progress_var.set(dt))
                
            elif status == 'finished':
                filename = d.get('filename', 'file')
                if self.audio_only_var.get():
                    # For audio downloads, show conversion status
                    self.root.after(0, lambda: self.progress_var.set("🎵 Converting to MP3..."))
                    self.root.after(0, lambda: self.detail_progress_var.set("🔄 Converting audio format, please wait..."))
                else:
                    self.root.after(0, lambda: self.progress_var.set("🔄 Processing..."))
                    self.root.after(0, lambda: self.detail_progress_var.set("✨ Finalizing download..."))
                self.root.after(0, lambda: self.progress_bar.config(value=100))
                
            elif status == 'error':
                error_msg = d.get('error', 'Unknown error occurred')
                self.root.after(0, lambda: self.progress_var.set("❌ Error occurred"))
                self.root.after(0, lambda em=str(error_msg): self.detail_progress_var.set(f"⚠️ Error: {em}"))
                
            # Handle post-processor events (for MP3 conversion)
            elif 'postprocessor' in d:
                postprocessor = d.get('postprocessor', '')
                if 'FFmpegExtractAudio' in postprocessor:
                    self.root.after(0, lambda: self.progress_var.set("🎵 Converting to MP3..."))
                    self.root.after(0, lambda: self.detail_progress_var.set("🔄 Extracting audio and converting to MP3..."))
                elif 'finished' in str(d).lower():
                    self.root.after(0, lambda: self.progress_var.set("✅ Conversion complete"))
                    self.root.after(0, lambda: self.detail_progress_var.set("🎉 MP3 conversion finished"))
                
        except Exception as e:
            # Prevent progress callback errors from crashing the download
            print(f"Progress callback error: {e}")
            pass
    
    def cancel_download(self):
        """Cancel the current download"""
        self.download_cancelled = True
        self.progress_var.set("⏹️ Cancelling...")
        self.detail_progress_var.set("🛑 Please wait while download is cancelled...")
    
    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        self.download_cancelled = False
            
        def download():
            try:
                # Reset progress and update UI
                self.root.after(0, lambda: self.progress_var.set("🚀 Initializing download..."))
                self.root.after(0, lambda: self.detail_progress_var.set("🔄 Preparing to download..."))
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
                    self.root.after(0, lambda: self.progress_var.set("⏹️ Cancelled"))
                    self.root.after(0, lambda: self.detail_progress_var.set("🛑 Download was cancelled by user"))
                elif success:
                    self.root.after(0, lambda: self.progress_var.set("🎉 Download Complete!"))
                    if self.audio_only_var.get():
                        self.root.after(0, lambda: self.detail_progress_var.set("🎵 MP3 file ready to enjoy!"))
                        self.root.after(0, lambda: messagebox.showinfo("🎉 Success!", 
                            f"🎵 Audio download completed!\n\n📁 MP3 file saved to:\n{output_path}"))
                    else:
                        self.root.after(0, lambda: self.detail_progress_var.set("🎬 Video file ready to watch!"))
                        self.root.after(0, lambda: messagebox.showinfo("🎉 Success!", 
                            f"🎬 Video download completed!\n\n📁 File saved to:\n{output_path}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("❌ Error", "Download failed!"))
                    
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
                self.root.after(0, lambda: self.progress_var.set("✨ Ready to download"))
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