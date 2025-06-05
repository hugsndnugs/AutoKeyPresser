# Auto Key Clicker

A Python-based auto key clicker that simulates keyboard presses at customizable intervals. This tool includes a GUI interface and system tray support.

## Project Structure

```
AutoKeyClicker/
├── key_clicker.py      # Main application file
├── build.py           # Executable build script
├── requirements.txt   # Project dependencies
├── README.md         # Documentation
├── .gitignore        # Git ignore patterns
├── dist/             # Generated executable (ignored)
│   └── AutoKeyClicker.exe
└── build/            # Build artifacts (ignored)
```

## Features

- Simulate keyboard key presses at customizable intervals
- Support for both regular keys and special keys (enter, space, tab, arrow keys, etc.)
- GUI interface with dropdown for special keys
- System tray support with quick access menu
- Customizable hotkey (default: F6)
- Option to limit the number of key presses
- Real-time press counter
- Reset counter functionality
- Cross-platform support (Windows, macOS, Linux)
- Safety features to prevent system flooding

## Requirements

- Python 3.7 or higher
- Required Python packages (install using `pip install -r requirements.txt`):
  - pynput
  - Pillow
  - pystray
  - pyinstaller (for building executable)

## Installation

### Option 1: Using the Executable (Recommended for Windows Users)

1. Download the latest `AutoKeyClicker.exe` from the releases
2. Double-click to run the application
3. No Python installation required

### Option 2: Running from Source

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the script:
   ```bash
   python key_clicker.py
   ```

### Building the Executable

To build the executable yourself:

1. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the build script:
   ```bash
   python build.py
   ```

3. The executable will be created in the `dist` folder

## Usage

1. Launch the application (either the executable or Python script)

2. Configure the settings in the GUI:
   - Key to press: 
     - Enter a regular key (e.g., "a", "b", "1")
     - Or select a special key from the dropdown (e.g., "enter", "space", "tab")
   - Interval: Set the time between key presses in seconds (minimum 0.01s)
   - Hotkey: Choose a key to start/stop the clicking (default: F6)
   - Press limit: Set the number of times to press the key (0 for unlimited)

3. Click "Start" or press the configured hotkey to begin key pressing
4. The application can be minimized to the system tray
5. Use the system tray icon to:
   - Show/hide the main window
   - Start/stop the key pressing
   - Reset the press counter
   - Exit the application

## Special Keys Support

The application supports the following special keys:
- enter
- space
- tab
- backspace
- delete
- esc
- shift
- ctrl
- alt
- up/down/left/right arrow keys

## Safety Features

- Minimum interval of 0.01 seconds to prevent system flooding
- Easy to stop using the hotkey or system tray menu
- Error handling for invalid inputs
- Thread-safe implementation
- Real-time press counter to monitor activity

## Notes

- The application requires appropriate permissions to simulate keyboard input
- Some applications may block simulated key presses
- Use responsibly and in accordance with the terms of service of the applications you're using it with
- The press counter can be reset at any time through the system tray menu
- Windows users may need to run the executable as administrator for some applications 