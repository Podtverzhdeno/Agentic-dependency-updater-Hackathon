# inspector.py
import asyncio
from datetime import datetime

class Inspector:
    """
    Простая система мониторинга прогресса графа.
    Используется для логирования выполнения инструментов MCP + LangGraph.
    """

    def __init__(self):
        self.nodes = {}  # node_name -> status
        self.logs = []   # список логов событий

    async def log(self, node_name: str, message: str, level: str = "INFO"):
        """
        Добавляет событие в лог и обновляет статус узла.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append((timestamp, node_name, level, message))

        # Выводим сразу в консоль
        print(f"[{timestamp}] [{level}] [{node_name}] {message}")

        if level == "INFO":
            self.nodes[node_name] = "running"
        elif level == "SUCCESS":
            self.nodes[node_name] = "success"
        elif level == "FAILED":
            self.nodes[node_name] = "failed"
        elif level == "WARNING":
            self.nodes[node_name] = "warning"
        elif level == "DEBUG":
            self.nodes[node_name] = "debug"
        elif level == "ERROR":
            self.nodes[node_name] = "failed"

    async def node_start(self, node_name: str):
        await self.log(node_name, "Запуск узла...", "INFO")

    async def node_success(self, node_name: str):
        await self.log(node_name, "Узел успешно выполнен", "SUCCESS")

    async def node_failed(self, node_name: str, reason: str):
        await self.log(node_name, f"Узел завершился с ошибкой: {reason}", "FAILED")

    def summary(self):
        print("\n=== Итоговый статус узлов ===")
        for node, status in self.nodes.items():
            print(f"{node}: {status}")

# ------------------------------
# Пример использования
# ------------------------------
async def demo():
    inspector = Inspector()

    await inspector.node_start("scan_project")
    await asyncio.sleep(0.5)
    await inspector.node_success("scan_project")

    await inspector.node_start("fetch_latest_version")
    await asyncio.sleep(0.3)
    await inspector.node_failed("fetch_latest_version", "Timeout при запросе PyPI")

    inspector.summary()

if __name__ == "__main__":
    asyncio.run(demo())