@echo off
rem ==============================================================================
rem Enterprise Python Environment Setup Script (Windows CMD/PowerShell)
rem ==============================================================================
rem Description: Automates virtual environment bootstrap, pip upgrade, and
rem              deterministic dependency installation.
rem Enterprise Mapping: Equivalent to `npm ci` or `composer install --no-dev`.
rem
rem Official Documentation References:
rem - Python Virtual Environments (venv): https://docs.python.org/3/library/venv.html
rem - Pip Package Installer: https://pip.pypa.io/en/stable/
rem - PEP 508 / Requirements: https://peps.python.org/pep-0508/
rem ==============================================================================

setlocal enabledelayedexpansion

echo [INFO] Initializing Enterprise Python Environment Setup...

rem Check if Python is accessible
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python executable not found on PATH. Please install Python 3.10+ and re-run.
    exit /b 1
)

rem Define target virtual environment directory
set VENV_DIR=%~dp0..\.venv

rem Create venv if missing
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment at %VENV_DIR%...
    python -m venv "%VENV_DIR%"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo [INFO] Existing virtual environment detected at %VENV_DIR%.
)

rem Upgrade pip, setuptools, and wheel
echo [INFO] Upgrading pip, setuptools, and wheel...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

rem Install pinned dependencies from requirements.txt
echo [INFO] Installing enterprise dependencies from setup\requirements.txt...
"%VENV_DIR%\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Dependency installation encountered errors.
    exit /b 1
)

echo [SUCCESS] Virtual environment configured successfully.
echo [INFO] Run the following to activate:
echo        %VENV_DIR%\Scripts\activate.bat
echo [INFO] Verifying environment sanity...
"%VENV_DIR%\Scripts\python.exe" "%~dp0verify_environment.py"

endlocal
