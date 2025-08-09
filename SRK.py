# SRK.py — v2.3 (исправлены импорты, сигнатуры вызовов, стабильный reasoning-цикл, GUI-фиксы)

# --- Подготовка PYTHONPATH для локальных модулей (исправляет ModuleNotFoundError) ---
import sys, os, pathlib
_ROOT = pathlib.Path(__file__).parent if '__file__' in globals() else pathlib.Path().resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# --- Стандартные импорты SRK ---
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
from tuning_module import safety_filter
from response_generator import generate_sris_response

# --- Продвинутые модули (опционально) ---
import logging
try:
    from temporality_core import TimeSense, ReasoningTimeline
    from reflective_intelligence_unit import ReflectiveIntelligenceUnit
    _ADV_OK = True
except ImportError as e:
    _ADV_OK = False
    logging.error(f"Критическая ошибка импорта продвинутых модулей: {e}")

# --- Стандартные импорты Python ---
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import threading
import platform
import json

# ---- GUI Imports ----
import tkinter as tk
from tkinter import scrolledtext, Menu, END, DISABLED, NORMAL

# --- Глобальные переменные и экземпляры ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

sris_timesense: Optional["TimeSense"] = None
sris_timeline: Optional["ReasoningTimeline"] = None
sris_riu: Optional["ReflectiveIntelligenceUnit"] = None
initial_semantic_index: Optional[Any] = None

# --- Константы SRK ---
DEFAULT_SDNA = {
    "adaptivity": 0.7, "ethics_sensitivity": 0.8, "thinking_style": "deductive", "curiosity_level": 0.6,
    "security_priority": 0.4, "risk_aversion": 0.5, "empathy_level": 0.5, "novelty_seeking": 0.6,
    "risk_taking": 0.5, "proactiveness": 0.5, "efficiency_preference": 0.5,
    "ethical_risk_aversion": 0.5, "assertiveness_level": 0.5, "transparency_level": 0.5
}
PRELIMINARY_MOTIVATION_SIGNAL = {"dominant_drive": "coherence_initial", "motivation_level": 0.5}
DEFAULT_REASONING_MODE = "default_exploration"
DEFAULT_ACTION_CONTEXT_FLAGS = {"threat_confirmed": True}

# --- Инициализация SRK ядра ---
def initialize_srk_backend(app_instance):
    global sris_timesense, sris_timeline, sris_riu, initial_semantic_index, _ADV_OK
    try:
        logger.info("Фоновая инициализация SRK... Начало.")
        app_instance.add_message_to_chat("System", "Инициализация модулей...", is_system=True)

        if _ADV_OK:
            sris_timesense = TimeSense()
            sris_timeline = ReasoningTimeline(timesense_instance=sris_timesense)
            sris_riu = ReflectiveIntelligenceUnit(agent_name="SRK-Prometheus")
            logger.info("Temporality Core и RIU успешно инициализированы.")
            app_instance.add_message_to_chat("System", "Temporality Core и RIU активны.", is_system=True)
        else:
            logger.error("Продвинутые модули не были загружены из-за ошибки импорта.")
            app_instance.add_message_to_chat("System", "ПРЕДУПРЕЖДЕНИЕ: Продвинутые модули не загружены.", is_system=True)
            # Продолжаем без них

        logger.info("Инициализация семантического индекса памяти...")
        app_instance.add_message_to_chat("System", "Загрузка семантической памяти...", is_system=True)
        initial_semantic_index = get_or_build_semantic_index(rebuild=False)
        if initial_semantic_index:
            logger.info("Семантический индекс памяти успешно инициализирован.")
            app_instance.add_message_to_chat("System", "Семантическая память успешно загружена.", is_system=True)
        else:
            logger.warning("Семантический индекс памяти не был инициализирован.")
            app_instance.add_message_to_chat("System", "ВНИМАНИЕ: Семантическая память НЕ инициализирована.", is_system=True)

        logger.info("Фоновая инициализация SRK... Завершено.")
        app_instance.add_message_to_chat("SRK", "Я полностью готов к работе. Чем могу помочь?", is_sris=True)
        app_instance.enable_input()

    except Exception as e:
        logger.critical(f"КРИТИЧЕСКАЯ ОШИБКА во время фоновой инициализации: {e}", exc_info=True)
        app_instance.add_message_to_chat("System", f"КРИТИЧЕСКАЯ ОШИБКА ИНИЦИАЛИЗАЦИИ: {e}", is_system=True)

