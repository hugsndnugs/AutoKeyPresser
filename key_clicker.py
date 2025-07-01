import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
from pynput import keyboard
from pynput.keyboard import Key, Controller
import time
import threading
import sys
import pystray
from PIL import Image, ImageDraw
import os
import json
import urllib.request
import datetime
import webbrowser
import shutil
import tempfile
import subprocess
# Add winsound for notification (Windows only)
if sys.platform == 'win32':
    import winsound
from playsound import playsound

__version__ = "1.3"

VERSION_CHECK_URL = "https://raw.githubusercontent.com/hugsndnugs/AutoKeyPresser/main/latest_version.txt"  # Update this to your actual version file URL
DOWNLOAD_URL = "https://github.com/hugsndnugs/AutoKeyPresser/releases/latest"  # Update to your releases page
CACHE_FILE = "version_check_cache.json"
CACHE_DURATION_HOURS = 24
SKIP_UPDATE_FILE = "skipped_update.json"

def check_for_update():
    # Check cache first
    now = datetime.datetime.utcnow()
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
            last_check = datetime.datetime.fromisoformat(cache.get('last_check'))
            cached_version = cache.get('latest_version')
            if (now - last_check).total_seconds() < CACHE_DURATION_HOURS * 3600:
                return cached_version
        except Exception:
            pass  # Ignore cache errors
    # Fetch from remote
    try:
        with urllib.request.urlopen(VERSION_CHECK_URL, timeout=5) as response:
            latest_version = response.read().decode('utf-8').strip()
            # Cache result
            with open(CACHE_FILE, 'w') as f:
                json.dump({'last_check': now.isoformat(), 'latest_version': latest_version}, f)
            return latest_version
    except Exception as e:
        print(f"[Warning] Could not check for updates: {e}")
        return None

def get_latest_release_exe_url():
    """Get the direct download URL for the latest .exe from GitHub releases API."""
    import json
    api_url = "https://api.github.com/repos/hugsndnugs/AutoKeyPresser/releases/latest"
    try:
        with urllib.request.urlopen(api_url, timeout=10) as response:
            data = json.load(response)
            for asset in data.get("assets", []):
                name = asset.get("name", "").lower()
                if name.endswith(".exe"):
                    return asset.get("browser_download_url")
    except Exception as e:
        print(f"[Warning] Could not get latest release .exe URL: {e}")
    return None

