from typing import Dict, Optional

def compare_versions(current: str, latest: str) -> Dict[str, Optional[str]]:
    """
    Сравнивает текущую версию пакета с последней доступной на PyPI.
    Определяет тип изменения: Major, Minor, Patch или None (если версии равны).

    Args:
        current (str): Текущая установленная версия (например, '2.28.1').
        latest (str): Последняя доступная версия (например, '3.0.0').

    Returns:
        Dict: Словарь с ключами 'update_type', 'needs_analysis', и опционально 'description'/'error'.
    """
    if current == latest or latest == "unknown":
        return {"update_type": None, "needs_analysis": False}

    # Очищаем от символов ^ и ~ и разбиваем на части
    curr_parts = current.replace('^', '').replace('~', '').split('.')
    late_parts = latest.split('.')

    try:
        # ИСПРАВЛЕНИЕ: берем ПЕРВЫЙ элемент списка, а не весь список
        c_major = int(curr_parts[0]) if len(curr_parts) > 0 else 0
        l_major = int(late_parts[0]) if len(late_parts) > 0 else 0

        c_minor = int(curr_parts[1]) if len(curr_parts) > 1 else 0
        l_minor = int(late_parts[1]) if len(late_parts) > 1 else 0

        c_patch = int(curr_parts[2]) if len(curr_parts) > 2 else 0
        l_patch = int(late_parts[2]) if len(late_parts) > 2 else 0

        # Логика определения типа обновления
        if l_major > c_major:
            return {
                "update_type": "Major",
                "needs_analysis": True,
                "description": "Существенные изменения, возможны ломающие правки (breaking changes)."
            }
        elif l_minor > c_minor:
            return {
                "update_type": "Minor",
                "needs_analysis": False,
                "description": "Добавление функционала без потери обратной совместимости."
            }
        elif l_patch > c_patch:
            return {
                "update_type": "Patch",
                "needs_analysis": False,
                "description": "Исправление ошибок и мелкие улучшения."
            }
        else:
            return {
                "update_type": None,
                "needs_analysis": False,
                "description": "Версии совпадают"
            }

    except (ValueError, IndexError) as e:
        return {
            "update_type": "Unknown",
            "needs_analysis": True,
            "error": f"Нестандартный формат версии: {e}"
        }

