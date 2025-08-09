# sris_kernel.py — Integrated Reasoning Kernel SRIS 1.0 (with Temporality Core & Full GUI code)

# Стандартные импорты SRIS
from perception_analysis import analyze_perception
from sensorium_core import integrate_sensorium
from goal_engine import form_goal
from motivation_engine import evaluate_motivation
from affect_layer import assess_affect
from hypothesis_generator import generate_hypotheses
from adaptive_logic import adjust_hypotheses
from zav2_context_validator import validate_contextual_hypothesis
from fractal_ontology import check_ontology
from hypothesis_evaluator import evaluate_hypotheses
from emotional_processor import evaluate_emotion
from cause_effect import extract_cause_effect
from semantic_memory_fs import save_chain_to_fs
from semantic_memory_index import query_semantic_memory, get_or_build_semantic_index
from communication_intent import determine_communication_intent
from neural_motion_core import plan_action
from tuning_module import run_self_refinement, safety_filter, trace_reasoning_path
from dream_cycle import run_dream_cycle
from response_generator import generate_sris_response

# Стандартные импорты Python
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import json
import random
import logging
import time

# ---- GUI Imports ----
import tkinter as tk
from tkinter import scrolledtext, Menu, END, DISABLED, NORMAL
import threading
import platform

# --- Импорты и экземпляры Temporality Core ---
try:
    from temporality_core import TimeSense, ReasoningTimeline
    sris_timesense = TimeSense()
    sris_timeline = ReasoningTimeline(timesense_instance=sris_timesense)
    temporality_modules_loaded = True
    logging.info("Temporality Core (TimeSense, ReasoningTimeline) успешно инициализирован.")
except ImportError:
    logging.error("Ошибка импорта temporality_core.py. Функциональность темпоральности будет отключена.")
    temporality_modules_loaded = False
    class TimeSense: # type: ignore
        def tick(self): return 0
        def mark_event(self, event_id: str, specific_tick: Optional[int] = None): pass
        def get_time_since_event(self, event_id: str) -> Optional[int]: return None
        def get_current_tick(self): return 0
    class ReasoningTimeline: # type: ignore
        def __init__(self, timesense_instance: Any): pass
        def record_event(self, event_type: str, event_data: Dict[str, Any], reasoning_chain_id: Optional[str]=None, related_to_tick: Optional[int]=None): pass
    sris_timesense = TimeSense() # type: ignore
    sris_timeline = ReasoningTimeline(sris_timesense) # type: ignore

# Настройка логирования
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

# --- Константы и глобальные переменные SRIS ---
DEFAULT_SDNA = {"adaptivity":0.7,"ethics_sensitivity":0.8,"thinking_style":"deductive","curiosity_level":0.6,"security_priority":0.4,"risk_aversion":0.5,"empathy_level":0.5,"novelty_seeking":0.6,"risk_taking":0.5,"proactiveness":0.5,"efficiency_preference":0.5,"ethical_risk_aversion":0.5,"assertiveness_level":0.5,"transparency_level":0.5}
DEFAULT_ACTION_CONTEXT_FLAGS = {"threat_confirmed": True}
PRELIMINARY_MOTIVATION_SIGNAL = {"dominant_drive": "coherence_initial", "motivation_level": 0.5}
DEFAULT_REASONING_MODE = "default_exploration"
initial_semantic_index = None

# --- Инициализация "тяжелых" компонентов ---
def initialize_sris_components():
    global initial_semantic_index
    if initial_semantic_index is None:
        try:
            logger.info("Инициализация семантического индекса памяти при запуске...")
            initial_semantic_index = get_or_build_semantic_index(rebuild=False)
            if initial_semantic_index:
                logger.info("Семантический индекс памяти успешно инициализирован.")
            else:
                logger.warning("Семантический индекс памяти не был инициализирован.")
        except Exception as e_index_init:
            logger.error(f"Критическая ошибка при инициализации семантического индекса: {e_index_init}", exc_info=True)

# --- Вспомогательные функции для разных путей рассуждений ---
# (Я перенесу их определение перед основным циклом для ясности)

