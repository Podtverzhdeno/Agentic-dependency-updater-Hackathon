import sys
import asyncio
from fastmcp import FastMCP, Context
from datetime import datetime

from agent.orchestrator import ScanAgent, ParseAgent, ProcessAgent, ReportAgent

# Создаем MCP сервер
mcp = FastMCP(
    name="Agentic Dependency Updater",
    instructions="Сервер для автоматического управления жизненным циклом зависимостей Python-проектов с агентами."
)

@mcp.tool()
async def health_check() -> dict:
    """Проверка здоровья сервиса (вызывается как tool)"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "agentic-dependency-updater",
        "version": "1.0.0"
    }

@mcp.tool()
async def get_service_info() -> dict:
    """Информация о сервисе"""
    return {
        "name": "Agentic Dependency Updater",
        "version": "1.0.0",
        "description": "MCP сервер для управления зависимостями",
        "tools": [
            "health_check",
            "ping",
            "scan_project_agent",
            "parse_dependencies_agent",
            "process_dependencies_agent",
            "generate_report_agent",
            "run_dependency_update"
        ]
    }

@mcp.tool()
async def ping(message: str = "Hello MCP") -> str:
    """Проверка связи с сервером."""
    return f"Pong: {message}"

@mcp.tool()
async def scan_project_agent(project_path: str, ctx: Context):
    """Сканирование проекта на зависимые файлы."""
    state = {"project_path": project_path, "dependency_files": [], "ctx": ctx}
    agent = ScanAgent()
    final_state = await agent.run(state)
    return final_state["dependency_files"]

@mcp.tool()
async def parse_dependencies_agent(dependency_files: list, ctx: Context):
    """Парсинг зависимостей из файлов."""
    state = {"dependency_files": dependency_files, "dependencies": [], "ctx": ctx}
    agent = ParseAgent()
    final_state = await agent.run(state)
    return final_state["dependencies"]

@mcp.tool()
async def process_dependencies_agent(dependencies: list, project_path: str, db_path: str, ctx: Context):
    """Обновление и проверка зависимостей."""
    state = {
        "dependencies": dependencies,
        "project_path": project_path,
        "db_path": db_path,
        "results": [],
        "ctx": ctx
    }
    agent = ProcessAgent()
    final_state = await agent.run(state)
    return final_state["results"]

@mcp.tool()
async def generate_report_agent(results: list, project_path: str, ctx: Context):
    """Генерация отчета по обновлениям."""
    state = {
        "results": results,
        "project_path": project_path,
        "ctx": ctx
    }
    agent = ReportAgent()
    final_state = await agent.run(state)
    return final_state.get("report_path")

@mcp.tool()
async def run_dependency_update(project_path: str, db_path: str, ctx: Context):
    """Полный запуск графа обновления зависимостей через агентов."""
    await ctx.info(f"Запуск полного workflow для {project_path}")

    dependency_files = await scan_project_agent(project_path, ctx)
    dependencies = await parse_dependencies_agent(dependency_files, ctx)
    results = await process_dependencies_agent(dependencies, project_path, db_path, ctx)
    report_path = await generate_report_agent(results, project_path, ctx)

    if report_path:
        await ctx.info(f"Workflow завершен. Отчет: {report_path}")
        return {"report_path": report_path}
    else:
        await ctx.warning("Отчет не был создан.")
        return {"error": "report_path отсутствует"}

async def run_smoke_test():
    print(" Запуск smoke-теста...")
    try:
        # Проверяем ping
        ping_result = await ping("Smoke Test Connection")
        print(f" Ping: {ping_result}")
        
        # Проверяем health
        health = await health_check()
        print(f" Health: {health['status']}")
        
        print(" Smoke-тест пройден!")
    except Exception as e:
        print(f" Ошибка smoke-теста: {e}")
        sys.exit(1)

class DummyContext:
    async def info(self, msg): print(f"[INFO] {msg}")
    async def warning(self, msg): print(f"[WARN] {msg}")
    async def error(self, msg): print(f"[ERROR] {msg}")
    async def debug(self, msg): print(f"[DEBUG] {msg}")

# ========== MAIN ==========

def main():
    if len(sys.argv) < 2:
        print("Использование: python entrypoint.py [serve|smoke|update]")
        print("  serve  - запустить MCP сервер")
        print("  smoke  - запустить smoke-тест")
        print("  update - запустить анализ проекта")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "serve":
        print(" Запуск MCP сервера...")
        print(f" MCP endpoint: http://0.0.0.0:8000/mcp")
        print(f" Health check tool: health_check()")
        print(f"  Info tool: get_service_info()")
        
        # Запускаем сервер
        mcp.run(transport="http", port=8000, host="0.0.0.0")

    elif command == "smoke":
        asyncio.run(run_smoke_test())

    elif command == "update":
        if len(sys.argv) < 4:
            print("Использование: python entrypoint.py update <project_path> <db_path>")
            sys.exit(1)
        project_path = sys.argv[2]
        db_path = sys.argv[3]
        
        print(f" Анализ проекта: {project_path}")
        print(f" База данных: {db_path}")
        
        result = asyncio.run(run_dependency_update(
            project_path,
            db_path,
            ctx=DummyContext()
        ))
        
        if "report_path" in result:
            print(f"\n Готово! Отчет: {result['report_path']}")
        else:
            print(f"\n Ошибка: {result}")

    else:
        print(f" Неизвестная команда: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
