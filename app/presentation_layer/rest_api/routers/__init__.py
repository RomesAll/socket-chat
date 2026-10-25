from fastapi import FastAPI
from .auth import router as auth_router
from .chats import router as chats_router
from .health import router as health_router
from .invites import router as invites_router
from .messages import router as msg_router
from .reports import router as reports_router
from .rooms import router as room_router
from .users import router as user_router
from .websocket import router as wb_router
from .tokens import router as tokens_router
from app.presentation_layer.rest_api.routers.audit import router as audit_router


def api_register(app: FastAPI):
    """Регистрация api"""
    api_v1 = '/api/v1'
    app.include_router(wb_router)
    app.include_router(auth_router, prefix=api_v1)
    app.include_router(chats_router, prefix=api_v1)
    app.include_router(health_router, prefix=api_v1)
    app.include_router(invites_router, prefix=api_v1)
    app.include_router(msg_router, prefix=api_v1)
    app.include_router(reports_router, prefix=api_v1)
    app.include_router(room_router, prefix=api_v1)
    app.include_router(user_router, prefix=api_v1)
    app.include_router(tokens_router, prefix=api_v1)
    app.include_router(audit_router, prefix=api_v1)


__version__ = 'v1.0.0'
__author__ = 'RomesAll'