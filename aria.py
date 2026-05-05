import os
import io
import wave
import threading
import queue
import pyaudio
import speech_recognition as sr

from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompt import PROMPT
from app import handle_command

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY .env file mein nahi mili!")

# ─── Models ──────────────────────────────────────────
CHAT_MODEL = "gemini-2.5-flash"
TTS_MODEL  = "gemini-2.5-flash-preview-tts"
VOICE_NAME = "Aoede"

# ─── Audio config ─────────────────────────────────────
SPK_RATE     = 24000
SPK_CHANNELS = 1
SPK_WIDTH    = 2
MIC_LANG     = "en-IN"   # Hinglish — Indian English accent

# ─── Gemini client ────────────────────────────────────
client = genai.Client(api_key=API_KEY)

# ─── Global flags ─────────────────────────────────────
audio_queue        = queue.Queue()
stop_speaking_flag = threading.Event()
aria_is_speaking   = threading.Event()   # ← NEW: mic block karta hai jab ARIA bol rahi ho

# ─── Chat history ─────────────────────────────────────
chat = client.chats.create(
    model=CHAT_MODEL,
    config=types.GenerateContentConfig(system_instruction=PROMPT)
)

# ─── PyAudio ──────────────────────────────────────────
pa = pyaudio.PyAudio()

# ─── GUI reference ────────────────────────────────────
gui = None


# ─────────────────────────────────────────────────────
#  AUDIO HELPERS
# ─────────────────────────────────────────────────────
def pcm_to_wav_bytes(pcm_data: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(SPK_CHANNELS)
        wf.setsampwidth(SPK_WIDTH)
        wf.setframerate(SPK_RATE)
        wf.writeframes(pcm_data)
    return buf.getvalue()

def play_wav_bytes_interruptible(wav_bytes: bytes):
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        stream = pa.open(
            format=pa.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
        )
        data = wf.readframes(1024)
        while data:
            if stop_speaking_flag.is_set():
                break
            stream.write(data)
            data = wf.readframes(1024)
        stream.stop_stream()
        stream.close()


# ─────────────────────────────────────────────────────
#  TTS WORKER
# ─────────────────────────────────────────────────────
def tts_worker():
    while True:
        text = audio_queue.get()
        if text is None:
            break
        try:
            aria_is_speaking.set()       # ← mic block: ARIA bol rahi hai
            if gui:
                gui.set_state("speaking")

            response = client.models.generate_content(
                model=TTS_MODEL,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=VOICE_NAME
                            )
                        )
                    ),
                )
            )
            pcm_data = response.candidates[0].content.parts[0].inline_data.data
            wav_bytes = pcm_to_wav_bytes(pcm_data)
            play_wav_bytes_interruptible(wav_bytes)

        except Exception as e:
            print("[TTS Error]", e)
        finally:
            audio_queue.task_done()

threading.Thread(target=tts_worker, daemon=True).start()


# ─────────────────────────────────────────────────────
#  SPEAK
# ─────────────────────────────────────────────────────
def speak(text: str):
    stop_speaking_flag.clear()
    aria_is_speaking.set()          # ← block mic before queuing
    audio_queue.put(text)
    audio_queue.join()              # wait until audio done
    aria_is_speaking.clear()        # ← mic unblock: ab sun sakte hain
    if gui:
        gui.set_state("idle")


# ─────────────────────────────────────────────────────
#  LISTEN — mic block during TTS (feedback loop fix)
# ─────────────────────────────────────────────────────
def listen() -> str | None:
    # ARIA bol rahi hai? Wait karo
    if aria_is_speaking.is_set():
        aria_is_speaking.wait(timeout=15)  # max 15 sec wait

    recognizer = sr.Recognizer()
    recognizer.energy_threshold        = 300
    recognizer.pause_threshold         = 0.8
    recognizer.dynamic_energy_threshold = True

    if gui:
        gui.set_state("listening")

    with sr.Microphone() as source:
        print("\n🎤 Sun raha hoon...")
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            print("⏱️  Koi awaaz nahi aayi.")
            if gui:
                gui.set_state("idle")
            return None

    if gui:
        gui.set_state("thinking")

    print("⏳ Samajh raha hoon...")
    try:
        text = recognizer.recognize_google(audio, language=MIC_LANG)
        print(f"👤 Aap: {text}")
        if gui:
            gui.add_user(text)
        return text
    except sr.UnknownValueError:
        print("❓ Samajh nahi aaya.")
        if gui:
            gui.set_state("idle")
            gui.add_sys("Samajh nahi aaya, dobara bolo.")
        return None
    except sr.RequestError as e:
        print(f"[STT Error] {e}")
        if gui:
            gui.set_state("idle")
        return None


# ─────────────────────────────────────────────────────
#  GET REPLY (Gemini)
# ─────────────────────────────────────────────────────
def get_reply(user_text: str) -> str:
    try:
        response = chat.send_message(user_text)
        return response.text.strip()
    except Exception as e:
        return f"Kuch gadbad ho gayi: {e}"


# ─────────────────────────────────────────────────────
#  ARIA MAIN LOOP (background thread)
# ─────────────────────────────────────────────────────
def aria_loop():
    global gui
    import time
    time.sleep(1.2)

    from gui import get_gui
    gui = get_gui()

    print("=" * 50)
    print("  🎙️  ARIA — Voice Assistant")
    print(f"  TTS   : {TTS_MODEL}")
    print(f"  Voice : {VOICE_NAME}")
    print(f"  Chat  : {CHAT_MODEL}")
    print("  'bye' bolke band karo")
    print("=" * 50)

    greeting = "Hello! Main ARIA hoon. Boliye, kya karna hai?"
    if gui:
        gui.add_aria(greeting)
        gui.add_sys("PC Control ready. Hinglish mode on.")
    speak(greeting)

    EXIT_WORDS = {"bye", "exit", "quit", "goodbye", "alvida", "ok bye", "band ho jao"}

    while True:
        try:
            user_input = listen()

            if not user_input:
                continue

            if any(word in user_input.lower() for word in EXIT_WORDS):
                farewell = "Theek hai, alvida! Jab bhi zaroorat ho, main hoon."
                if gui:
                    gui.add_aria(farewell)
                speak(farewell)
                break

            # ── PC command check (Gemini NLU) ──────────
            pc_response = handle_command(user_input)
            if pc_response:
                print(f"🖥️  PC: {pc_response}")
                if gui:
                    gui.add_aria(pc_response)
                speak(pc_response)
                continue

            # ── Normal conversation → Gemini ────────────
            if gui:
                gui.set_state("thinking")
            reply = get_reply(user_input)
            if gui:
                gui.add_aria(reply)
            speak(reply)

        except KeyboardInterrupt:
            farewell = "Alvida!"
            if gui:
                gui.add_aria(farewell)
            speak(farewell)
            break

    pa.terminate()
    print("\n✅ ARIA band ho gayi.")


# ─────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    # ARIA loop → background thread
    aria_thread = threading.Thread(target=aria_loop, daemon=True)
    aria_thread.start()

    # GUI → main thread (Tkinter requirement)
    from gui import launch_gui
    launch_gui()