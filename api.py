"""Весь обмен с сервером. Приложение ходит в сеть только через класс ApiClient."""
import json
import ssl
import threading
import urllib.error
import urllib.request

from kivy.clock import Clock


class ApiError(Exception):
    """status=0 значит, что до сервера достучаться не удалось."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def normalize_url(text):
    """'192.168.1.5:8000' -> http://..., 'abc.trycloudflare.com' -> https://..."""
    text = text.strip().rstrip("/")
    if text and "://" not in text:
        host = text.split(":")[0]
        local = host == "localhost" or host.replace(".", "").isdigit()
        text = ("http://" if local else "https://") + text
    return text


def _ssl_context():
    # на Android у Python нет системных сертификатов, поэтому берём их из certifi
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


class ApiClient:
    def __init__(self, path):
        self.path = path
        self.state = {}
        try:
            with open(path, encoding="utf-8") as f:
                self.state = json.load(f)
        except (OSError, ValueError):
            pass

    # ---- сессия на телефоне ----
    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.state, f)
        except OSError:
            pass

    @property
    def logged_in(self):
        return bool(self.state.get("refresh"))

    def set_server(self, text):
        self.state["server"] = normalize_url(text)
        self.save()

    def set_tokens(self, pair):
        self.state["access"] = pair["access_token"]
        self.state["refresh"] = pair["refresh_token"]
        self.save()

    def clear_tokens(self):
        self.state.pop("access", None)
        self.state.pop("refresh", None)
        self.save()

    # ---- запросы ----
    def request(self, method, path, body=None, auth=True, _retry=True):
        """Обычный (блокирующий) запрос. Вызывать только из потока, см. call()."""
        server = self.state.get("server", "")
        if not server:
            raise ApiError(0, "Укажите адрес сервера")
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(server + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        req.add_header("ngrok-skip-browser-warning", "1")  # без этого ngrok подсовывает свою страницу
        if auth and self.state.get("access"):
            req.add_header("Authorization", "Bearer " + self.state["access"])
        try:
            with urllib.request.urlopen(req, timeout=15, context=_ssl_context()) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if e.code == 401 and auth and _retry and self._refresh():
                return self.request(method, path, body, auth, _retry=False)
            raise ApiError(e.code, self._detail(e)) from None
        except (OSError, ValueError):
            raise ApiError(0, "Нет связи с сервером") from None

    def _refresh(self):
        """Меняет refresh-токен на новую пару. True, если получилось."""
        token = self.state.get("refresh")
        if not token:
            return False
        try:
            self.set_tokens(self.request("POST", "/auth/refresh", {"refresh_token": token}, auth=False))
            return True
        except ApiError as e:
            if e.status == 401:  # токен отозван или просрочен: вход нужен заново
                self.clear_tokens()
            return False

    @staticmethod
    def _detail(e):
        try:
            detail = json.loads(e.read().decode())["detail"]
            return detail if isinstance(detail, str) else "Некорректные данные"
        except Exception:
            return "Сервер недоступен" if e.code in (502, 503, 504, 530) else f"Ошибка сервера ({e.code})"

    def call(self, ok, fail, method, path, body=None, auth=True):
        """Запрос в отдельном потоке, чтобы экран не зависал. ok/fail вызываются в основном потоке."""

        def work():
            try:
                result = self.request(method, path, body, auth)
            except ApiError as e:
                Clock.schedule_once(lambda dt, err=e: fail(err))
            except Exception:
                Clock.schedule_once(lambda dt: fail(ApiError(0, "Неизвестная ошибка")))
            else:
                Clock.schedule_once(lambda dt: ok(result))

        threading.Thread(target=work, daemon=True).start()
