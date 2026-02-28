import re
from typing import List, Dict

def parse_requirements(file_path: str) -> List[Dict[str, str]]:
    """
    Парсит файл requirements.txt и извлекает названия пакетов и их версии.
    Позволяет агенту получить текущее состояние зависимостей.

    Args:
        file_path (str): Полный путь к файлу requirements.txt.

    Returns:
        List[Dict[str, str]]: Список зависимостей со спецификациями версий.
    """
    dependencies = []
    # Регулярное выражение для базового парсинга: имя_пакета и версия
    pattern = re.compile(r'^([a-zA-Z0-9\-_]+)(?:==|>=|<=|~=|>|<)?([0-9a-zA-Z\.\-_]*)')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем комментарии, пустые строки и флаги (-r, -e)
                if not line or line.startswith('#') or line.startswith('-'):
                    continue

                match = pattern.match(line)
                if match:
                    name, version = match.groups()
                    dependencies.append({
                        "name": name,
                        "version": version if version else "latest"
                    })
    except Exception as e:
        # В агентских системах важно возвращать понятные ошибки в контекст [3]
        return [{"error": f"Could not read {file_path}: {str(e)}"}]

    return dependencies

