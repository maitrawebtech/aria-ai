"""
app.py — ARIA PC Controller (Gemini NLU Edition)
Natural Hinglish commands samjhta hai — rule-based nahi, AI-based hai.
Import: from app import handle_command
"""

import os
import re
import json
import shutil
import platform
import subprocess
import webbrowser
import time
from pathlib import Path
from datetime import datetime

# ─── Optional deps ────────────────────────────────────
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX   = platform.system() == "Linux"
IS_MAC     = platform.system() == "Darwin"

# ─── Common folders ───────────────────────────────────
COMMON_FOLDERS = {
    "desktop"   : Path.home() / "Desktop",
    "downloads" : Path.home() / "Downloads",
    "documents" : Path.home() / "Documents",
    "pictures"  : Path.home() / "Pictures",
    "videos"    : Path.home() / "Videos",
    "music"     : Path.home() / "Music",
    "home"      : Path.home(),
    "temp"      : Path(os.environ.get("TEMP", "/tmp")),
}

WEBSITES = {
    "youtube"       : "https://youtube.com",
    "google"        : "https://google.com",
    "github"        : "https://github.com",
    "gmail"         : "https://mail.google.com",
    "whatsapp"      : "https://web.whatsapp.com",
    "instagram"     : "https://instagram.com",
    "twitter"       : "https://twitter.com",
    "x"             : "https://x.com",
    "linkedin"      : "https://linkedin.com",
    "netflix"       : "https://netflix.com",
    "amazon"        : "https://amazon.in",
    "flipkart"      : "https://flipkart.com",
    "reddit"        : "https://reddit.com",
    "chatgpt"       : "https://chat.openai.com",
    "claude"        : "https://claude.ai",
    "stackoverflow" : "https://stackoverflow.com",
    "spotify"       : "https://open.spotify.com",
    "maps"          : "https://maps.google.com",
}


# ══════════════════════════════════════════════════════
#  GEMINI NLU — Intent Extractor
# ══════════════════════════════════════════════════════
_genai_client = None

def _get_client():
    global _genai_client
    if _genai_client is None:
        from google import genai
        from dotenv import load_dotenv
        load_dotenv()
        _genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _genai_client

NLU_PROMPT = """
Tu ek PC command extractor hai. User Hinglish mein bolta hai (Hindi + English mixed, Indian style).
Tera kaam sirf intent aur details extract karna hai JSON mein.

SIRF JSON return kar. Koi explanation nahi. Koi markdown nahi. Sirf raw JSON.

Format:
{"intent": "<intent>", "target": "<name or null>", "value": <number or null>, "extra": "<string or null>"}

Intents:
- open_app       : koi app/software kholna
- close_app      : koi app band karna
- open_folder    : folder kholna
- open_file      : file kholna
- open_website   : website browser mein kholna
- search_web     : google pe search karna
- play_youtube   : youtube pe kuch bajana ya search karna
- set_volume     : volume ek specific number pe set karna (value mein 0-100)
- volume_up      : volume badhana
- volume_down    : volume kam karna
- mute           : mute karna
- unmute         : unmute / sound wapas lana
- screenshot     : screen capture karna
- lock_screen    : screen lock karna
- shutdown       : PC band karna
- restart        : PC restart karna
- sleep          : PC sleep mode mein daalna
- cancel_shutdown: shutdown cancel karna
- battery        : battery status poochna
- system_info    : system/CPU/RAM info
- get_time       : time ya date poochna
- create_folder  : naya folder banana
- create_file    : naya file banana
- delete         : kuch delete karna
- search_files   : file system mein file dhundna
- list_apps      : chal rahe apps dikhana
- clipboard_copy : clipboard mein copy karna
- type_text      : keyboard se kuch type karna
- hotkey         : keyboard shortcut (extra mein "ctrl,c" format)
- not_pc_command : ye PC se related nahi, normal conversation hai

Examples:
"notepad khol de" -> {"intent":"open_app","target":"notepad","value":null,"extra":null}
"yaar spotify chala na" -> {"intent":"open_app","target":"spotify","value":null,"extra":null}
"YouTube pe lofi music baja" -> {"intent":"play_youtube","target":"lofi music","value":null,"extra":null}
"awaaz thodi zyada kar" -> {"intent":"volume_up","target":null,"value":null,"extra":null}
"volume 60 kar de" -> {"intent":"set_volume","target":null,"value":60,"extra":null}
"downloads wala folder dikha" -> {"intent":"open_folder","target":"downloads","value":null,"extra":null}
"ek screenshot le mere liye" -> {"intent":"screenshot","target":null,"value":null,"extra":null}
"battery kitni bachi" -> {"intent":"battery","target":null,"value":null,"extra":null}
"aaj kaun sa din hai" -> {"intent":"get_time","target":null,"value":null,"extra":null}
"discord band kar" -> {"intent":"close_app","target":"discord","value":null,"extra":null}
"python kya hai" -> {"intent":"not_pc_command","target":null,"value":null,"extra":null}
"computer thoda restart kar" -> {"intent":"restart","target":null,"value":null,"extra":null}
"ctrl c daba" -> {"intent":"hotkey","target":null,"value":null,"extra":"ctrl,c"}
"instagram khol" -> {"intent":"open_website","target":"instagram","value":null,"extra":null}
"google pe react tutorial search kar" -> {"intent":"search_web","target":"react tutorial","value":null,"extra":null}
"mujhe time bata" -> {"intent":"get_time","target":null,"value":null,"extra":null}
"""

