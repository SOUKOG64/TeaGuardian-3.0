from kivy.app import App
from kivy.uix.screenmanager import Screen

from widgets import toast


class RecipeEditScreen(Screen):
    def load(self, r):
        r = r or {}
        self.ids.name.text = r.get("name", "")
        self.ids.temp.text = str(r.get("temperature", ""))
        self.ids.seconds.text = str(r.get("brew_seconds", ""))
        self.ids.rating.text = str(r.get("rating", 0))
        self.ids.category.text = r.get("category") or ""
        self.ids.tags.text = ", ".join(r.get("tags", []))
        self.ids.notes.text = r.get("notes", "")

    def save(self):
        app = App.get_running_app()
        name = self.ids.name.text.strip()
        if not name:
            return toast("Ошибка: введите название")
        try:
            temperature = int(self.ids.temp.text)
            seconds = int(self.ids.seconds.text)
            rating = int(self.ids.rating.text or 0)
        except ValueError:
            return toast("Ошибка: температура, время и оценка должны быть числами")
        if not 0 <= temperature <= 100:
            return toast("Ошибка: температура от 0 до 100")
        if seconds <= 0:
            return toast("Ошибка: время должно быть больше нуля")
        if not 0 <= rating <= 5:
            return toast("Ошибка: оценка от 0 до 5")
        data = {
            "name": name,
            "temperature": temperature,
            "brew_seconds": seconds,
            "rating": rating,
            "category": self.ids.category.text.strip() or None,
            "tags": [t.strip() for t in self.ids.tags.text.split(",") if t.strip()],
            "notes": self.ids.notes.text.strip(),
        }
        if app.current_id is None:
            app.fetch("POST", "/recipes", data, ok=app.saved)
        else:
            app.fetch("PATCH", f"/recipes/{app.current_id}", data, ok=app.saved)
