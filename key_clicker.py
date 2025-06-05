import tkinter as tk
from tkinter import ttk, messagebox
from pynput import keyboard
from pynput.keyboard import Key, Controller
import time
import threading
import sys
import pystray
from PIL import Image, ImageDraw
import os

class KeyClicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Auto Key Clicker")
        self.root.geometry("400x500")  # Increased height for new features
        self.root.resizable(False, False)
        
        # Initialize variables
        self.keyboard_controller = Controller()
        self.is_running = False
        self.click_thread = None
        self.tray_icon = None
        self.press_count = 0
        
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
            'right': Key.right
        }
        
        # Create GUI elements
        self.create_gui()
        
        # Set up keyboard listener for hotkey
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
        
        # Create tray icon
        self.create_tray_icon()
        
        # Protocol for window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_gui(self):
        # Key selection with dropdown
        ttk.Label(self.root, text="Key to press:").pack(pady=5)
        self.key_var = tk.StringVar(value="a")
        self.key_frame = ttk.Frame(self.root)
        self.key_frame.pack(pady=5)
        
        self.key_entry = ttk.Entry(self.key_frame, textvariable=self.key_var, width=10)
        self.key_entry.pack(side=tk.LEFT, padx=5)
        
        # Add special keys dropdown
        self.special_key_var = tk.StringVar(value="")
        self.special_key_combo = ttk.Combobox(self.key_frame, textvariable=self.special_key_var, 
                                            values=list(self.special_keys.keys()), width=10)
        self.special_key_combo.pack(side=tk.LEFT, padx=5)
        self.special_key_combo.bind('<<ComboboxSelected>>', self.on_special_key_selected)
        
        # Interval selection
        ttk.Label(self.root, text="Interval (seconds):").pack(pady=5)
        self.interval_var = tk.StringVar(value="1.0")
        self.interval_entry = ttk.Entry(self.root, textvariable=self.interval_var, width=10)
        self.interval_entry.pack(pady=5)
        
        # Hotkey selection
        ttk.Label(self.root, text="Hotkey (F6):").pack(pady=5)
        self.hotkey_var = tk.StringVar(value="F6")
        self.hotkey_entry = ttk.Entry(self.root, textvariable=self.hotkey_var, width=10)
        self.hotkey_entry.pack(pady=5)
        
        # Press limit
        ttk.Label(self.root, text="Press limit (0 for unlimited):").pack(pady=5)
        self.limit_var = tk.StringVar(value="0")
        self.limit_entry = ttk.Entry(self.root, textvariable=self.limit_var, width=10)
        self.limit_entry.pack(pady=5)
        
        # Press counter
        self.counter_var = tk.StringVar(value="Presses: 0")
        self.counter_label = ttk.Label(self.root, textvariable=self.counter_var)
        self.counter_label.pack(pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Status: Stopped")
        self.status_label = ttk.Label(self.root, textvariable=self.status_var)
        self.status_label.pack(pady=5)
        
        # Start/Stop button
        self.toggle_button = ttk.Button(self.root, text="Start (F6)", command=self.toggle_clicking)
        self.toggle_button.pack(pady=10)
        
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
            self.listener.join(timeout=1.0)
        
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
            
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = KeyClicker()
    app.run() 