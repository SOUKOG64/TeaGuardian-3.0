from kivy.app import App
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen

from articles import ARTICLES
from widgets import TeaButton, render_blocks


class KnowScreen(Screen):
    """Список статей «Чайные знания». Работает без сервера."""

    def on_pre_enter(self):
        box = self.ids.box
        box.clear_widgets()
        for i, a in enumerate(ARTICLES):
            btn = TeaButton(text=f"{a['title']}\n{a['summary']}", halign="center", height=dp(72))
            btn.bind(on_release=lambda _, n=i: App.get_running_app().open_article(n))
            box.add_widget(btn)


class ArticleScreen(Screen):
    def show(self, article):
        self.ids.title.text = article["title"]
        self.ids.box.clear_widgets()
        render_blocks(self.ids.box, article["blocks"])
        self.ids.scroll.scroll_y = 1
