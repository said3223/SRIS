# temporality_core.py
import logging
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timezone # <--- ВОТ ЭТА СТРОКА ДОБАВЛЕНА

# Настройка логгера для этого модуля
logger = logging.getLogger(__name__)
if not logger.handlers:
    pass # Предполагаем, что логирование настроено в sris_kernel.py

class TimeSense:
    # ... (остальной код класса TimeSense без изменений) ...
    def __init__(self):
        self.current_tick: int = 0
        self.event_last_tick: Dict[str, int] = {}
        logger.info("TimeSense initialized at tick 0.")

    def tick(self) -> int:
        self.current_tick += 1
        return self.current_tick

    def mark_event(self, event_id: str, specific_tick: Optional[int] = None):
        tick_to_mark = specific_tick if specific_tick is not None else self.current_tick
        self.event_last_tick[event_id] = tick_to_mark
        logger.info(f"TimeSense: Event '{event_id}' marked at tick {tick_to_mark}.")

    def get_time_since_event(self, event_id: str) -> Optional[int]:
        last_tick = self.event_last_tick.get(event_id)
        if last_tick is not None:
            return self.current_tick - last_tick
        logger.warning(f"TimeSense: Event ID '{event_id}' not found in event_last_tick history. Cannot calculate time since.")
        return None

    def get_current_tick(self) -> int:
        return self.current_tick


class ReasoningTimeline:
    # ... (код конструктора __init__ без изменений) ...
    def __init__(self, timesense_instance: TimeSense):
        self.events: List[Dict[str, Any]] = [] 
        self.timesense = timesense_instance
        logger.info("ReasoningTimeline initialized.")

    def record_event(self, 
                     event_type: str, 
                     event_data: Dict[str, Any], 
                     reasoning_chain_id: Optional[str] = None,
                     related_to_tick: Optional[int] = None):
        current_event_tick = self.timesense.get_current_tick()
        record = {
            "tick": current_event_tick,
            # Вот здесь используется datetime и timezone, которые мы теперь импортировали
            "timestamp_utc": datetime.now(timezone.utc).isoformat(), 
            "reasoning_chain_id": reasoning_chain_id,
            "event_type": event_type,
            "data": event_data
        }
        if related_to_tick is not None:
            record["related_tick"] = related_to_tick
            
        self.events.append(record)
        logger.info(f"Timeline: Recorded event '{event_type}' at SRIS Tick {current_event_tick} (Chain ID: {reasoning_chain_id}).")
    
    # ... (остальной код класса ReasoningTimeline без изменений) ...
    def get_recent_events(self, n: int = 10) -> List[Dict[str, Any]]:
        return self.events[-n:]

    def get_events_for_chain(self, reasoning_chain_id: str) -> List[Dict[str, Any]]:
        return [event for event in self.events if event.get("reasoning_chain_id") == reasoning_chain_id]

    def get_events_by_type(self, event_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        filtered_events = [event for event in reversed(self.events) if event.get("event_type") == event_type]
        if limit:
            return filtered_events[:limit] 
        return list(reversed(filtered_events))
