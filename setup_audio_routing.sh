#!/bin/bash

echo "============================================================"
echo "Interview Copilot - Audio Routing Setup"
echo "============================================================"
echo ""
echo "This script will configure your Mac to route browser audio"
echo "to the Interview Copilot app, so it can 'hear' the interviewer."
echo ""

# Check if BlackHole is installed
if brew list blackhole-2ch &>/dev/null; then
    echo "✓ BlackHole already installed"
else
    echo "Installing BlackHole (virtual audio driver)..."
    brew install blackhole-2ch
    echo "✓ BlackHole installed"
fi

echo ""
echo "============================================================"
echo "Next Steps (Manual Configuration)"
echo "============================================================"
echo ""
echo "1. Open 'Audio MIDI Setup' app:"
echo "   - Press Cmd+Space"
echo "   - Type: Audio MIDI Setup"
echo "   - Press Enter"
echo ""
echo "2. Create Multi-Output Device:"
echo "   - Click '+' (bottom left)"
echo "   - Select 'Create Multi-Output Device'"
echo "   - Name it: 'Interview Output'"
echo "   - Check BOTH boxes:"
echo "     ✓ BlackHole 2ch"
echo "     ✓ Your headphones/speakers (so you can hear too)"
echo ""
echo "3. Set System Output:"
echo "   - System Preferences → Sound → Output"
echo "   - Select: 'Interview Output'"
echo ""
echo "4. Done! Now run the app:"
echo "   cd ~/repos/Repo/interview-copilot"
echo "   python3 main.py"
echo ""
echo "The app will now hear browser audio + your mic!"
echo "============================================================"
