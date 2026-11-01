from kivy.app import App
from kivy.uix.screenmanager import Screen

from widgets import toast


class RegisterScreen(Screen):
    def on_pre_enter(self):
        self.ids.server.text = "Сервер: " + App.get_running_app().api.state.get("server", "")
        for field in ("username", "password", "repeat"):
            self.ids[field].text = ""

    def submit(self):
        app = App.get_running_app()
        username = self.ids.username.text.strip()
        password = self.ids.password.text
        if not 3 <= len(username) <= 32:
            return toast("Ошибка: логин от 3 до 32 символов")
        if len(password) < 6:
            return toast("Ошибка: пароль не короче 6 символов")
        if password != self.ids.repeat.text:
            return toast("Ошибка: пароли не совпадают")
        app.fetch("POST", "/auth/register", {"username": username, "password": password},
                  ok=app.logged_in, auth=False)
