from unittest import result

from pydantic import BaseModel, Field
from typing import Dict, Any, List
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

# Определяем схему ответа для LLM через Pydantic
class SafetyAssessment(BaseModel):
    is_safe: bool = Field(description="Можно ли обновлять пакет автоматически")
    risk_level: str = Field(description="Уровень риска: Low, Medium, High")
    breaking_changes: List[str] = Field(description="Список потенциально ломающих изменений")
    reasoning: str = Field(description="Краткое обоснование решения")

def analyze_breaking_changes(
        package: str,
        current: str,
        latest: str,
        llm: Any
) -> Dict[str, Any]:
    """
    Использует LLM для оценки рисков обновления пакета.

    Args:
        package: Имя пакета.
        current: Текущая версия.
        latest: Новая версия.
        llm: Инициализированный объект локальной LLM (ОБЯЗАТЕЛЬНО).

    Returns:
        Dict: Структурированный отчет о безопасности обновления.
    """

    parser = JsonOutputParser(pydantic_object=SafetyAssessment)

    prompt = PromptTemplate(
        template="""Ты — эксперт по Python-зависимостям. 
        Проанализируй обновление пакета '{package}' с версии {current} до {latest}.
        Оцени вероятность наличия breaking changes.
        
        {format_instructions}
        
        Твой ответ должен быть только в формате JSON.""",
        input_variables=["package", "current", "latest"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    try:
        chain = prompt | llm | parser
        result = chain.invoke({
            "package": package,
            "current": current,
            "latest": latest
        })
        return result
    except Exception as e:
        return {
            "is_safe": False,
            "risk_level": "High",
            "breaking_changes": ["Error during LLM analysis"],
            "reasoning": f"Анализ не удался: {str(e)}. Требуется ручная проверка."
        }
