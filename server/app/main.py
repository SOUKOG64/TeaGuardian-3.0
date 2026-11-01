import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api import auth, recipes
from .database import Base, SessionLocal, engine
from .errors import BadRequest, NotFound, TooManyRequests, Unauthorized
from .repositories.users import ensure_roles

log = logging.getLogger("teaguardian")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        ensure_roles(db)
    yield


app = FastAPI(title="TeaGuardian API", version="1.0", lifespan=lifespan,
              description="Сервер чайного дневника. Документация: /docs")
app.include_router(auth.router)
app.include_router(recipes.router)


def _error(status: int, message: str, headers=None) -> JSONResponse:
    return JSONResponse({"detail": message}, status_code=status, headers=headers)


@app.exception_handler(BadRequest)
async def _bad_request(_: Request, e: BadRequest):
    return _error(400, str(e))


@app.exception_handler(Unauthorized)
async def _unauthorized(_: Request, e: Unauthorized):
    return _error(401, str(e), {"WWW-Authenticate": "Bearer"})


@app.exception_handler(NotFound)
async def _not_found(_: Request, e: NotFound):
    return _error(404, str(e))


@app.exception_handler(TooManyRequests)
async def _too_many(_: Request, e: TooManyRequests):
    return _error(429, str(e))


@app.exception_handler(RequestValidationError)
async def _validation(_: Request, e: RequestValidationError):
    # по умолчанию FastAPI отвечает 422, а нужен 400
    parts = [f"{'.'.join(str(x) for x in err['loc'][1:])}: {err['msg']}" for err in e.errors()]
    return _error(400, "Некорректные данные: " + "; ".join(parts))


@app.exception_handler(Exception)
async def _server_error(_: Request, e: Exception):
    log.exception("Необработанная ошибка")
    return _error(500, "Внутренняя ошибка сервера")