def _handle_fast_path_query(input_dict: Dict[str, Any], perception: Dict[str, Any], reasoning_chain_id: str, tick_at_cycle_start: int) -> Dict[str, Any]:
    logger.info("Fast-Path: Активирован 'короткий путь' для простого запроса.")
    user_query_type = perception.get("user_query_type")
    communication_intent_obj: Dict[str, Any] = {}
    chosen_hypothesis_text = "Сгенерировать простой ответ на основе намерения."

    if user_query_type == "social_greeting":
        communication_intent_obj = {"intent_type": "reciprocate_social_interaction", "style": "friendly_conversational", "explanation_priority": "low_social", "emotional_tone": "relaxed", "target_focus": "general"}
        chosen_hypothesis_text = f"Сформулировать дружелюбный ответ на приветствие: '{input_dict.get('text', '')}'"
    elif user_query_type == "feedback_statement":
        sentiment = perception.get("sentiment", "neutral")
        if "позитивный" in sentiment:
            chosen_hypothesis_text = "Поблагодарить пользователя за позитивную обратную связь."
        elif "негативный" in sentiment:
            chosen_hypothesis_text = "Принять к сведению негативную обратную связь и выразить сожаление."
        else:
            chosen_hypothesis_text = "Принять к сведению обратную связь от пользователя."
        communication_intent_obj = {"intent_type": "acknowledge_feedback", "style": "empathetic_professional", "explanation_priority": "low_social", "emotional_tone": "neutral", "target_focus": "general"}

    reasoning_chain = {
        "id": reasoning_chain_id, "timestamp": datetime.now(timezone.utc).isoformat(),
        "sris_start_tick": tick_at_cycle_start, "sris_end_tick": sris_timesense.get_current_tick(),
        "input_text": input_dict.get("text"), "perception_struct": perception,
        "chosen_hypothesis": {"hypothesis": chosen_hypothesis_text},
        "communication_intent": communication_intent_obj, "mode": "fast_path_reasoning"
    }
    logger.info(f"Fast-Path: Сформировано коммуникационное намерение: {communication_intent_obj}")
    if temporality_modules_loaded:
        sris_timeline.record_event("fast_path_activated", {"user_query_type": user_query_type}, reasoning_chain_id)
        sris_timeline.record_event("sris_cycle_completed_fast_path", {"status": "ok"}, reasoning_chain_id, related_to_tick=tick_at_cycle_start)
    logger.info(f"--- (Tick: {sris_timesense.get_current_tick()}) Цикл SRIS (Fast-Path) завершен (ID: {reasoning_chain_id}) ---")
    return {"status": "ok", "reasoning_id": reasoning_chain_id, "hypothesis": chosen_hypothesis_text, "full_reasoning_chain": reasoning_chain}

