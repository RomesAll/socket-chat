import os
from app.shared.config import AppMode, create_config
import uvicorn


if __name__ == '__main__':
    env_mode = os.getenv("CHAT_APP_MODE", "DEV")
    mode_enum = AppMode(env_mode)
    config = create_config(mode_enum)
    uvicorn.run('app.fastapi_app:app', port=8003)