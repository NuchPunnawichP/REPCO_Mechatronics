#!/bin/bash
# ============================================================
#  AE Analyzer — Fix & Rebuild Script
#  Fixes the "cannot open" error on macOS.
#  Usage: cd MacBookSoftware_ed4 && bash fix_and_rebuild.sh
# ============================================================

APPNAME="AEAnalyzer"

echo "=============================================="
echo "  AE Analyzer — Fix & Rebuild for macOS"
echo "=============================================="
echo ""

# ── Step 1: Remove existing broken build (force, ignore errors) ──
echo "[1/4] Removing previous build..."
find build dist __pycache__ -type f -exec chmod u+w {} \; 2>/dev/null || true
rm -rf build dist __pycache__ 2>/dev/null || true
echo "  Done."

# ── Step 2: Install / ensure dependencies ────────────────────
echo ""
echo "[2/4] Checking dependencies..."
pip3 install --upgrade --quiet numpy matplotlib pyinstaller
echo "  Dependencies OK."

# ── Step 3: Build with PyInstaller ───────────────────────────
echo ""
echo "[3/4] Building AEAnalyzer.app..."
pyinstaller AEAnalyzer.spec --noconfirm

# ── Step 4: Remove quarantine attribute (Gatekeeper fix) ─────
echo ""
echo "[4/4] Removing macOS quarantine attribute..."
xattr -cr "dist/${APPNAME}.app" 2>/dev/null && echo "  Quarantine removed." || echo "  (xattr not needed or already clean)"

echo ""
if [ -d "dist/${APPNAME}.app" ]; then
    echo "=============================================="
    echo "  BUILD SUCCESSFUL!"
    echo "  App: dist/${APPNAME}.app"
    echo "=============================================="
    echo ""
    echo "Open the app:"
    echo "  open dist/${APPNAME}.app"
    echo ""
    echo "If it still won't open, run from Terminal to see errors:"
    echo "  dist/${APPNAME}.app/Contents/MacOS/${APPNAME}"
    echo ""
    echo "Optional — move to /Applications:"
    echo "  cp -r dist/${APPNAME}.app /Applications/"
else
    echo "ERROR: Build failed."
    exit 1
fi
