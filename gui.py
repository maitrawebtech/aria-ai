"""
gui.py — ARIA Visual Interface
Techy + AI Girlfriend aesthetic using Tkinter + Canvas animations.
Auto-launched by aria.py — DO NOT run directly.
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import math
import time
import random
import queue
from datetime import datetime


# ══════════════════════════════════════════════════════
#  THEME — Cyberpunk Rose
# ══════════════════════════════════════════════════════
BG          = "#050510"
PANEL       = "#0a0a1a"
ACCENT1     = "#ff2d78"       # hot pink / rose
ACCENT2     = "#00f0ff"       # cyan
ACCENT3     = "#bf5fff"       # violet
TEXT_MAIN   = "#ffe6f0"
TEXT_DIM    = "#7a6a7a"
TEXT_CHAT_U = "#00f0ff"
TEXT_CHAT_A = "#ff2d78"
GRID_COLOR  = "#0d0d25"
GLOW_PINK   = "#ff2d7844"
GLOW_CYAN   = "#00f0ff33"

# ══════════════════════════════════════════════════════
#  GUI CLASS
# ══════════════════════════════════════════════════════
class AriaGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("A.R.I.A — Adaptive Responsive Intelligence Assistant")
        self.root.geometry("900x680")
        self.root.minsize(800, 600)
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        # State
        self.state        = "idle"   # idle | listening | thinking | speaking
        self.orb_phase    = 0.0
        self.wave_phase   = 0.0
        self.scan_y       = 0
        self.particles    = []
        self.chat_lines   = []
        self._running     = True
        self.gui_queue    = queue.Queue()

        # Load fonts (fallback gracefully)
        self._load_fonts()
        self._build_ui()
        self._spawn_particles(18)
        self._animate()
        self._poll_queue()

    # ─── Fonts ───────────────────────────────────────
    def _load_fonts(self):
        available = list(tkfont.families())
        mono_candidates  = ["Consolas", "Courier New", "Lucida Console", "monospace"]
        title_candidates = ["Orbitron", "Rajdhani", "Exo 2", "Segoe UI", "Tahoma"]
        body_candidates  = ["Segoe UI", "Calibri", "Helvetica", "TkDefaultFont"]

        def pick(candidates):
            for f in candidates:
                if f in available:
                    return f
            return "TkDefaultFont"

        self.font_mono   = (pick(mono_candidates),  10)
        self.font_title  = (pick(title_candidates), 22, "bold")
        self.font_sub    = (pick(title_candidates), 10)
        self.font_status = (pick(mono_candidates),  11, "bold")
        self.font_chat   = (pick(body_candidates),  11)
        self.font_tiny   = (pick(mono_candidates),   8)

    # ─── Build Layout ─────────────────────────────────
    def _build_ui(self):
        # ── Top bar ──────────────────────────────────
        top = tk.Frame(self.root, bg=BG, height=56)
        top.pack(fill="x", padx=0, pady=0)
        top.pack_propagate(False)

        tk.Label(top, text="◈  A.R.I.A", font=self.font_title,
                 bg=BG, fg=ACCENT1).pack(side="left", padx=20, pady=10)

        tk.Label(top, text="ADAPTIVE RESPONSIVE INTELLIGENCE ASSISTANT",
                 font=self.font_sub, bg=BG, fg=TEXT_DIM).pack(side="left", pady=18)

        self.clock_lbl = tk.Label(top, text="", font=self.font_mono,
                                  bg=BG, fg=ACCENT2)
        self.clock_lbl.pack(side="right", padx=20)

        # Separator line
        sep = tk.Canvas(self.root, height=1, bg=BG, highlightthickness=0)
        sep.pack(fill="x")
        sep.create_line(0, 0, 2000, 0, fill=ACCENT1, width=1)

        # ── Main area ────────────────────────────────
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=12, pady=8)

        # Left panel — ORB + status
        left = tk.Frame(main, bg=BG, width=300)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        # Orb canvas
        self.orb_canvas = tk.Canvas(left, width=280, height=280,
                                    bg=BG, highlightthickness=0)
        self.orb_canvas.pack(pady=(10, 6))

        # Status badge
        self.status_frame = tk.Frame(left, bg=PANEL, bd=0)
        self.status_frame.pack(fill="x", padx=8, pady=2)

        self.status_dot = tk.Label(self.status_frame, text="●",
                                   font=("Consolas", 14), bg=PANEL, fg=ACCENT2)
        self.status_dot.pack(side="left", padx=(10, 4), pady=6)

        self.status_lbl = tk.Label(self.status_frame, text="STANDBY",
                                   font=self.font_status, bg=PANEL, fg=ACCENT2)
        self.status_lbl.pack(side="left", pady=6)

        # Waveform canvas
        self.wave_canvas = tk.Canvas(left, width=280, height=60,
                                     bg=PANEL, highlightthickness=0)
        self.wave_canvas.pack(padx=8, pady=6)

        # System info panel
        info_frame = tk.Frame(left, bg=PANEL)
        info_frame.pack(fill="x", padx=8, pady=4)

        self.info_lines = []
        for label in ["NEURAL LINK", "VOICE ENGINE", "PC CONTROL", "STT ENGINE"]:
            row = tk.Frame(info_frame, bg=PANEL)
            row.pack(fill="x", padx=8, pady=2)
            tk.Label(row, text=label, font=self.font_tiny,
                     bg=PANEL, fg=TEXT_DIM, width=14, anchor="w").pack(side="left")
            dot = tk.Label(row, text="◆ ONLINE", font=self.font_tiny,
                           bg=PANEL, fg="#00ff88")
            dot.pack(side="right")
            self.info_lines.append(dot)

        # Right panel — Chat log
        right = tk.Frame(main, bg=BG)
        right.pack(side="right", fill="both", expand=True)

        chat_header = tk.Frame(right, bg=PANEL, height=32)
        chat_header.pack(fill="x")
        chat_header.pack_propagate(False)
        tk.Label(chat_header, text="◤ CONVERSATION LOG ◢",
                 font=self.font_tiny, bg=PANEL, fg=ACCENT3).pack(pady=8)

        # Chat scrollable area
        chat_container = tk.Frame(right, bg=PANEL)
        chat_container.pack(fill="both", expand=True, pady=(1, 0))

        self.chat_text = tk.Text(
            chat_container,
            bg=PANEL, fg=TEXT_MAIN,
            font=self.font_chat,
            wrap="word",
            state="disabled",
            bd=0,
            padx=14, pady=10,
            spacing1=4, spacing3=4,
            insertbackground=ACCENT1,
            selectbackground=ACCENT3,
            relief="flat",
            highlightthickness=0,
        )
        self.chat_text.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(chat_container, command=self.chat_text.yview,
                                 bg=PANEL, troughcolor=PANEL,
                                 activebackground=ACCENT1, width=6)
        scrollbar.pack(side="right", fill="y")
        self.chat_text.configure(yscrollcommand=scrollbar.set)

        # Tag colors
        self.chat_text.tag_configure("user",  foreground=TEXT_CHAT_U, font=(self.font_chat[0], 11, "bold"))
        self.chat_text.tag_configure("aria",  foreground=TEXT_CHAT_A, font=(self.font_chat[0], 11, "bold"))
        self.chat_text.tag_configure("body",  foreground=TEXT_MAIN)
        self.chat_text.tag_configure("sys",   foreground=TEXT_DIM, font=(self.font_chat[0], 9))
        self.chat_text.tag_configure("sep",   foreground=GRID_COLOR)

        # ── Bottom bar ───────────────────────────────
        bottom = tk.Frame(self.root, bg=PANEL, height=30)
        bottom.pack(fill="x", side="bottom")
        bottom.pack_propagate(False)

        self.bottom_lbl = tk.Label(
            bottom,
            text="  ◈ ARIA v2.0  |  MaitraGPT |  Hinglish Mode  |  PC Control: ACTIVE | Developer Ishan",
            font=self.font_tiny, bg=PANEL, fg=TEXT_DIM, anchor="w"
        )
        self.bottom_lbl.pack(side="left", padx=10, pady=6)

        self.fps_lbl = tk.Label(bottom, text="", font=self.font_tiny, bg=PANEL, fg=TEXT_DIM)
        self.fps_lbl.pack(side="right", padx=10)

        # Initial system message
        self._append_chat("sys", None, "◈ System initialized. ARIA is ready.")

    # ─── Particles ────────────────────────────────────
    def _spawn_particles(self, n):
        W, H = 280, 280
        cx, cy = W // 2, H // 2
        for _ in range(n):
            angle  = random.uniform(0, 2 * math.pi)
            radius = random.uniform(30, 110)
            speed  = random.uniform(0.003, 0.012)
            size   = random.uniform(1.5, 3.5)
            color  = random.choice([ACCENT1, ACCENT2, ACCENT3])
            self.particles.append({
                "angle": angle, "radius": radius,
                "speed": speed, "size": size, "color": color,
                "alpha_phase": random.uniform(0, 2 * math.pi),
            })

    # ─── Animation loop ───────────────────────────────
    def _animate(self):
        if not self._running:
            return
        t = time.time()
        self.orb_phase  += 0.025
        self.wave_phase += 0.12

        self._draw_orb(t)
        self._draw_wave(t)
        self._update_clock()

        self.root.after(33, self._animate)   # ~30 fps

    def _draw_orb(self, t):
        c = self.orb_canvas
        c.delete("all")
        W, H = 280, 280
        cx, cy = W // 2, H // 2

        # ── Grid background ──────────────────────────
        grid_step = 22
        for x in range(0, W, grid_step):
            c.create_line(x, 0, x, H, fill=GRID_COLOR, width=1)
        for y in range(0, H, grid_step):
            c.create_line(0, y, W, y, fill=GRID_COLOR, width=1)

        # ── State colors ─────────────────────────────
        state_colors = {
            "idle"      : (ACCENT3, ACCENT1, 0.3),
            "listening" : (ACCENT2, "#ffffff", 0.7),
            "thinking"  : (ACCENT1, ACCENT3, 0.6),
            "speaking"  : (ACCENT1, ACCENT2, 0.8),
        }
        col1, col2, intensity = state_colors.get(self.state, state_colors["idle"])

        # ── Outer glow rings ─────────────────────────
        pulse = 0.5 + 0.5 * math.sin(self.orb_phase * 1.3)
        for i, r in enumerate([118, 108, 96]):
            alpha = int((0.15 + 0.12 * pulse) * (3 - i) * 80)
            alpha = min(255, alpha)
            hex_a = format(alpha, '02x')
            glow_col = col1[:7] + hex_a if len(col1) == 7 else col1
            c.create_oval(cx - r, cy - r, cx + r, cy + r,
                          outline=col1, width=1 + i * 0.4)

        # ── Rotating arc ring ─────────────────────────
        arc_start = (self.orb_phase * 40) % 360
        for i in range(3):
            offset = i * 120
            c.create_arc(cx - 90, cy - 90, cx + 90, cy + 90,
                         start=arc_start + offset,
                         extent=55 + i * 15,
                         outline=col2, style="arc", width=2)

        # ── Inner orb body ───────────────────────────
        r_inner = 62 + 5 * math.sin(self.orb_phase * 0.9)
        r_inner = int(r_inner)

        # Layered fill for depth
        layers = [
            (r_inner,      "#1a0525"),
            (r_inner - 8,  "#2a0835"),
            (r_inner - 18, "#3d0f4a"),
            (r_inner - 28, "#5a1a6a"),
        ]
        for lr, lc in layers:
            c.create_oval(cx - lr, cy - lr, cx + lr, cy + lr,
                          fill=lc, outline="")

        # Orb outline
        c.create_oval(cx - r_inner, cy - r_inner,
                      cx + r_inner, cy + r_inner,
                      outline=col1, width=2)

        # ── Face / core symbol ───────────────────────
        if self.state == "idle":
            # Closed eyes (resting) — two small lines
            for ex in [cx - 12, cx + 12]:
                c.create_line(ex - 6, cy - 4, ex + 6, cy - 4,
                              fill=ACCENT2, width=2, capstyle="round")
            # Gentle smile
            c.create_arc(cx - 14, cy + 2, cx + 14, cy + 18,
                         start=200, extent=140, outline=ACCENT1,
                         style="arc", width=2)

        elif self.state == "listening":
            # Open eyes — glowing circles
            for ex in [cx - 13, cx + 13]:
                c.create_oval(ex - 7, cy - 11, ex + 7, cy + 3,
                              fill="#001a2a", outline=ACCENT2, width=2)
                pulse_r = 3 + 2 * math.sin(self.orb_phase * 3)
                c.create_oval(ex - pulse_r, cy - 4 - pulse_r,
                              ex + pulse_r, cy - 4 + pulse_r,
                              fill=ACCENT2, outline="")
            # Open mouth (listening O)
            c.create_oval(cx - 8, cy + 8, cx + 8, cy + 22,
                          outline=ACCENT2, width=2)

        elif self.state == "thinking":
            # Eyes looking sideways
            for i, ex in enumerate([cx - 13, cx + 13]):
                c.create_oval(ex - 7, cy - 11, ex + 7, cy + 3,
                              fill="#0a0015", outline=ACCENT3, width=2)
                shift = 3 * (1 if i == 0 else -1)
                c.create_oval(ex + shift - 3, cy - 5,
                              ex + shift + 3, cy + 1,
                              fill=ACCENT3, outline="")
            # Thinking dots
            for di, dx in enumerate([-12, 0, 12]):
                delay = math.sin(self.orb_phase * 2 + di * 1.2)
                dy_off = -4 * max(0, delay)
                c.create_oval(cx + dx - 3, cy + 14 + dy_off,
                              cx + dx + 3, cy + 20 + dy_off,
                              fill=ACCENT3, outline="")

        elif self.state == "speaking":
            # Animated speaking eyes
            blink = math.sin(self.orb_phase * 1.1)
            eye_h = max(2, int(8 * (1 - max(0, blink) ** 8)))
            for ex in [cx - 13, cx + 13]:
                c.create_oval(ex - 7, cy - 4 - eye_h,
                              ex + 7, cy - 4 + eye_h,
                              fill="#1a0010", outline=ACCENT1, width=2)
                c.create_oval(ex - 3, cy - 6, ex + 3, cy - 2,
                              fill=ACCENT1, outline="")
            # Animated mouth (speaking wave)
            pts = []
            for i in range(20):
                mx = cx - 15 + i * 1.5
                wave_y = cy + 14 + 5 * math.sin(self.orb_phase * 4 + i * 0.6)
                pts.extend([mx, wave_y])
            if len(pts) >= 4:
                c.create_line(*pts, fill=ACCENT1, width=2, smooth=True)

        # ── Particles ─────────────────────────────────
        for p in self.particles:
            p["angle"] += p["speed"]
            px = cx + p["radius"] * math.cos(p["angle"])
            py = cy + p["radius"] * math.sin(p["angle"])
            blink = 0.4 + 0.6 * math.sin(p["alpha_phase"] + t * 2)
            s = p["size"] * blink
            c.create_oval(px - s, py - s, px + s, py + s,
                          fill=p["color"], outline="")

        # ── Corner brackets (HUD style) ───────────────
        br = 12
        for (x1, y1, x2, y2) in [
            (8, 8, 8 + br, 8), (8, 8, 8, 8 + br),
            (W - 8, 8, W - 8 - br, 8), (W - 8, 8, W - 8, 8 + br),
            (8, H - 8, 8 + br, H - 8), (8, H - 8, 8, H - 8 - br),
            (W - 8, H - 8, W - 8 - br, H - 8), (W - 8, H - 8, W - 8, H - 8 - br),
        ]:
            c.create_line(x1, y1, x2, y2, fill=ACCENT2, width=2)

        # ── State label ───────────────────────────────
        state_text = {
            "idle"      : "◈  STANDBY",
            "listening" : "◉  LISTENING...",
            "thinking"  : "◎  PROCESSING...",
            "speaking"  : "◆  SPEAKING",
        }
        c.create_text(cx, H - 16, text=state_text.get(self.state, ""),
                      fill=col1, font=self.font_tiny, anchor="center")

    def _draw_wave(self, t):
        c = self.wave_canvas
        c.delete("all")
        W, H = 280, 60
        cx, cy = W // 2, H // 2

        c.create_rectangle(0, 0, W, H, fill=PANEL, outline="")

        if self.state == "idle":
            # Flat line with tiny noise
            pts = []
            for x in range(W):
                y = cy + random.uniform(-0.8, 0.8)
                pts.extend([x, y])
            c.create_line(*pts, fill=TEXT_DIM, width=1, smooth=True)

        elif self.state == "listening":
            # Active mic waveform
            pts = []
            for x in range(W):
                amp = 18 + 8 * math.sin(x * 0.04 + self.wave_phase)
                y = cy + amp * math.sin(x * 0.18 + self.wave_phase * 1.5)
                pts.extend([x, y])
            c.create_line(*pts, fill=ACCENT2, width=2, smooth=True)

        elif self.state == "thinking":
            # Pulsing sine
            pts = []
            for x in range(W):
                amp = 12 * abs(math.sin(self.wave_phase * 0.5))
                y = cy + amp * math.sin(x * 0.12 + self.wave_phase)
                pts.extend([x, y])
            c.create_line(*pts, fill=ACCENT3, width=2, smooth=True)

        elif self.state == "speaking":
            # Rich harmonic wave
            pts = []
            for x in range(W):
                y = (cy
                     + 16 * math.sin(x * 0.10 + self.wave_phase)
                     + 8  * math.sin(x * 0.22 + self.wave_phase * 1.7)
                     + 4  * math.sin(x * 0.38 + self.wave_phase * 2.3))
                pts.extend([x, y])
            c.create_line(*pts, fill=ACCENT1, width=2, smooth=True)

        # Border
        c.create_rectangle(0, 0, W - 1, H - 1, outline=TEXT_DIM, width=1)

    def _update_clock(self):
        now = datetime.now()
        self.clock_lbl.config(text=now.strftime("  %H:%M:%S  |  %d %b %Y  "))

        # Update status
        state_map = {
            "idle"      : ("STANDBY",    ACCENT2),
            "listening" : ("LISTENING",  ACCENT2),
            "thinking"  : ("PROCESSING", ACCENT3),
            "speaking"  : ("SPEAKING",   ACCENT1),
        }
        label, color = state_map.get(self.state, ("STANDBY", ACCENT2))
        self.status_lbl.config(text=label, fg=color)
        self.status_dot.config(fg=color)

    # ─── Chat log ─────────────────────────────────────
    def _append_chat(self, role: str, name: str | None, message: str):
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", "\n")

        if role == "user":
            self.chat_text.insert("end", "  YOU  ", "user")
            self.chat_text.insert("end", f"  {message}\n", "body")
        elif role == "aria":
            self.chat_text.insert("end", "  ARIA  ", "aria")
            self.chat_text.insert("end", f"  {message}\n", "body")
        elif role == "sys":
            self.chat_text.insert("end", f"  {message}\n", "sys")

        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    # ─── Queue polling (thread-safe updates) ──────────
    def _poll_queue(self):
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                action = msg.get("action")

                if action == "set_state":
                    self.state = msg["state"]

                elif action == "chat":
                    self._append_chat(msg["role"], msg.get("name"), msg["text"])

                elif action == "sys":
                    self._append_chat("sys", None, msg["text"])

        except Exception:
            pass

        self.root.after(80, self._poll_queue)

    # ─── Public API (called from aria.py threads) ─────
    def set_state(self, state: str):
        """Call from any thread."""
        self.gui_queue.put({"action": "set_state", "state": state})

    def add_user(self, text: str):
        self.gui_queue.put({"action": "chat", "role": "user", "text": text})

    def add_aria(self, text: str):
        self.gui_queue.put({"action": "chat", "role": "aria", "text": text})

    def add_sys(self, text: str):
        self.gui_queue.put({"action": "sys", "text": text})

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self._running = False
        self.root.destroy()


# ══════════════════════════════════════════════════════
#  GLOBAL INSTANCE (imported by aria.py)
# ══════════════════════════════════════════════════════
_gui_instance: AriaGUI | None = None

def get_gui() -> AriaGUI | None:
    return _gui_instance

def launch_gui():
    """Called from aria.py — runs GUI on main thread."""
    global _gui_instance
    _gui_instance = AriaGUI()
    _gui_instance.run()