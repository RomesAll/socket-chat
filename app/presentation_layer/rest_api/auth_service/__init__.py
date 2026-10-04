from fastapi import FastAPI
from app.presentation_layer.rest_api.auth_service.auth import route as auth_route
from app.presentation_layer.rest_api.auth_service.check_tokens import route as ch_token_route
from app.presentation_layer.rest_api.auth_service.verify_code import route as verify_code_route
from app.presentation_layer.rest_api.auth_service.roles import route as role_route


def register_route(app: FastAPI):
    api_v1 = '/api/v1'
    app.include_router(auth_route, prefix=api_v1)
    app.include_router(ch_token_route, prefix=api_v1)
    app.include_router(verify_code_route, prefix=api_v1)
    app.include_router(role_route, prefix=api_v1)


__version__ = 'v0.3.0'
__author__ = 'RomesAll'
__all__ = [
    'register_route'
]