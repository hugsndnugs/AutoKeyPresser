import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from pynput import keyboard
from pynput.keyboard import Key, Controller
import time
import threading
import sys
import pystray
from PIL import Image, ImageDraw
import os
import json

class KeyClicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Auto Key Clicker")
        
        # Initialize variables
        self.keyboard_controller = Controller()
        self.is_running = False
        self.click_thread = None
        self.tray_icon = None
        self.press_count = 0
        
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
            'F1': Key.f1,
            'F2': Key.f2,
            'F3': Key.f3,
            'F4': Key.f4,
            'F5': Key.f5,
            'F6': Key.f6,
            'F7': Key.f7,
            'F8': Key.f8,
            'F9': Key.f9,
            'F10': Key.f10,
            'F11': Key.f11,
            'F12': Key.f12
        }
        
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

    def save_theme(self):
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

    def on_special_key_selected(self, event):
        selected = self.special_key_var.get()
        if selected:
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
                    
                self.is_running = True
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
                if limit > 0 and self.press_count >= limit:
                    self.is_running = False
                    self.status_var.set("Status: Completed")
                    self.toggle_button.config(text="Start (F6)")
                    break
                    
                self.keyboard_controller.press(key_to_press)
                self.keyboard_controller.release(key_to_press)
                self.press_count += 1
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

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = KeyClicker()
    app.run() 