# --- Обработчик простого запроса (fast-path) ---
def _handle_fast_path_query(input_dict: Dict[str, Any], perception: Dict[str, Any], reasoning_chain_id: str, tick_at_cycle_start: int) -> Dict[str, Any]:
    logger.info("Fast-Path: Активирован 'короткий путь' для простого запроса.")
    communication_intent_obj: Dict[str, Any] = {}
    chosen_hypothesis_text = "Сгенерировать простой ответ на основе намерения."

    riu_state_for_log = sris_riu.get_context_for_llm() if _ADV_OK and sris_riu else {}
    reasoning_chain = {
        "id": reasoning_chain_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sris_start_tick": tick_at_cycle_start,
        "sris_end_tick": sris_timesense.get_current_tick() if sris_timesense else 0,
        "input_text": input_dict.get("text"),
        "perception_struct": perception,
        "chosen_hypothesis": {"hypothesis": chosen_hypothesis_text},
        "communication_intent": communication_intent_obj,
        "reflective_intelligence_unit_state": riu_state_for_log,
        "mode": "fast_path_reasoning"
    }
    save_chain_to_fs(reasoning_chain)
    logger.info("Fast-Path: Сформировано и сохранено reasoning_chain.")
    return {"status": "ok", "reasoning_id": reasoning_chain_id, "full_reasoning_chain": reasoning_chain}

# --- Обработчик полного reasoning-цикла ---
def _handle_full_cycle_query(input_dict: Dict[str, Any], perception: Dict[str, Any], reasoning_chain_id: str, tick_at_cycle_start: int) -> Dict[str, Any]:
    logger.info("Full-Path: Активирован полный цикл рассуждений.")

    if _ADV_OK and sris_riu:
        sris_riu.process_perception(perception)

    # 1) Цель и мотивация
    goal = form_goal(perception, DEFAULT_SDNA, PRELIMINARY_MOTIVATION_SIGNAL)
    motivation = evaluate_motivation(goal.get("concept", "analyze situation"), DEFAULT_SDNA, {})

    # 2) Память (учитываем корректный порядок аргументов)
    memory_results = None
    try:
        if initial_semantic_index and perception.get("summary"):
            memory_results = query_semantic_memory(index=initial_semantic_index, query_text=perception.get("summary", ""), similarity_top_k=1)
    except Exception as e:
        logger.warning(f"Ошибка запроса к семантической памяти: {e}")

    memory_context_text = None
    if memory_results:
        # Берём полный текст первого узла
        memory_context_text = memory_results[0].get("full_text") or memory_results[0].get("text_preview")

    # 3) Аффект
    affect = assess_affect(perception, motivation, [goal], DEFAULT_SDNA)
    if _ADV_OK and sris_riu:
        sris_riu.process_affect(affect)

    riu_context = sris_riu.get_context_for_llm() if _ADV_OK and sris_riu else None

    # 4) Гипотезы
    raw_hyp = generate_hypotheses(
        perception_struct=perception,
        current_goals=[goal],
        sDNA_traits=DEFAULT_SDNA,
        current_mode=DEFAULT_REASONING_MODE,
        memory_context=memory_context_text
    )
    adjusted_hypotheses = adjust_hypotheses(raw_hyp, DEFAULT_REASONING_MODE, perception)

    # 5) Фильтры безопасности/онтологии (делаем по одной гипотезе, а не списком)
    valid_hypotheses = [h for h in adjusted_hypotheses if isinstance(h, str) and h.strip()]
    evaluated = []
    for h in valid_hypotheses:
        zchk = validate_contextual_hypothesis(h)
        if not zchk.get("valid", True):
            continue
        onchk = check_ontology(h, perception, DEFAULT_REASONING_MODE, DEFAULT_SDNA)
        if not onchk.get("valid", True):
            continue
        # Доп. safety фильтр, если он есть
        try:
            h_safe = safety_filter(h)
            if h_safe is False:
                continue
        except Exception:
            pass
        evaluated.append(h)

    if not evaluated:
        evaluated = valid_hypotheses or ["Нет валидных гипотез"]

    # 6) Оценка гипотез по качеству
    scored_list = evaluate_hypotheses(evaluated, perception, [goal], DEFAULT_SDNA, DEFAULT_REASONING_MODE)
    best_obj = scored_list[0] if scored_list else {"hypothesis": evaluated[0], "score": 0.0}

    # 7) Эмоция, причинно-следственные связи, план действия, намерение коммуникации
    emotion = evaluate_emotion(perception, best_obj.get("hypothesis", ""))
    causal = extract_cause_effect(perception, best_obj.get("hypothesis", ""), {"current_goals": [goal], "current_mode": DEFAULT_REASONING_MODE, "sdna_traits": DEFAULT_SDNA})
    action_plan = plan_action(best_obj.get("hypothesis", ""), goal, DEFAULT_ACTION_CONTEXT_FLAGS)
    comm_intent = determine_communication_intent(perception, [goal], affect, motivation, DEFAULT_SDNA)

    # 8) Итоговая цепочка рассуждений
    reasoning_chain = {
        "id": reasoning_chain_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sris_start_tick": tick_at_cycle_start,
        "sris_end_tick": sris_timesense.get_current_tick() if sris_timesense else 0,
        "input_text": input_dict.get("text"),
        "perception_struct": perception,
        "goal": goal,
        "motivation": motivation,
        "memory_context_text": memory_context_text,
        "affect": affect,
        "raw_hypotheses_llm": raw_hyp,
        "adjusted_hypotheses": adjusted_hypotheses,
        "chosen_hypothesis": best_obj,
        "emotion": emotion,
        "preconditions": causal.get("preconditions"),
        "effects": causal.get("effects"),
        "action_plan": action_plan,
        "communication_intent": comm_intent,
        "reflective_intelligence_unit_state": riu_context,
        "mode": "full_reasoning"
    }
    save_chain_to_fs(reasoning_chain)
    return {"status": "ok", "reasoning_id": reasoning_chain_id, "full_reasoning_chain": reasoning_chain}

