@echo off
:: ============================================================
::   Activity Bot - Setup & Run (Windows)
::   For macOS / Linux use: setup.sh
::   IDE Priority: Antigravity > VS Code > Chrome-only mode
:: ============================================================

chcp 65001 >nul
setlocal EnableDelayedExpansion

:: Use the folder where this .bat file lives
set "PROJECT_DIR=%~dp0"
:: Strip trailing backslash
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
cd /d "%PROJECT_DIR%"

:: ── Optional folder argument ───────────────────
:: Usage: setup.bat [project-folder]
:: Example: setup.bat E:\myproject
set "FOLDER_ARG="
if not "%~1"=="" (
    set "FOLDER_ARG=--folder %~1"
    echo [OK] Project folder override: %~1
)

echo.
echo == Platform ==================================
echo [OK] Windows detected

:: ── Python check ──────────────────────────────
echo.
echo == Python 3 ==================================
python --version >nul 2>&1
if errorlevel 1 (
    echo [!!] Python not found.
    echo      Download from https://www.python.org/downloads/
    echo      Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v

:: ── Virtual environment ────────────────────────
echo.
echo == Virtual Environment =======================
set "VENV_DIR=%PROJECT_DIR%\venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"

if not exist "%VENV_DIR%\" (
    echo [..] Creating venv at %VENV_DIR%
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [!!] Failed to create venv.
        pause
        exit /b 1
    )
)

if not exist "%VENV_ACTIVATE%" (
    echo [!!] activate.bat not found — deleting broken venv and retrying...
    rmdir /s /q "%VENV_DIR%"
    python -m venv "%VENV_DIR%"
)

call "%VENV_ACTIVATE%"
if errorlevel 1 (
    echo [!!] Could not activate venv.
    pause
    exit /b 1
)

python -m pip install --upgrade pip --quiet
echo [OK] venv ready

:: ── Python dependencies ────────────────────────
:: Install deps BEFORE IDE detection so 'code' on PATH is available
echo.
echo == Python Dependencies =======================
pip install pyautogui pynput pywin32 --quiet
if errorlevel 1 (
    echo [!!] Dependency install failed. Check your internet connection.
    pause
    exit /b 1
)
echo [OK] pyautogui, pynput, pywin32 installed

:: ── IDE Detection (after venv + deps) ─────────
echo.
echo == IDE Detection =============================
set "IDE_NAME="

if exist "C:\Program Files\Antigravity\Antigravity.exe" (
    set "IDE_NAME=Antigravity"
    echo [OK] Antigravity found
    goto ide_done
)
if exist "%LOCALAPPDATA%\Programs\Antigravity\Antigravity.exe" (
    set "IDE_NAME=Antigravity"
    echo [OK] Antigravity found (user install)
    goto ide_done
)
if exist "C:\Program Files\Microsoft VS Code\Code.exe" (
    set "IDE_NAME=VS Code"
    echo [OK] VS Code found
    goto ide_done
)
if exist "%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe" (
    set "IDE_NAME=VS Code"
    echo [OK] VS Code found (user install ^& %LOCALAPPDATA%^)
    goto ide_done
)
where code >nul 2>&1
if not errorlevel 1 (
    set "IDE_NAME=VS Code"
    echo [OK] VS Code found on PATH
    goto ide_done
)
echo [!!] No IDE found - running in Chrome-only mode
echo      Install Antigravity or VS Code to enable IDE file features

:ide_done

:: ── Launch Chrome with CDP if not already open ──
echo.
echo == Chrome Check ==============================
set "CHROME_EXE="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe"
)
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

:: Check if Chrome is already running with CDP
set "CDP_ACTIVE=0"
powershell -Command "try { $r = Invoke-WebRequest -Uri http://127.0.0.1:9222/json -TimeoutSec 1 -UseBasicParsing; Write-Host 'CDP_OK' } catch { Write-Host 'CDP_NO' }" 2>nul | findstr /C:"CDP_OK" >nul && set "CDP_ACTIVE=1"

if "%CDP_ACTIVE%"=="1" (
    echo [OK] Chrome already running with remote debugging
) else if defined CHROME_EXE (
    echo [..] Launching Chrome with remote debugging port 9222...
    start "" "%CHROME_EXE%" --remote-debugging-port=9222
    timeout /t 3 /nobreak >nul
    echo [OK] Chrome launched with --remote-debugging-port=9222
) else (
    echo [!!] Chrome not found in standard locations
    echo      Please open Chrome manually before running the bot
    echo      For best results launch Chrome with: --remote-debugging-port=9222
)

:: ── Notes ──────────────────────────────────────
echo.
echo == Windows Notes =============================
echo   - Chrome launched automatically with remote debugging (port 9222)
echo   - This lets the bot read existing tabs and avoid duplicates
echo   - Windows Defender may flag pyautogui - add an exclusion if needed
echo   - To stop: press Ctrl+C in this window, or move mouse to top-left corner

:: ── Launch ─────────────────────────────────────
echo.
echo == Launching Activity Bot ====================
if not exist "%PROJECT_DIR%\activity_bot.py" (
    echo [!!] activity_bot.py not found in: %PROJECT_DIR%
    pause
    exit /b 1
)

if defined IDE_NAME (
    echo   IDE    : %IDE_NAME%
) else (
    echo   IDE    : Chrome-only
)
echo   Script : %PROJECT_DIR%\activity_bot.py
if defined FOLDER_ARG echo   Folder : %~1
echo.

python "%PROJECT_DIR%\activity_bot.py" %FOLDER_ARG%
pause