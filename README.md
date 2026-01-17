<p align="center">
  <img src="assets/logo.png" alt="Interview Copilot" width="150">
</p>
<p align="center">
  <em>Real-time AI-powered interview assistant</em>
</p>
  <p align="center">
    <a href="#features"><img src="https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python" alt="Python"></a>
    <a href="#tech-stack"><img src="https://img.shields.io/badge/Flet-UI-purple?style=flat-square" alt="Flet"></a>
    <a href="#tech-stack"><img src="https://img.shields.io/badge/Vosk-Speech-green?style=flat-square" alt="Vosk"></a>
    <a href="#tech-stack"><img src="https://img.shields.io/badge/Ollama-LLM-orange?style=flat-square" alt="Ollama"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License"></a>
  </p>
</p>

<p align="center">
  <img src="assets/screenshots/app-screenshot.png" alt="Interview Copilot Screenshot" width="700" style="border-radius: 10px; border: 1px solid #30363d;">
</p>

---

## ✨ Features

- **🎤 Real-time Transcription** - Uses Vosk for fast, offline speech-to-text
- **🤖 AI-Powered Responses** - Generates contextual answers using Ollama (llama3.2)
- **🎯 Dynamic Context Management** - Edit profile and job context directly in UI, no file editing needed
- **💬 Conversation Memory** - Maintains last 3 Q&A pairs for intelligent follow-up questions
- **💾 Session Persistence** - Auto-saves and restores your interview sessions
- **🖥️ Modern UI** - Clean, minimal Flet-based interface with shadcn-inspired design
- **⌨️ Keyboard Shortcuts** - Quick controls for seamless interview flow
- **🔒 Privacy-First** - All processing happens locally, no data sent to cloud
- **🎧 System Audio Support** - Capture audio from any source using BlackHole

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Ollama** - Local LLM server
   ```bash
   brew install ollama
   ollama pull llama3.2:1b
   ollama serve
   ```
3. **BlackHole** (for system audio capture on macOS)
   ```bash
   brew install blackhole-2ch
   ```

### Installation

```bash
# Clone the repository
git clone https://github.com/SemiAutomat1c/interview-copilot.git
cd interview-copilot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your configuration
cp config.example.json config.json
```

> **Note:** With the new dynamic context management system, you can now edit your profile and job context directly in the UI! The config.json file is optional and serves as defaults.

### Run

```bash
python3 main.py
```

---

## 🎯 Using Dynamic Context Management

**NEW!** Interview Copilot now features a powerful context management system that lets you switch between different interview contexts without editing files or restarting the app.

### Quick Start

1. **Launch the app** - Your last session is automatically restored
2. **Expand the Context Panel** at the top of the UI
3. **Fill in your details:**
   - **My Profile**: Your background, skills, and experience
   - **Job Context**: The role you're interviewing for
4. **Click "Start New Session"** - Context is processed once, then reused for all questions
5. **Ask questions** as usual!

### Key Features

- **Zero Performance Impact** - Context processed once per session, not per question
- **Conversation Memory** - Remembers last 3 Q&A for follow-up questions
- **Auto-Save** - Sessions persist across app restarts
- **Hot-Swap Contexts** - Switch between different interviews instantly

### Example Workflow

```
1. Enter profile: "Senior Python Developer, 5 years ML experience..."
2. Enter context: "Applying for ML Engineer at AI Startup..."
3. Click "Start New Session"
4. Ask: "Tell me about your Python experience"
   → Answer references your specific background
5. Ask: "What about ML projects?" 
   → Answer builds on previous exchange
6. Need to prep for a different interview?
   → Expand panel, enter new context, start new session!
```

For detailed documentation, see [QUICK_START.md](QUICK_START.md)

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|:---:|--------|
| `S` | Start/Stop listening |
| `Space` / `Enter` | Process current transcription |
| `Escape` | Clear transcription buffer |

---

## 🎧 Audio Setup

The app works on **macOS, Windows, and Linux**. For system audio capture (hearing the interviewer from Zoom/Meet), follow the guide for your OS:

<details>
<summary><strong>🍎 macOS (BlackHole)</strong></summary>

1. **Install BlackHole:**
   ```bash
   brew install blackhole-2ch
   ```

2. **Create Multi-Output Device:**
   - Open **Audio MIDI Setup** (Spotlight → "Audio MIDI Setup")
   - Click **+** → Create Multi-Output Device
   - Check your speakers/headphones AND BlackHole 2ch
   - Set as your system output

