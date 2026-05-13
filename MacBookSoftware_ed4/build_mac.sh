#!/bin/bash
# ============================================================
#  AE Analyzer — macOS Build Script
#  Usage: cd MacBookSoftware_ed4 && bash build_mac.sh
# ============================================================

set -e   # Stop on any error

APPNAME="AEAnalyzer"
SPECFILE="AEAnalyzer.spec"

echo "=============================================="
echo "  AE Analyzer — macOS PyInstaller Build"
echo "=============================================="
echo ""

# ── 1. Check Python ──────────────────────────────────────────
echo "[1/5] Checking Python..."
python3 --version || { echo "ERROR: python3 not found."; exit 1; }

# ── 2. Install / upgrade dependencies ────────────────────────
echo ""
echo "[2/5] Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install --upgrade numpy matplotlib pyinstaller

# ── 3. Clean previous build artefacts ────────────────────────
echo ""
echo "[3/5] Cleaning previous build..."
rm -rf build dist __pycache__
echo "  Clean done."

# ── 4. Run PyInstaller ────────────────────────────────────────
echo ""
echo "[4/5] Running PyInstaller..."
pyinstaller "$SPECFILE" --noconfirm

# ── 5. Verify output ─────────────────────────────────────────
echo ""
echo "[5/5] Verifying output..."
if [ -d "dist/${APPNAME}.app" ]; then
    echo ""
    echo "=============================================="
    echo "  BUILD SUCCESSFUL!"
    echo "  App location: dist/${APPNAME}.app"
    echo "=============================================="
    echo ""
    echo "To run directly:"
    echo "  open dist/${APPNAME}.app"
    echo ""
    echo "Optional — Code-sign for macOS Gatekeeper:"
    echo "  codesign --deep --force --sign \"Developer ID Application: YOUR_NAME (TEAMID)\" dist/${APPNAME}.app"
    echo ""
    echo "Optional — Move to /Applications:"
    echo "  cp -r dist/${APPNAME}.app /Applications/"
    echo ""
else
    echo "ERROR: Build failed — dist/${APPNAME}.app not found."
    exit 1
fi
