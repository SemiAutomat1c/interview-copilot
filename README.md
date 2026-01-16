# Interview Copilot 🎙️

A real-time AI-powered interview assistant that listens to interview questions and generates intelligent responses using local LLM (Ollama).

![Interview Copilot Screenshot](assets/screenshots/app-screenshot.png)

## ✨ Features

- **🎤 Real-time Transcription** - Uses Vosk for fast, offline speech-to-text
- **🤖 AI-Powered Responses** - Generates contextual answers using Ollama (llama3.2)
- **🖥️ Modern UI** - Clean, minimal Flet-based interface with shadcn-inspired design
- **⌨️ Keyboard Shortcuts** - Quick controls for seamless interview flow
- **🔒 Privacy-First** - All processing happens locally, no data sent to cloud
- **🎧 System Audio Support** - Capture audio from any source using BlackHole

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

1. Clone the repository:
   ```bash
   git clone https://github.com/SemiAutomat1c/interview-copilot.git
   cd interview-copilot
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your configuration:
   ```bash
   cp config.example.json config.json
   ```

5. Edit `config.json` with your profile:
   ```json
   {
     "my_profile": "Your experience and skills...",
     "job_context": "Role you're interviewing for..."
   }
   ```

### Running the App

```bash
python main.py
```

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `S` | Start/Stop listening |
| `Space` or `Enter` | Process current transcription |
| `Escape` | Clear transcription buffer |

## 🎧 Audio Setup (macOS)

To capture system audio (e.g., from Zoom, Google Meet):

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

## ⚙️ Configuration

Edit `config.json` to customize:

```json
{
  "my_profile": "Your professional background and skills",
  "job_context": "The role and company you're interviewing for",
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

## 📁 Project Structure

```
interview-copilot/
├── main.py              # Application entry point
├── config.json          # Your configuration (gitignored)
├── config.example.json  # Example configuration
├── requirements.txt     # Python dependencies
├── src/
│   ├── audio_handler.py # Audio capture and processing
│   ├── vosk_handler.py  # Speech recognition with Vosk
│   ├── llm_client.py    # Ollama integration
│   ├── gui.py           # Flet UI components
│   ├── config.py        # Configuration loader
│   └── enums.py         # State enumerations
└── assets/
    └── screenshots/     # Documentation images
```

## 🛠️ Tech Stack

- **[Flet](https://flet.dev/)** - Modern Python UI framework
- **[Vosk](https://alphacephei.com/vosk/)** - Offline speech recognition
- **[Ollama](https://ollama.ai/)** - Local LLM inference
- **[PyAudio](https://pypi.org/project/PyAudio/)** - Audio capture

## 📝 License

MIT License - feel free to use this for your own interview prep!

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

---

**⚠️ Disclaimer:** This tool is meant for interview preparation and practice. Use responsibly and ethically during actual interviews based on the policies of the company you're interviewing with.
