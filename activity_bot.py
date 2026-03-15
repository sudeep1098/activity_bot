"""
Activity Bot - macOS Chrome Tab Switcher
===============================================
Features:
  - Switches Chrome tabs every 20 seconds using AppleScript
  - Opens target URLs if not already open
  - Scrolls pages after switching
  - Alphabet + space keystrokes only
  - Random mouse movement
  - Opens random files from a folder using Antigravity or VS Code (auto-detected)
  - Falls back to Chrome-only mode if neither IDE is installed

Setup:
    pip install pyautogui pynput

Run:
    python3 activity_bot.py

Controls:
    CTRL+C         = Quit
    Mouse TOP-LEFT = Emergency stop
"""

import pyautogui
import random
import time
import subprocess
import threading
import os

# ── Target URLs ────────────────────────────────
TARGET_URLS = [
    "https://local-admin.yardsignplus.com/",
    "https://local.yardsignplus.com/sign-riders/shop/yard-sign/SR00137",
    "https://local-admin.yardsignplus.com/warehouse/queue/printer/P1",
    "http://localhost/phpmyadmin/index.php?route=/&db=ysp_local&table=daily_cogs_report",
    "https://dev2-admin.yardsignplus.com/orders",
    "https://dev2-admin.yardsignplus.com/orders/2603595878/overview",
]

# ── IDE / Folder Config ────────────────────────
ANTIGRAVITY_APP   = "/Applications/Antigravity.app"
VSCODE_APP        = "/Applications/Visual Studio Code.app"
PROJECT_FOLDER    = "/Users/apple/Sites/yardsignplus"
IDE_OPEN_INTERVAL = 30          # seconds between file opens

# ── Config ─────────────────────────────────────
TAB_SWITCH_INTERVAL = 20        # seconds between tab switches
MOUSE_MOVE_INTERVAL = (2.0, 4.0)
MOVE_DURATION       = (0.4, 0.9)
SAFE_MARGINS        = 80
TYPE_INTERVAL       = 0.09
SCROLL_CHANCE       = 0.7

TYPING_WORDS = [
    "hello", "test", "sample", "random", "input",
    "data", "check", "work", "great", "nice",
    "done", "good", "yes", "okay", "fine",
]

# ── Globals ────────────────────────────────────
stop_event = threading.Event()
pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.05

# ── IDE Detection ──────────────────────────────
def detect_ide():
    """
    Returns (ide_name, app_path) for the first available IDE.
    Priority: Antigravity > VS Code > None (Chrome-only mode).
    """
    if os.path.isdir(ANTIGRAVITY_APP):
        print(f"  IDE Detect -> Antigravity found: {ANTIGRAVITY_APP}")
        return ("antigravity", ANTIGRAVITY_APP)
    elif os.path.isdir(VSCODE_APP):
        print(f"  IDE Detect -> VS Code found: {VSCODE_APP}")
        return ("vscode", VSCODE_APP)
    else:
        print("  IDE Detect -> No IDE found. Running in Chrome-only mode.")
        return (None, None)

IDE_NAME, IDE_PATH = detect_ide()

# ── AppleScript helpers ────────────────────────
def run_applescript(script):
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.stdout.strip()

def get_chrome_tab_urls():
    """Returns list of open tab URLs in Chrome window 1."""
    script = 'tell application "Google Chrome" to get URL of every tab of window 1'
    output = run_applescript(script)
    if not output:
        return []
    return [u.strip() for u in output.split(",")]

def open_url_in_new_tab(url):
    script = f'tell application "Google Chrome" to tell window 1 to make new tab with properties {{URL:"{url}"}}'
    run_applescript(script)
    time.sleep(1.5)
    print(f"  Chrome -> Opened new tab: {url[:55]}")

def switch_to_tab_index(index):
    """Switch Chrome to tab at 1-based index."""
    script = f'tell application "Google Chrome" to tell window 1 to set active tab index to {index}'
    run_applescript(script)
    run_applescript('tell application "Google Chrome" to activate')
    time.sleep(0.8)

