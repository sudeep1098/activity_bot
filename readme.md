# Activity Bot 🤖

A macOS automation bot that simulates human-like activity by rotating Chrome tabs, moving the mouse, scrolling pages, and opening project files in your IDE — keeping your machine looking active at all times.

---

## What It Does

| Feature | Details |
|---|---|
| **Chrome tab switching** | Rotates through a list of target URLs every 20 seconds |
| **Auto tab opener** | Opens any missing target URLs automatically on startup |
| **Page scrolling** | Scrolls up/down after each tab switch |
| **Mouse movement** | Moves the mouse to random positions every 2–4 seconds |
| **Typing simulation** | Occasionally types harmless words (alphabet + space only) |
| **IDE file opener** | Opens random project files in your IDE every 30 seconds |

---

## IDE Detection (Auto)

The bot detects your IDE automatically at startup — no config needed:

```
Antigravity installed?  →  uses Antigravity
VS Code installed?      →  uses VS Code
Neither?                →  Chrome-only mode (tab switching + mouse only)
```

---

## Requirements

- macOS (uses AppleScript for Chrome control)
- Google Chrome
- Python 3.9+
- `pyautogui`, `pynput`, `pyobjc` (installed automatically by `setup.sh`)

Optional (one of):
- [Antigravity IDE](https://antigravity.app)
- [Visual Studio Code](https://code.visualstudio.com)

---

## Quick Start

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd activity

# 2. Run the setup script (installs deps and launches the bot)
bash setup.sh
```

The setup script will:
1. Check for Xcode CLI tools and Homebrew
2. Install Python 3 if missing
3. Create a virtual environment
4. Detect your IDE (Antigravity → VS Code → Chrome-only)
5. Install Python dependencies
6. Launch the bot

---

## Configuration

Edit the top of `activity_bot.py` to customise behaviour:

```python
# URLs the bot will rotate through
TARGET_URLS = [
    "https://your-site.com/",
    ...
]

# Path to your project folder (for IDE file opens)
PROJECT_FOLDER = "/Users/you/Sites/myproject"

# Timing
TAB_SWITCH_INTERVAL = 20   # seconds between tab switches
IDE_OPEN_INTERVAL   = 30   # seconds between IDE file opens
MOUSE_MOVE_INTERVAL = (2.0, 4.0)  # seconds between mouse moves
```

---

## Controls

| Action | Effect |
|---|---|
| `CTRL+C` | Graceful quit |
| Move mouse to **top-left corner** | Emergency stop (PyAutoGUI failsafe) |

---

## macOS Permissions

On first run, macOS may prompt for permissions. You can grant them in:

**System Settings → Privacy & Security**

| Permission | Required for |
|---|---|
| **Accessibility** | Mouse & keyboard control |
| **Automation → Google Chrome** | AppleScript tab switching |

---

## Project Structure

```
activity/
├── activity_bot.py   # Main bot script
├── setup.sh          # One-command setup & launcher
├── .gitignore        # Git ignore rules
├── README.md         # This file
└── venv/             # Python virtual environment (git-ignored)
```

---

## Safety

Files opened in the IDE are filtered to avoid sensitive content. The following are **never** opened:

- `.env` files and secrets (`.pem`, `.key`, `.cert`, etc.)
- Lock files (`package-lock.json`, `composer.lock`, etc.)
- Config files (`.yaml`, `.toml`, `.ini`, etc.)
- Logs, databases, and archives
- Hidden files and dotfiles
- Dependency folders (`node_modules/`, `vendor/`, `.git/`, etc.)