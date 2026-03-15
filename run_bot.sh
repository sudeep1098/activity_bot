#!/bin/bash
# ============================================================
#   Activity Bot - Full Setup & Run Script (macOS)
#   IDE Priority: Antigravity > VS Code > Chrome-only mode
# ============================================================

set -e

PROJECT_DIR="/Users/apple/Sites/activity"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[✔]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✘]${NC} $1"; exit 1; }
section() { echo -e "\n${YELLOW}══ $1 ══${NC}"; }

# ── 1. Xcode Command Line Tools ────────────────────────────
section "Xcode Command Line Tools"
if ! xcode-select -p &>/dev/null; then
    warn "Installing Xcode Command Line Tools..."
    xcode-select --install
    echo "  -> Follow the popup to install, then re-run this script."
    exit 0
else
    info "Xcode CLI tools already installed"
fi

# ── 2. Homebrew ────────────────────────────────────────────
section "Homebrew"
if ! command -v brew &>/dev/null; then
    warn "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    elif [[ -f "/usr/local/bin/brew" ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    info "Homebrew installed"
else
    info "Homebrew already installed ($(brew --version | head -1))"
fi

# ── 3. Python 3 ────────────────────────────────────────────
section "Python 3"
if ! command -v python3 &>/dev/null; then
    warn "python3 not found — installing via Homebrew..."
    brew install python3
    info "Python 3 installed"
else
    PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    info "Python $PYVER already installed"
fi

# ── 4. pip ─────────────────────────────────────────────────
section "pip"
if ! python3 -m pip --version &>/dev/null; then
    warn "pip not found — installing..."
    python3 -m ensurepip --upgrade || brew install python3
    info "pip installed"
else
    info "pip already installed"
fi

# ── 5. Project directory ───────────────────────────────────
section "Project Directory"
mkdir -p "$PROJECT_DIR"
info "Project dir ready: $PROJECT_DIR"

# ── 6. Virtual environment ─────────────────────────────────
section "Virtual Environment"
if [[ ! -d "$PROJECT_DIR/venv" ]]; then
    warn "Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
    info "venv created"
else
    info "venv already exists"
fi

source "$PROJECT_DIR/venv/bin/activate"
info "venv activated ($(python3 --version))"
pip install --upgrade pip --quiet

# ── 7. IDE Detection ───────────────────────────────────────
section "IDE Detection"

IDE_NAME=""
IDE_PATH=""

if [[ -d "/Applications/Antigravity.app" ]]; then
    info "Antigravity IDE found — will use Antigravity for file opens"
    IDE_NAME="Antigravity"
    IDE_PATH="/Applications/Antigravity.app"
elif [[ -d "/Applications/Visual Studio Code.app" ]]; then
    info "VS Code found — will use VS Code for file opens"
    IDE_NAME="VS Code"
    IDE_PATH="/Applications/Visual Studio Code.app"
else
    warn "No IDE found (Antigravity or VS Code)"
    echo "  -> Bot will run in Chrome-only mode (tab switching + mouse only)"
    echo "  -> To enable IDE features, install one of:"
    echo "       Antigravity: https://antigravity.app"
    echo "       VS Code:     https://code.visualstudio.com"
fi

# ── 8. Python dependencies ─────────────────────────────────
section "Python Dependencies"

PACKAGES=("pyautogui" "pynput")
for pkg in "${PACKAGES[@]}"; do
    if python3 -c "import ${pkg//-/_}" &>/dev/null 2>&1; then
        info "$pkg already installed"
    else
        warn "Installing $pkg..."
        pip install "$pkg" --quiet
        info "$pkg installed"
    fi
done

if ! python3 -c "import AppKit" &>/dev/null 2>&1; then
    warn "Installing pyobjc (required by pyautogui on macOS)..."
    pip install pyobjc --quiet
    info "pyobjc installed"
else
    info "pyobjc already installed"
fi

# ── 9. macOS Permissions reminder ─────────────────────────
section "macOS Permissions Check"
echo ""
echo "  pyautogui needs Accessibility access to control mouse/keyboard."
echo "  If the bot seems stuck or throws permission errors:"
echo ""
echo "    System Settings → Privacy & Security → Accessibility"
echo "    → Add Terminal (or your terminal app) ✔"
echo ""
echo "  Also for AppleScript / Chrome control:"
echo "    System Settings → Privacy & Security → Automation"
echo "    → Terminal → Google Chrome ✔"
echo ""

# ── 10. Check activity_bot.py exists ──────────────────────
section "Bot Script"
if [[ ! -f "$PROJECT_DIR/activity_bot.py" ]]; then
    error "activity_bot.py not found in $PROJECT_DIR — please place it there first!"
fi
info "activity_bot.py found"

# ── 11. Summary & Launch ───────────────────────────────────
section "Summary"
echo ""
echo "  IDE Mode    : ${IDE_NAME:-Chrome-only (no IDE found)}"
[[ -n "$IDE_NAME" ]] && echo "  IDE Path    : $IDE_PATH"
echo "  Bot Script  : $PROJECT_DIR/activity_bot.py"
echo ""

section "Launching Activity Bot"
echo ""
cd "$PROJECT_DIR"
python3 activity_bot.py