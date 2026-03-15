# Activity Bot 🤖

A cross-platform automation bot that simulates human-like activity by rotating Chrome tabs, moving the mouse, clicking, scrolling, and opening project files in your IDE — keeping your machine looking active at all times.

Supports **macOS**, **Windows**, and **Linux**.

---

## What It Does

| Feature | Details |
|---|---|
| **Chrome tab switching** | Rotates through a list of target URLs every 20 seconds |
| **Auto tab opener** | Opens any missing target URLs once at startup — no duplicates |
| **Mouse movement** | Moves to random screen positions every 2–4 seconds |
| **Clicking** | Clicks randomly inside the page content area (50% chance per cycle) |
| **Page scrolling** | Scrolls up/down randomly (70% chance per cycle) |
| **Keyboard navigation** | Presses PageDown, PageUp, arrow keys, Home, End, Tab, F5 (40% chance) |
| **Typing simulation** | Occasionally types harmless words — alphabet + space only (20% chance) |
| **IDE file opener** | Opens random project files in your IDE every 30 seconds |

---

## IDE Detection (Auto)

The bot detects your IDE automatically at startup — no config needed:

```
Antigravity installed?  →  uses Antigravity
VS Code installed?      →  uses VS Code
Neither?                →  Chrome-only mode (tab switching + mouse + clicks only)
```

---

## Platform Support

| Feature | macOS | Windows | Linux |
|---|---|---|---|
| Chrome tab switching | AppleScript ✅ | Ctrl+number hotkeys ✅ | xdotool ✅ |
| Mouse movement & clicks | pyautogui ✅ | pyautogui ✅ | pyautogui ✅ |
| IDE: Antigravity | `open -a` ✅ | `.exe` direct ✅ | binary/PATH ✅ |
| IDE: VS Code | `open -a` ✅ | `.exe` / `code` ✅ | `code` on PATH ✅ |

> **Note:** On macOS, the bot reads actual Chrome tab URLs via AppleScript for precise switching.
> On Windows and Linux, the bot tracks URLs it opened itself and switches by tab position (Ctrl+1–8, then Ctrl+Tab).

---

## Requirements

- **Python 3.9+**
- **Google Chrome** (open before running)

| Platform | Python packages | System packages |
|---|---|---|
| macOS | `pyautogui` `pynput` `pyobjc` | — |
| Windows | `pyautogui` `pynput` `pywin32` | — |
| Linux | `pyautogui` `pynput` | `xdotool` `wmctrl` |

All installed automatically by the setup script.

Optional IDE (one of):
- [Antigravity IDE](https://antigravity.app)
- [Visual Studio Code](https://code.visualstudio.com)

---

## Quick Start

### macOS / Linux
```bash
git clone <your-repo-url>
cd activity
bash setup.sh
```

### Windows
```bat
git clone <your-repo-url>
cd activity
setup.bat
```

---

## Dynamic Project Folder

Pass a custom project folder at runtime without editing the script:

### Windows
```bat
:: Use hardcoded default (E:\yardsignplus)
setup.bat

:: Override with a different folder
setup.bat E:\myproject

:: Or run directly
python activity_bot.py --folder E:\myproject
python activity_bot.py -f E:\myproject
```

### macOS / Linux
```bash
# Use hardcoded default
bash setup.sh

# Override with a different folder
bash setup.sh /var/www/html/myproject

# Or run directly
python3 activity_bot.py --folder /var/www/html/myproject
python3 activity_bot.py -f /var/www/html/myproject
```

### Help
```bash
python3 activity_bot.py --help
```

---

## Configuration

Edit the top of `activity_bot.py` to change defaults:

```python
# URLs the bot will rotate through
TARGET_URLS = [
    "https://your-site.com/",
    ...
]

# Default project folder per platform (overridable via --folder at runtime)
_MAC_FOLDER = "/Users/apple/Sites/yardsignplus"
_WIN_FOLDER = r"E:\yardsignplus"
_LIN_FOLDER = "/var/www/html/yardsignplus"

# Timing
TAB_SWITCH_INTERVAL = 20        # seconds between tab switches
IDE_OPEN_INTERVAL   = 30        # seconds between IDE file opens
MOUSE_MOVE_INTERVAL = (2.0, 4.0)  # seconds between mouse move cycles

# Action probabilities (0.0 – 1.0 per cycle)
CLICK_CHANCE    = 0.5   # click inside page
SCROLL_CHANCE   = 0.7   # scroll up or down
KEYPRESS_CHANCE = 0.4   # navigation key press
TYPE_CHANCE     = 0.20  # type a random word
COPY_CHANCE     = 0.08  # Ctrl+A + Ctrl+C
```

IDE install paths (if in a non-standard location):
```python
_WIN_ANTIGRAVITY = r"C:\Program Files\Antigravity\Antigravity.exe"
_WIN_VSCODE      = r"C:\Program Files\Microsoft VS Code\Code.exe"
_LIN_VSCODE      = "/usr/bin/code"
```

---

## Controls

| Action | Effect |
|---|---|
| `CTRL+C` | Graceful quit |
| Move mouse to **top-left corner** | Emergency stop (PyAutoGUI failsafe) |

---

## Permissions

### macOS
> System Settings → Privacy & Security

| Permission | Required for |
|---|---|
| **Accessibility** | Mouse, keyboard & click control |
| **Automation → Google Chrome** | AppleScript tab switching |

### Windows
- Run as a **regular user** (not Administrator)
- Windows Defender may flag `pyautogui` — add the `activity` folder as an exclusion if needed
- Chrome must be open before the bot starts (or it will launch it automatically)

### Linux
- Requires a display (X11). Wayland may need `xwayland` for xdotool support
- Verify xdotool works: `xdotool getactivewindow`

---

## Project Structure

```
activity/
├── activity_bot.py   # Main bot (cross-platform)
├── setup.sh          # Setup & launcher — macOS / Linux
├── setup.bat         # Setup & launcher — Windows
├── .gitignore        # Git ignore rules
└── README.md         # This file
```

---

## File Safety

Files opened in the IDE are filtered — the following are **never** opened:

- `.env` files and secrets (`.pem`, `.key`, `.cert`, etc.)
- Lock files (`package-lock.json`, `composer.lock`, etc.)
- Config files (`.yaml`, `.toml`, `.ini`, etc.)
- Logs, databases, and archives
- Hidden files and dotfiles
- Dependency folders (`node_modules/`, `vendor/`, `.git/`, `dist/`, `build/`, etc.)