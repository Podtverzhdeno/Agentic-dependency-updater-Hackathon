from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
from langchain_ollama import ChatOllama

from agent.state import DependencyState
from mcp_server.tools.scan_project import scan_project
from mcp_server.tools.parse_requirements import parse_requirements
from mcp_server.tools.parse_pyproject import parse_pyproject
from mcp_server.tools.fetch_latest_version import fetch_latest_version
from mcp_server.tools.compare_versions import compare_versions
from mcp_server.tools.update_dependency_file import update_dependency_file
from mcp_server.tools.save_to_history import save_to_history
from mcp_server.tools.generate_report import generate_report
from mcp_server.tools.analyze_breaking_changes import analyze_breaking_changes


# ---------- NODES ----------

async def scan_node(state: DependencyState):
    ctx = state["ctx"]

    await ctx.info("Сканирование проекта...")
    files = scan_project(state["project_path"])

    await ctx.info(f"Найдено файлов зависимостей: {len(files)}")

    state["dependency_files"] = files
    return state


async def parse_node(state: DependencyState):
    ctx = state["ctx"]
    await ctx.info("Парсинг зависимостей...")

    dependencies = []

    for file_path in state["dependency_files"]:
        if file_path.endswith(".txt"):
            deps = parse_requirements(file_path)
        else:
            deps = parse_pyproject(file_path)

        for d in deps:
            d["file_path"] = file_path

        dependencies.extend(deps)

    await ctx.info(f"Найдено зависимостей: {len(dependencies)}")

    state["dependencies"] = dependencies
    return state


async def process_node(state: DependencyState):
    ctx = state["ctx"]
    await ctx.info("Начинаю обработку зависимостей...")

    results = []

    llm = ChatOllama(
        model="qwen2.5:7b",
        temperature=0,
        base_url="http://localhost:11434"
    )

    for dep in state["dependencies"]:
        package = dep["name"]
        current_version = dep["version"]
        file_path = dep["file_path"]

        await ctx.info(f"Проверка пакета: {package}")

        latest_data = fetch_latest_version(package)

        if "error" in latest_data:
            await ctx.warning(f"Ошибка получения версии для {package}")
            results.append({
                "package": package,
                "status": "error",
                "reason": latest_data["error"]
            })
            continue

        latest_version = latest_data["latest_version"]

        comparison = compare_versions(
            current_version,
            latest_version
        )

        update_type = comparison["update_type"]

        result_entry = {
            "package": package,
            "current_version": current_version,
            "latest_version": latest_version,
            "update_type": update_type,
            "status": "skipped"
        }

        # ---- Decision logic ----

        if update_type in ["patch", "minor"]:
            await ctx.info(f"{package}: безопасное {update_type}-обновление")

            update_result = update_dependency_file(
                file_path,
                package,
                latest_version
            )

            if update_result.get("success"):
                save_to_history(state["db_path"], {
                    "package": package,
                    "old_version": current_version,
                    "new_version": latest_version,
                    "status": "success"
                })

                result_entry["status"] = "updated"
                await ctx.info(f"{package} обновлён")

        elif update_type == "major":
            await ctx.warning(f"{package}: major-обновление, анализ рисков")

            risk = analyze_breaking_changes(
                package,
                current_version,
                latest_version,
                llm
            )

            result_entry["risk_level"] = risk.get("risk_level")

            if risk.get("is_safe"):
                await ctx.info(f"{package}: LLM считает обновление безопасным")

                update_result = update_dependency_file(
                    file_path,
                    package,
                    latest_version
                )

                if update_result.get("success"):
                    save_to_history(state["db_path"], {
                        "package": package,
                        "old_version": current_version,
                        "new_version": latest_version,
                        "status": "success"
                    })

                    result_entry["status"] = "updated"
                    await ctx.info(f"{package} обновлён после анализа")
                else:
                    result_entry["status"] = "failed"
                    await ctx.error(f"{package} не удалось обновить")

            else:
                result_entry["status"] = "skipped_risky"
                await ctx.warning(f"{package}: обновление пропущено (риск: {risk.get('risk_level')})")

        results.append(result_entry)

    state["results"] = results
    return state


async def report_node(state: DependencyState):
    ctx = state["ctx"]
    await ctx.info("Генерация финального отчета...")

    report_path = generate_report(
        state["results"],
        state["project_path"]
    )

    await ctx.info(f"Отчет сохранён: {report_path}")

    state["report_path"] = report_path
    return state


# ---------- GRAPH ----------

def build_graph():
    from typing import Dict, Any
    builder = StateGraph(Dict[str, Any])
    builder.add_node("scan", scan_node)
    builder.add_node("parse", parse_node)
    builder.add_node("process", process_node)
    builder.add_node("report", report_node)

    builder.set_entry_point("scan")

    builder.add_edge("scan", "parse")
    builder.add_edge("parse", "process")
    builder.add_edge("process", "report")
    builder.add_edge("report", END)

    return builder.compile()


async def run_dependency_graph(project_path: str, db_path: str, ctx):
    graph = build_graph()

    initial_state = {
        "project_path": project_path,
        "db_path": db_path,
        "dependency_files": [],
        "dependencies": [],
        "results": [],
        "ctx": ctx
    }

    return await graph.ainvoke(initial_state)