import PyInstaller.__main__
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the icon path (we'll create a simple icon)
icon_path = os.path.join(current_dir, 'icon.ico')

# Create a simple icon if it doesn't exist
if not os.path.exists(icon_path):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (256, 256), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([64, 64, 192, 192], fill='black')
    img.save(icon_path)

# PyInstaller arguments
args = [
    'key_clicker.py',  # Your main script
    '--name=AutoKeyClicker',  # Name of the executable
    '--onefile',  # Create a single executable file
    '--windowed',  # Don't show console window
    f'--icon={icon_path}',  # Icon for the executable
    '--add-data=README.md;.',  # Include README
    '--clean',  # Clean PyInstaller cache
    '--noconfirm',  # Replace existing build without asking
]

# Run PyInstaller
PyInstaller.__main__.run(args) 