def get_skipped_version():
    if os.path.exists(SKIP_UPDATE_FILE):
        try:
            with open(SKIP_UPDATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('skipped_version')
        except Exception:
            return None
    return None

def set_skipped_version(version):
    try:
        with open(SKIP_UPDATE_FILE, 'w') as f:
            json.dump({'skipped_version': version}, f)
    except Exception:
        pass

def auto_download_and_prompt_install(root, latest_version):
    exe_url = get_latest_release_exe_url()
    if not exe_url:
        messagebox.showerror("Update Error", "Could not find the latest installer. Please update manually.")
        return
    temp_dir = tempfile.mkdtemp()
    exe_path = os.path.join(temp_dir, os.path.basename(exe_url))

    # Progress dialog
    progress_dialog = tk.Toplevel(root)
    progress_dialog.title("Downloading Update")
    progress_dialog.resizable(False, False)
    progress_dialog.grab_set()
    tk.Label(progress_dialog, text=f"Downloading v{latest_version}...").pack(padx=20, pady=(20, 5))
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(progress_dialog, variable=progress_var, maximum=100, length=300)
    progress_bar.pack(padx=20, pady=10)
    cancel_flag = {'cancel': False}
    def cancel():
        cancel_flag['cancel'] = True
        progress_dialog.destroy()
    cancel_btn = tk.Button(progress_dialog, text="Cancel", command=cancel)
    cancel_btn.pack(pady=(0, 20))
    progress_dialog.update_idletasks()
    w = progress_dialog.winfo_width()
    h = progress_dialog.winfo_height()
    x = root.winfo_x() + (root.winfo_width() - w) // 2
    y = root.winfo_y() + (root.winfo_height() - h) // 2
    progress_dialog.geometry(f"{w}x{h}+{x}+{y}")

    # Download with progress
    try:
        with urllib.request.urlopen(exe_url) as response:
            total = int(response.getheader('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192
            with open(exe_path, 'wb') as out_file:
                while True:
                    if cancel_flag['cancel']:
                        out_file.close()
                        os.remove(exe_path)
                        return
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        percent = (downloaded / total) * 100
                        progress_var.set(percent)
                        progress_dialog.update()
        progress_dialog.destroy()
    except Exception as e:
        progress_dialog.destroy()
        messagebox.showerror("Update Error", f"Failed to download update: {e}")
        return
    # Prompt to install
    def do_install():
        try:
            subprocess.Popen([exe_path], shell=True)
        except Exception as e:
            messagebox.showerror("Install Error", f"Failed to launch installer: {e}")
        root.quit()
        sys.exit(0)
    if messagebox.askyesno("Install Update", f"Update v{latest_version} downloaded. Install now?\nThe app will close and the installer will run."):
        do_install()
    else:
        messagebox.showinfo("Update Deferred", f"You can install the update later from: {exe_path}")

def notify_if_update_gui(root):
    latest_version = check_for_update()
    if latest_version is None:
        return  # Network or cache error, skip
    skipped_version = get_skipped_version()
    if skipped_version and skipped_version == latest_version:
        return  # User chose to skip this version
    def version_tuple(v):
        return tuple(map(int, (v.split("."))))
    try:
        if version_tuple(latest_version) > version_tuple(__version__):
            # If auto-download is enabled and running as .exe, do auto-download
            auto_download = getattr(root, 'master', root)
            try:
                app = auto_download.app if hasattr(auto_download, 'app') else None
            except Exception:
                app = None
            try:
                from __main__ import app as main_app
            except Exception:
                main_app = None
            auto_download_enabled = False
            if app and hasattr(app, 'auto_download_update'):
                auto_download_enabled = app.auto_download_update
            elif main_app and hasattr(main_app, 'auto_download_update'):
                auto_download_enabled = main_app.auto_download_update
            is_frozen = getattr(sys, 'frozen', False)
            if auto_download_enabled and is_frozen:
                auto_download_and_prompt_install(root, latest_version)
                return
            # Otherwise, show the manual update dialog with skip option
            dialog = tk.Toplevel(root)
            dialog.title("Update Available")
            dialog.resizable(False, False)
            dialog.grab_set()
            dialog.transient(root)
            msg = tk.Label(dialog, text=f"A new version (v{latest_version}) is available!\nYou are using v{__version__}.", justify="left", padx=20, pady=10)
            msg.pack()
            def open_url():
                webbrowser.open(DOWNLOAD_URL)
                dialog.destroy()
            btn = tk.Button(dialog, text="Download Latest Version", command=open_url, padx=10, pady=5)
            btn.pack(pady=(0,10))
            def skip_update():
                set_skipped_version(latest_version)
                dialog.destroy()
            skip_btn = tk.Button(dialog, text="Skip this update", command=skip_update, padx=10, pady=5)
            skip_btn.pack(pady=(0,10))
            close_btn = tk.Button(dialog, text="Close", command=dialog.destroy, padx=10, pady=5)
            close_btn.pack(pady=(0,10))
            dialog.update_idletasks()
            w = dialog.winfo_width()
            h = dialog.winfo_height()
            x = root.winfo_x() + (root.winfo_width() - w) // 2
            y = root.winfo_y() + (root.winfo_height() - h) // 2
            dialog.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass  # Ignore version comparison errors

class KeyClicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Auto Key Clicker")
        
        # Initialize variables
        self.keyboard_controller = Controller()
        self.is_running = False
        self.click_thread = None
        self.tray_icon = None
        self.press_count = 0  # Total presses across all sessions
        self.session_press_count = 0  # Presses in current session
        
        # Load or create default theme
        self.theme_file = "theme.json"
        self.load_theme()
        
        # Special keys mapping
        self.special_keys = {
            'enter': Key.enter,
            'space': Key.space,
            'tab': Key.tab,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'esc': Key.esc,
            'shift': Key.shift,
            'ctrl': Key.ctrl,
            'alt': Key.alt,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'f1': Key.f1,
            'f2': Key.f2,
            'f3': Key.f3,
            'f4': Key.f4,
            'f5': Key.f5,
            'f6': Key.f6,
            'f7': Key.f7,
            'f8': Key.f8,
            'f9': Key.f9,
            'f10': Key.f10,
            'f11': Key.f11,
            'f12': Key.f12
        }
        
        # Notification settings
        self.notification_type = self.theme.get("notification_type", "sound")  # 'sound', 'messagebox', 'both', 'none'
        self.custom_sound_path = self.theme.get("custom_sound_path", "")
        
        # Create GUI elements
        self.create_gui()
        
        # Apply theme after GUI creation
        self.apply_theme()
        
        # Set up keyboard listener for hotkey
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
        
        # Create tray icon
        self.create_tray_icon()
        
        # Protocol for window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Make window resizable
        self.root.resizable(True, True)
        
        # Set minimum window size
        self.root.minsize(400, 600)
        
        # Center window on screen
        self.center_window()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def load_theme(self):
        default_theme = {
            "theme": "light",
            "font_size": 10,
            "transparency": 1.0,
            "padding": 5,
            "auto_download_update": False,
            "notification_type": "sound",
            "custom_sound_path": "",
            "colors": {
                "bg": "#ffffff",
                "fg": "#000000",
                "button_bg": "#e0e0e0",
                "button_fg": "#000000",
                "entry_bg": "#ffffff",
                "entry_fg": "#000000",
                "frame_bg": "#f0f0f0",
                "label_bg": "#ffffff",
                "hover_bg": "#d0d0d0",
                "active_bg": "#c0c0c0",
                "disabled_bg": "#e8e8e8",
                "disabled_fg": "#808080"
            }
        }
        
        try:
            if os.path.exists(self.theme_file):
                with open(self.theme_file, 'r') as f:
                    loaded_theme = json.load(f)
                    # Ensure all required properties exist
                    for key, value in default_theme.items():
                        if key not in loaded_theme:
                            loaded_theme[key] = value
                        elif key == "colors":
                            # Ensure all color properties exist
                            for color_key, color_value in value.items():
                                if color_key not in loaded_theme["colors"]:
                                    loaded_theme["colors"][color_key] = color_value
                    self.theme = loaded_theme
            else:
                self.theme = default_theme
                self.save_theme()
        except:
            self.theme = default_theme
            self.save_theme()
        self.auto_download_update = self.theme.get("auto_download_update", False)
        self.notification_type = self.theme.get("notification_type", "sound")
        self.custom_sound_path = self.theme.get("custom_sound_path", "")

    def save_theme(self):
        self.theme["auto_download_update"] = self.auto_download_update
        self.theme["notification_type"] = self.notification_type
        self.theme["custom_sound_path"] = self.custom_sound_path
        with open(self.theme_file, 'w') as f:
            json.dump(self.theme, f, indent=4)

    def apply_theme(self):
        style = ttk.Style()
        
        # Calculate padding based on font size
        padding = self.theme["font_size"] // 2
        
        # Configure ttk styles with proper padding and colors
        style.configure("TFrame",
                       background=self.theme["colors"]["frame_bg"])
        
        style.configure("TLabel", 
                       background=self.theme["colors"]["label_bg"],
                       foreground=self.theme["colors"]["fg"],
                       font=("TkDefaultFont", self.theme["font_size"]),
                       padding=padding)
        
        style.configure("TButton",
                       background=self.theme["colors"]["button_bg"],
                       foreground=self.theme["colors"]["button_fg"],
                       font=("TkDefaultFont", self.theme["font_size"]),
                       padding=padding)
        
        style.map("TButton",
                 background=[("active", self.theme["colors"]["hover_bg"]),
                           ("pressed", self.theme["colors"]["active_bg"])],
                 foreground=[("disabled", self.theme["colors"]["disabled_fg"])])
        
        style.configure("TEntry",
                       fieldbackground=self.theme["colors"]["entry_bg"],
                       foreground=self.theme["colors"]["entry_fg"],
                       font=("TkDefaultFont", self.theme["font_size"]),
                       padding=padding)
        
        # Add warning style for entry fields
        style.configure("Warning.TEntry",
                       fieldbackground="#fff3cd",  # Light yellow background
                       foreground="#856404",       # Dark yellow text
                       font=("TkDefaultFont", self.theme["font_size"]),
                       padding=padding)
        
        style.configure("TLabelframe",
                       background=self.theme["colors"]["frame_bg"],
                       foreground=self.theme["colors"]["fg"],
                       font=("TkDefaultFont", self.theme["font_size"]))
        
        style.configure("TLabelframe.Label",
                       background=self.theme["colors"]["frame_bg"],
                       foreground=self.theme["colors"]["fg"],
                       font=("TkDefaultFont", self.theme["font_size"]))
        
        style.configure("TScale",
                       background=self.theme["colors"]["frame_bg"],
                       foreground=self.theme["colors"]["fg"],
                       font=("TkDefaultFont", self.theme["font_size"]))
        
        style.configure("TCombobox",
                       fieldbackground=self.theme["colors"]["entry_bg"],
                       background=self.theme["colors"]["button_bg"],
                       foreground=self.theme["colors"]["entry_fg"],
                       font=("TkDefaultFont", self.theme["font_size"]),
                       padding=padding)
        
        # Set window transparency
        self.root.attributes('-alpha', self.theme["transparency"])
        
        # Configure root window and all frames
        self.root.configure(bg=self.theme["colors"]["bg"])
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.configure(style="TFrame")
            elif isinstance(widget, ttk.LabelFrame):
                widget.configure(style="TLabelframe")
        
        # Update window size based on font size
        self.update_window_size()

    def update_window_size(self):
        # Calculate base size
        base_width = 400
        base_height = 600
        
        # Scale based on font size
        font_scale = self.theme["font_size"] / 10  # 10 is the default font size
        new_width = int(base_width * font_scale)
        new_height = int(base_height * font_scale)
        
        # Set new size
        self.root.geometry(f"{new_width}x{new_height}")
        
        # Update minimum size
        self.root.minsize(new_width, new_height)

    def create_gui(self):
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Key selection with dropdown
        key_frame = ttk.Frame(main_frame)
        key_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(key_frame, text="Key to press:").pack(side=tk.LEFT, padx=5)
        self.key_var = tk.StringVar(value="a")
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_var, width=10)
        self.key_entry.pack(side=tk.LEFT, padx=5)
        self.key_entry.bind('<KeyRelease>', self.on_key_entry_change)
        
        # Add special keys dropdown
        self.special_key_var = tk.StringVar(value="")
        self.special_key_combo = ttk.Combobox(key_frame, textvariable=self.special_key_var, 
                                            values=list(self.special_keys.keys()), width=10)
        self.special_key_combo.pack(side=tk.LEFT, padx=5)
        self.special_key_combo.bind('<<ComboboxSelected>>', self.on_special_key_selected)
        
        # Interval selection
        interval_frame = ttk.Frame(main_frame)
        interval_frame.pack(fill=tk.X, pady=5)
        ttk.Label(interval_frame, text="Interval (seconds):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.StringVar(value="1.0")
        self.interval_entry = ttk.Entry(interval_frame, textvariable=self.interval_var, width=10)
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        
        # Hotkey selection
        hotkey_frame = ttk.Frame(main_frame)
        hotkey_frame.pack(fill=tk.X, pady=5)
        ttk.Label(hotkey_frame, text="Hotkey (F6):").pack(side=tk.LEFT, padx=5)
        self.hotkey_var = tk.StringVar(value="F6")
        self.hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.hotkey_var, width=10)
        self.hotkey_entry.pack(side=tk.LEFT, padx=5)
        self.hotkey_entry.bind('<KeyRelease>', self.on_hotkey_entry_change)
        
        # Press limit
        limit_frame = ttk.Frame(main_frame)
        limit_frame.pack(fill=tk.X, pady=5)
        ttk.Label(limit_frame, text="Press limit (0 for unlimited):").pack(side=tk.LEFT, padx=5)
        self.limit_var = tk.StringVar(value="0")
        self.limit_entry = ttk.Entry(limit_frame, textvariable=self.limit_var, width=10)
        self.limit_entry.pack(side=tk.LEFT, padx=5)
        
        # Press counter
        counter_frame = ttk.Frame(main_frame)
        counter_frame.pack(fill=tk.X, pady=5)
        self.counter_var = tk.StringVar(value="Presses: 0")
        self.counter_label = ttk.Label(counter_frame, textvariable=self.counter_var)
        self.counter_label.pack(pady=5)
        
        # Status label
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)
        self.status_var = tk.StringVar(value="Status: Stopped")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)
        
        # Start/Stop button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        self.toggle_button = ttk.Button(button_frame, text="Start (F6)", command=self.toggle_clicking)
        self.toggle_button.pack(pady=5)

        # Theme customization section
        theme_frame = ttk.LabelFrame(main_frame, text="Theme Settings", padding="5")
        theme_frame.pack(fill=tk.X, pady=10)

        # Theme selector
        theme_select_frame = ttk.Frame(theme_frame)
        theme_select_frame.pack(fill=tk.X, pady=5)
        ttk.Label(theme_select_frame, text="Theme:").pack(side=tk.LEFT, padx=5)
        self.theme_var = tk.StringVar(value=self.theme["theme"])
        theme_combo = ttk.Combobox(theme_select_frame, textvariable=self.theme_var, 
                                 values=["light", "dark"], width=10)
        theme_combo.pack(side=tk.LEFT, padx=5)
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)

        # Font size slider
        font_frame = ttk.Frame(theme_frame)
        font_frame.pack(fill=tk.X, pady=5)
        ttk.Label(font_frame, text="Font Size:").pack(side=tk.LEFT, padx=5)
        self.font_size_var = tk.IntVar(value=self.theme["font_size"])
        font_size_scale = ttk.Scale(font_frame, from_=8, to=16, 
                                  variable=self.font_size_var, orient=tk.HORIZONTAL)
        font_size_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        font_size_scale.bind("<ButtonRelease-1>", self.change_font_size)

        # Transparency slider
        trans_frame = ttk.Frame(theme_frame)
        trans_frame.pack(fill=tk.X, pady=5)
        ttk.Label(trans_frame, text="Transparency:").pack(side=tk.LEFT, padx=5)
        self.transparency_var = tk.DoubleVar(value=self.theme["transparency"])
        transparency_scale = ttk.Scale(trans_frame, from_=0.5, to=1.0, 
                                     variable=self.transparency_var, orient=tk.HORIZONTAL)
        transparency_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        transparency_scale.bind("<ButtonRelease-1>", self.change_transparency)

        # Color customization buttons
        color_frame = ttk.Frame(theme_frame)
        color_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(color_frame, text="Background Color", 
                  command=lambda: self.choose_color("bg")).pack(side=tk.LEFT, padx=5)
        ttk.Button(color_frame, text="Text Color", 
                  command=lambda: self.choose_color("fg")).pack(side=tk.LEFT, padx=5)
        ttk.Button(color_frame, text="Button Color", 
                  command=lambda: self.choose_color("button_bg")).pack(side=tk.LEFT, padx=5)

        # Reset button
        reset_frame = ttk.Frame(theme_frame)
        reset_frame.pack(fill=tk.X, pady=5)
        ttk.Button(reset_frame, text="Reset to Default Theme", 
                  command=self.reset_theme).pack(pady=5)

        # Auto-download updates checkbox
        self.auto_download_var = tk.BooleanVar(value=self.auto_download_update)
        auto_dl_cb = ttk.Checkbutton(
            theme_frame,
            text="Auto-download updates",
            variable=self.auto_download_var,
            command=self.on_auto_download_toggle
        )
        auto_dl_cb.pack(anchor="w", padx=5, pady=(5, 0))

        # Notification settings section
        notif_frame = ttk.LabelFrame(main_frame, text="Notification Settings", padding="5")
        notif_frame.pack(fill=tk.X, pady=10, padx=10)
        ttk.Label(notif_frame, text="On press limit:").pack(side=tk.LEFT, padx=5)
        self.notif_type_var = tk.StringVar(value=self.notification_type)
        notif_combo = ttk.Combobox(notif_frame, textvariable=self.notif_type_var, values=["sound", "messagebox", "both", "none"], width=12)
        notif_combo.pack(side=tk.LEFT, padx=5)
        notif_combo.bind('<<ComboboxSelected>>', self.on_notif_type_change)
        self.sound_path_var = tk.StringVar(value=self.custom_sound_path)
        sound_btn = ttk.Button(notif_frame, text="Choose Sound...", command=self.choose_sound_file)
        sound_btn.pack(side=tk.LEFT, padx=5)
        self.sound_label = ttk.Label(notif_frame, text=os.path.basename(self.custom_sound_path) if self.custom_sound_path else "Default beep")
        self.sound_label.pack(side=tk.LEFT, padx=5)

    def on_special_key_selected(self, event):
        selected = self.special_key_var.get()
        if selected:
            # Check for hotkey conflict
            hotkey = self.hotkey_var.get().lower()
            if selected.lower() == hotkey:
                messagebox.showwarning("Hotkey Conflict", 
                                     f"Warning: '{selected}' is currently set as your hotkey.\n"
                                     f"Using the same key for both hotkey and key to press will create a conflict.\n"
                                     f"Consider changing your hotkey to a different key.")
            self.key_var.set(selected)
            
    def create_tray_icon(self):
        # Create a simple icon
        icon_image = Image.new('RGB', (64, 64), color='white')
        dc = ImageDraw.Draw(icon_image)
        dc.rectangle([16, 16, 48, 48], fill='black')
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Start/Stop", self.toggle_clicking),
            pystray.MenuItem("Reset Counter", self.reset_counter),
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        # Create tray icon
        self.tray_icon = pystray.Icon("key_clicker", icon_image, "Key Clicker", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
    def reset_counter(self):
        self.press_count = 0
        self.session_press_count = 0
        self.counter_var.set("Presses: 0")
        
    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        
    def on_closing(self):
        self.root.withdraw()
        
    def quit_app(self):
        # Stop the key clicking if it's running
        if self.is_running:
            self.is_running = False
            if self.click_thread and self.click_thread.is_alive():
                self.click_thread.join(timeout=1.0)  # Wait for thread to finish with timeout
        
        # Stop the keyboard listener
        if self.listener and self.listener.is_alive():
            self.listener.stop()
            self.listener.join()
        
        # Stop the tray icon
        if self.tray_icon:
            self.tray_icon.stop()
        
        # Destroy the root window and all its widgets
        if self.root:
            self.root.quit()
            self.root.destroy()
        
        # Force exit after cleanup
        sys.exit(0)
        
    def on_key_press(self, key):
        try:
            if key == keyboard.Key[self.hotkey_var.get().lower()]:
                self.toggle_clicking()
        except (KeyError, AttributeError):
            pass
            
    def toggle_clicking(self):
        if not self.is_running:
            try:
                interval = float(self.interval_var.get())
                if interval < 0.01:
                    messagebox.showerror("Error", "Interval must be at least 0.01 seconds")
                    return
                
                # Check for hotkey conflict
                key_to_press = self.key_var.get().lower()
                hotkey = self.hotkey_var.get().lower()
                if key_to_press == hotkey:
                    messagebox.showerror("Error", f"Cannot use '{self.hotkey_var.get()}' as both hotkey and key to press.\nThis would create a conflict. Please choose a different key or hotkey.")
                    return
                    
                self.is_running = True
                self.session_press_count = 0  # Reset session counter when starting
                self.status_var.set("Status: Running")
                self.toggle_button.config(text="Stop (F6)")
                self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
                self.click_thread.start()
            except ValueError:
                messagebox.showerror("Error", "Invalid interval value")
        else:
            self.is_running = False
            self.status_var.set("Status: Stopped")
            self.toggle_button.config(text="Start (F6)")
            
    def click_loop(self):
        try:
            key = self.key_var.get()
            interval = float(self.interval_var.get())
            limit = int(self.limit_var.get())
            
            # Convert key to special key if needed
            key_to_press = self.special_keys.get(key.lower(), key)
            
            while self.is_running:
                if limit > 0 and self.session_press_count >= limit:
                    self.is_running = False
                    self.status_var.set("Status: Completed")
                    self.toggle_button.config(text="Start (F6)")
                    self.notify_press_limit()
                    break
                
                self.keyboard_controller.press(key_to_press)
                self.keyboard_controller.release(key_to_press)
                self.press_count += 1
                self.session_press_count += 1
                self.counter_var.set(f"Presses: {self.press_count}")
                time.sleep(interval)
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.is_running = False
            self.status_var.set("Status: Error")
            self.toggle_button.config(text="Start (F6)")
            
    def change_theme(self, event=None):
        theme = self.theme_var.get()
        if theme == "light":
            self.theme["colors"] = {
                "bg": "#ffffff",
                "fg": "#000000",
                "button_bg": "#e0e0e0",
                "button_fg": "#000000",
                "entry_bg": "#ffffff",
                "entry_fg": "#000000",
                "frame_bg": "#f0f0f0",
                "label_bg": "#ffffff",
                "hover_bg": "#d0d0d0",
                "active_bg": "#c0c0c0",
                "disabled_bg": "#e8e8e8",
                "disabled_fg": "#808080"
            }
        else:  # dark theme
            self.theme["colors"] = {
                "bg": "#2b2b2b",
                "fg": "#ffffff",
                "button_bg": "#404040",
                "button_fg": "#ffffff",
                "entry_bg": "#404040",
                "entry_fg": "#ffffff",
                "frame_bg": "#333333",
                "label_bg": "#2b2b2b",
                "hover_bg": "#505050",
                "active_bg": "#606060",
                "disabled_bg": "#383838",
                "disabled_fg": "#a0a0a0"
            }
        self.theme["theme"] = theme
        self.apply_theme()
        self.save_theme()

    def change_font_size(self, event=None):
        self.theme["font_size"] = self.font_size_var.get()
        self.apply_theme()
        self.save_theme()

    def change_transparency(self, event=None):
        self.theme["transparency"] = self.transparency_var.get()
        self.root.attributes('-alpha', self.theme["transparency"])
        self.save_theme()

    def choose_color(self, color_key):
        color = colorchooser.askcolor(color=self.theme["colors"][color_key])[1]
        if color:
            self.theme["colors"][color_key] = color
            self.apply_theme()
            self.save_theme()

    def reset_theme(self):
        """Reset the theme to default settings with confirmation."""
        if messagebox.askyesno("Reset Theme", 
                              "Are you sure you want to reset all theme settings to default?\n"
                              "This will reset colors, font size, and transparency."):
            # Reset to default theme
            self.theme = {
                "theme": "light",
                "font_size": 10,
                "transparency": 1.0,
                "padding": 5,
                "auto_download_update": False,
                "notification_type": "sound",
                "custom_sound_path": "",
                "colors": {
                    "bg": "#ffffff",
                    "fg": "#000000",
                    "button_bg": "#e0e0e0",
                    "button_fg": "#000000",
                    "entry_bg": "#ffffff",
                    "entry_fg": "#000000",
                    "frame_bg": "#f0f0f0",
                    "label_bg": "#ffffff",
                    "hover_bg": "#d0d0d0",
                    "active_bg": "#c0c0c0",
                    "disabled_bg": "#e8e8e8",
                    "disabled_fg": "#808080"
                }
            }
            
            # Update UI variables
            self.theme_var.set("light")
            self.font_size_var.set(10)
            self.transparency_var.set(1.0)
            
            # Apply theme and save
            self.apply_theme()
            self.save_theme()
            
            messagebox.showinfo("Theme Reset", "Theme has been reset to default settings.")

    def on_key_entry_change(self, event):
        # Check for hotkey conflict when user manually types a key
        entered_key = self.key_var.get().lower()
        hotkey = self.hotkey_var.get().lower()
        if entered_key == hotkey and entered_key:
            # Show a subtle warning (not a blocking error since user might be typing)
            self.key_entry.config(style="Warning.TEntry")
            # Reset style after a short delay
            self.root.after(2000, lambda: self.key_entry.config(style="TEntry"))
        else:
            self.key_entry.config(style="TEntry")

    def on_hotkey_entry_change(self, event):
        # Check for hotkey conflict when user manually types a key
        entered_key = self.hotkey_var.get().lower()
        key_to_press = self.key_var.get().lower()
        if entered_key == key_to_press and entered_key:
            # Show a subtle warning (not a blocking error since user might be typing)
            self.hotkey_entry.config(style="Warning.TEntry")
            # Reset style after a short delay
            self.root.after(2000, lambda: self.hotkey_entry.config(style="TEntry"))
        else:
            self.hotkey_entry.config(style="TEntry")

    def on_auto_download_toggle(self):
        self.auto_download_update = self.auto_download_var.get()
        self.save_theme()

    def on_notif_type_change(self, event=None):
        self.notification_type = self.notif_type_var.get()
        self.save_theme()

    def choose_sound_file(self):
        filetypes = [("Audio Files", "*.wav *.mp3"), ("All Files", "*.*")]
        path = filedialog.askopenfilename(title="Select Sound File", filetypes=filetypes)
        if path:
            self.custom_sound_path = path
            self.sound_path_var.set(path)
            self.sound_label.config(text=os.path.basename(path))
            self.save_theme()

    def notify_press_limit(self):
        # Handle notification based on user settings
        if self.notification_type in ("sound", "both"):
            if self.custom_sound_path:
                try:
                    playsound(self.custom_sound_path, block=False)
                except Exception:
                    pass
            elif sys.platform == 'win32':
                try:
                    winsound.Beep(1000, 400)
                except Exception:
                    pass
        if self.notification_type in ("messagebox", "both"):
            try:
                messagebox.showinfo("Limit Reached", "The press limit has been reached.")
            except Exception:
                pass
        # If 'none', do nothing

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = KeyClicker()
    notify_if_update_gui(app.root)
    app.run() 
