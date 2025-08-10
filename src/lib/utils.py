import os
import platform
import urllib.parse

from loguru import logger

from src.db.models import Onsen


def generate_google_maps_link(onsen: Onsen) -> str:
    """Generate a Google Maps link for an onsen."""
    if onsen.latitude is not None and onsen.longitude is not None:
        return f"https://maps.google.com/?q={onsen.latitude},{onsen.longitude}"
    elif onsen.address:
        # URL encode the address for Google Maps
        encoded_address = urllib.parse.quote(onsen.address)
        return f"https://maps.google.com/?q={encoded_address}"
    else:
        return "N/A"


def open_folder_dialog() -> str:
    """
    Open a folder selection dialog and return the selected path.
    Returns empty string if cancelled or failed.
    """
    system = platform.system().lower()

    if system == "darwin":  # macOS
        try:
            # Try using osascript (AppleScript) for native folder selection
            import subprocess

            script = """
            tell application "System Events"
                activate
                set folderPath to choose folder with prompt "Select backup folder"
                return POSIX path of folderPath
            end tell
            """

            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.warning(
                    "AppleScript folder selection failed, falling back to manual input"
                )
                return ""

        except Exception as e:
            logger.warning(f"AppleScript folder selection failed: {e}")
            return ""

    elif system == "windows":
        try:
            import tkinter as tk
            from tkinter import filedialog

            # Create a hidden root window
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            # Open folder selection dialog
            folder_path = filedialog.askdirectory(
                title="Select backup folder", initialdir=os.path.expanduser("~")
            )

            root.destroy()
            return folder_path if folder_path else ""

        except ImportError:
            logger.warning(
                "tkinter not available on Windows, falling back to manual input"
            )
            return ""
        except Exception as e:
            logger.warning(f"Failed to open folder dialog on Windows: {e}")
            return ""

    else:  # Linux and other Unix-like systems
        try:
            import tkinter as tk
            from tkinter import filedialog

            # Create a hidden root window
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            # Open folder selection dialog
            folder_path = filedialog.askdirectory(
                title="Select backup folder", initialdir=os.path.expanduser("~")
            )

            root.destroy()
            return folder_path if folder_path else ""

        except ImportError:
            logger.warning(
                "tkinter not available on Linux, falling back to manual input"
            )
            return ""
        except Exception as e:
            logger.warning(f"Failed to open folder dialog on Linux: {e}")
            return ""