def _extract_intent(user_text: str) -> dict:
    """Gemini se intent extract karo."""
    try:
        from google.genai import types
        client = _get_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=NLU_PROMPT,
                max_output_tokens=150,
                temperature=0.1,
            )
        )
        raw = response.text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[NLU Error] {e}")
        return {"intent": "not_pc_command", "target": None, "value": None, "extra": None}


# ══════════════════════════════════════════════════════
#  ACTION FUNCTIONS
# ══════════════════════════════════════════════════════

def _run(cmd: str):
    try:
        subprocess.Popen(cmd, shell=True)
        return True
    except Exception as e:
        print(f"[Run Error] {e}")
        return False

def _open_path(path):
    path = str(path)
    if IS_WINDOWS:
        os.startfile(path)
    elif IS_MAC:
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

# ── Apps ──────────────────────────────────────────────
APP_ALIASES = {
    # ── System ──────────────────────────────────────
    "notepad"            : "notepad.exe",
    "note pad"           : "notepad.exe",
    "calculator"         : "calc.exe",
    "calc"               : "calc.exe",
    "paint"              : "mspaint.exe",
    "ms paint"           : "mspaint.exe",
    "wordpad"            : "wordpad.exe",
    "cmd"                : "cmd.exe",
    "command prompt"     : "cmd.exe",
    "powershell"         : "powershell.exe",
    "task manager"       : "taskmgr.exe",
    "taskmgr"            : "taskmgr.exe",
    "control panel"      : "control.exe",
    "control"            : "control.exe",
    "settings"           : "ms-settings:",
    "windows settings"   : "ms-settings:",
    "file explorer"      : "explorer.exe",
    "explorer"           : "explorer.exe",
    "my computer"        : "explorer.exe",
    "registry"           : "regedit.exe",
    "regedit"            : "regedit.exe",
    "snipping tool"      : "snippingtool.exe",
    "snip"               : "snippingtool.exe",
    "screenshot tool"    : "snippingtool.exe",
    "clock"              : "ms-clock:",
    "camera"             : "microsoft.windows.camera:",
    "weather"            : "bingweather:",
    "maps"               : "bingmaps:",

    # ── Browsers ────────────────────────────────────
    "chrome"             : "chrome",
    "google chrome"      : "chrome",
    "firefox"            : "firefox",
    "mozilla"            : "firefox",
    "mozilla firefox"    : "firefox",
    "edge"               : "msedge",
    "microsoft edge"     : "msedge",
    "brave"              : "brave",
    "brave browser"      : "brave",
    "opera"              : "opera",

    # ── Dev Tools ───────────────────────────────────
    "vscode"             : "code",
    "vs code"            : "code",
    "visual studio code" : "code",
    "visual studio"      : "code",
    "git bash"           : "git-bash",
    "gitbash"            : "git-bash",
    "postman"            : "postman",
    "android studio"     : "studio64",
    "figma"              : "figma",

    # ── Office ──────────────────────────────────────
    "word"               : "WINWORD",
    "ms word"            : "WINWORD",
    "microsoft word"     : "WINWORD",
    "excel"              : "EXCEL",
    "ms excel"           : "EXCEL",
    "microsoft excel"    : "EXCEL",
    "powerpoint"         : "POWERPNT",
    "ms powerpoint"      : "POWERPNT",
    "ppt"                : "POWERPNT",
    "outlook"            : "OUTLOOK",
    "ms outlook"         : "OUTLOOK",
    "onenote"            : "ONENOTE",
    "one note"           : "ONENOTE",
    "teams"              : "teams",
    "microsoft teams"    : "teams",

    # ── Media ───────────────────────────────────────
    "vlc"                : "vlc",
    "vlc media player"   : "vlc",
    "spotify"            : "spotify",
    "obs"                : "obs64",
    "obs studio"         : "obs64",

    # ── Communication ───────────────────────────────
    "discord"            : "discord",
    "telegram"           : "telegram",
    "whatsapp"           : "whatsapp",
    "zoom"               : "zoom",
    "slack"              : "slack",

    # ── Utilities ───────────────────────────────────
    "winrar"             : "winrar",
    "7zip"               : "7zfm",
    "7-zip"              : "7zfm",
    "steam"              : "steam",
}

