import math

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import Screen


def vibrate():
    """Вибрация на Android. На компьютере молча ничего не делает."""
    try:
        from jnius import autoclass
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        context = autoclass("android.content.Context")
        activity.getSystemService(context.VIBRATOR_SERVICE).vibrate(1000)
    except Exception:
        pass


class RecipeViewScreen(Screen):
    remaining = NumericProperty(0)
    total = 0
    running = False

    def show(self, r):
        self.stop_timer()
        self.total = r["brew_seconds"]
        self.ids.title.text = r["name"]
        lines = []
        if r["category"]:
            lines.append(r["category"])
        lines.append(f"{r['temperature']} °C · {r['brew_seconds']} с · оценка {r['rating']}/5")
        if r["tags"]:
            lines.append("Теги: " + ", ".join(r["tags"]))
        self.ids.info.text = "\n".join(lines)
        self.ids.notes.text = r["notes"] or "Без заметок"
        self.reset()

    def update_label(self):
        minutes, seconds = divmod(math.ceil(self.remaining), 60)
        self.ids.timer.text = f"{minutes:02d}:{seconds:02d}"

    def start(self):
        if self.running:
            return
        if self.remaining <= 0:
            self.remaining = self.total
        self.running = True
        Clock.schedule_interval(self.tick, 0.25)

    def pause(self):
        self.stop_timer()

    def reset(self):
        self.stop_timer()
        self.remaining = self.total
        self.ids.timer.color = (0.25, 0.15, 0.08, 1)
        self.update_label()

    def stop_timer(self):
        if self.running:
            Clock.unschedule(self.tick)
            self.running = False

    def tick(self, dt):
        self.remaining -= dt
        if self.remaining <= 0:
            self.remaining = 0
            self.stop_timer()
            self.ids.timer.color = (0.7, 0.1, 0.1, 1)
            vibrate()
            App.get_running_app().toast("Чай готов!", 3)
        self.update_label()

    def on_leave(self):
        self.stop_timer()