3. **Configure in config.json:**
   ```json
   {
     "audio_settings": {
       "use_system_audio": true,
       "device_name": "BlackHole"
     }
   }
   ```
</details>

<details>
<summary><strong>🪟 Windows (VB-CABLE)</strong></summary>

1. **Download & Install [VB-CABLE](https://vb-audio.com/Cable/)** (free)

2. **Set VB-CABLE as Default:**
   - Right-click Speaker icon → Sound Settings
   - Set "VB-CABLE Input" as your output device

3. **Configure in config.json:**
   ```json
   {
     "audio_settings": {
       "use_system_audio": true,
       "device_name": "CABLE Output"
     }
   }
   ```
</details>

<details>
<summary><strong>🐧 Linux (PulseAudio)</strong></summary>

1. **Create a loopback device:**
   ```bash
   pactl load-module module-loopback latency_msec=1
   ```

2. **Use `pavucontrol`** to route your app's audio to the loopback.

3. **Configure in config.json:**
   ```json
   {
     "audio_settings": {
       "use_system_audio": true,
       "device_name": "pulse"
     }
   }
   ```
</details>

> **Note:** Microphone-only mode works out of the box on all platforms without any extra setup!


---

## ⚙️ Configuration

> **💡 Pro Tip:** With dynamic context management, you can now edit your profile and job context directly in the UI! The config.json file serves as default values that can be loaded with the "Load from Config" button.

| Setting | Description |
|---------|-------------|
| `my_profile` | Your professional background and skills (can be edited in UI) |
| `job_context` | The role and company you're interviewing for (can be edited in UI) |
| `ollama_settings.model` | LLM model to use (default: `llama3.2:1b`) |
| `transcription_settings.engine` | Speech engine (`vosk`) |

<details>
<summary>Full config.json example</summary>

```json
{
  "my_profile": "5 years Python development experience...",
  "job_context": "Senior Python Developer role at AI Startup...",
  "system_instruction": "Custom instructions for the AI",
  "ollama_settings": {
    "model": "llama3.2:1b",
    "temperature": 0.3,
    "max_tokens": 80
  },
  "gui_settings": {
    "window_width": 800,
    "window_height": 800
  },
  "transcription_settings": {
    "engine": "vosk",
    "vosk_model": "small"
  }
}
```
</details>

---

## 📁 Project Structure

```
interview-copilot/
├── main.py                 # Application entry point
├── config.json             # Your configuration (gitignored)
├── config.example.json     # Example configuration
├── requirements.txt        # Python dependencies
├── QUICK_START.md          # User guide for context management
├── SESSION_MANAGEMENT.md   # Technical documentation
├── src/
│   ├── audio_handler.py    # Audio capture and processing
│   ├── vosk_handler.py     # Speech recognition with Vosk
│   ├── llm_client.py       # Ollama integration
│   ├── gui.py              # Flet UI components
│   ├── config_loader.py    # Configuration loader
│   └── session_manager.py  # Session lifecycle management (NEW)
└── assets/
    └── screenshots/        # Documentation images
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| UI Framework | [Flet](https://flet.dev/) |
| Speech Recognition | [Vosk](https://alphacephei.com/vosk/) |
| LLM Inference | [Ollama](https://ollama.ai/) |
| Audio Capture | [PyAudio](https://pypi.org/project/PyAudio/) |

---

## 📖 Documentation

- **[QUICK_START.md](QUICK_START.md)** - User guide for dynamic context management
- **[SESSION_MANAGEMENT.md](SESSION_MANAGEMENT.md)** - Technical documentation and architecture

---

## 🆕 What's New

### v2.0 - Dynamic Context Management (Latest)

- ✨ **UI-based context editing** - No more editing config files!
- 💬 **Conversation memory** - Maintains last 3 Q&A for follow-up questions
- 💾 **Session persistence** - Auto-saves and restores sessions
- 🚀 **Hot-swap contexts** - Switch between different interviews instantly
- ⚡ **Zero performance impact** - Context processed once, reused for all questions

---

## Credits

Built with [OpenCode](https://opencode.ai) - The open source AI coding agent.

## 📝 License

MIT License - feel free to use this for your own interview prep!

---

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

---

<p align="center">
  <strong>⚠️ Disclaimer</strong><br>
  <em>This tool is meant for interview preparation and practice. Use responsibly and ethically during actual interviews based on the policies of the company you're interviewing with.</em>
</p>