def ensure_urls_open():
    """Open any target URLs that aren't already in Chrome."""
    print("  Chrome -> Checking target URLs are open...")
    open_tabs = get_chrome_tab_urls()
    print(f"  Chrome -> Found {len(open_tabs)} open tab(s)")
    for url in TARGET_URLS:
        already_open = any(url in tab or tab in url for tab in open_tabs)
        if not already_open:
            open_url_in_new_tab(url)
        else:
            print(f"  Chrome -> Already open: {url[:55]}")

def find_tab_index_for_url(url):
    """Find the 1-based tab index of a URL in Chrome window 1."""
    tabs = get_chrome_tab_urls()
    for i, tab in enumerate(tabs):
        if url in tab or tab in url:
            return i + 1
    return None

def switch_to_url(url):
    """Switch to a tab with the given URL, or open it if not found."""
    idx = find_tab_index_for_url(url)
    if idx:
        switch_to_tab_index(idx)
        print(f"  Chrome -> Switched to tab {idx}: {url[:50]}")
    else:
        print(f"  Chrome -> Not found, opening: {url[:50]}")
        open_url_in_new_tab(url)
        idx = find_tab_index_for_url(url)
        if idx:
            switch_to_tab_index(idx)

# ── File safety filter ─────────────────────────
BLOCKED_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development",
    ".env.staging", ".env.test", ".env.example", ".gitignore",
    ".htpasswd", "package-lock.json", "yarn.lock", "composer.lock",
    "Gemfile.lock", "Pipfile.lock", "poetry.lock", "pnpm-lock.yaml",
}

BLOCKED_EXTENSIONS = {
    ".env", ".pem", ".key", ".cert", ".crt", ".p12", ".pfx", ".der",
    ".lock",
    ".json", ".txt", ".xml", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".conf", ".config",
    ".log", ".sql", ".sqlite", ".db",
    ".zip", ".tar", ".gz", ".rar",
}

BLOCKED_FOLDERS = {
    "node_modules", ".git", ".svn", "__pycache__",
    ".cache", "dist", "build", ".next", ".nuxt",
    "vendor", "var", "public",
}

def is_safe_file(filename):
    """Returns True only if the file is safe to open in an IDE."""
    name_lower = filename.lower()
    if filename.startswith("."):
        return False
    if name_lower in {n.lower() for n in BLOCKED_NAMES}:
        return False
    _, ext = os.path.splitext(name_lower)
    if ext in BLOCKED_EXTENSIONS:
        return False
    return True

def get_random_file_from_folder(folder):
    """Returns a random SAFE file path from the folder (recursive, skips blocked dirs)."""
    try:
        files = []
        for dirpath, dirnames, filenames in os.walk(folder):
            dirnames[:] = [d for d in dirnames if d not in BLOCKED_FOLDERS and not d.startswith(".")]
            for f in filenames:
                if is_safe_file(f):
                    files.append(os.path.join(dirpath, f))
        if not files:
            print(f"  IDE -> No safe files found in {folder}")
            return None
        chosen = random.choice(files)
        rel = os.path.relpath(chosen, folder)
        print(f"  IDE -> {len(files)} safe file(s) available, picked: {rel}")
        return chosen
    except Exception as e:
        print(f"  IDE -> Error walking folder: {e}")
        return None

# ── IDE file opener ────────────────────────────
def open_file_with_ide(filepath):
    """Opens a file using the detected IDE (Antigravity or VS Code)."""
    if IDE_NAME == "antigravity":
        subprocess.Popen(["open", "-a", "Antigravity", filepath])
        print(f"  Antigravity -> Opened: {os.path.basename(filepath)}")
    elif IDE_NAME == "vscode":
        subprocess.Popen(["open", "-a", "Visual Studio Code", filepath])
        print(f"  VS Code -> Opened: {os.path.basename(filepath)}")
    else:
        print("  IDE -> No IDE available, skipping file open.")

def ide_loop():
    """
    Periodically opens a random project file in the available IDE.
    Skipped entirely if no IDE is detected (Chrome-only mode).
    """
    if IDE_NAME is None:
        print("[IDE LOOP] No IDE detected — IDE loop disabled.")
        return

    time.sleep(10)  # initial delay before first run
    while not stop_event.is_set():
        try:
            filepath = get_random_file_from_folder(PROJECT_FOLDER)
            if filepath:
                print(f"\n[IDE] Opening random file: {os.path.basename(filepath)}")
                open_file_with_ide(filepath)
        except Exception as e:
            print(f"[IDE ERROR] {e}")

        stop_event.wait(IDE_OPEN_INTERVAL)

