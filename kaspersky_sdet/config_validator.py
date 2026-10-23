import json
import logging
import os

logger = logging.getLogger(__name__)


def validate_config(path: str) -> bool:
    """
    Проверяет конфигурационный файл.
    Возвращает True, если конфигурация валидна, иначе False.
    """
    if not os.path.isfile(path):
        logger.error(f"Файл не найден: {path}")
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Некорректный JSON в файле {path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {path}: {e}")
        return False

    if not isinstance(config, dict):
        logger.error("Корневой элемент JSON должен быть объектом.")
        return False

    # Проверка наличия всех обязательных полей
    required_fields = {"host", "port", "timeout", "enabled"}
    if not required_fields.issubset(config.keys()):
        missing = required_fields - config.keys()
        logger.error(f"Отсутствуют обязательные поля: {missing}")
        return False

    host = config["host"]
    if not isinstance(host, str) or not host.strip():
        logger.error("Поле 'host' должно быть непустой строкой.")
        return False

    port = config["port"]
    if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
        logger.error("Поле 'port' должно быть целым числом в диапазоне 1..65535.")
        return False

    timeout = config["timeout"]
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not (1 <= timeout <= 300):
        logger.error("Поле 'timeout' должно быть числом в диапазоне 1..300.")
        return False

    enabled = config["enabled"]
    if not isinstance(enabled, bool):
        logger.error("Поле 'enabled' должно быть булевым значением (true/false).")
        return False

    return True