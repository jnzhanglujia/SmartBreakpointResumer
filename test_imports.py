import sys
import os
try:
    import win32gui
    import win32con
    import win32clipboard
    from pynput import keyboard, mouse
    from plyer import notification
    from PIL import ImageGrab
    with open("pythonw_test.log","w") as f:
        f.write("All imports OK\n")
        f.write(f"Python: {sys.executable}\n")
except Exception as e:
    with open("pythonw_test.log","w") as f:
        f.write(f"Error: {e}\n")