# --- Основной reasoning-цикл ---
def run_srk_cycle(input_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not all([sris_timesense is not None, sris_timeline is not None]):
        return {"status": "error", "full_reasoning_chain": {"error_message": "SRK core components not initialized."}}

    tick_at_cycle_start = sris_timesense.get_current_tick() if sris_timesense else 0
    current_sris_tick = sris_timesense.tick() if sris_timesense else 0
    reasoning_chain_id = str(uuid.uuid4())
    logger.info(f"--- (Tick: {current_sris_tick}) Начало нового цикла SRK (ID: {reasoning_chain_id}) ---")

    try:
        logger.info(f"(Tick: {current_sris_tick}) Шаг 1: Сенсориум...")
        sensorium = integrate_sensorium(input_dict.get("text"), input_dict.get("audio"), input_dict.get("vision"))

        logger.info(f"(Tick: {current_sris_tick}) Шаг 2: Анализ восприятия...")
        perception = analyze_perception(sensorium["raw_fused"])
        if perception.get("error"):
            raise ValueError(f"Ошибка на этапе анализа восприятия: {perception.get('error')}")

        user_query_type = perception.get("query_type") or perception.get("user_query_type")
        FAST_PATH_QUERY_TYPES = [
            "conversation_flow:greeting_social",
            "conversation_flow:feedback",
            "conversation_flow:closing",
        ]

        if user_query_type in FAST_PATH_QUERY_TYPES:
            return _handle_fast_path_query(input_dict, perception, reasoning_chain_id, tick_at_cycle_start)
        else:
            return _handle_full_cycle_query(input_dict, perception, reasoning_chain_id, tick_at_cycle_start)

    except Exception as e_cycle:
        logger.error(f"SRK: Ошибка во время reasoning-цикла: {e_cycle}", exc_info=True)
        return {"status": "error", "full_reasoning_chain": {"error_message": str(e_cycle)}}

# ==============================================================================
# GUI ДЛЯ ДИАЛОГА С SRK (исправлен ввод/копирование)
# ==============================================================================
class SRISChatApp:
    def __init__(self, root_tk):
        self.root = root_tk
        self.root.title("SRK - Диалоговый агент")
        self.root.geometry("700x550")

        self.bg_color, self.text_color, self.entry_bg = "#282c34", "#abb2bf", "#1e2228"
        self.button_bg, self.button_fg = "#61afef", "#282c34"
        self.sris_color, self.user_color, self.system_color = "#98c379", "#61afef", "#c678dd"
        self.root.configure(bg=self.bg_color)

        self.chat_history = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=NORMAL, bg=self.entry_bg, fg=self.text_color,
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

        self.add_message_to_chat("System", "Инициализация SRK...")

        self.user_input_entry.config(state=DISABLED)
        self.send_button.config(state=DISABLED)

        init_thread = threading.Thread(target=initialize_srk_backend, args=(self,), daemon=True)
        init_thread.start()

    def _prevent_chat_edit(self, event):
        is_copy_combo = (event.state & 4 and event.keysym.lower() == 'c')
        is_select_all_combo = (event.state & 4 and event.keysym.lower() == 'a')
        if platform.system() == "Darwin":
            is_copy_combo = (event.state & 8 and event.keysym.lower() == 'c')
            is_select_all_combo = (event.state & 8 and event.keysym.lower() == 'a')
        if is_copy_combo or is_select_all_combo:
            return
        if len(event.char) > 0 and event.char.isprintable() and not (event.state & 4 or event.state & 8):
            return "break"
        return

    def _make_context_menu(self, widget):
        menu = Menu(widget, tearoff=0, bg=self.entry_bg, fg=self.text_color,
                    activebackground=self.button_bg, activeforeground=self.button_fg,
                    relief=tk.FLAT, font=("Arial", 9))
        def _copy():
            try:
                selection = widget.selection_get()
                self.root.clipboard_clear(); self.root.clipboard_append(selection)
            except tk.TclError:
                pass
        def _cut():
            try:
                selection = widget.selection_get()
                self.root.clipboard_clear(); self.root.clipboard_append(selection)
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
        def _paste():
            try:
                widget.insert(widget.index(tk.INSERT), self.root.clipboard_get())
            except tk.TclError:
                pass
        def _sel_all():
            if isinstance(widget, (tk.Text, scrolledtext.ScrolledText)):
                widget.tag_add(tk.SEL, "1.0", tk.END); widget.mark_set(tk.INSERT, "1.0"); widget.see(tk.INSERT)
            elif isinstance(widget, tk.Entry):
                widget.select_range(0, tk.END); widget.icursor(tk.END)
        if isinstance(widget, (tk.Text, scrolledtext.ScrolledText, tk.Entry)):
            menu.add_command(label="Копировать", command=_copy)
        if isinstance(widget, tk.Entry):
            menu.add_command(label="Вырезать", command=_cut)
            menu.add_command(label="Вставить", command=_paste)
        if isinstance(widget, (tk.Text, scrolledtext.ScrolledText, tk.Entry)):
            menu.add_separator(); menu.add_command(label="Выделить все", command=_sel_all)
        popup_event = "<Button-3>" if platform.system() != "Darwin" else "<Button-2>"
        widget.bind(popup_event, lambda event, m=menu: m.tk_popup(event.x_root, event.y_root))

    def _bind_keyboard_shortcuts(self):
        copy_accel = 'Control-c'; paste_accel = 'Control-v'; cut_accel = 'Control-x'; select_all_accel = 'Control-a'
        if platform.system() == 'Darwin':
            copy_accel = 'Command-c'; paste_accel = 'Command-v'; cut_accel = 'Command-x'; select_all_accel = 'Command-a'
        self.user_input_entry.bind(f"<{paste_accel}>", lambda e: None)
        self.user_input_entry.bind(f"<{copy_accel}>", lambda e: None)
        self.user_input_entry.bind(f"<{cut_accel}>", lambda e: None)
        self.user_input_entry.bind(f"<{select_all_accel}>", lambda e: None)
        self.chat_history.bind(f"<{copy_accel}>", lambda e: None)
        self.chat_history.bind(f"<{select_all_accel}>", lambda e: None)

    def add_message_to_chat(self, sender: str, message: str, is_sris: bool = False, is_system: bool = False):
        self.chat_history.config(state=NORMAL)
        sender_tag = "user"
        if is_sris: sender_tag = "sris"
        elif is_system: sender_tag = "system"
        self.chat_history.insert(tk.END, f"{sender}: ", (sender_tag,))
        self.chat_history.insert(tk.END, f"{message}\n\n")
        self.chat_history.see(tk.END)
        # оставляем включённым для копирования; блокируем только при обновлениях

    def process_srk_cycle_in_thread(self, user_text: str):
        self.add_message_to_chat("SRK", "*обрабатываю ваш запрос...*", is_sris=True, is_system=True)
        self.user_input_entry.config(state=DISABLED)
        self.send_button.config(state=DISABLED)
        input_dict = {"text": user_text, "audio": None, "vision": None}

        result = run_srk_cycle(input_dict)

        def update_gui_with_response():
            # Удаляем сообщение-заглушку
            self.chat_history.config(state=NORMAL)
            # (простое решение — не искать и не удалять, а просто добавить ответ ниже)
            if result and result.get("status") == "ok":
                reply = generate_sris_response(result["full_reasoning_chain"]) or "(пустой ответ)"
                self.add_message_to_chat("SRK", reply, is_sris=True)
            elif result:
                err = result.get("full_reasoning_chain", {}).get("error_message", "неизвестная ошибка")
                self.add_message_to_chat("SRK", f"[Ошибка] {err}", is_sris=True, is_system=True)
            else:
                self.add_message_to_chat("SRK", "Произошла неожиданная внутренняя ошибка.", is_sris=True, is_system=True)

            self.user_input_entry.config(state=NORMAL)
            self.send_button.config(state=NORMAL)
            self.user_input_entry.focus_set()
        self.root.after(0, update_gui_with_response)

    def enable_input(self):
        self.user_input_entry.config(state=NORMAL)
        self.send_button.config(state=NORMAL)
        self.user_input_entry.focus_set()

    def send_message_event(self, event=None):
        user_text = self.user_input_entry.get().strip()
        if not user_text:
            return
        self.add_message_to_chat("Вы", user_text)
        self.user_input_entry.delete(0, tk.END)
        thread = threading.Thread(target=self.process_srk_cycle_in_thread, args=(user_text,))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    print("--- SRK Kernel с GUI ---")
    main_window = tk.Tk()
    app = SRISChatApp(main_window)
    main_window.mainloop()
    print("\n--- Программа SRK завершена ---")