def open_app(app_name: str) -> str:
    if not app_name:
        return "Kaunsa app kholun bolo?"
    name = app_name.lower().strip()
    cmd = APP_ALIASES.get(name, name)
    if cmd.endswith(":"):
        # ms-settings: / ms-clock: style URIs
        _run(f"start {cmd}")
    elif cmd.endswith(".exe"):
        # Direct .exe
        _run(f"start {cmd}")
    else:
        # Named executable in PATH (chrome, code, spotify, etc.)
        _run(cmd)
    return f"{app_name} khol diya!"

def close_app(app_name: str) -> str:
    if not app_name:
        return "Kaunsa app band karun?"
    if IS_WINDOWS:
        _run(f"taskkill /f /im {app_name}.exe")
        _run(f"taskkill /f /im {app_name}")
    if HAS_PSUTIL:
        killed = []
        for proc in psutil.process_iter(['name', 'pid']):
            if app_name.lower() in proc.info['name'].lower():
                try:
                    proc.kill()
                    killed.append(proc.info['name'])
                except:
                    pass
        if killed:
            return f"{', '.join(set(killed))} band kar diya!"
    return f"{app_name} band karne ki koshish ki."

# ── Folders ───────────────────────────────────────────
def open_folder(folder_name: str) -> str:
    if not folder_name:
        return "Kaunsa folder kholun?"
    name = folder_name.lower().strip()
    if name in COMMON_FOLDERS:
        _open_path(COMMON_FOLDERS[name])
        return f"{folder_name} folder khol diya!"
    p = Path(folder_name)
    if p.exists() and p.is_dir():
        _open_path(p)
        return f"Folder khol diya!"
    results = [r for r in Path.home().rglob(folder_name) if r.is_dir()]
    if results:
        _open_path(results[0])
        return f"{results[0].name} folder mila aur khol diya!"
    return f"'{folder_name}' naam ka folder nahi mila."

# ── Files ─────────────────────────────────────────────
def open_file(file_name: str) -> str:
    if not file_name:
        return "Kaunsi file kholun?"
    p = Path(file_name)
    if p.exists():
        _open_path(p)
        return f"File khol di!"
    for d in [Path.home() / "Desktop", Path.home() / "Downloads",
              Path.home() / "Documents", Path.home()]:
        results = list(d.rglob(file_name))
        if results:
            _open_path(results[0])
            return f"{results[0].name} khol di!"
    return f"'{file_name}' file nahi mili."

def create_folder(name: str) -> str:
    base = Path.home() / "Desktop"
    new_dir = base / name
    new_dir.mkdir(parents=True, exist_ok=True)
    _open_path(new_dir)
    return f"'{name}' naam ka folder Desktop pe bana diya!"

def create_file_cmd(filename: str) -> str:
    base = Path.home() / "Desktop"
    new_file = base / filename
    new_file.touch(exist_ok=True)
    return f"'{filename}' file Desktop pe bana di!"

def delete_target(target: str) -> str:
    if not target:
        return "Kya delete karun?"
    p = Path(target)
    if not p.exists():
        p = Path.home() / "Desktop" / target
    if p.exists():
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return f"{p.name} delete kar diya!"
    return f"'{target}' nahi mila delete karne ke liye."

def search_files(query: str) -> str:
    if not query:
        return "Kya dhundun?"
    results = list(Path.home().rglob(f"*{query}*"))[:8]
    if not results:
        return f"'{query}' se koi file nahi mila."
    lines = [f"  {r}" for r in results]
    return "Ye mila:\n" + "\n".join(lines)

# ── Web ───────────────────────────────────────────────
def open_website(site: str) -> str:
    if not site:
        return "Kaunsi website kholun?"
    name = site.lower().strip()
    if name in WEBSITES:
        webbrowser.open(WEBSITES[name])
        return f"{site} khol diya browser mein!"
    for key, url in WEBSITES.items():
        if key in name:
            webbrowser.open(url)
            return f"{key} khol diya!"
    url = site if site.startswith("http") else f"https://{site}"
    webbrowser.open(url)
    return f"{site} khol diya!"

