import argparse, os
from shared.config import AppMode, create_config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Запуск приложения с выбором конфигурации'
    )
    env_mode = os.getenv("CHAT_APP_MODE", "dev").lower()
    parser.add_argument(
        '-m', '--mode',
        type=AppMode,
        required=False,
        default=env_mode,
        choices=['dev', 'prod', 'test'],
        help='Режим работы приложения (по умолчанию: dev)'
    )
    try:
        args = parser.parse_args()
        try:
            mode_enum = AppMode(args.mode)
        except KeyError:
            mode_enum = AppMode(args.mode)
        config = create_config(mode_enum)
        print(f"Конфигурация успешно загружена для режима: {config.mode.value.upper()}")
    except Exception as e:
        print(f"Ошибка при инициализации конфигурации: {e}")