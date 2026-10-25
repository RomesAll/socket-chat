import secrets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jwt import ExpiredSignatureError
from app.business_logic.use_cases.ws import (
    ConnectWebSocketUseCase, DisconnectWebSocketUseCase,
)
from app.di.use_cases import (
    get_connect_ws_use_case, get_disconnect_ws_use_case,
)
from app.infrastructure.security import JWTFacade

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    token: str = Query(...),
    connect_use_case: ConnectWebSocketUseCase = Depends(get_connect_ws_use_case),
    disconnect_use_case: DisconnectWebSocketUseCase = Depends(get_disconnect_ws_use_case),
):
    jwt_facade: JWTFacade = ws.app.state.jwt_facade
    try:
        payload = jwt_facade.jwt_access_manager.decode_token(token)
    except ExpiredSignatureError:
        await ws.close(code=4001, reason="Token expired")
        return
    except Exception:
        await ws.close(code=4002, reason="Invalid token")
        return

    session_key = secrets.token_bytes(32)
    session_id = await connect_use_case.execute(ws, payload.user_id, session_key)

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await disconnect_use_case.execute(ws, payload.user_id, session_id)