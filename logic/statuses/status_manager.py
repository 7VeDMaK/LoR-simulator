# logic/statuses/status_manager.py
from typing import List
from core.unit.unit import Unit
from logic.statuses.status_definitions import STATUS_REGISTRY


class StatusManager:
    @staticmethod
    def process_turn_end(unit: 'Unit') -> List[str]:
        """
        Управляет жизненным циклом статусов: снижение длительности, удаление истекших,
        обработка очереди Delayed.
        ВНИМАНИЕ: Сам эффект on_round_end теперь вызывается через unit.trigger_mechanics!
        """
        logs = []

        active_ids = list(unit._status_effects.keys())

        for status_id in active_ids:
            if status_id not in unit._status_effects: continue

            # --- ЛОГИКА ЭФФЕКТОВ ПЕРЕНЕСЕНА В TRIGGER_MECHANICS ---
            # Здесь мы только управляем длительностью (Duration)

            # 1. Уменьшаем Duration
            current_instances = unit._status_effects[status_id]
            next_instances = []

            for item in current_instances:
                item["duration"] -= 1
                if item["duration"] > 0:
                    next_instances.append(item)

            # 2. Обновляем или удаляем
            if next_instances:
                unit._status_effects[status_id] = next_instances
            else:
                del unit._status_effects[status_id]

        # Обработка Delayed (без изменений)
        if unit.delayed_queue:
            remaining = []
            for item in unit.delayed_queue:
                item["delay"] -= 1
                if item["delay"] <= 0:
                    unit.add_status(item["name"], item["amount"], duration=item["duration"])
                    logs.append(f"⏰ {item['name'].capitalize()} activated!")
                else:
                    remaining.append(item)
            unit.delayed_queue = remaining

        return logs