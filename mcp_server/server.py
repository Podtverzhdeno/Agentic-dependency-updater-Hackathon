# server_with_inspector.py
import os
import asyncio
from fastmcp import FastMCP, Context
from inspector import Inspector

# Импорт логики инструментов
from mcp_server.tools.scan_project import scan_project
from mcp_server.tools.parse_requirements import parse_requirements
from mcp_server.tools.parse_pyproject import parse_pyproject
from mcp_server.tools.fetch_latest_version import fetch_latest_version
from mcp_server.tools.compare_versions import compare_versions
from mcp_server.tools.update_dependency_file import update_dependency_file
from mcp_server.tools.save_to_history import save_to_history
from mcp_server.tools.generate_report import generate_report
from mcp_server.tools.analyze_breaking_changes import analyze_breaking_changes

# Инициализация сервера
mcp = FastMCP(
    "Agentic Dependency Updater",
    instructions="Сервер для автоматического управления жизненным циклом зависимостей Python-проектов."
)

# Инициализация Inspector
inspector = Inspector()

@mcp.tool()
def ping(message: str = "Hello MCP") -> str:
    return f"Pong: {message}"

def log_decorator(tool_func):
    """
    Декоратор для обёртки инструмента MCP, чтобы логировать start/success/fail.
    """
    async def wrapper(*args, ctx: Context, **kwargs):
        node_name = tool_func.__name__
        await inspector.node_start(node_name)
        try:
            result = await tool_func(*args, ctx=ctx, **kwargs)
            await inspector.node_success(node_name)
            return result
        except Exception as e:
            await inspector.node_failed(node_name, str(e))
            raise e
    return wrapper

# Пример обёрнутого инструмента
@mcp.tool()
@log_decorator
async def tool_scan_project(path: str, ctx: Context) -> list:
    await ctx.info(f"Начинаю сканирование директории: {path}")
    return scan_project(path)

@mcp.tool()
@log_decorator
async def tool_parse_dependencies(file_path: str, ctx: Context) -> list:
    await ctx.info(f"Парсинг файла: {file_path}")
    if file_path.endswith('.txt'):
        return parse_requirements(file_path)
    return parse_pyproject(file_path)

@mcp.tool()
@log_decorator
async def tool_get_latest_and_compare(package: str, current_version: str, ctx: Context) -> dict:
    await ctx.debug(f"Запрос PyPI для пакета: {package}")
    latest_data = fetch_latest_version(package)
    if "error" in latest_data:
        return latest_data
    comparison = compare_versions(current_version, latest_data["latest_version"])
    return {**latest_data, **comparison}

@mcp.tool()
@log_decorator
async def tool_apply_update(file_path: str, package: str, new_version: str, db_path: str, ctx: Context) -> dict:
    await ctx.info(f"Обновление {package} до {new_version} в {file_path}")
    update_result = update_dependency_file(file_path, package, new_version)
    if update_result.get("success"):
        history_data = {
            "package": package,
            "old_version": "unknown",
            "new_version": new_version,
            "status": "success"
        }
        save_to_history(db_path, history_data)
    return update_result

@mcp.tool()
@log_decorator
async def tool_generate_final_report(results: list, project_path: str, ctx: Context) -> str:
    await ctx.info("Генерация финального отчета...")
    return generate_report(results, project_path)

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)