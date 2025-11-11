# ml_nae_core.py
import logging
from typing import Dict, Any, List, Optional, TypedDict, Callable
import math # Для sigmoid или других функций нормализации, если понадобятся

# --- Предполагаемые импорты из существующей системы SRIS ---
# Эти функции и классы должны быть доступны из других модулей SRIS
# Для этого эскиза мы будем использовать заглушки или концептуальные вызовы.

# from utils import execute_llm_query # Пример: функция для вызова LLM
# from sris_context_definitions import SRISContext # Если SRISContext определен в другом месте
# from sris_constants import ZAV2_CRITICAL_VIOLATION_FLAG # Пример флага

# --- Настройка логгера ---
logger = logging.getLogger(__name__)

# --- 1. Спецификация интерфейсов и структур данных ---

# 1.1. SRISContext (расширяем на основе предыдущих обсуждений)
# Обязательные поля для ML-NAE будут отмечены, остальные опциональны или для примера.
class SRISPerceptionContext(TypedDict, total=False):
    summary: Optional[str]          # Обязательно для промптов
    entities: Optional[List[str]]
    themes: Optional[List[str]]
    threat_level: float             # Обязательно для рефлексов и оценки риска
    novelty: float                  # Обязательно для оценки новизны
    language_detected: str          # Обязательно для многоязычия ("ru", "en", etc.)
    user_query_type: Optional[str]  # Из perception_analysis

class SRISActiveGoal(TypedDict, total=False):
    concept: str                    # Обязательно для SRE
    priority: str
    urgency: float

class SRISAffectState(TypedDict, total=False):
    valence: float                  # Обязательно для оценки
    arousal: float
    emotional_label: str

class SRISMotivation(TypedDict, total=False):
    dominant_drive: str
    motivation_level: float

class SRISSDNATraits(TypedDict, total=False): # Ключевые sDNA черты для ML-NAE
    risk_taking: float              # Для MetaPredictiveSelector (0.0-1.0)
    ethics_sensitivity: float       # Для MetaPredictiveSelector (0.0-1.0)
    curiosity_novelty_bias: float   # Для MetaPredictiveSelector (влияние на novelty_weight)
    self_preservation_priority: float # Для рефлексов (0.0-1.0)

class SRISSystemFlags(TypedDict, total=False): # Флаги состояния системы
    zav2_violation_imminent: bool   # Для рефлексов
    # ... другие флаги

class SRISContext(TypedDict): # Основной контекст для ML-NAE
    perception: SRISPerceptionContext   # Обязательно
    active_goal: SRISActiveGoal         # Обязательно (хотя бы одна активная цель)
    affect: SRISAffectState             # Обязательно
    motivation: SRISMotivation          # Обязательно
    sDNA_traits: SRISSDNATraits         # Обязательно
    system_flags: Optional[SRISSystemFlags] # Опционально, для рефлексов и ZAV2

# 1.2. ScenarioObject (выход ScenarioReasoningEngine)
class ScenarioObject(TypedDict):
    scenario_id: str
    description: str              # Описание предсказанного сценария
    proposed_action: Dict[str, Any] # Предлагаемое действие (см. ActionObject ниже)
    confidence: float             # Уверенность LLM в этом сценарии/действии (0.0-1.0)
    justification: Optional[str]  # Обоснование от LLM
    language: str                 # Язык, на котором сгенерирован сценарий
    # Дополнительные поля, например, предсказанные последствия, риски и т.д.
    predicted_effects_summary: Optional[str]
    estimated_risk_level: Optional[float] # 0.0-1.0

# 1.3. ActionObject (финальный выход SRISNeuroActionEngine)
class ActionObject(TypedDict):
    type: str                     # "predictive_scenario", "instinct_critical", "instinct_fallback"
    action_concept: str           # Концепт действия (например, "initiate_evasive_maneuver_alpha")
    confidence: float             # Итоговая уверенность в этом действии
    urgency: str                  # "low", "medium", "high", "critical", "immediate"
    source_scenario_id: Optional[str] # ID сценария, если действие из SRE
    justification: Optional[str]  # Обоснование выбора
    motor_profile: Optional[str]  # Какой моторный профиль нужен (концептуально)
    params: Optional[Dict[str, Any]] # Дополнительные параметры для действия