def search_web(query: str) -> str:
    if not query:
        return "Kya search karun?"
    q = query.replace(" ", "+")
    webbrowser.open(f"https://google.com/search?q={q}")
    return f"'{query}' Google pe search kar diya!"

def play_youtube(query: str) -> str:
    if not query:
        return "Kya bajaaun YouTube pe?"
    q = query.replace(" ", "+")
    webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
    return f"YouTube pe '{query}' search kar diya!"

# ── Volume ────────────────────────────────────────────
def _get_pycaw_vol():
    if not HAS_PYCAW or not IS_WINDOWS:
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except:
        return None

def set_volume(level: int) -> str:
    level = max(0, min(100, level))
    vol = _get_pycaw_vol()
    if vol:
        vol.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume {level} percent kar diya!"
    return "Volume control nahi ho saka."

def volume_up() -> str:
    vol = _get_pycaw_vol()
    if vol:
        current = int(vol.GetMasterVolumeLevelScalar() * 100)
        new_level = min(100, current + 20)
        vol.SetMasterVolumeLevelScalar(new_level / 100, None)
        return f"Volume badha diya, ab {new_level} percent hai!"
    return "Volume control nahi ho saka."

def volume_down() -> str:
    vol = _get_pycaw_vol()
    if vol:
        current = int(vol.GetMasterVolumeLevelScalar() * 100)
        new_level = max(0, current - 20)
        vol.SetMasterVolumeLevelScalar(new_level / 100, None)
        return f"Volume kam kar diya, ab {new_level} percent hai!"
    return "Volume control nahi ho saka."

def mute_volume() -> str:
    vol = _get_pycaw_vol()
    if vol:
        vol.SetMute(1, None)
        return "Mute kar diya!"
    return "Mute nahi ho saka."

def unmute_volume() -> str:
    vol = _get_pycaw_vol()
    if vol:
        vol.SetMute(0, None)
        return "Unmute kar diya, awaaz wapas aa gayi!"
    return "Unmute nahi ho saka."

# ── System ────────────────────────────────────────────
def take_screenshot() -> str:
    if not HAS_PYAUTOGUI:
        return "pyautogui install karo pehle."
    fname = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    save_path = Path.home() / "Desktop" / fname
    img = pyautogui.screenshot()
    img.save(str(save_path))
    return f"Screenshot le liya! Desktop pe {fname} save ho gaya."

def lock_screen() -> str:
    if IS_WINDOWS:
        _run("rundll32.exe user32.dll,LockWorkStation")
        return "Screen lock kar di!"
    return "Is platform pe lock supported nahi."

def shutdown_pc(delay: int = 0) -> str:
    if IS_WINDOWS:
        _run(f"shutdown /s /t {delay}")
        return f"PC {delay} second mein band ho jayega!"
    return "Is platform pe shutdown supported nahi."

def restart_pc(delay: int = 0) -> str:
    if IS_WINDOWS:
        _run(f"shutdown /r /t {delay}")
        return f"PC {delay} second mein restart hoga!"
    return "Is platform pe restart supported nahi."

def sleep_pc() -> str:
    if IS_WINDOWS:
        _run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "PC sleep mode mein ja raha hai, good night!"
    return "Is platform pe sleep supported nahi."

def cancel_shutdown() -> str:
    if IS_WINDOWS:
        _run("shutdown /a")
        return "Shutdown cancel kar diya, PC chalta rahega!"
    return "Cancel nahi ho saka."

def get_battery() -> str:
    if not HAS_PSUTIL:
        return "Battery check karne ke liye psutil chahiye."
    batt = psutil.sensors_battery()
    if not batt:
        return "Battery info nahi mili, shayad desktop PC hai."
    status = "charging ho rahi hai" if batt.power_plugged else "battery pe chal raha hai"
    return f"Battery {batt.percent:.0f} percent hai aur {status}."

def get_system_info() -> str:
    info = [f"System {platform.system()} {platform.release()} chal raha hai."]
    if HAS_PSUTIL:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        info.append(f"CPU {cpu} percent use ho raha hai.")
        info.append(f"RAM mein {ram.percent} percent use ho rahi hai, matlab {ram.used // 1024**3} GB out of {ram.total // 1024**3} GB.")
    return " ".join(info)

def get_time() -> str:
    now = datetime.now()
    return f"Abhi {now.strftime('%I:%M %p')} baj rahe hain. Aaj {now.strftime('%d %B %Y')} hai."

