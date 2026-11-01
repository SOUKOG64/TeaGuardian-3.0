from kivy.app import App
from kivy.uix.screenmanager import Screen

from widgets import toast


class LoginScreen(Screen):
    def on_pre_enter(self):
        self.ids.server.text = App.get_running_app().api.state.get("server", "")
        self.ids.password.text = ""

    def submit(self):
        app = App.get_running_app()
        server = self.ids.server.text.strip()
        username = self.ids.username.text.strip()
        password = self.ids.password.text
        if not server:
            return toast("Ошибка: укажите адрес сервера")
        if not username or not password:
            return toast("Ошибка: введите логин и пароль")
        app.api.set_server(server)
        app.fetch("POST", "/auth/login", {"username": username, "password": password},
                  ok=app.logged_in, auth=False)

    def to_register(self):
        server = self.ids.server.text.strip()
        if not server:
            return toast("Ошибка: сначала укажите адрес сервера")
        App.get_running_app().api.set_server(server)
        App.get_running_app().go("register")
