import os

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
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

from langchain_openai import ChatOpenAI

load_dotenv()
def get_openrouter_llm(model="openai/gpt-5.2-chat"):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY не найден в .env")
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
        max_tokens=100
    )

llm = get_openrouter_llm


class BaseAgent:
    async def run(self, state: DependencyState) -> DependencyState:
        raise NotImplementedError


class ScanAgent(BaseAgent):
    async def run(self, state: DependencyState) -> DependencyState:
        ctx = state["ctx"]
        await ctx.info("Сканирование проекта...")
        files = scan_project(state["project_path"])
        await ctx.info(f"Найдено файлов зависимостей: {len(files)}")
        state["dependency_files"] = files
        return state


class ParseAgent(BaseAgent):
    async def run(self, state: DependencyState) -> DependencyState:
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


class ProcessAgent(BaseAgent):
    async def run(self, state: DependencyState) -> DependencyState:
        ctx = state["ctx"]
        await ctx.info("Обработка зависимостей...")

        results = []
        for dep in state["dependencies"]:
            package = dep["name"]
            current_version = dep["version"]
            file_path = dep["file_path"]

            await ctx.info(f"Проверка пакета: {package}")

            latest_data = await fetch_latest_version(package)
            if "error" in latest_data:
                await ctx.warning(f"Ошибка получения версии для {package}: {latest_data['error']}")
                results.append({
                    "package": package,
                    "current_version": current_version,
                    "latest_version": None,
                    "update_type": None,
                    "status": "error",
                    "reason": latest_data["error"]
                })
                continue

            latest_version = latest_data["latest_version"]
            comparison = compare_versions(current_version, latest_version)
            update_type = comparison["update_type"]

            result_entry = {
                "package": package,
                "current_version": current_version,
                "latest_version": latest_version,
                "update_type": update_type,
                "status": "skipped"
            }

            # --- Patch/Minor обновления ---
            if update_type in ["patch", "minor"]:
                await ctx.info(f"{package}: безопасное {update_type}-обновление")
                update_result = update_dependency_file(file_path, package, latest_version)
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
                try:
                    risk = await analyze_breaking_changes(package, current_version, latest_version, llm)
                    result_entry["risk_level"] = risk.get("risk_level", "Unknown")
                    result_entry["breaking_changes"] = risk.get("breaking_changes", [])
                    result_entry["reasoning"] = risk.get("reasoning", "")
                except Exception as e:
                    await ctx.warning(f"LLM-анализ не удался для {package}: {str(e)}")
                    result_entry["risk_level"] = "High"
                    result_entry["breaking_changes"] = []
                    result_entry["reasoning"] = f"LLM анализ завершился ошибкой: {str(e)}"

                # Демо-обновление major
                update_result = update_dependency_file(file_path, package, latest_version)
                if update_result.get("success"):
                    save_to_history(state["db_path"], {
                        "package": package,
                        "old_version": current_version,
                        "new_version": latest_version,
                        "status": "success"
                    })
                    result_entry["status"] = "updated"
                    await ctx.info(f"{package} major обновлён (демо)")
                else:
                    result_entry["status"] = "skipped"
                    await ctx.info(f"{package} major обновление пропущено")

            results.append(result_entry)

        state["results"] = results
        return state


class ReportAgent(BaseAgent):
    async def run(self, state: DependencyState) -> DependencyState:
        ctx = state["ctx"]
        await ctx.info("Генерация финального отчета...")
        report_path = generate_report(state["results"], state["project_path"])
        await ctx.info(f"Отчет сохранён: {report_path}")
        state["report_path"] = report_path
        return state


def build_graph():
    builder = StateGraph(DependencyState)

    agents = {
        "scan": ScanAgent(),
        "parse": ParseAgent(),
        "process": ProcessAgent(),
        "report": ReportAgent()
    }

    for name, agent in agents.items():
        builder.add_node(name, agent.run)

    builder.set_entry_point("scan")
    builder.add_edge("scan", "parse")
    builder.add_edge("parse", "process")
    builder.add_edge("process", "report")
    builder.add_edge("report", END)
    return builder.compile()


async def run_graph(project_path: str, db_path: str, ctx):
    graph = build_graph()
    initial_state = {
        "project_path": project_path,
        "db_path": db_path,
        "dependency_files": [],
        "dependencies": [],
        "results": [],
        "ctx": ctx
    }
    final_state = await graph.ainvoke(initial_state)
    return {"report_path": final_state.get("report_path")}