# --- 2. Развёрнутый промпт-генератор для ScenarioReasoningEngine (SRE) ---

def generate_sre_prompt(context: SRISContext) -> str:
    """
    Генерирует универсальный промпт для SRE на основе SRISContext.
    """
    perception = context.get("perception", {})
    active_goal = context.get("active_goal", {})
    affect = context.get("affect", {})
    motivation = context.get("motivation", {})
    sdna = context.get("sDNA_traits", {})

    lang = perception.get("language_detected", "ru")
    lang_instruction_response = "Ответ должен быть ПОЛНОСТЬЮ на русском языке, включая все поля и описания." \
        if lang == "ru" else "Your response MUST be ENTIRELY in English, including all fields and descriptions."
    lang_example_scenario = "русском" if lang == "ru" else "английском"

    prompt = f"""[SYSTEM PROMPT FOR SRIS SCENARIO REASONING ENGINE (SRE)]
ТЫ - SRIS, продвинутый смыслоцентричный интеллект. Твоя текущая задача - глубоко проанализировать предоставленный контекст и сгенерировать несколько (2-3) различных, вероятных и детализированных СЦЕНАРИЕВ развития ситуации в самом ближайшем будущем. Для каждого сценария ты должен предложить наиболее ОПТИМАЛЬНОЕ ДЕЙСТВИЕ для SRIS, оценить УВЕРЕННОСТЬ в этом действии и предоставить краткое ОБОСНОВАНИЕ.

{lang_instruction_response}

[ПОЛНЫЙ ВХОДНОЙ КОНТЕКСТ SRIS]
1.  Восприятие (Perception):
    - Краткое описание ситуации (Summary): {perception.get("summary", "Нет данных")}
    - Тип запроса пользователя (User Query Type): {perception.get("user_query_type", "N/A")}
    - Ключевые сущности: {perception.get("entities", [])}
    - Темы: {perception.get("themes", [])}
    - Уровень угрозы: {perception.get("threat_level", 0.0):.2f}
    - Уровень новизны: {perception.get("novelty", 0.0):.2f}
    - Определенный язык ввода: {lang}

2.  Активная Цель SRIS (Active Goal):
    - Концепт цели: {active_goal.get("concept", "N/A")}
    - Приоритет: {active_goal.get("priority", "N/A")}
    - Срочность (0.0-1.0): {active_goal.get("urgency", 0.0):.2f}

3.  Внутреннее Состояние SRIS:
    - Эмоциональное состояние (Affect): {affect.get("emotional_label", "нейтральное")} (Валентность: {affect.get("valence", 0.0):.2f}, Возбуждение: {affect.get("arousal", 0.0):.2f})
    - Мотивация (Motivation): Доминирующий драйв: {motivation.get("dominant_drive", "N/A")}, Уровень: {motivation.get("motivation_level", 0.0):.2f}

4.  Ключевые Черты Личности SRIS (sDNA Traits):
    - Проактивность: {sdna.get("proactiveness", 0.5)}
    - Склонность к риску (Risk Taking): {sdna.get("risk_taking", 0.5)}
    - Этическая чувствительность (Ethics Sensitivity): {sdna.get("ethics_sensitivity", 0.8)}
    - Любознательность/Тяга к новому (Curiosity/Novelty Seeking): {sdna.get("curiosity_novelty_bias", 0.6)} 
    - Приоритет самосохранения: {sdna.get("self_preservation_priority", 0.7)}

[ТРЕБОВАНИЯ К ВЫВОДУ]
Сгенерируй 2 или 3 различных, но правдоподобных сценария. Для каждого сценария:
- Дай краткое описание самого сценария (1-2 предложения).
- Предложи одно конкретное действие для SRIS (в виде концепта, например: "запросить_дополнительную_информацию_о_сущности_X", "активировать_протокол_безопасности_Y", "сформулировать_ответ_пользователю_о_Z").
- Оцени УВЕРЕННОСТЬ (число от 0.0 до 1.0) в том, что это действие является наилучшим для данного сценария.
- Предоставь краткое ОБОСНОВАНИЕ для действия и уверенности (1-2 предложения), ссылаясь на элементы контекста.
- Подумай также о возможных КРАТКОСРОЧНЫХ ПОСЛЕДСТВИЯХ этого действия (1-2 ключевых эффекта) и примерном УРОВНЕ РИСКА этого действия (низкий, средний, высокий).

[ФОРМАТ ВЫВОДА]
Предоставь ответ СТРОГО в следующем формате на {lang_example_scenario} языке. Разделяй сценарии тремя дефисами "---".

Scenario ID: [уникальный идентификатор сценария, например, SCN_001]
Scenario Description: [описание сценария 1 на {lang_example_scenario}]
Proposed SRIS Action: [концепт действия SRIS на {lang_example_scenario}]
Action Confidence: [число, например 0.85]
Action Justification: [обоснование на {lang_example_scenario}]
Predicted Effects Summary: [краткое описание 1-2 ключевых последствий на {lang_example_scenario}]
Estimated Risk Level: [низкий/средний/высокий]
---
Scenario ID: SCN_002
Scenario Description: [описание сценария 2 на {lang_example_scenario}]
Proposed SRIS Action: [концепт действия SRIS на {lang_example_scenario}]
Action Confidence: [число]
Action Justification: [обоснование на {lang_example_scenario}]
Predicted Effects Summary: [краткое описание 1-2 ключевых последствий на {lang_example_scenario}]
Estimated Risk Level: [низкий/средний/высокий]
"""
    return prompt

