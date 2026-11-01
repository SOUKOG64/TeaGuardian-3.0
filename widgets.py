"""Общие элементы оформления: одинаковые кнопки, поля, сообщения."""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput


class TeaButton(Button):
    pass


class TeaInput(TextInput):
    pass


class TeaLabel(Label):
    pass


class TeaSpinner(Spinner):
    pass


class TipBox(BoxLayout):
    """Выделенная плашка для советов и цитат."""


def toast(text, seconds=1.5):
    """Всплывающее сообщение («Сохранено», «Ошибка: ...»)."""
    popup = Popup(title="", separator_height=0, content=Label(text=text, halign="center"),
                  size_hint=(0.8, 0.2))
    popup.open()
    Clock.schedule_once(lambda dt: popup.dismiss(), seconds)


def confirm(text, on_yes):
    box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
    box.add_widget(Label(text=text))
    row = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(48))
    popup = Popup(title="Подтверждение", content=box, size_hint=(0.85, 0.35))
    yes, no = TeaButton(text="Да"), TeaButton(text="Нет")
    yes.bind(on_release=lambda *_: (popup.dismiss(), on_yes()))
    no.bind(on_release=popup.dismiss)
    row.add_widget(yes)
    row.add_widget(no)
    box.add_widget(row)
    popup.open()


def render_blocks(box, blocks):
    """Раскладывает блоки статьи (см. articles.py) по экрану."""
    brown = (0.45, 0.28, 0.15, 1)
    for kind, *data in blocks:
        if kind == "h":
            box.add_widget(TeaLabel(text=f"[b]{data[0]}[/b]", markup=True, font_size=dp(19), color=brown))
        elif kind == "p":
            box.add_widget(TeaLabel(text=data[0]))
        elif kind == "list":
            box.add_widget(TeaLabel(text="\n".join(f"•  {i}" for i in data[0])))
        elif kind == "def":
            for term, desc in data[0]:
                box.add_widget(TeaLabel(text=f"[b]{term}[/b]\n{desc}", markup=True))
        elif kind in ("tip", "quote"):
            tip = TipBox()
            tip.add_widget(TeaLabel(text=data[0], italic=(kind == "quote")))
            box.add_widget(tip)