# ── Tab switch thread ──────────────────────────
def tab_switch_loop():
    time.sleep(6)  # initial delay
    while not stop_event.is_set():
        try:
            url = random.choice(TARGET_URLS)
            print(f"\n[TAB] Switching to -> {url[:55]}")
            switch_to_url(url)

            time.sleep(0.5)
            for _ in range(random.randint(2, 4)):
                do_scroll()
                time.sleep(random.uniform(0.4, 0.9))

        except Exception as e:
            print(f"[TAB ERROR] {e}")

        stop_event.wait(TAB_SWITCH_INTERVAL)

# ── Mouse & keyboard ───────────────────────────
def do_move():
    w, h = pyautogui.size()
    x = random.randint(SAFE_MARGINS, w - SAFE_MARGINS)
    y = random.randint(SAFE_MARGINS, h - SAFE_MARGINS)
    pyautogui.moveTo(x, y, duration=random.uniform(*MOVE_DURATION))
    print(f"  Mouse  -> ({x}, {y})")

def do_scroll():
    amount = random.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    pyautogui.scroll(amount)
    direction = "up" if amount > 0 else "down"
    print(f"  Scroll -> [{direction} {abs(amount)}]")

def do_type():
    word = random.choice(TYPING_WORDS)
    pyautogui.typewrite(word, interval=TYPE_INTERVAL)
    print(f"  Type   -> \"{word}\"")

# ── Main bot loop ──────────────────────────────
def bot_loop():
    run_applescript('tell application "Google Chrome" to activate')
    time.sleep(1)
    ensure_urls_open()
    time.sleep(1)

    print("\n[BOT] Running...\n")
    cycle = 1
    while not stop_event.is_set():
        print(f"── Cycle {cycle} ─────────────────────────")
        try:
            do_move()

            if random.random() < SCROLL_CHANCE:
                do_scroll()

            if random.random() < 0.25:
                do_type()

        except pyautogui.FailSafeException:
            print("\n[FAILSAFE] Stopped.")
            stop_event.set()
            break
        except Exception as e:
            print(f"[ERROR] {e}")

        cycle += 1
        wait = random.uniform(*MOUSE_MOVE_INTERVAL)
        print(f"  ... next in {wait:.1f}s")
        stop_event.wait(wait)

    print("[BOT] Loop exited.")

# ── Main ───────────────────────────────────────
def main():
    ide_label = IDE_NAME.capitalize() if IDE_NAME else "None (Chrome-only mode)"

    print("=" * 58)
    print("   Activity Bot  v8.0  (AppleScript Tab Switcher)")
    print("=" * 58)
    print("  IDE detected     :", ide_label)
    print("  Tab switch every :", TAB_SWITCH_INTERVAL, "seconds")
    if IDE_NAME:
        print("  IDE open every   :", IDE_OPEN_INTERVAL, "seconds")
        print("  Project folder   :", PROJECT_FOLDER)
    print("  Rotating URLs    :")
    for u in TARGET_URLS:
        print(f"    {u}")
    print("  Keys             : alphabet + space only")
    print("  CTRL+C           : Quit")
    print("  Mouse TOP-LEFT   : Emergency stop")
    print("=" * 58)
    print("\n[BOT] Make sure Google Chrome is open!")
    print("[BOT] Starting in 4 seconds...\n")
    time.sleep(4)

    tab_thread = threading.Thread(target=tab_switch_loop, daemon=True)
    bot_thread = threading.Thread(target=bot_loop,        daemon=True)
    ide_thread = threading.Thread(target=ide_loop,        daemon=True)

    bot_thread.start()
    tab_thread.start()
    ide_thread.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[BOT] CTRL+C — Quitting...")
        stop_event.set()

    bot_thread.join(timeout=3)
    tab_thread.join(timeout=3)
    ide_thread.join(timeout=3)
    print("[BOT] Goodbye.")

if __name__ == "__main__":
    main()