# goal_engine.py (v2.2 - "Hardcore" версия с улучшенной обработкой Query Type)
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def form_goal(
    perception_struct: Dict[str, Any], 
    sdna_traits: Dict[str, Any], 
    motivation_signal: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Формирует цель на основе комплексного вывода от perception_analysis v5.0+.
    """
    query_type = perception_struct.get("query_type", "other_unclassified")
    if not isinstance(query_type, str): query_type = "other_unclassified" # Доп. проверка

    primary_intent = perception_struct.get("primary_intent", "N/A")
    core_task = perception_struct.get("core_task", {})
    if not isinstance(core_task, dict): core_task = {}

    complexity = perception_struct.get("complexity", "Низкая")
    urgency_perception = perception_struct.get("urgency", "Низкая")

    # --- 1. Определяем Приоритет и Срочность цели ---
    priority = "low"
    urgency_score = 0.1

    if urgency_perception == "Высокая":
        priority = "critical"; urgency_score = 0.9
    elif urgency_perception == "Средняя":
        priority = "high"; urgency_score = 0.7
    
    if complexity == "Высокая / Многошаговая" and priority != "critical":
        priority = "high"; urgency_score = max(urgency_score, 0.7)
    elif complexity == "Средняя" and priority not in ["critical", "high"]:
        priority = "medium"; urgency_score = max(urgency_score, 0.5)

    # --- 2. Определяем Концепт, Источник и Детали цели ---
    concept = "analyze_situation"
    source = "default_observation"
    details = {}

    # --- УЛУЧШЕННАЯ ЛОГИКА ОБРАБОТКИ QUERY TYPE ---
    if "problem_solving" in query_type or primary_intent == "Solve":
        concept = f"solve_problem:{core_task.get('action', 'generic')}"
        source = "user_problem_solving_request"
        details = {"task_description": core_task.get("object")}
        priority = "high"
    
    elif "information_request" in query_type:
        sub_type = query_type.split(':')[-1].strip() if ':' in query_type else 'general'
        # Дополнительная проверка на случай, если подтип не извлекся и остался равным "information_request"
        if sub_type == "information_request": sub_type = "general"
        concept = f"answer_information_request:{sub_type}"
        source = "user_information_request"
        details = {"topic": core_task.get("object")}
        if priority == "low": priority = "medium"
    
    elif "instruction_command" in query_type:
        sub_type = query_type.split(':')[-1].strip() if ':' in query_type else 'general'
        if sub_type == "instruction_command": sub_type = "general"
        concept = f"execute_command:{sub_type}"
        source = "user_instruction_command"
        details = {"command_details": core_task.get("object")}
        priority = "high"
    
    elif "conversation_flow" in query_type:
        sub_type = query_type.split(':')[-1].strip() if ':' in query_type else 'general'
        if sub_type == "conversation_flow": sub_type = "general"
        source = f"user_{sub_type}"
        if sub_type == "greeting_social":
            concept = "engage_in_social_dialogue"; priority = "medium"
        elif sub_type == "feedback":
            concept = "acknowledge_and_process_feedback"; priority = "medium"
        elif sub_type == "closing":
            concept = "conclude_conversation"; priority = "low"
        else: # correction_clarification
            concept = "clarify_and_adjust_understanding"; priority = "high"

    elif "ai_self_inquiry" in query_type:
        concept = "provide_information_about_self"
        source = "user_self_inquiry"
        priority = "medium"
    
    # --- 3. Сборка итогового объекта цели ---
    goal_object = {
        "goal_id": f"g_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{str(uuid.uuid4())[:8]}",
        "concept": concept, "details": details, "priority": priority,
        "urgency": urgency_score, "source": source
    }
    
    logger.info(f"GoalEngine v2.2: Сформирована новая цель -> {goal_object}")
    return goal_object