def _handle_full_cycle_query(input_dict: Dict[str, Any], perception: Dict[str, Any], reasoning_chain_id: str, tick_at_cycle_start: int) -> Dict[str, Any]:
    logger.info("Full-Path: Активирован полный цикл рассуждений.")
    retrieved_memories_summary = None; goal = {}; motivation = {}; affect = {}; raw_hyp = []; hypotheses = []; valid_hypotheses = []; evaluated_hypotheses = []; best_hypothesis_obj = {}; emotion = {}; cause_effect_analysis = {}; action_plan_result = {}; communication_intent_obj = {}; sensorium = {"raw_fused": perception.get("original_input","")}
    
    # Шаг 2.5: Запрос к семантической памяти
    if initial_semantic_index:
        try:
            perception_summary_for_query = perception.get('summary')
            if perception_summary_for_query and perception_summary_for_query.lower() not in ["n/a", "не удалось извлечь"]:
                relevant_memories = query_semantic_memory(index=initial_semantic_index, query_text=perception_summary_for_query, similarity_top_k=1)
                if relevant_memories:
                    memory_snippets = [f"- Прошлый опыт (ID: {m.get('chain_id') or m.get('wikidata_qid') or m.get('metadata',{}).get('doc_id') or 'N/A'}, Сходство: {m.get('score',0):.2f}): {m.get('text_preview', 'N/A')[:150]}..." for m in relevant_memories]
                    retrieved_memories_summary = "\n".join(memory_snippets)
                    logger.info(f"Извлечено из памяти ({len(relevant_memories)} записей): {retrieved_memories_summary[:200]}...")
                    if temporality_modules_loaded: sris_timeline.record_event("semantic_memory_retrieved", {"count": len(relevant_memories)}, reasoning_chain_id)
        except Exception as e: logger.error(f"Ошибка при запросе к памяти: {e}", exc_info=True)

    # Шаги 3, 4, 5
    goal = form_goal(perception, DEFAULT_SDNA, PRELIMINARY_MOTIVATION_SIGNAL)
    if temporality_modules_loaded: sris_timeline.record_event("goal_formed", goal.copy(), reasoning_chain_id)
    motivation = evaluate_motivation(goal.get("concept", "analyze_situation"), DEFAULT_SDNA)
    if temporality_modules_loaded: sris_timeline.record_event("motivation_evaluated", motivation.copy(), reasoning_chain_id)
    affect = assess_affect(perception, motivation, [goal] if goal else [], DEFAULT_SDNA)
    if temporality_modules_loaded: sris_timeline.record_event("affect_assessed", affect.copy(), reasoning_chain_id)

    # Шаги 6, 7, 8
    raw_hyp = generate_hypotheses(perception, [goal] if goal else [], DEFAULT_SDNA, DEFAULT_REASONING_MODE, retrieved_memories_summary)
    hypotheses = adjust_hypotheses(raw_hyp, goal.get("concept", "analyze_situation"), perception)
    valid_hypotheses = [h for h in hypotheses if isinstance(h, str) and h.strip()] # ВРЕМЕННО УПРОЩЕННЫЙ ФИЛЬТР
    if not valid_hypotheses: raise ValueError("Не осталось валидных гипотез после фильтрации.")
    evaluated_hypotheses = evaluate_hypotheses(valid_hypotheses, perception, [goal] if goal else [], DEFAULT_SDNA, DEFAULT_REASONING_MODE)
    if not evaluated_hypotheses: raise ValueError("Оценка гипотез не дала результатов.")
    best_hypothesis_obj = evaluated_hypotheses[0]
    logger.info(f"Лучшая гипотеза: {best_hypothesis_obj.get('hypothesis', 'N/A')[:70]}...")
    if temporality_modules_loaded and best_hypothesis_obj.get('hypothesis'): sris_timeline.record_event("hypothesis_chosen", {"hypothesis_preview": best_hypothesis_obj.get('hypothesis', 'N/A')[:70], "score": best_hypothesis_obj.get('score')}, reasoning_chain_id)

    # Шаги 9, 10, 11
    emotion = evaluate_emotion(perception, best_hypothesis_obj.get("hypothesis", ""))
    cause_effect_analysis = extract_cause_effect(perception, best_hypothesis_obj.get("hypothesis", ""), {"current_goals": [goal] if goal else [], "current_mode": DEFAULT_REASONING_MODE, "sdna_traits": DEFAULT_SDNA})
    action_plan_result = plan_action(best_hypothesis_obj.get("hypothesis", ""), goal if goal else {}, DEFAULT_ACTION_CONTEXT_FLAGS)
    communication_intent_obj = determine_communication_intent(perception, [goal] if goal else [], affect, motivation, DEFAULT_SDNA)
    if temporality_modules_loaded: sris_timeline.record_event("communication_intent_determined", communication_intent_obj.copy(), reasoning_chain_id)
    
    # Шаг 12
    reasoning_chain = {
        "id": reasoning_chain_id, "timestamp": datetime.now(timezone.utc).isoformat(),
        "sris_start_tick": tick_at_cycle_start, "sris_end_tick": sris_timesense.get_current_tick(),
        "input_text": input_dict.get("text"), "sensorium": sensorium, "perception_struct": perception,
        "retrieved_memories_summary": retrieved_memories_summary, "goal": goal, "motivation": motivation,
        "affect": affect, "raw_hypotheses_llm": raw_hyp, "adjusted_hypotheses": hypotheses, 
        "valid_hypotheses": valid_hypotheses, "evaluated_hypotheses": evaluated_hypotheses, 
        "chosen_hypothesis": best_hypothesis_obj, "emotion": emotion,
        "preconditions": cause_effect_analysis.get("preconditions"),
        "effects": cause_effect_analysis.get("effects"), "action_plan": action_plan_result,
        "communication_intent": communication_intent_obj,
        "entity_id": "SRIS-001", "mode": "full_reasoning"
    }
    save_chain_to_fs(reasoning_chain)
    logger.info(f"--- (Tick: {sris_timesense.get_current_tick()}) Цикл SRIS (Full-Path) завершен (ID: {reasoning_chain_id}) ---")
    if temporality_modules_loaded: sris_timeline.record_event("sris_cycle_completed_full_path", {"status": "ok"}, reasoning_chain_id, related_to_tick=tick_at_cycle_start)
    
    return {"status": "ok", "reasoning_id": reasoning_chain_id, "hypothesis": best_hypothesis_obj.get("hypothesis", "N/A"), "full_reasoning_chain": reasoning_chain}

