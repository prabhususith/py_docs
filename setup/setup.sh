#!/usr/bin/env bash
# ==============================================================================
# Enterprise Python Environment Setup Script (POSIX / Linux / macOS / WSL)
# ==============================================================================
# Description: Automates virtual environment bootstrap, pip upgrade, and
#              deterministic dependency installation.
# Enterprise Mapping: Equivalent to `npm ci` or `composer install`.
#
# Official Documentation References:
# - Python Virtual Environments (venv): https://docs.python.org/3/library/venv.html
# - Pip Package Installer: https://pip.pypa.io/en/stable/
# - PEP 508 / Requirements: https://peps.python.org/pep-0508/
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/.venv"

echo "[INFO] Initializing Enterprise Python Environment Setup..."

# Locate python3 binary
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[ERROR] Python 3 executable not found on PATH. Please install Python 3.10+."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "[INFO] Using Python interpreter: $($PYTHON_CMD --version)"

# Create venv if not present
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[INFO] Creating virtual environment at $VENV_DIR..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
else
    echo "[INFO] Existing virtual environment detected at $VENV_DIR."
fi

# Upgrade pip and core tooling
echo "[INFO] Upgrading pip, setuptools, and wheel..."
"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel

# Install pinned dependencies
echo "[INFO] Installing enterprise dependencies from $SCRIPT_DIR/requirements.txt..."
"$VENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"

echo "[SUCCESS] Virtual environment configured successfully."
echo "[INFO] To activate run: source $VENV_DIR/bin/activate"
echo "[INFO] Verifying environment sanity..."
"$VENV_DIR/bin/python" "$SCRIPT_DIR/verify_environment.py"
