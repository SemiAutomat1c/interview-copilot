#!/bin/bash

echo "=========================================="
echo "Interview Copilot - Headphones Setup"
echo "=========================================="
echo ""
echo "Step 1: Installing BlackHole..."
echo ""

brew install blackhole-2ch

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ BlackHole installed successfully!"
    echo ""
    echo "=========================================="
    echo "⚠️  REBOOT REQUIRED"
    echo "=========================================="
    echo ""
    echo "Audio driver requires a restart to work."
    echo ""
    echo "After reboot, follow these steps:"
    echo ""
    echo "1. Open HEADPHONES_SETUP.md for full guide:"
    echo "   open ~/repos/Repo/interview-copilot/HEADPHONES_SETUP.md"
    echo ""
    echo "2. Quick steps:"
    echo "   - Audio MIDI Setup → Create Multi-Output Device"
    echo "   - Check: BlackHole 2ch + EDIFIER K750W"
    echo "   - System Preferences → Sound → Output → Interview Output"
    echo ""
    echo "3. Test the app:"
    echo "   cd ~/repos/Repo/interview-copilot"
    echo "   python3 main.py"
    echo ""
    echo "=========================================="
    echo ""
    read -p "Restart now? (y/n): " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        echo "Rebooting in 5 seconds..."
        sleep 5
        sudo reboot
    else
        echo "Remember to restart before using the app!"
    fi
else
    echo ""
    echo "✗ Installation failed or canceled"
    echo "Try manually: brew install blackhole-2ch"
fi
