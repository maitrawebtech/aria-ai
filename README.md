ndendendednedne# ◈ A.R.I.A — Adaptive Responsive Intelligence Assistant

> *Your AI girlfriend who also controls your PC. Hinglish mein baat karo, kaam karwao.*

![Python](https://img.shields.io/badge/Python-3.10+-ff2d78?style=for-the-badge&logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-AI_Core-00f0ff?style=for-the-badge&logo=google&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-bf5fff?style=for-the-badge&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-ff2d78?style=for-the-badge)

---

## What is ARIA?

ARIA is a **voice-controlled AI assistant** that runs on your PC with a **cyberpunk/AI girlfriend GUI**. She listens to your Hinglish commands, executes PC actions directly, and chats with Gemini 2.5 Flash for everything else — all with a human-like TTS voice.

```
You: "notepad kholo"         → Opens Notepad instantly
You: "YouTube pe lofi bajao" → Opens YouTube search
You: "volume 60 karo"        → Sets volume to 60%
You: "mujhe Python samjhao"  → Gemini answers with Aoede's voice
```

---

## Features

### 🎙️ Voice & AI
- **Hinglish STT** — speaks in Indian English accent, understands mixed Hindi-English
- **Gemini 2.5 Flash** — powers the conversation brain with memory (chat history)
- **Human-like TTS** — Aoede voice via `gemini-2.5-flash-preview-tts`
- **Interruptible playback** — speaking stops instantly on new input

### 🖥️ PC Control (`app.py`)
- Open/close any **app** — Chrome, VS Code, Notepad, Spotify, Discord, and 40+ more
- Open **folders** — Desktop, Downloads, Documents, or any custom path
- Open/search **files** anywhere on your system
- **Volume** control — set, mute, unmute, increase, decrease
- **Web** — open websites, Google search, YouTube search
- **System** — screenshot, lock screen, shutdown, restart, sleep, battery info
- **Keyboard** — Ctrl+C, Ctrl+V, Alt+Tab, Win+D and more
- Create/delete folders and files by voice

### 🌸 GUI (`gui.py`)
- **Animated orb** with 4 emotional states — idle, listening, thinking, speaking
- **Live waveform** that reacts to ARIA's current state
- **Particle ring** floating around the orb
- **Conversation log** with color-coded chat (you = cyan, ARIA = pink)
- **HUD-style** cyberpunk interface with live clock and system status
- Fully **thread-safe** — GUI stays smooth while ARIA processes in background

---

## Project Structure

```
ARIA - Voice Assistant/
│
├── aria.py          ← Main entry point — run this
├── gui.py           ← Tkinter GUI (auto-launched by aria.py)
├── app.py           ← PC controller (apps, files, volume, web, system)
├── prompt.py        ← ARIA's personality & system instructions
├── .env             ← Your Gemini API key (never commit this)
│
└── README.md
```

---

## Setup

### 1. Clone / Download
```bash
git clone https://github.com/yourusername/aria-ai
cd "ARIA - Voice Assistant"
```

### 2. Install Dependencies
```bash
pip install google-genai python-dotenv pyaudio SpeechRecognition psutil pycaw pyautogui pyperclip comtypes
```

> **PyAudio on Windows** — if it fails, install via wheel:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 3. Get Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Create `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

### 4. Run
```bash
python aria.py
```

That's it. GUI opens automatically. Say something.

---

## Voice Commands Reference

### Apps
| Say | Action |
|-----|--------|
| `"notepad kholo"` | Opens Notepad |
| `"Chrome open karo"` | Opens Chrome |
| `"VS Code chalao"` | Opens VS Code |
| `"Spotify band karo"` | Closes Spotify |
| `"Discord kholo"` | Opens Discord |

### Folders & Files
| Say | Action |
|-----|--------|
| `"Desktop kholo"` | Opens Desktop folder |
| `"Downloads folder open karo"` | Opens Downloads |
| `"resume.pdf kholo"` | Finds and opens file |
| `"Projects naam ka folder banao"` | Creates folder on Desktop |

### Web
| Say | Action |
|-----|--------|
| `"YouTube kholo"` | Opens youtube.com |
| `"lofi bajao YouTube pe"` | Searches YouTube |
| `"Python tutorial dhundo"` | Google search |
| `"GitHub open karo"` | Opens github.com |

### System
| Say | Action |
|-----|--------|
| `"volume 70 karo"` | Sets volume to 70% |
| `"mute karo"` | Mutes audio |
| `"screenshot lo"` | Takes screenshot to Desktop |
| `"battery kitni hai"` | Shows battery % |
| `"screen lock karo"` | Locks screen |
| `"PC restart karo"` | Restarts PC |
| `"system info batao"` | CPU, RAM, battery info |

### Exit
| Say | Action |
|-----|--------|
| `"bye"` / `"alvida"` | ARIA shuts down |

---

## Configuration

### Change Voice
In `aria.py`, change `VOICE_NAME`:
```python
VOICE_NAME = "Aoede"    # Default — warm feminine
# Options: "Kore" | "Charon" | "Fenrir" | "Puck"
```

### Change ARIA's Personality
Edit `prompt.py` — this is ARIA's system instruction sent to Gemini. Make her sassy, professional, or whatever you want.

### Change Models
```python
CHAT_MODEL = "gemini-2.5-flash"              # Conversation
TTS_MODEL  = "gemini-2.5-flash-preview-tts" # Voice
```

---

## How It Works

```
Your Voice
    ↓
Google STT (en-IN)
    ↓
handle_command() in app.py
    ├── PC Command? → Execute directly → speak result
    └── Not a command? → Send to Gemini → speak reply
                              ↓
                      TTS Worker Thread
                              ↓
                       Aoede Voice Output
```

The GUI runs on the **main thread** (Tkinter requirement). ARIA's voice loop runs on a **background thread**. All GUI updates go through a thread-safe queue so there's no freezing.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `google-genai` | Gemini API — chat + TTS |
| `SpeechRecognition` | Microphone → text (Google STT) |
| `pyaudio` | Audio capture and playback |
| `python-dotenv` | Load `.env` API key |
| `psutil` | CPU, RAM, battery, process control |
| `pycaw` | Windows volume control |
| `pyautogui` | Screenshots, keyboard simulation |
| `pyperclip` | Clipboard access |
| `comtypes` | Windows COM interface (required by pycaw) |
| `tkinter` | GUI — built into Python, no install needed |

---

## Known Limitations

- **Windows only** for full PC control (volume, some system commands). Linux/Mac partial support.
- **Internet required** — Gemini API and Google STT both need connection.
- **Microphone required** — no text input mode currently.
- Background noise can affect STT accuracy — use in a reasonably quiet environment.

---

## Roadmap

- [ ] Wake word detection (`"Hey ARIA"`)
- [ ] Brightness control
- [ ] WhatsApp / email sending via voice
- [ ] Offline STT fallback (Whisper)
- [ ] Custom hotkey to interrupt ARIA mid-speech
- [ ] Multiple language support

---

## Built By

**Ishan Maitra** — [github.com/maitrawebtech](https://github.com/maitrawebtech)

Part of the **Maitra** personal AI ecosystem:
- `MNCS` — Neural touchless computer control
- `MaitraGPT` — Personal RAG-based AI assistant
- `ARIA` — Voice assistant with PC control ← you are here

---

*"She listens. She responds. She controls your PC. Just don't call her a chatbot."*
