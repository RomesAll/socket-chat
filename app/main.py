import os
from app.shared.config import AppMode, create_config
from app.shared.log_config.config import init_log_config
import uvicorn


if __name__ == '__main__':
    env_mode = os.getenv("CHAT_APP_MODE", "DEV")
    mode_enum = AppMode(env_mode)
    config = create_config(mode_enum)
    init_log_config()
    uvicorn.run('app.fastapi_app:app', port=8003)