import json
import os
import pytest
from config_validator import validate_config

@pytest.fixture(scope="module")
def valid_config_dict():
    """Фикстура с эталонным валидным конфигом."""
    return {
        "host": "localhost",
        "port": 8080,
        "timeout": 30,
        "enabled": True
    }

@pytest.fixture
def temp_json_file(tmp_path, request):
    """
    Фикстура, создающая временный JSON-файл.
    """
    data = getattr(request, "param", None)
    file_path = tmp_path / "config.json"
    
    if data is not None:
        with open(file_path, 'w', encoding='utf-8') as f:
            if isinstance(data, str):
                f.write(data) # Для тестов с битым JSON
            else:
                json.dump(data, f)
    
    return str(file_path)

def pytest_runtest_logreport(report):
    """Хук для вывода диагностики при падении теста."""
    if report.when == "call" and report.failed:
        print(f"\n[DIAGNOSTIC] Тест упал: {report.nodeid}")
        print(f"[DIAGNOSTIC] Длительность: {report.duration:.4f} сек.")

@pytest.mark.parametrize("config_data", [
    {"host": "localhost", "port": 8080, "timeout": 30, "enabled": True}, # Валид
    {"host": "a", "port": 1, "timeout": 1, "enabled": False},            # Границы (мин)
    {"host": "test", "port": 65535, "timeout": 300, "enabled": True},    # Границы (макс)
    {"host": "localhost", "port": 8080, "timeout": 1.5, "enabled": True} # Float timeout
])
def test_positive_scenarios(temp_json_file, config_data):
    """Позитивные тесты: валидные конфигурации возвращают True."""
    # Записываем данные в файл вручную, так как indirect не удобен для словарей
    with open(temp_json_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f)
    
    assert validate_config(temp_json_file) is True


@pytest.mark.parametrize("config_data", [
    {"host": "localhost", "port": 0, "timeout": 30, "enabled": True},      # port < 1
    {"host": "localhost", "port": 65536, "timeout": 30, "enabled": True},  # port > 65535
    {"host": "localhost", "port": 8080, "timeout": 0, "enabled": True},    # timeout < 1
    {"host": "localhost", "port": 8080, "timeout": 301, "enabled": True},  # timeout > 300
    {"host": "", "port": 8080, "timeout": 30, "enabled": True},            # host пустой
    {"host": "   ", "port": 8080, "timeout": 30, "enabled": True},         # host пробелы
    {"host": "localhost", "port": "8080", "timeout": 30, "enabled": True}, # port строка
    {"host": "localhost", "port": 8080, "timeout": 30, "enabled": "true"}, # enabled строка
    {"host": "localhost", "port": 8080, "enabled": True},                  # нет timeout
])
def test_negative_scenarios(temp_json_file, config_data):
    """Негативные тесты: некорректные поля возвращают False."""
    with open(temp_json_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f)
    
    assert validate_config(temp_json_file) is False


def test_invalid_json(temp_json_file):
    """Тест на битый JSON."""
    with open(temp_json_file, 'w', encoding='utf-8') as f:
        f.write('{"host": "localhost",')
    
    assert validate_config(temp_json_file) is False


def test_json_not_object(temp_json_file):
    """Тест на JSON, корень которого не объект."""
    with open(temp_json_file, 'w', encoding='utf-8') as f:
        json.dump([1, 2, 3], f)
    
    assert validate_config(temp_json_file) is False


def test_file_not_found(tmp_path):
    """Тест на отсутствующий файл."""
    missing_file = tmp_path / "nonexistent.json"
    assert validate_config(str(missing_file)) is False