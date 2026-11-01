from kivy.app import App
from kivy.uix.screenmanager import Screen


class HomeScreen(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        self.ids.greeting.text = "Здравствуйте!"
        self.ids.stats.text = ""
        app.fetch("GET", "/auth/me", ok=self.got_user, fail=self.offline)

    def got_user(self, user):
        self.ids.greeting.text = f"Здравствуйте, {user['username']}!"
        App.get_running_app().fetch("GET", "/recipes", ok=self.got_recipes, fail=self.offline)

    def got_recipes(self, items):
        rated = [r["rating"] for r in items if r["rating"]]
        avg = sum(rated) / len(rated) if rated else 0
        self.ids.stats.text = f"Записей: {len(items)} · средняя оценка: {avg:.1f}"

    def offline(self, error):
        # кнопки остаются доступными: можно выйти и сменить адрес сервера
        if error.status == 401:
            return App.get_running_app().on_error(error)
        self.ids.stats.text = f"Ошибка: {error.message}"
