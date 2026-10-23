from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from app.business_logic.exceptions import RefreshTokenInActive
from app.presentation_layer.lifespan import lifespan
from fastapi import FastAPI


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="../static"), name="static")


@app.exception_handler(RefreshTokenInActive)
async def refresh_token_inactive_handler(request: Request, exc: RefreshTokenInActive):
    return JSONResponse(
        status_code=401,
        content={"detail": "Сессия истекла. Пожалуйста, войдите снова."},
    )