def list_running_apps() -> str:
    if not HAS_PSUTIL:
        return "psutil chahiye running apps dekhne ke liye."
    names = sorted(set(
        p.info['name'] for p in psutil.process_iter(['name']) if p.info['name']
    ))[:20]
    return "Ye apps chal rahe hain:\n" + "\n".join(f"  {n}" for n in names)

def copy_to_clipboard(text: str) -> str:
    if not text:
        return "Kya copy karun?"
    if HAS_CLIPBOARD:
        pyperclip.copy(text)
        return "Clipboard mein copy ho gaya!"
    return "pyperclip install karo."

def type_text(text: str) -> str:
    if not text:
        return "Kya type karun?"
    if HAS_PYAUTOGUI:
        time.sleep(0.5)
        pyautogui.typewrite(text, interval=0.05)
        return "Type kar diya!"
    return "pyautogui chahiye."

def do_hotkey(extra: str) -> str:
    if not HAS_PYAUTOGUI or not extra:
        return "Hotkey nahi daba saka."
    keys = [k.strip() for k in extra.split(",")]
    pyautogui.hotkey(*keys)
    return f"{' + '.join(keys)} daba diya!"


# ══════════════════════════════════════════════════════
#  INTENT → ACTION MAP
# ══════════════════════════════════════════════════════
INTENT_MAP = {
    "open_app"        : lambda d: open_app(d.get("target") or ""),
    "close_app"       : lambda d: close_app(d.get("target") or ""),
    "open_folder"     : lambda d: open_folder(d.get("target") or ""),
    "open_file"       : lambda d: open_file(d.get("target") or ""),
    "open_website"    : lambda d: open_website(d.get("target") or ""),
    "search_web"      : lambda d: search_web(d.get("target") or ""),
    "play_youtube"    : lambda d: play_youtube(d.get("target") or ""),
    "set_volume"      : lambda d: set_volume(int(d.get("value") or 50)),
    "volume_up"       : lambda d: volume_up(),
    "volume_down"     : lambda d: volume_down(),
    "mute"            : lambda d: mute_volume(),
    "unmute"          : lambda d: unmute_volume(),
    "screenshot"      : lambda d: take_screenshot(),
    "lock_screen"     : lambda d: lock_screen(),
    "shutdown"        : lambda d: shutdown_pc(int(d.get("value") or 0)),
    "restart"         : lambda d: restart_pc(int(d.get("value") or 0)),
    "sleep"           : lambda d: sleep_pc(),
    "cancel_shutdown" : lambda d: cancel_shutdown(),
    "battery"         : lambda d: get_battery(),
    "system_info"     : lambda d: get_system_info(),
    "get_time"        : lambda d: get_time(),
    "create_folder"   : lambda d: create_folder(d.get("target") or "NewFolder"),
    "create_file"     : lambda d: create_file_cmd(d.get("target") or "newfile.txt"),
    "delete"          : lambda d: delete_target(d.get("target") or ""),
    "search_files"    : lambda d: search_files(d.get("target") or ""),
    "list_apps"       : lambda d: list_running_apps(),
    "clipboard_copy"  : lambda d: copy_to_clipboard(d.get("target") or ""),
    "type_text"       : lambda d: type_text(d.get("target") or ""),
    "hotkey"          : lambda d: do_hotkey(d.get("extra") or ""),
}


# ══════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ══════════════════════════════════════════════════════
def handle_command(user_text: str) -> str | None:
    """
    aria.py yahi call karta hai.
    PC command hai to response string return karo.
    Normal baat hai to None return karo (Gemini handle karega).
    """
    if not user_text or len(user_text.strip()) < 2:
        return None

    print(f"[NLU] → '{user_text}'")
    intent_data = _extract_intent(user_text)
    intent = intent_data.get("intent", "not_pc_command")
    print(f"[NLU] Intent: {intent} | Target: {intent_data.get('target')} | Value: {intent_data.get('value')}")

    if intent == "not_pc_command" or intent not in INTENT_MAP:
        return None

    try:
        return INTENT_MAP[intent](intent_data)
    except Exception as e:
        print(f"[Action Error] {e}")
        return f"Kuch gadbad ho gayi: {e}"


# ── Quick test ────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "notepad khol de",
        "yaar spotify chala na",
        "YouTube pe lofi music baja",
        "awaaz thodi zyada kar",
        "downloads wala folder dikha",
        "ek screenshot le mere liye",
        "battery kitni bachi",
        "python kya hai",
        "discord band kar",
        "computer restart kar",
    ]
    for t in tests:
        print(f"\n> {t}")
        r = handle_command(t)
        print(f"  → {r}")