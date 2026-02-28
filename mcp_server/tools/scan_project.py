import os
from typing import List

def scan_project(path: str) -> List[str]:
    """
    Находит все файлы зависимостей в проекте по указанному пути.
    Ищет requirements.txt и pyproject.toml, игнорируя служебные папки (venv, .git).

    Args:
        path (str): Абсолютный или относительный путь к корню проекта.

    Returns:
        List[str]: Список найденных путей к файлам зависимостей.
    """
    dependency_files = []
    # Определяем целевые файлы, которые умеет обрабатывать наш агент
    target_files = {"requirements.txt", "pyproject.toml"}

    # Рекурсивный обход директории
    for root, dirs, files in os.walk(path):
        # Оптимизация: не заходим в venv, .git и скрытые папки
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'venv', 'node_modules'}]

        for file in files:
            if file in target_files:
                # Сохраняем полный путь к найденному файлу
                full_path = os.path.join(root, file)
                dependency_files.append(full_path)

    return dependency_files

