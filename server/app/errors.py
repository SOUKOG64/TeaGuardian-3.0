"""Ошибки бизнес-логики. Они ничего не знают про HTTP: в коды их превращает main.py."""


class BadRequest(Exception):
    pass


class Unauthorized(Exception):
    pass


class NotFound(Exception):
    pass


class TooManyRequests(Exception):
    pass
