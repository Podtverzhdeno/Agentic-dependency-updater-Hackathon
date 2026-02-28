import urllib.request
import json
from typing import Dict, Union


def fetch_latest_version(package_name: str) -> Dict[str, Union[str, bool]]:
    """
    Запрашивает последнюю версию пакета из репозитория PyPI.
    Это позволяет агенту сравнивать локальные зависимости с актуальными данными.

    Args:
        package_name (str): Имя Python-пакета (например, 'requests').

    Returns:
        Dict: Словарь с ключом 'latest_version' или 'error'.
    """
    # PyPI предоставляет JSON API для каждого пакета
    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        # Используем стандартную библиотеку urllib для минимизации зависимостей
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                # Извлекаем версию из основного информационного блока
                latest_version = data.get("info", {}).get("version", "unknown")
                return {"package": package_name, "latest_version": latest_version}
            else:
                return {"package": package_name, "error": f"PyPI returned status {response.getcode()}"}
    except Exception as e:
        # В агентных системах важно возвращать структурированную ошибку,
        # чтобы LLM могла "отрефлексировать" её и продолжить работу [3, 4]
        return {"package": package_name, "error": str(e)}