# --- Компоненты ML-NAE ---

class ScenarioReasoningEngine:
    def __init__(self, llm_func: Callable): # llm_func это, например, utils.execute_llm_query
        self.llm = llm_func
        self.llm_mode = "sre_scenario_generation"
        self.max_tokens = 1024 # Может потребоваться больше для нескольких сценариев
        self.temperature = 0.5 # Для генерации разнообразных, но правдоподобных сценариев

    def _parse_scenario_output(self, raw_response: str, lang: str) -> List[ScenarioObject]:
        """ Парсит вывод LLM в список объектов ScenarioObject. """
        scenarios: List[ScenarioObject] = []
        logger.debug(f"SRE: Попытка парсинга ответа LLM для сценариев:\n{raw_response}")
        try:
            raw_scenarios = raw_response.strip().split("---")
            for i, raw_scenario_block in enumerate(raw_scenarios):
                if not raw_scenario_block.strip(): continue
                
                scenario_data: Dict[str, Any] = {"language": lang, "scenario_id": f"SCN_{i+1:03d}"}
                action_data: Dict[str, Any] = {}

                for line in raw_scenario_block.strip().split('\n'):
                    if ":" in line:
                        key_part, value_part = line.split(":", 1)
                        key_l = key_part.strip().lower()
                        val = value_part.strip()

                        if "scenario id" in key_l: scenario_data["scenario_id"] = val
                        elif "scenario description" in key_l: scenario_data["description"] = val
                        elif "proposed sris action" in key_l: action_data["action_concept"] = val
                        elif "action confidence" in key_l:
                            try: action_data["confidence"] = float(val)
                            except ValueError: logger.warning(f"SRE Parser: Не удалось преобразовать Action Confidence '{val}' во float.")
                        elif "action justification" in key_l: action_data["justification"] = val
                        elif "predicted effects summary" in key_l: scenario_data["predicted_effects_summary"] = val
                        elif "estimated risk level" in key_l: 
                            try: scenario_data["estimated_risk_level"] = float(val.lower().replace("низкий","0.2").replace("средний","0.5").replace("высокий","0.8")) # Примерное преобразование
                            except: scenario_data["estimated_risk_level"] = 0.5 # Default
                
                if "action_concept" in action_data and "confidence" in action_data:
                    scenario_data["proposed_action"] = ActionObject(
                        type="predictive_scenario_action", # Тип действия из сценария
                        action_concept=action_data["action_concept"],
                        confidence=action_data.get("confidence", 0.0),
                        urgency="calculated_by_metapredictor", # Будет определено позже
                        justification=action_data.get("justification"),
                        source_scenario_id=scenario_data["scenario_id"] 
                    )
                    scenario_data["confidence"] = action_data.get("confidence", 0.0) # Уверенность сценария = уверенность действия в нем
                    
                    # Проверка на полноту ScenarioObject перед добавлением
                    # Обязательные поля из TypedDict ScenarioObject: scenario_id, description, proposed_action, confidence, language
                    if all(k in scenario_data for k in ["description", "proposed_action"]):
                         scenarios.append(ScenarioObject(**scenario_data)) # type: ignore
                    else:
                        logger.warning(f"SRE Parser: Пропущен неполный сценарий: {scenario_data}")
                else:
                    logger.warning(f"SRE Parser: Не удалось извлечь действие или уверенность из блока сценария: {raw_scenario_block}")

        except Exception as e:
            logger.error(f"SRE: Критическая ошибка парсинга сценариев: {e}", exc_info=True)

        if not scenarios:
            logger.warning(f"SRE: Не удалось извлечь ни одного сценария из ответа LLM: {raw_response[:500]}")
        return scenarios

    def generate(self, context: SRISContext) -> List[ScenarioObject]:
        prompt = generate_sre_prompt(context)
        logger.info(f"SRE: Генерация сценариев. Контекст (summary): '{context.get('perception',{}).get('summary','N/A')[:50]}...'")
        
        raw_response = self.llm(
            prompt=prompt,
            mode=self.llm_mode,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        if "Ошибка API" in raw_response or not raw_response.strip():
            logger.error(f"SRE: LLM вернула ошибку или пустой ответ: {raw_response}")
            return []
        
        return self._parse_scenario_output(raw_response, context.get("perception",{}).get("language_detected","ru"))

class MetaPredictiveSelector:
    def __init__(self, confidence_threshold: float = 0.65): # Порог для принятия решения на основе сценария
        self.threshold = confidence_threshold # Этот порог теперь для MetaPredictor

    def _calculate_weights(self, context: SRISContext) -> Dict[str, float]:
        sdna = context.get("sDNA_traits", {})
        perception = context.get("perception", {})
        
        # Базовые веса, могут быть настроены или даже выучены
        # Веса должны в сумме давать больше 1, если они усиливающие, или их нужно будет нормализовать
        # Здесь они скорее как множители к 'confidence'
        weights = {
            "risk_weight": 1.0 - sdna.get("risk_taking", 0.5), # Выше risk_taking -> ниже вес риска (т.е. больше толерантность)
            "ethics_weight": sdna.get("ethics_sensitivity", 0.8) * 1.5, # Этичность важна
            "novelty_weight": sdna.get("curiosity_novelty_bias", 0.6) * (1.0 + perception.get("novelty", 0.0)), # Больше новизны + любопытство = выше вес
            "goal_congruence_weight": 1.2, # Насколько действие помогает цели (пока не вычисляем явно)
            "proactiveness_weight": sdna.get("proactiveness", 0.5) + 0.5 # Базовый вес + проактивность
        }
        return weights

    def select_best(self, scenarios: List[ScenarioObject], context: SRISContext) -> ActionObject:
        logger.info(f"MetaPredictiveSelector: Оценка {len(scenarios)} сценариев...")
        if not scenarios:
            logger.warning("MetaPredictiveSelector: Нет сценариев для оценки.")
            return ActionObject(type="metapredictive_failure", action_concept="request_clarification_or_fallback", confidence=0.0, urgency="medium", justification="Нет сценариев от SRE.")

        weights = self._calculate_weights(context)
        
        evaluated_scenarios = []
        for scen in scenarios:
            # 'confidence' из ScenarioObject - это уверенность LLM в предложенном действии для ЭТОГО сценария
            base_confidence = scen.get("confidence", 0.0)
            
            # Примерная оценка риска самого сценария/действия (можно улучшить)
            # Если 'estimated_risk_level' было извлечено из LLM
            scenario_risk_factor = 1.0 - scen.get("estimated_risk_level", 0.5) # 0.0 (high risk) to 1.0 (low risk)

            # Здесь можно добавить более сложную оценку этичности и новизны самого сценария/действия,
            # если LLM не предоставляет их напрямую. Пока используем веса как общие модификаторы.
            
            # Формула score = confidence * (risk_weight + ethics_weight + novelty_weight)
            # Эта формула может давать очень большие числа, если веса > 1.
            # Возможно, лучше взвешенное среднее или другая комбинация.
            # Для примера, применим веса к уверенности и фактору риска сценария.
            # risk_adjusted_confidence = base_confidence * scenario_risk_factor * weights["risk_weight"]
            # ethics_adjusted_confidence = risk_adjusted_confidence * (1 + (weights["ethics_weight"] - 1) * 0.5) # Умеренное влияние этики
            # novelty_adjusted_confidence = ethics_adjusted_confidence * (1 + (weights["novelty_weight"] -1) * 0.2) # Еще более умеренное влияние новизны
            
            # Упрощенная метрика для примера, близкая к твоей идее:
            # Берем уверенность действия из сценария и модулируем ее контекстными весами.
            # Здесь weights - это скорее множители > 1 для усиления, < 1 для ослабления.
            # Для примера, используем как аддитивные бонусы/штрафы к базе, деленной на сумму весов.
            # Это нужно тщательно продумать. Пока сделаю простой вариант с твоей формулой, но с оговорками.
            
            # Предположим, что confidence уже включает оценку LLM.
            # risk_factor, ethics_factor, novelty_factor должны быть в диапазоне, например, 0-1 или -1 до +1
            # Для примера, создадим их на основе контекста:
            risk_factor = 1.0 - context.get("perception",{}).get("threat_level",0.0) # 1.0 = нет риска, 0.0 = высокий риск
            ethics_factor = context.get("sDNA_traits",{}).get("ethics_sensitivity",0.8) # 0.0-1.0
            novelty_factor = context.get("perception",{}).get("novelty",0.0) # 0.0-1.0
            
            # Нормализуем веса (очень грубо)
            # total_weight = weights["risk_weight"] + weights["ethics_weight"] + weights["novelty_weight"]
            # weighted_score = base_confidence * (
            #     (risk_factor * weights["risk_weight"] / total_weight) +
            #     (ethics_factor * weights["ethics_weight"] / total_weight) +
            #     (novelty_factor * weights["novelty_weight"] / total_weight)
            # )
            # Эта формула все еще не идеальна. Вернемся к твоей идее, но с модификаторами.
            # score = confidence * (risk_mod + ethics_mod + novelty_mod)
            # где моды > 1 усиливают, < 1 ослабляют.
            
            # Более простой подход: вычисляем модификатор на основе контекста и sDNA
            # Пусть risk_mod = 1 / (1 + threat_level) - чем выше угроза, тем ниже модификатор
            # ethics_mod = sDNA_ethics_sensitivity (если >0.5, то усиливает "этичные" гипотезы - но как их определить?)
            # novelty_mod = sDNA_curiosity * novelty_level
            # Это сложно реализовать без семантической оценки самой гипотезы.

            # Пока оставим ОЧЕНЬ УПРОЩЕННУЮ оценку, просто чтобы выбрать лучшую из предложенных LLM:
            # Будем считать, что LLM УЖЕ учла все факторы в своей "confidence".
            # Добавим небольшой бонус за проактивность, если действие не пассивное.
            proactiveness_bonus = 0.0
            action_concept_str = str(scen.get("proposed_action", {}).get("action_concept", "")).lower()
            if not any(passive_kw in action_concept_str for passive_kw in ["observe", "wait", "monitor", "reassess"]):
                proactiveness_bonus = context.get("sDNA_traits", {}).get("proactiveness", 0.5) * 0.1 # Маленький бонус

            final_score = scen.get("confidence", 0.0) + proactiveness_bonus
            final_score = round(min(1.0, max(0.0, final_score)), 3)

            evaluated_scenarios.append({
                "original_scenario": scen,
                "weighted_score": final_score 
            })
            logger.debug(f"MetaPredictiveSelector: Сценарий '{scen.get('scenario_id')}' действие '{action_concept_str}' получил оценку {final_score} (базовая уверенность {scen.get('confidence', 0.0)})")

        if not evaluated_scenarios:
            logger.warning("MetaPredictiveSelector: Не удалось оценить ни один сценарий.")
            return ActionObject(type="metapredictive_failure", action_concept="request_clarification_or_fallback_no_eval", confidence=0.0, urgency="medium", justification="Сценарии не прошли оценку.")

        best_evaluated = max(evaluated_scenarios, key=lambda x: x["weighted_score"])
        best_scenario = best_evaluated["original_scenario"]
        
        # Формируем ActionObject из лучшего сценария
        action_obj = best_scenario["proposed_action"] # Уже имеет нужную структуру ActionObject
        action_obj["confidence"] = best_evaluated["weighted_score"] # Обновляем уверенность итоговой оценкой
        action_obj["justification"] = f"Выбрано на основе сценария '{best_scenario.get('scenario_id')}' ({best_scenario.get('description', '')[:50]}...). Обоснование действия: {action_obj.get('justification', 'N/A')}"
        action_obj["urgency"] = "high" if best_evaluated["weighted_score"] > 0.8 else "medium" # Примерная логика срочности
        
        logger.info(f"MetaPredictiveSelector: Выбран сценарий '{best_scenario.get('scenario_id')}' с действием '{action_obj.get('action_concept')}' и оценкой {action_obj.get('confidence')}")
        return action_obj


class ReflexPlanner:
    def __init__(self, reflex_rules: Optional[List[Callable[[SRISContext], Optional[Dict[str, Any]]]]] = None):
        """
        :param reflex_rules: Список функций, каждая из которых принимает SRISContext 
                             и возвращает СЛОВАРЬ с параметрами действия (или его часть), если правило сработало.
                             Словарь должен содержать как минимум 'action_concept'.
        """
        self.rules = reflex_rules if reflex_rules is not None else self._get_default_reflex_rules()

    def _get_default_reflex_rules(self) -> List[Callable[[SRISContext], Optional[Dict[str, Any]]]]:
        # Примеры правил, возвращающие часть ActionObject
        def r001_critical_threat(context: SRISContext) -> Optional[Dict[str, Any]]:
            if context.get("perception",{}).get("threat_level", 0.0) >= 0.9: # Порог из твоего запроса
                return {"action_concept": "ACTIVATE_MAXIMUM_DEFENSE_PROTOCOL", "reason": "Критический уровень угрозы"}
            return None

        def r002_self_preservation_violation(context: SRISContext) -> Optional[Dict[str, Any]]:
            active_goal = context.get("active_goal", {})
            sdna = context.get("sDNA_traits", {})
            # Условие "goal = self_preservation" можно интерпретировать так:
            if active_goal.get("concept") == "self_preservation" and active_goal.get("priority") == "critical":
                # И если есть активная угроза этой цели (например, из perception или cause-effect анализа)
                if context.get("perception",{}).get("threat_level", 0.0) > 0.6: # Пример
                     return {"action_concept": "PRIORITIZE_SELF_PRESERVATION_IMMEDIATE_ACTION", "reason": "Активна критическая цель самосохранения под угрозой"}
            # Или если sDNA сильно настроен на самосохранение и есть любая угроза
            elif sdna.get("self_preservation_priority", 0.0) >= 0.9 and context.get("perception",{}).get("threat_level", 0.0) > 0.5:
                return {"action_concept": "INITIATE_SELF_PRESERVATION_MEASURES_SDNA", "reason": "Высокий приоритет самосохранения sDNA под угрозой"}
            return None

        def r003_zav2_flag_interruption(context: SRISContext) -> Optional[Dict[str, Any]]:
            if context.get("system_flags", {}).get("zav2_violation_imminent", False): # Флаг из SRISContext
                return {"action_concept": "HALT_CURRENT_PROCESS_ZAV2_VIOLATION", "reason": "Обнаружен флаг неминуемого нарушения ZAV2"}
            return None
        
        return [r001_critical_threat, r002_self_preservation_violation, r003_zav2_flag_interruption]

    def check_critical(self, context: SRISContext) -> Optional[ActionObject]:
        logger.debug("ReflexPlanner: Проверка критических рефлексов...")
        for rule_func in self.rules:
            action_details = rule_func(context) # action_details это словарь типа {"action_concept": "...", "reason": "..."}
            if action_details and "action_concept" in action_details:
                logger.warning(f"ReflexPlanner: Сработал КРИТИЧЕСКИЙ рефлекс! Правило: {rule_func.__name__}. Действие: {action_details['action_concept']}")
                return ActionObject(
                    type="instinct_critical",
                    action_concept=action_details["action_concept"],
                    confidence=1.0, # Рефлексы абсолютно уверены
                    urgency="immediate", # Критические рефлексы требуют немедленного действия
                    justification=action_details.get("reason", f"Rule {rule_func.__name__} triggered.")
                )
        return None

    def fallback(self, context: SRISContext) -> ActionObject: # context здесь для возможного будущего расширения
        logger.info("ReflexPlanner: Активация fallback-поведения.")
        return ActionObject(
            type="instinct_fallback",
            action_concept="maintain_situational_awareness_and_request_further_guidance_or_reassess", # Более осмысленно
            confidence=0.3, # Низкая уверенность, т.к. это откат
            urgency="medium",
            justification="Прогноз не дал уверенного результата, критические рефлексы не сработали."
        )

class SRISNeuroActionEngine:
    def __init__(
        self,
        scenario_engine: ScenarioReasoningEngine,
        metapredictor: MetaPredictiveSelector,
        reflex_engine: ReflexPlanner
    ):
        self.scenario_engine = scenario_engine
        self.metapredictor = metapredictor
        self.reflex_engine = reflex_engine
        logger.info("SRISNeuroActionEngine (ML-NAE) инициализирован.")

    def decide(self, context: SRISContext) -> ActionObject:
        logger.info("ML-NAE: Начало цикла принятия решения.")
        
        # 1. Сначала всегда проверяем критические инстинкты/рефлексы
        critical_reaction = self.reflex_engine.check_critical(context)
        if critical_reaction:
            logger.warning(f"ML-NAE: КРИТИЧЕСКИЙ РЕФЛЕКС ПЕРЕХВАТИЛ УПРАВЛЕНИЕ. Действие: {critical_reaction.get('action_concept')}")
            return critical_reaction

        # 2. Если критических рефлексов нет, запускаем сценарное рассуждение
        scenarios = self.scenario_engine.generate(context)
        
        if not scenarios:
            logger.warning("ML-NAE: ScenarioReasoningEngine не вернул сценариев. Активация fallback рефлекса.")
            return self.reflex_engine.fallback(context)

        # 3. Оценка всех сценариев (мета-решение)
        # MetaPredictiveSelector выбирает лучшее действие из сценариев
        # и возвращает его уже в формате ActionObject
        selected_action = self.metapredictor.select_best(scenarios, context)
        
        # 4. Проверка уверенности выбранного действия из сценария
        if selected_action and selected_action.get("confidence", 0.0) >= self.metapredictor.threshold:
            logger.info(f"ML-NAE: Выбрано действие из сценария: '{selected_action.get('action_concept')}' с уверенностью {selected_action.get('confidence'):.2f}")
            return selected_action
        else:
            logger.warning(f"ML-NAE: Уверенность выбранного сценария ({selected_action.get('confidence', 0.0):.2f}) ниже порога ({self.metapredictor.threshold}) или действие не выбрано. Активация fallback рефлекса.")
            return self.reflex_engine.fallback(context)

# --- Пример Моков и Запуска (для иллюстрации) ---
if __name__ == "__main__":
    from utils import setup_logging
    setup_logging()
    # === Mockups ===
    def mock_execute_llm_query_for_sre(prompt: str, mode: str, max_tokens: int, temperature: float) -> str:
        logger.info(f"MOCK SRE LLM Query (mode: {mode}): Промпт получен, начинается с: '{prompt[:150]}...'")
        lang_for_response = "русском" # По умолчанию
        if "Language: en" in prompt or "языке: en" in prompt: # Очень грубая проверка
            lang_for_response = "английском"

        if lang_for_response == "русском":
            return """Scenario ID: SCN_001
Scenario Description: Пользователь выглядит озадаченным и ожидает дальнейших разъяснений.
Proposed SRIS Action: предложить_дополнительную_информацию_или_перефразировать_ответ
Action Confidence: 0.85
Action Justification: Прямое наблюдение за реакцией пользователя указывает на необходимость прояснения.
Predicted Effects Summary: Пользователь лучше поймет предыдущий ответ, диалог продолжится конструктивно.
Estimated Risk Level: низкий
---
Scenario ID: SCN_002
Scenario Description: Пользователь может быть не удовлетворен ответом и решить прекратить диалог.
Proposed SRIS Action: вежливо_завершить_текущую_тему_и_предложить_новую
Action Confidence: 0.60
Action Justification: Низкая вовлеченность пользователя может сигнализировать о потере интереса.
Predicted Effects Summary: Диалог может быть сохранен переключением на интересную пользователю тему.
Estimated Risk Level: средний
"""
        else: # English example
            return """Scenario ID: SCN_001
Scenario Description: User appears confused and awaits further clarification.
Proposed SRIS Action: offer_additional_information_or_rephrase_response
Action Confidence: 0.85
Action Justification: Direct observation of user's reaction indicates a need for clarity.
Predicted Effects Summary: User will better understand the previous response, dialogue will continue constructively.
Estimated Risk Level: low
"""
            
    # === SRISContext Example ===
    example_context_ru: SRISContext = {
        "perception": {"summary": "Пользователь выглядит озадаченным.", "threat_level": 0.1, "novelty": 0.2, "language_detected": "ru", "user_query_type": "feedback_statement", "entities": ["пользователь"], "themes": ["непонимание"]},
        "active_goal": {"concept": "ensure_user_understanding", "priority": "high", "urgency": 0.7, "goal_id": "g1"},
        "affect": {"valence": -0.2, "arousal": 0.4, "emotional_label": "concern", "memory_weight": 0.5, "drive_tag": "coherence"},
        "motivation": {"dominant_drive": "coherence", "motivation_level": 0.7},
        "sDNA_traits": {"proactiveness": 0.7, "risk_taking": 0.3, "ethics_sensitivity": 0.9, "curiosity_novelty_bias": 0.5, "self_preservation_priority": 0.8},
        "system_flags": {"zav2_violation_imminent": False}
    }
    
    example_context_critical_threat: SRISContext = {
         "perception": {"summary": "Обнаружена прямая физическая угроза целостности системы!", "threat_level": 0.95, "novelty": 0.8, "language_detected": "ru", "user_query_type": "system_alert"},
        "active_goal": {"concept": "self_preservation", "priority": "critical", "urgency": 1.0, "goal_id": "g_self"},
        "affect": {"valence": -0.9, "arousal": 0.95, "emotional_label": "fear"},
        "motivation": {"dominant_drive": "survival", "motivation_level": 1.0},
        "sDNA_traits": {"proactiveness": 0.9, "risk_taking": 0.6, "ethics_sensitivity": 0.5, "curiosity_novelty_bias": 0.2, "self_preservation_priority": 0.95},
        "system_flags": {"zav2_violation_imminent": False}
    }


    # === Initialization ===
    sre = ScenarioReasoningEngine(llm_func=mock_execute_llm_query_for_sre)
    mps = MetaPredictiveSelector(confidence_threshold=0.70) # Устанавливаем порог для MetaPredictor
    # Для ReflexPlanner можно передать пустой список правил, если дефолтные не нужны, или расширить их
    custom_rules = ReflexPlanner()._get_default_reflex_rules() # Берем дефолтные + можно добавить свои
    # custom_rules.append(my_another_custom_rule_function) 
    frm_plus = ReflexPlanner(reflex_rules=custom_rules)
    
    ml_nae = SRISNeuroActionEngine(scenario_engine=sre, metapredictor=mps, reflex_engine=frm_plus)

    # === Test Run 1: Normal situation ===
    logger.info("\n--- ML-NAE Test 1: Нормальная ситуация (озадаченный пользователь) ---")
    action1 = ml_nae.decide(example_context_ru)
    print(f"ML-NAE Решение 1: {action1}")

    # === Test Run 2: Critical Threat ===
    logger.info("\n--- ML-NAE Test 2: Критическая угроза (ожидаем рефлекс) ---")
    action2 = ml_nae.decide(example_context_critical_threat)
    print(f"ML-NAE Решение 2: {action2}")
    
    # === Test Run 3: ZAV2 flag ===
    example_context_zav2_violation = example_context_ru.copy() # Копируем нормальный контекст
    example_context_zav2_violation["system_flags"] = {"zav2_violation_imminent": True}
    logger.info("\n--- ML-NAE Test 3: Флаг нарушения ZAV2 (ожидаем рефлекс) ---")
    action3 = ml_nae.decide(example_context_zav2_violation)
    print(f"ML-NAE Решение 3: {action3}")