# --- Основная функция ядра SRIS (теперь это ДИСПЕТЧЕР) ---
def run_sris_cycle(input_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    tick_at_cycle_start = sris_timesense.get_current_tick() 
    current_sris_tick = sris_timesense.tick() 
    reasoning_chain_id = str(uuid.uuid4())
    logger.info(f"--- (Tick: {current_sris_tick}) Начало нового цикла SRIS (ID: {reasoning_chain_id}) ---")
    
    if temporality_modules_loaded: sris_timeline.record_event("sris_cycle_started", {"input_text": input_dict.get("text")}, reasoning_chain_id)

    try:
        # Шаги 1 и 2 выполняются всегда
        logger.info(f"(Tick: {sris_timesense.get_current_tick()}) Шаг 1: Сенсориум...")
        sensorium = integrate_sensorium(input_dict.get("text"), input_dict.get("audio"), input_dict.get("vision"))
        
        logger.info(f"(Tick: {sris_timesense.get_current_tick()}) Шаг 2: Анализ восприятия...")
        perception = analyze_perception(sensorium["raw_fused"])
        if perception.get("error"): raise ValueError(f"Ошибка на этапе анализа восприятия: {perception.get('error')}")

        # --- НОВЫЙ ДИСПЕТЧЕР: Выбор пути рассуждений ---
        user_query_type = perception.get("user_query_type")
        FAST_PATH_QUERY_TYPES = ["social_greeting", "feedback_statement"]
        
        if user_query_type in FAST_PATH_QUERY_TYPES:
            # Выполняем упрощенный цикл
            return _handle_fast_path_query(input_dict, perception, reasoning_chain_id, tick_at_cycle_start)
        else:
            # Выполняем полный, глубокий цикл рассуждений
            return _handle_full_cycle_query(input_dict, perception, reasoning_chain_id, tick_at_cycle_start)

    except Exception as e_cycle:
        final_tick = sris_timesense.get_current_tick()
        logger.critical(f"Критическая ошибка в цикле SRIS (ID: {reasoning_chain_id}, Tick: {final_tick}): {e_cycle}", exc_info=True)
        if temporality_modules_loaded:
            sris_timeline.record_event("sris_cycle_error", {"error_message": str(e_cycle)}, reasoning_chain_id, related_to_tick=tick_at_cycle_start)
        
        error_details = {"error_message": str(e_cycle), "sris_start_tick": tick_at_cycle_start, "sris_end_tick": final_tick}
        if 'perception' in locals() and perception: error_details["perception_at_error"] = perception
        return {"status": "cycle_error", "reasoning_id": reasoning_chain_id, "hypothesis": None, "full_reasoning_chain": error_details}


# ==============================================================================
# GUI ДЛЯ ДИАЛОГА С SRIS
# ==============================================================================
class SRISChatApp:
    def __init__(self, root_tk):
        self.root = root_tk
        self.root.title("SRIS - Диалоговый агент")
        self.root.geometry("700x550")

        self.bg_color = "#282c34"
        self.text_color = "#abb2bf"
        self.entry_bg = "#1e2228"
        self.button_bg = "#61afef"
        self.button_fg = "#282c34"
        self.sris_color = "#98c379" 
        self.user_color = "#61afef" 
        self.system_color = "#c678dd"

        self.root.configure(bg=self.bg_color)

        self.chat_history = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=DISABLED, bg=self.entry_bg, fg=self.text_color,
            font=("Arial", 10), padx=10, pady=10, relief=tk.FLAT, borderwidth=0, exportselection=True
        )
        self.chat_history.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_history.bind("<KeyPress>", self._prevent_chat_edit)

        self.chat_history.tag_config("user", foreground=self.user_color, font=("Arial", 10, "bold"))
        self.chat_history.tag_config("sris", foreground=self.sris_color, font=("Arial", 10, "italic"))
        self.chat_history.tag_config("system", foreground=self.system_color, font=("Arial", 9, "italic"))

        self.input_frame = tk.Frame(self.root, bg=self.bg_color)
        self.input_frame.pack(padx=10, pady=(0,10), fill=tk.X, expand=False)
        
        self.user_input_entry = tk.Entry(
            self.input_frame, width=70, bg=self.entry_bg, fg=self.text_color,
            insertbackground=self.text_color, font=("Arial", 11), relief=tk.FLAT,
            borderwidth=0, exportselection=True
        )
        self.user_input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.user_input_entry.bind("<Return>", self.send_message_event)

        self.send_button = tk.Button(
            self.input_frame, text="Отправить", command=self.send_message_event,
            bg=self.button_bg, fg=self.button_fg, activebackground="#528baf", 
            activeforeground=self.button_fg, relief=tk.FLAT, borderwidth=0, 
            padx=10, pady=5, font=("Arial", 10, "bold")
        )
        self.send_button.pack(side=tk.RIGHT, padx=(5,0))
        
        self._make_context_menu(self.chat_history)
        self._make_context_menu(self.user_input_entry)
        self._bind_keyboard_shortcuts()
        
        self.add_message_to_chat("System", "Инициализация SRIS...")
        
        # Вызываем инициализацию компонентов здесь
        initialize_sris_components()
        
        self.add_message_to_chat("SRIS", "Здравствуйте! Я SRIS. Чем могу помочь?", is_sris=True)
        self.add_message_to_chat("System", "Подсказка: логи работы ядра SRIS выводятся в эту консоль.", is_system=True)
        if initial_semantic_index:
            self.add_message_to_chat("System", "Семантический индекс памяти успешно инициализирован.", is_system=True)
        else:
            self.add_message_to_chat("System", "ВНИМАНИЕ: Семантический индекс памяти НЕ инициализирован.", is_system=True)
        
        if temporality_modules_loaded:
            self.add_message_to_chat("System", f"Temporality Core активен. Начальный тик: {sris_timesense.get_current_tick()}", is_system=True)
        else:
            self.add_message_to_chat("System", "ПРЕДУПРЕЖДЕНИЕ: Temporality Core не загружен.", is_system=True)

    def _prevent_chat_edit(self, event):
        allowed_keys_specific = ['c', 'C', 'a', 'A'] 
        allowed_modifiers_general = ['Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Super_L', 'Super_R', 'Meta_L', 'Meta_R', 'Alt_L', 'Alt_R']
        navigation_keys = ['Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Prior', 'Next', 'Page_Up', 'Page_Down']
        is_modifier_pressed = event.state & (1<<2)
        if platform.system() == "Darwin": is_modifier_pressed = event.state & (1<<3)
        if is_modifier_pressed and event.keysym.lower() in allowed_keys_specific: return 
        if event.keysym in allowed_modifiers_general or event.keysym in navigation_keys: return 
        return "break" 

    def _make_context_menu(self, widget):
        menu = Menu(widget, tearoff=0, bg=self.entry_bg, fg=self.text_color, activebackground=self.button_bg, activeforeground=self.button_fg, relief=tk.FLAT, font=("Arial", 9))
        is_text_widget = isinstance(widget, (tk.Text, scrolledtext.ScrolledText))
        is_entry_widget = isinstance(widget, tk.Entry)
        if is_text_widget or is_entry_widget: menu.add_command(label="Копировать", command=lambda: self._copy_text(widget))
        if is_entry_widget:
            menu.add_command(label="Вырезать", command=lambda: self._cut_text(widget))
            menu.add_command(label="Вставить", command=lambda: self._paste_text(widget))
        if is_text_widget or is_entry_widget:
            menu.add_separator()
            menu.add_command(label="Выделить все", command=lambda: self._select_all_text(widget))
        popup_event = "<Button-3>" if platform.system() != "Darwin" else "<Button-2>"
        widget.bind(popup_event, lambda event: menu.tk_popup(event.x_root, event.y_root))

    def _copy_text(self, widget):
        try:
            if widget.selection_get():
                self.root.clipboard_clear()
                self.root.clipboard_append(widget.selection_get())
        except tk.TclError: pass 
            
    def _cut_text(self, widget):
        try:
            if widget.selection_get():
                self._copy_text(widget)
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError: pass

    def _paste_text(self, widget):
        try:
            widget.insert(widget.index(tk.INSERT), self.root.clipboard_get())
        except tk.TclError: pass
            
    def _select_all_text(self, widget):
        if isinstance(widget, (tk.Text, scrolledtext.ScrolledText)):
            widget.tag_add(tk.SEL, "1.0", tk.END); widget.mark_set(tk.INSERT, "1.0"); widget.see(tk.INSERT)
        elif isinstance(widget, tk.Entry):
            widget.select_range(0, tk.END); widget.icursor(tk.END)
        return "break" 

    def _bind_keyboard_shortcuts(self):
        copy_accel = 'Control-c'; paste_accel = 'Control-v'; cut_accel = 'Control-x'; select_all_accel = 'Control-a'
        if platform.system() == 'Darwin': 
            copy_accel = 'Command-c'; paste_accel = 'Command-v'; cut_accel = 'Command-x'; select_all_accel = 'Command-a'
        self.user_input_entry.bind(f"<{paste_accel}>", lambda e: self._paste_text(self.user_input_entry))
        self.user_input_entry.bind(f"<{copy_accel}>", lambda e: self._copy_text(self.user_input_entry))
        self.user_input_entry.bind(f"<{cut_accel}>", lambda e: self._cut_text(self.user_input_entry))
        self.user_input_entry.bind(f"<{select_all_accel}>", lambda e: self._select_all_text(self.user_input_entry))
        self.chat_history.bind(f"<{copy_accel}>", lambda e: self._copy_text(self.chat_history))
        self.chat_history.bind(f"<{select_all_accel}>", lambda e: self._select_all_text(self.chat_history))

    def add_message_to_chat(self, sender: str, message: str, is_sris: bool = False, is_system: bool = False):
        self.chat_history.config(state=NORMAL)
        sender_tag = "user"
        if is_sris: sender_tag = "sris"
        elif is_system: sender_tag = "system"
        self.chat_history.insert(tk.END, f"{sender}: ", (sender_tag,))
        self.chat_history.insert(tk.END, f"{message}\n\n")
        self.chat_history.see(tk.END) 
        self.chat_history.config(state=DISABLED)

    def process_sris_cycle_in_thread(self, user_text: str):
        self.add_message_to_chat("SRIS", "*обрабатываю ваш запрос...*", is_sris=True, is_system=True)
        self.user_input_entry.config(state=DISABLED)
        self.send_button.config(state=DISABLED)
        input_dict = {"text": user_text, "audio": None, "vision": None}
        
        sris_reasoning_result = run_sris_cycle(input_dict) 
        
        if sris_reasoning_result and sris_reasoning_result.get("full_reasoning_chain") and logger.isEnabledFor(logging.DEBUG):
             logger.debug(f"Полная цепочка рассуждений для ответа: {json.dumps(sris_reasoning_result['full_reasoning_chain'], indent=2, ensure_ascii=False)}")
        
        def update_gui_with_response():
            # Здесь можно будет реализовать удаление сообщения "*обрабатываю ваш запрос...*"
            # self.chat_history.config(state=NORMAL)
            # self.chat_history.delete("end-3l", "end-1c") # Удаляет 2 предыдущие строки
            # self.chat_history.config(state=DISABLED)
            
            if sris_reasoning_result and sris_reasoning_result.get("status") == "ok":
                sris_reply_text = generate_sris_response(sris_reasoning_result["full_reasoning_chain"])
                self.add_message_to_chat("SRIS", sris_reply_text, is_sris=True)
            elif sris_reasoning_result:
                error_msg = sris_reasoning_result.get("full_reasoning_chain", {}).get("error_message", "неизвестная ошибка")
                reply = f"[Внутренний статус: {sris_reasoning_result.get('status', 'ошибка')}, Детали: {error_msg}] Я не могу сейчас ответить должным образом."
                self.add_message_to_chat("SRIS", reply, is_sris=True, is_system=True)
            else:
                reply = "Произошла неожиданная внутренняя ошибка (run_sris_cycle вернул None)."
                self.add_message_to_chat("SRIS", reply, is_sris=True, is_system=True)
            self.enable_input()
        self.root.after(0, update_gui_with_response)

    def enable_input(self):
        self.user_input_entry.config(state=NORMAL)
        self.send_button.config(state=NORMAL)
        self.user_input_entry.focus_set()

    def send_message_event(self, event=None):
        user_text = self.user_input_entry.get().strip()
        if not user_text: return
        self.add_message_to_chat("Вы", user_text)
        self.user_input_entry.delete(0, tk.END)
        thread = threading.Thread(target=self.process_sris_cycle_in_thread, args=(user_text,))
        thread.daemon = True 
        thread.start()


