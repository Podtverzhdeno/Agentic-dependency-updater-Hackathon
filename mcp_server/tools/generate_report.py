import os
from datetime import datetime
from typing import List, Dict, Any


def generate_report(results: List[Dict[str, Any]], project_path: str) -> str:
    """
    Генерирует подробный Markdown-отчёт о результатах анализа и обновления зависимостей.
    """

    timestamp = datetime.now()
    report_filename = f"dependency_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
    report_path = os.path.join(project_path, report_filename)

    total = len(results)
    updated = 0
    skipped = 0
    skipped_risky = 0
    failed = 0
    errors = 0

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            # Заголовок
            f.write("# Dependency Update Report\n\n")
            f.write(f"**Project path:** `{project_path}`\n\n")
            f.write(f"**Generated at:** {timestamp.isoformat()}\n\n")
            f.write("---\n\n")

            # Детализация по каждому пакету
            for item in results:
                package = item.get("package", "unknown")
                current = item.get("current_version", "unknown")
                latest = item.get("latest_version", "unknown")
                update_type = item.get("update_type", "unknown")
                risk_level = item.get("risk_level")
                status = item.get("status", "skipped")
                reason = item.get("reason")

                if status == "updated":
                    updated += 1
                elif status == "failed":
                    failed += 1
                elif status == "skipped_risky":
                    skipped_risky += 1
                elif status == "error":
                    errors += 1
                else:
                    skipped += 1

                f.write(f"## {package}\n\n")
                f.write(f"- Current version: `{current}`\n")
                f.write(f"- Latest version: `{latest}`\n")
                f.write(f"- Update type: `{update_type}`\n")
                f.write(f"- Status: `{status}`\n")

                if risk_level:
                    f.write(f"- Risk level: `{risk_level}`\n")

                if reason:
                    f.write(f"- Error: {reason}\n")

                f.write("\n---\n\n")

            # Итоговая сводка
            f.write("# Summary\n\n")
            f.write(f"- Total packages analyzed: **{total}**\n")
            f.write(f"- Successfully updated: **{updated}**\n")
            f.write(f"- Skipped (no update needed): **{skipped}**\n")
            f.write(f"- Skipped (risky major updates): **{skipped_risky}**\n")
            f.write(f"- Failed updates: **{failed}**\n")
            f.write(f"- Errors during processing: **{errors}**\n")

        return report_path

    except Exception as e:
        return f"Ошибка генерации отчета: {e}"