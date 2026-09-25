from logging import Filter, LogRecord, INFO, Formatter
import json


class InfoOrDownFilter(Filter):
    """
    Фильтр для проверки уровня логирования. В лог файл: log-info.json
    добавляются только логи уровня не выше INFO
    """
    def filter(self, record: LogRecord) -> bool | LogRecord:
        return INFO >= record.levelno


class JsonFormatter(Formatter):
    """Формат для сохранения в лог файл данные формата json"""
    def format(self, record: LogRecord) -> str:
        log_data = {
            'asctime': self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            'exc_info': record.exc_info,
        }
        return json.dumps(log_data, ensure_ascii=False)