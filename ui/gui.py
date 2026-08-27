"""
Тёмное плавающее окно с пульсирующим кругом (в духе Jarvis из Iron Man).
Работает поверх остальных окон, всегда сверху.

Состояния:
  idle      - тускло-синий, медленная пульсация ("жду 'Hey Jarvis'")
  listening - яркий циан, быстрая пульсация ("слушаю команду")
  thinking  - фиолетовый, вращение ("обрабатываю")
  speaking  - оранжево-белый, резкая пульсация в такт речи ("отвечаю")
"""
import tkinter as tk
import math
import threading
import queue

COLORS = {
    "idle": "#1b3a4b",
    "listening": "#00e5ff",
    "thinking": "#8b5cf6",
    "speaking": "#ffb74d",
}

SPEEDS = {
    "idle": 0.03,
    "listening": 0.12,
    "thinking": 0.08,
    "speaking": 0.18,
}


class JarvisGUI:
    def __init__(self, width=340, height=420):
        self.width = width
        self.height = height
        self.state = "idle"
        self.text = "Жду 'Hey Jarvis'..."
        self._angle = 0.0
        self._queue = queue.Queue()  # для потокобезопасных обновлений из voice-потока

        self.root = tk.Tk()
        self.root.title("Jarvis")
        self.root.geometry(f"{width}x{height}+80+80")
        self.root.configure(bg="#0a0e14")
        self.root.attributes("-topmost", True)  # всегда поверх окон
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root, width=width, height=height - 80,
            bg="#0a0e14", highlightthickness=0
        )
        self.canvas.pack()

        self.label = tk.Label(
            self.root, text=self.text, fg="#8fd6ff", bg="#0a0e14",
            font=("SF Pro Display", 13), wraplength=width - 20, justify="center"
        )
        self.label.pack(pady=(4, 10))

        self._animate()

    # --- Публичные методы (можно вызывать из другого потока) ---
    def set_state(self, state: str):
        self._queue.put(("state", state))

    def set_text(self, text: str):
        self._queue.put(("text", text))

    def start(self):
        """Блокирующий запуск GUI. Вызывать из главного потока."""
        self.root.mainloop()

    # --- Внутреннее ---
    def _process_queue(self):
        try:
            while True:
                kind, value = self._queue.get_nowait()
                if kind == "state":
                    self.state = value
                elif kind == "text":
                    self.text = value
                    self.label.config(text=value)
        except queue.Empty:
            pass

    def _animate(self):
        self._process_queue()
        self.canvas.delete("all")

        cx, cy = self.width / 2, (self.height - 80) / 2
        color = COLORS.get(self.state, COLORS["idle"])
        speed = SPEEDS.get(self.state, 0.03)
        self._angle += speed

        base_r = 70
        pulse = math.sin(self._angle) * 12
        r = base_r + pulse

        # внешнее свечение (несколько полупрозрачных колец через stipple)
        for i, extra in enumerate([36, 24, 12]):
            self.canvas.create_oval(
                cx - r - extra, cy - r - extra, cx + r + extra, cy + r + extra,
                outline=color, width=1
            )

        # основной круг
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=color, width=3
        )

        # внутренние вращающиеся сегменты - "реактор"
        for i in range(8):
            a = self._angle * 2 + i * (math.pi / 4)
            x1 = cx + math.cos(a) * (r - 20)
            y1 = cy + math.sin(a) * (r - 20)
            x2 = cx + math.cos(a) * (r - 5)
            y2 = cy + math.sin(a) * (r - 5)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

        # центральная точка
        self.canvas.create_oval(
            cx - 6, cy - 6, cx + 6, cy + 6, fill=color, outline=""
        )

        self.root.after(30, self._animate)  # ~33 fps
