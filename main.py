import os

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager

from api import ApiClient
from articles import ARTICLES
from screens.home import HomeScreen
from screens.know import ArticleScreen, KnowScreen
from screens.login import LoginScreen
from screens.recipe_edit import RecipeEditScreen
from screens.recipe_list import RecipeListScreen
from screens.recipe_view import RecipeViewScreen
from screens.register import RegisterScreen
from widgets import confirm, toast

# куда ведёт кнопка «Назад» на телефоне
BACK = {"register": "login", "list": "home", "view": "list", "know": "home", "article": "know"}


class TeaApp(App):
    def build(self):
        self.title = "TeaGuardian"
        Window.clearcolor = (0.98, 0.95, 0.88, 1)
        Window.softinput_mode = "below_target"
        Window.bind(on_keyboard=self.on_key)
        os.makedirs(self.user_data_dir, exist_ok=True)
        self.api = ApiClient(os.path.join(self.user_data_dir, "session.json"))
        self.current = None      # открытый рецепт
        self.current_id = None   # его id (None, когда создаём новый)
        self._busy = 0
        self._busy_timer = None
        self._busy_popup = None
        self.sm = ScreenManager()
        for cls, name in ((LoginScreen, "login"), (RegisterScreen, "register"), (HomeScreen, "home"),
                          (RecipeListScreen, "list"), (RecipeViewScreen, "view"),
                          (RecipeEditScreen, "edit"), (KnowScreen, "know"), (ArticleScreen, "article")):
            self.sm.add_widget(cls(name=name))
        self.sm.current = "home" if self.api.logged_in else "login"
        return self.sm

    # ---- сеть: единая точка для всех запросов к API ----
    def fetch(self, method, path, body=None, ok=None, fail=None, auth=True, quiet=False):
        """quiet=True: без окна «Загрузка…» (для поиска по мере ввода)."""
        if not quiet:
            self._busy_on()

        def done_ok(result):
            if not quiet:
                self._busy_off()
            if ok:
                ok(result)

        def done_fail(error):
            if not quiet:
                self._busy_off()
            (fail or self.on_error)(error)

        self.api.call(done_ok, done_fail, method, path, body, auth)

    def on_error(self, error):
        # 401 вне экранов входа и без сохранённых токенов = сессия закончилась
        if error.status == 401 and self.sm.current not in ("login", "register") and not self.api.logged_in:
            self.go("login")
            return toast("Сессия истекла, войдите снова", 2.5)
        toast(f"Ошибка: {error.message}", 2.5)

    def _busy_on(self):
        self._busy += 1
        if self._busy == 1:
            self._busy_timer = Clock.schedule_once(self._show_busy, 0.4)  # короткие запросы без мигания

    def _show_busy(self, dt):
        self._busy_popup = Popup(title="", separator_height=0, auto_dismiss=False, size_hint=(0.6, 0.18),
                                 content=Label(text="Загрузка…"))
        self._busy_popup.open()

    def _busy_off(self):
        self._busy = max(0, self._busy - 1)
        if self._busy == 0:
            if self._busy_timer:
                self._busy_timer.cancel()
                self._busy_timer = None
            if self._busy_popup:
                self._busy_popup.dismiss()
                self._busy_popup = None

    # ---- навигация ----
    def go(self, name):
        self.sm.current = name

    def on_key(self, window, key, *args):
        if key != 27:
            return False
        current = self.sm.current
        target = ("view" if self.current_id else "list") if current == "edit" else BACK.get(current)
        if target:
            self.go(target)
            return True
        return False  # с главного экрана и экрана входа приложение закрывается

    # ---- действия ----
    def logged_in(self, tokens):
        self.api.set_tokens(tokens)
        self.go("home")

    def logout(self):
        refresh = self.api.state.get("refresh")
        self.api.clear_tokens()  # выходим сразу, не дожидаясь сервера
        if refresh:
            self.api.call(lambda r: None, lambda e: None, "POST", "/auth/logout",
                          {"refresh_token": refresh}, auth=False)
        self.go("login")
        toast("Вы вышли из аккаунта")

    def show_recipe(self, recipe):
        self.current = recipe
        self.current_id = recipe["id"]
        self.sm.get_screen("view").show(recipe)
        self.go("view")

    def open_view(self, recipe_id):
        self.fetch("GET", f"/recipes/{recipe_id}", ok=self.show_recipe)

    def open_edit(self, create):
        if create:
            self.current, self.current_id = None, None
        self.sm.get_screen("edit").load(self.current)
        self.go("edit")

    def saved(self, recipe):
        toast("Сохранено")
        self.show_recipe(recipe)

    def confirm_delete(self):
        confirm("Точно удалить?", lambda: self.fetch("DELETE", f"/recipes/{self.current_id}", ok=self.deleted))

    def deleted(self, _):
        toast("Удалено")
        self.go("list")

    def open_article(self, index):
        self.sm.get_screen("article").show(ARTICLES[index])
        self.go("article")

    def toast(self, text, seconds=1.5):
        toast(text, seconds)


if __name__ == "__main__":
    TeaApp().run()
