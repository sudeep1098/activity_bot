#!/bin/bash
# ============================================================
#   Activity Bot - Setup & Run (macOS / Linux)
#   For Windows use: setup.bat
#   IDE Priority: Antigravity > VS Code > Chrome-only mode
# ============================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[✔]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✘]${NC} $1"; exit 1; }
section() { echo -e "\n${YELLOW}══ $1 ══${NC}"; }

OS="$(uname -s)"

# ── Optional folder argument ───────────────────
# Usage: bash setup.sh [project-folder]
# Example: bash setup.sh /var/www/html/myproject
FOLDER_ARG=""
if [[ -n "$1" ]]; then
    FOLDER_ARG="--folder $1"
    echo "  Project folder override: $1"
fi

section "Platform"
if [[ "$OS" == "Darwin" ]]; then
    info "macOS detected"
elif [[ "$OS" == "Linux" ]]; then
    info "Linux detected"
else
    error "Unsupported platform: $OS — use setup.bat on Windows"
fi

# ── macOS: Xcode CLI & Homebrew ────────────────
if [[ "$OS" == "Darwin" ]]; then
    section "Xcode Command Line Tools"
    if ! xcode-select -p &>/dev/null; then
        warn "Installing Xcode CLI tools..."
        xcode-select --install
        echo "  -> Re-run this script after installation."
        exit 0
    else
        info "Xcode CLI tools OK"
    fi

    section "Homebrew"
    if ! command -v brew &>/dev/null; then
        warn "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        [[ -f "/opt/homebrew/bin/brew" ]] && eval "$(/opt/homebrew/bin/brew shellenv)" \
            && echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        [[ -f "/usr/local/bin/brew" ]]    && eval "$(/usr/local/bin/brew shellenv)"
        info "Homebrew installed"
    else
        info "Homebrew OK ($(brew --version | head -1))"
    fi
fi

# ── Linux: system deps ─────────────────────────
if [[ "$OS" == "Linux" ]]; then
    section "Linux System Dependencies"
    MISSING=()
    command -v xdotool  &>/dev/null || MISSING+=("xdotool")
    command -v wmctrl   &>/dev/null || MISSING+=("wmctrl")
    command -v python3  &>/dev/null || MISSING+=("python3")
    command -v pip3     &>/dev/null || MISSING+=("python3-pip")

    if [[ ${#MISSING[@]} -gt 0 ]]; then
        warn "Installing: ${MISSING[*]}"
        sudo apt-get update -qq
        sudo apt-get install -y "${MISSING[@]}"
    fi
    info "System deps OK"
fi

# ── Python 3 ───────────────────────────────────
section "Python 3"
if ! command -v python3 &>/dev/null; then
    [[ "$OS" == "Darwin" ]] && brew install python3 || error "python3 not found"
fi
PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Python $PYVER"

# ── Virtual environment ────────────────────────
section "Virtual Environment"
if [[ ! -d "$PROJECT_DIR/venv" ]]; then
    warn "Creating venv..."
    python3 -m venv "$PROJECT_DIR/venv"
fi
source "$PROJECT_DIR/venv/bin/activate"
pip install --upgrade pip --quiet
info "venv ready ($(python3 --version))"

# ── IDE Detection ──────────────────────────────
section "IDE Detection"
IDE_NAME=""
if [[ "$OS" == "Darwin" ]]; then
    [[ -d "/Applications/Antigravity.app" ]]          && IDE_NAME="Antigravity"
    [[ -z "$IDE_NAME" && -d "/Applications/Visual Studio Code.app" ]] && IDE_NAME="VS Code"
elif [[ "$OS" == "Linux" ]]; then
    command -v antigravity &>/dev/null                && IDE_NAME="Antigravity"
    [[ -z "$IDE_NAME" ]] && command -v code &>/dev/null && IDE_NAME="VS Code"
fi

if [[ -n "$IDE_NAME" ]]; then
    info "IDE found: $IDE_NAME"
else
    warn "No IDE found — running in Chrome-only mode"
    echo "  -> Install Antigravity (https://antigravity.app) or VS Code to enable IDE features"
fi

# ── Python dependencies ────────────────────────
section "Python Dependencies"
PACKAGES=("pyautogui" "pynput")
for pkg in "${PACKAGES[@]}"; do
    python3 -c "import ${pkg//-/_}" &>/dev/null && info "$pkg OK" || { pip install "$pkg" --quiet && info "$pkg installed"; }
done

if [[ "$OS" == "Darwin" ]]; then
    python3 -c "import AppKit" &>/dev/null || { warn "Installing pyobjc..."; pip install pyobjc --quiet; info "pyobjc installed"; }
fi

# ── Permissions reminder ───────────────────────
section "Permissions"
if [[ "$OS" == "Darwin" ]]; then
    echo "  System Settings → Privacy & Security → Accessibility   → add Terminal ✔"
    echo "  System Settings → Privacy & Security → Automation      → Terminal → Chrome ✔"
elif [[ "$OS" == "Linux" ]]; then
    echo "  Ensure your user can use xdotool (usually no extra setup needed)."
    echo "  If Chrome keyboard shortcuts fail, check xdotool is working: xdotool getactivewindow"
fi

# ── Launch ─────────────────────────────────────
section "Launching Activity Bot"
[[ ! -f "$PROJECT_DIR/activity_bot.py" ]] && error "activity_bot.py not found in $PROJECT_DIR"
echo "  IDE   : ${IDE_NAME:-Chrome-only}"
echo "  Script: $PROJECT_DIR/activity_bot.py"
echo ""
cd "$PROJECT_DIR"
python3 activity_bot.py $FOLDER_ARG