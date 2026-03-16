"""
Activity Bot - Cross-Platform Chrome Tab Switcher
===================================================
Platforms : macOS, Windows, Linux
Features  :
  - Switches Chrome tabs every 20 seconds
    macOS   -> AppleScript
    Windows -> pywin32 (win32gui / win32con)
    Linux   -> xdotool
  - Opens target URLs ONCE at startup (no duplicates)
  - Scrolls pages after switching
  - Types only words from TYPING_WORDS (a-z letters, no special keys)
  - Random mouse movement
  - Opens random project files in detected IDE every 30 seconds
    IDE priority: Antigravity > VS Code > Chrome-only mode

Setup:
    pip install pyautogui pynput
    # Windows only:
    pip install pywin32
    # Linux only (also run):
    sudo apt install xdotool wmctrl

Run:
    python3 activity_bot.py   (macOS / Linux)
    python  activity_bot.py   (Windows)

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
import sys
import shutil
import argparse

# ── Platform detection ─────────────────────────
PLATFORM = sys.platform  # "darwin" | "win32" | "linux"
IS_MAC     = PLATFORM == "darwin"
IS_WINDOWS = PLATFORM == "win32"
IS_LINUX   = PLATFORM.startswith("linux")

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
_MAC_ANTIGRAVITY = "/Applications/Antigravity.app"
_MAC_VSCODE      = "/Applications/Visual Studio Code.app"
_MAC_FOLDER      = "/Users/apple/Sites/yardsignplus"

_WIN_ANTIGRAVITY = r"C:\Program Files\Antigravity\Antigravity.exe"
_WIN_VSCODE      = r"C:\Program Files\Microsoft VS Code\Code.exe"
_WIN_FOLDER      = r"E:\yardsignplus"

_LIN_ANTIGRAVITY = "/usr/local/bin/antigravity"
_LIN_VSCODE      = "/usr/bin/code"
_LIN_FOLDER      = "/var/www/html/yardsignplus"

IDE_OPEN_INTERVAL = 30

# ── Config ─────────────────────────────────────
TAB_SWITCH_INTERVAL = 20
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

# ── Windows tab registry ───────────────────────
_win_tab_registry = []
_win_cdp_available = False

# ══════════════════════════════════════════════
#   PLATFORM HELPERS
# ══════════════════════════════════════════════

# ── macOS: AppleScript ─────────────────────────
def _mac_run_applescript(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.stdout.strip()

def _mac_get_tab_urls():
    out = _mac_run_applescript(
        'tell application "Google Chrome" to get URL of every tab of window 1'
    )
    return [u.strip() for u in out.split(",")] if out else []

def _mac_open_tab(url):
    _mac_run_applescript(
        f'tell application "Google Chrome" to tell window 1 '
        f'to make new tab with properties {{URL:"{url}"}}'
    )
    time.sleep(1.5)

def _mac_switch_tab(index):
    _mac_run_applescript(
        f'tell application "Google Chrome" to tell window 1 '
        f'to set active tab index to {index}'
    )
    _mac_run_applescript('tell application "Google Chrome" to activate')
    time.sleep(0.8)

def _mac_focus_chrome():
    _mac_run_applescript('tell application "Google Chrome" to activate')

# ── Windows: pywin32 ───────────────────────────
def _win_get_chrome_hwnd():
    try:
        import win32gui
        hwnds = []
        def cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                if "Google Chrome" in win32gui.GetWindowText(hwnd):
                    hwnds.append(hwnd)
        win32gui.EnumWindows(cb, None)
        return hwnds[0] if hwnds else None
    except ImportError:
        return None

def _win_focus_chrome():
    try:
        import win32gui, win32con, win32process, ctypes
        hwnd = _win_get_chrome_hwnd()
        if not hwnd:
            print("  Chrome -> Not running, launching...")
            subprocess.Popen(["start", "chrome"], shell=True)
            time.sleep(3)
            hwnd = _win_get_chrome_hwnd()
        if hwnd:
            try:
                ctypes.windll.user32.AllowSetForegroundWindow(
                    win32process.GetWindowThreadProcessId(hwnd)[1]
                )
            except Exception:
                pass
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.2)
            try:
                ctypes.windll.user32.BringWindowToTop(hwnd)
            except Exception:
                pass
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.5)
    except Exception as e:
        print(f"  Chrome -> Focus warning (non-fatal): {e}")

def _win_open_tab(url):
    """Open a new Chrome tab and type the URL using pynput (no clipboard)."""
    _win_focus_chrome()
    pyautogui.hotkey("ctrl", "t")
    time.sleep(0.6)
    from pynput.keyboard import Controller as KbController
    kb = KbController()
    for ch in url:
        kb.type(ch)
        time.sleep(0.02)
    pyautogui.press("enter")
    time.sleep(2.0)
    print(f"  Chrome -> Opened new tab: {url[:55]}")

def _win_switch_tab(index):
    _win_focus_chrome()
    if index <= 8:
        pyautogui.hotkey("ctrl", str(index))
    else:
        pyautogui.hotkey("ctrl", "1")
        time.sleep(0.2)
        for _ in range(index - 1):
            pyautogui.hotkey("ctrl", "tab")
            time.sleep(0.15)
    time.sleep(0.6)

def _win_read_chrome_tabs_via_cdp(port=9222):
    try:
        import urllib.request, json
        url = f"http://127.0.0.1:{port}/json"
        with urllib.request.urlopen(url, timeout=2) as resp:
            tabs = json.loads(resp.read().decode())
        return [t["url"] for t in tabs if t.get("type") == "page" and t.get("url")]
    except Exception:
        return []

def _win_get_tab_urls():
    return list(_win_tab_registry)

def _win_init_tab_registry():
    global _win_cdp_available
    cdp_tabs = _win_read_chrome_tabs_via_cdp()
    if cdp_tabs:
        _win_cdp_available = True
        for url in cdp_tabs:
            if url not in _win_tab_registry:
                _win_tab_registry.append(url)
        print(f"  Chrome -> CDP: read {len(cdp_tabs)} existing tab(s) from Chrome")
    else:
        _win_cdp_available = False
        print("  Chrome -> CDP unavailable — will track only bot-opened tabs")
        print("  Chrome -> Tip: launch Chrome with --remote-debugging-port=9222 to read existing tabs")

# ── Linux: xdotool ────────────────────────────
def _lin_get_chrome_wid():
    r = subprocess.run(["xdotool", "search", "--name", "Google Chrome"],
                       capture_output=True, text=True)
    ids = r.stdout.strip().splitlines()
    return ids[-1] if ids else None

def _lin_focus_chrome():
    wid = _lin_get_chrome_wid()
    if wid:
        subprocess.run(["xdotool", "windowactivate", "--sync", wid])
        time.sleep(0.3)

def _lin_open_tab(url):
    _lin_focus_chrome()
    pyautogui.hotkey("ctrl", "t")
    time.sleep(0.5)
    from pynput.keyboard import Controller as KbController
    kb = KbController()
    for ch in url:
        kb.type(ch)
        time.sleep(0.02)
    pyautogui.press("enter")
    time.sleep(1.5)
    print(f"  Chrome -> Opened new tab: {url[:55]}")

def _lin_switch_tab(index):
    _lin_focus_chrome()
    if index <= 8:
        pyautogui.hotkey("ctrl", str(index))
    else:
        pyautogui.hotkey("ctrl", "1")
        time.sleep(0.2)
        for _ in range(index - 1):
            pyautogui.hotkey("ctrl", "tab")
            time.sleep(0.15)
    time.sleep(0.6)

_lin_tab_registry = []

def _lin_get_tab_urls():
    return list(_lin_tab_registry)

# ══════════════════════════════════════════════
#   UNIFIED CHROME API
# ══════════════════════════════════════════════

def focus_chrome():
    if IS_MAC:       _mac_focus_chrome()
    elif IS_WINDOWS: _win_focus_chrome()
    elif IS_LINUX:   _lin_focus_chrome()

def get_tab_urls():
    if IS_MAC:       return _mac_get_tab_urls()
    elif IS_WINDOWS: return _win_get_tab_urls()
    elif IS_LINUX:   return _lin_get_tab_urls()
    return []

def open_url_in_new_tab(url):
    if IS_MAC:
        _mac_open_tab(url)
    elif IS_WINDOWS:
        _win_open_tab(url)
        _win_tab_registry.append(url)
    elif IS_LINUX:
        _lin_open_tab(url)
        _lin_tab_registry.append(url)

def switch_to_tab_index(index):
    if IS_MAC:       _mac_switch_tab(index)
    elif IS_WINDOWS: _win_switch_tab(index)
    elif IS_LINUX:   _lin_switch_tab(index)

def ensure_urls_open():
    """Open target URLs that are not yet open. Called ONCE at startup."""
    print("  Chrome -> Checking target URLs are open...")
    focus_chrome()
    time.sleep(0.8)

    if IS_WINDOWS:
        _win_init_tab_registry()

    open_tabs = get_tab_urls()
    print(f"  Chrome -> {len(open_tabs)} tab(s) already tracked")
    for url in TARGET_URLS:
        already_open = any(url in tab or tab in url for tab in open_tabs)
        if not already_open:
            open_url_in_new_tab(url)
        else:
            print(f"  Chrome -> Already open: {url[:55]}")

def find_tab_index_for_url(url):
    """Return 1-based index of url in the tab list."""
    tabs = get_tab_urls()
    for i, tab in enumerate(tabs):
        if url in tab or tab in url:
            return i + 1
    return None

def switch_to_url(url):
    idx = find_tab_index_for_url(url)
    if idx:
        switch_to_tab_index(idx)
        print(f"  Chrome -> Switched to tab {idx}: {url[:50]}")
    else:
        print(f"  Chrome -> Tab missing, reopening: {url[:50]}")
        open_url_in_new_tab(url)
        idx = find_tab_index_for_url(url)
        if idx:
            switch_to_tab_index(idx)

# ══════════════════════════════════════════════
#   IDE DETECTION
# ══════════════════════════════════════════════

def detect_ide():
    """Returns (ide_name, launch_cmd) for the first available IDE."""
    if IS_MAC:
        if os.path.isdir(_MAC_ANTIGRAVITY):
            print("  IDE Detect -> Antigravity (macOS)")
            return ("antigravity", ["open", "-a", "Antigravity"])
        elif os.path.isdir(_MAC_VSCODE):
            print("  IDE Detect -> VS Code (macOS)")
            return ("vscode", ["open", "-a", "Visual Studio Code"])

    elif IS_WINDOWS:
        if os.path.isfile(_WIN_ANTIGRAVITY):
            print("  IDE Detect -> Antigravity (Windows)")
            return ("antigravity", [_WIN_ANTIGRAVITY])
        vscode_paths = [
            _WIN_VSCODE,
            os.path.join(os.environ.get("LOCALAPPDATA", ""),
                         "Programs", "Microsoft VS Code", "Code.exe"),
        ]
        for p in vscode_paths:
            if os.path.isfile(p):
                print(f"  IDE Detect -> VS Code (Windows): {p}")
                return ("vscode", [p])
        code_cmd = shutil.which("code") or shutil.which("code.cmd")
        if code_cmd:
            print(f"  IDE Detect -> VS Code on PATH: {code_cmd}")
            return ("vscode", [code_cmd])

    elif IS_LINUX:
        if os.path.isfile(_LIN_ANTIGRAVITY) or shutil.which("antigravity"):
            cmd = shutil.which("antigravity") or _LIN_ANTIGRAVITY
            print(f"  IDE Detect -> Antigravity (Linux): {cmd}")
            return ("antigravity", [cmd])
        code_cmd = shutil.which("code") or (os.path.isfile(_LIN_VSCODE) and _LIN_VSCODE)
        if code_cmd:
            print(f"  IDE Detect -> VS Code (Linux): {code_cmd}")
            return ("vscode", [code_cmd])

    print("  IDE Detect -> No IDE found. Chrome-only mode.")
    return (None, None)

def get_project_folder():
    if IS_MAC:       return _MAC_FOLDER
    elif IS_WINDOWS: return _WIN_FOLDER
    elif IS_LINUX:   return _LIN_FOLDER
    return os.path.expanduser("~/project")

IDE_NAME, IDE_CMD = detect_ide()

# ── CLI argument parsing ───────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Activity Bot - Cross-Platform Chrome Tab Switcher",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--folder", "-f",
        metavar="PATH",
        default=None,
        help=(
            "Project folder for IDE file opens.\n"
            "Defaults per platform:\n"
            f"  macOS  : {_MAC_FOLDER}\n"
            f"  Windows: {_WIN_FOLDER}\n"
            f"  Linux  : {_LIN_FOLDER}"
        )
    )
    return parser.parse_args()

_args = parse_args()

def _normalize_folder(path):
    if path is None:
        return None
    path = path.strip()
    if IS_WINDOWS:
        import re
        path = re.sub(r'^([A-Za-z]:)([^\\])', r'\1\\\2', path)
    return os.path.normpath(path)

PROJECT_FOLDER = _normalize_folder(_args.folder) if _args.folder else get_project_folder()

# ══════════════════════════════════════════════
#   FILE SAFETY FILTER
# ══════════════════════════════════════════════

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
    "vendor", "var", "public/bundles", "public/build",
}

def is_safe_file(filename):
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
    try:
        files = []
        for dirpath, dirnames, filenames in os.walk(folder):
            dirnames[:] = [
                d for d in dirnames
                if d not in BLOCKED_FOLDERS and not d.startswith(".")
            ]
            for f in filenames:
                if is_safe_file(f):
                    files.append(os.path.join(dirpath, f))
        if not files:
            print(f"  IDE -> No safe files found in {folder}")
            return None
        chosen = random.choice(files)
        rel = os.path.relpath(chosen, folder)
        print(f"  IDE -> {len(files)} safe file(s) found, picked: {rel}")
        return chosen
    except Exception as e:
        print(f"  IDE -> Error walking folder: {e}")
        return None

# ══════════════════════════════════════════════
#   IDE OPENER
# ══════════════════════════════════════════════

def open_file_with_ide(filepath):
    if IDE_CMD is None:
        return
    try:
        if IDE_NAME == "vscode":
            cmd = IDE_CMD + ["--reuse-window", filepath]
        else:
            cmd = IDE_CMD + [filepath]

        if IS_WINDOWS:
            import subprocess as _sp
            _sp.Popen(cmd, shell=False,
                      creationflags=_sp.CREATE_NO_WINDOW if hasattr(_sp, "CREATE_NO_WINDOW") else 0)
        else:
            subprocess.Popen(cmd)

        print(f"  {IDE_NAME.capitalize()} -> Opened: {os.path.basename(filepath)}")
    except FileNotFoundError as e:
        print(f"  IDE -> Launch failed ({e}). Check IDE path in config.")
    except Exception as e:
        print(f"  IDE -> Error: {e}")

def ide_loop():
    if IDE_NAME is None:
        print("[IDE LOOP] No IDE detected — disabled.")
        return
    time.sleep(10)
    while not stop_event.is_set():
        try:
            filepath = get_random_file_from_folder(PROJECT_FOLDER)
            if filepath:
                print(f"\n[IDE] Opening random file: {os.path.basename(filepath)}")
                open_file_with_ide(filepath)
        except Exception as e:
            print(f"[IDE ERROR] {e}")
        stop_event.wait(IDE_OPEN_INTERVAL)

# ══════════════════════════════════════════════
#   TAB SWITCH LOOP
# ══════════════════════════════════════════════

def tab_switch_loop():
    time.sleep(6)
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

# ══════════════════════════════════════════════
#   MOUSE & KEYBOARD
# ══════════════════════════════════════════════

# Safe navigation keys per platform.
# macOS excludes f5 (triggers fn layer) and home/end (act as Cmd+Left/Right).
_MAC_BROWSE_KEYS = [
    "pagedown", "pageup",
    "down", "down", "down",   # weighted toward scrolling down
    "up",
    "tab",
]
_OTHER_BROWSE_KEYS = [
    "pagedown", "pageup",
    "down", "down", "down",
    "up",
    "end", "home",
    "tab",
    "f5",
]

def do_move():
    """Move mouse to a random safe position."""
    w, h = pyautogui.size()
    x = random.randint(SAFE_MARGINS, w - SAFE_MARGINS)
    y = random.randint(SAFE_MARGINS, h - SAFE_MARGINS)
    pyautogui.moveTo(x, y, duration=random.uniform(*MOVE_DURATION))
    print(f"  Mouse  -> ({x}, {y})")

def do_scroll():
    """Scroll the page up or down."""
    amount = random.choice([-5, -4, -3, -2, 2, 3, 4, 5])
    pyautogui.scroll(amount)
    direction = "up" if amount > 0 else "down"
    print(f"  Scroll -> [{direction} {abs(amount)}]")

def do_type():
    """
    Type a random word from TYPING_WORDS one character at a time using pynput.
    pynput.keyboard.Controller.type() sends each character as a direct Unicode
    input event — it does NOT simulate key codes, so fn / modifier keys are
    never triggered on macOS or any other platform.
    Only plain a-z letters from TYPING_WORDS are ever sent.
    """
    from pynput.keyboard import Controller as KbController
    word = random.choice(TYPING_WORDS)
    kb = KbController()
    for ch in word:
        kb.type(ch)
        time.sleep(TYPE_INTERVAL)
    print(f"  Type   -> \"{word}\"")

def do_keypress():
    """Press a safe navigation key."""
    keys = _MAC_BROWSE_KEYS if IS_MAC else _OTHER_BROWSE_KEYS
    key = random.choice(keys)
    pyautogui.press(key)
    print(f"  Key    -> [{key}]")

# ══════════════════════════════════════════════
#   MAIN BOT LOOP
# ══════════════════════════════════════════════

KEYPRESS_CHANCE = 0.4
TYPE_CHANCE     = 0.25

def bot_loop():
    focus_chrome()
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

            if random.random() < KEYPRESS_CHANCE:
                do_keypress()

            if random.random() < TYPE_CHANCE:
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

# ══════════════════════════════════════════════
#   MAIN
# ══════════════════════════════════════════════

def main():
    platform_label = {"darwin": "macOS", "win32": "Windows"}.get(PLATFORM, "Linux")
    ide_label      = IDE_NAME.capitalize() if IDE_NAME else "None (Chrome-only mode)"

    print("=" * 58)
    print("   Activity Bot  v9.7  (Cross-Platform)")
    print("=" * 58)
    print("  Platform         :", platform_label)
    print("  IDE detected     :", ide_label)
    print("  Tab switch every :", TAB_SWITCH_INTERVAL, "seconds")
    if IDE_NAME:
        print("  IDE open every   :", IDE_OPEN_INTERVAL, "seconds")
        print("  Project folder   :", PROJECT_FOLDER)
    print("  Rotating URLs    :")
    for u in TARGET_URLS:
        print(f"    {u}")
    folder_source = f"(--folder {PROJECT_FOLDER})" if _args.folder else "(default)"
    print(f"  Project folder   : {PROJECT_FOLDER} {folder_source}")
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
        print("\n[BOT] CTRL+C -- Quitting...")
        stop_event.set()

    bot_thread.join(timeout=3)
    tab_thread.join(timeout=3)
    ide_thread.join(timeout=3)
    print("[BOT] Goodbye.")

if __name__ == "__main__":
    main()