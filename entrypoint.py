# entrypoint.py
import sys
import asyncio
from fastmcp import FastMCP, Context
from agent.orchestrator import run_graph
import os

# ------------------------------
# Инициализация MCP-сервера
# ------------------------------
mcp = FastMCP(
    name="Agentic Dependency Updater",
    instructions="Сервер для автоматического управления жизненным циклом зависимостей Python-проектов."
)

@mcp.tool()
async def ping(message: str = "Hello MCP") -> str:
    """Проверка связи с сервером."""
    return f"Pong: {message}"

@mcp.tool()
async def run_dependency_update(project_path: str, db_path: str, ctx: Context):
    """Запуск графа обновления зависимостей с логами в контекст."""
    await ctx.info(f"Запуск обновления зависимостей для {project_path}")
    try:
        final_state = await run_graph(project_path, db_path, ctx)  # передаем ctx
        report_path = final_state.get("report_path")
        if report_path:
            await ctx.info(f"Граф завершен. Отчет: {report_path}")
            return report_path
        else:
            await ctx.warning("Отчет не был создан.")
            return {"error": "report_path отсутствует в финальном состоянии"}

    except Exception as e:
        await ctx.error(f"Ошибка при запуске графа: {str(e)}")
        return {"error": str(e)}
# ------------------------------
# Smoke-тест для проверки MCP
# ------------------------------
async def run_smoke_test():
    print("Запуск smoke-теста MCP + LangGraph...")
    try:
        result = await ping("Smoke Test Connection")
        print(f"Ping результат: {result}")
        print("Smoke-тест пройден: инструменты и MCP работают корректно.")
    except Exception as e:
        print(f"Ошибка smoke-теста: {e}")
        sys.exit(1)

# ------------------------------
# Основной запуск
# ------------------------------
def main():
    if len(sys.argv) < 2:
        print("Использование: python entrypoint.py [serve|smoke|update]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "serve":
        print("Запуск MCP-сервера на порту 8000...")
        mcp.run(transport="http", port=8000, host="0.0.0.0")

    elif command == "smoke":
        asyncio.run(run_smoke_test())

    elif command == "update":
        if len(sys.argv) < 4:
            print("Использование: python entrypoint.py update <project_path> <db_path>")
            sys.exit(1)
        project_path = sys.argv[2]
        db_path = sys.argv[3]
        asyncio.run(run_dependency_update(
            project_path,
            db_path,
            ctx=DummyContext()  # DummyContext для CLI
        ))
    else:
        print(f"Неизвестная команда: {command}. Доступны: serve, smoke, update")
        sys.exit(1)

# ------------------------------
# Dummy контекст для CLI update
# ------------------------------
class DummyContext:
    async def info(self, msg): print(f"[INFO] {msg}")
    async def warning(self, msg): print(f"[WARN] {msg}")
    async def error(self, msg): print(f"[ERROR] {msg}")
    async def debug(self, msg): print(f"[DEBUG] {msg}")

if __name__ == "__main__":
    main()