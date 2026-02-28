**Agentic Dependency Updater** — интеллектуальный инструмент для анализа и обновления зависимостей Python-проектов, использующий агентную архитектуру на базе LangGraph и LangChain.

**Ключевые возможности**

Автоматическое сканирование — поиск всех файлов зависимостей (requirements.txt, pyproject.toml)

Агентная архитектура — 4 специализированных агента на базе LangGraph

Умный анализ версий — определение типа обновления (patch/minor/major)

Анализ рисков — LLM-анализ breaking changes для major-обновлений

История изменений — SQLite база данных для отслеживания обновлений

Детальные отчёты — генерация структурированных Markdown-отчётов

Проект построен на LangGraph с четырьмя специализированными агентами

Scan Agent - Ищет файлы зависимостей в проекте

Parse Agent - Читает файлы и извлекает зависимости

Report Agent - Генерирует отчёт и сохраняет историю

Process Agent - Проверяет версии, анализирует риски, обновляет

**Структура проекта**

<img width="962" height="798" alt="image" src="https://github.com/user-attachments/assets/b602fc55-ebce-4f91-8cbd-62cda8f5ff60" />

**Установка и запуск**

1. Клонирование репозитория

git clone https://github.com/Podtverzhdeno/Agentic-dependency-updater-Hackathon.git

cd Agentic-dependency-updater-Hackathon

mv .env.example .env

2. Настройка API ключа

Зайдите на https://openrouter.ai/settings/keys и создайте **бесплатный** API_KEY

зайдите в .env

Найдите строчку OPENROUTER_API_KEY и вставьте API_KEY

3. Сборка Docker-образа

docker build -t agentic-dependency-updater .

4. Запуск анализа проекта

Локальный запуск (Windows/Linux/Mac)

python entrypoint.py update ./demo_project ./data/history.db

Запуск в Docker

docker run --env-file .env agentic-dependency-updater update /app/demo_project /app/data/history.db

Smoke-тест

Локально

python entrypoint.py update smoke

В Docker

docker run --env-file .env agentic-dependency-updater update smoke
