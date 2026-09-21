import argparse
from app.shared.config import AppMode, create_config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Запуск приложения с выбором конфигурации'
    )
    parser.add_argument(
        '-m', '--mode',
        type=AppMode,
        default=AppMode.DEV,
        choices=['dev', 'prod', 'test'],
        help='Режим работы приложения (по умолчанию: dev)'
    )
    try:
        args = parser.parse_args()
        config = create_config(AppMode(args.mode))
        print(f"Конфигурация успешно загружена для режима: {config.mode.value.upper()}")
        ...
    except Exception as e:
        print(f"Ошибка при инициализации конфигурации: {e}")