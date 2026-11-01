from urllib.parse import urlencode

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen

from widgets import TeaButton, TeaLabel

ALL = "Все категории"


class RecipeListScreen(Screen):
    seq = 0
    _timer = None

    def on_pre_enter(self):
        App.get_running_app().fetch("GET", "/categories", ok=self.got_categories)

    def got_categories(self, names):
        spinner = self.ids.cat
        spinner.values = [ALL] + names
        if spinner.text not in spinner.values:
            spinner.text = ALL
        self.reload()

    def schedule(self):
        """Поиск по мере ввода: ждём 0.4 с после последней буквы."""
        if self._timer:
            self._timer.cancel()
        self._timer = Clock.schedule_once(self.reload, 0.4)

    def reload(self, *_):
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self.seq += 1
        seq = self.seq
        params = {}
        if self.ids.search.text.strip():
            params["search"] = self.ids.search.text.strip()
        if self.ids.cat.text != ALL:
            params["category"] = self.ids.cat.text
        path = "/recipes" + ("?" + urlencode(params) if params else "")
        App.get_running_app().fetch("GET", path, ok=lambda items: self.show(seq, items), quiet=True)

    def show(self, seq, items):
        if seq != self.seq:  # пришёл ответ на уже устаревший запрос
            return
        app = App.get_running_app()
        box = self.ids.box
        box.clear_widgets()
        if not items:
            box.add_widget(TeaLabel(text="Ничего не найдено"))
        for r in items:
            head = f"{r['category']} · " if r["category"] else ""
            btn = TeaButton(
                text=f"{r['name']}\n{head}{r['temperature']} °C · {r['brew_seconds']} с · {r['rating']}/5",
                halign="center", height=dp(72))
            btn.bind(on_release=lambda _, rid=r["id"]: app.open_view(rid))
            box.add_widget(btn)
