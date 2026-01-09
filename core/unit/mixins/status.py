from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    pass

class UnitStatusMixin:
    def _ensure_status_storage(self):
        if not hasattr(self, "_status_effects"): self._status_effects = {}
        if not hasattr(self, "delayed_queue"): self.delayed_queue = []

    @property
    def statuses(self) -> Dict[str, int]:
        self._ensure_status_storage()
        summary = {}
        for name, instances in self._status_effects.items():
            total = sum(i["amount"] for i in instances)
            if total > 0:
                summary[name] = total
        return summary

    def add_status(self, name: str, amount: int, duration: int = 1, delay: int = 0, trigger_events: bool = True):
        self._ensure_status_storage()
        if amount <= 0: return False, None

        # 1. Проверка через таланты (on_before_status_add)
        from logic.character_changing.talents import TALENT_REGISTRY
        for tid in self.talents:
            if tid in TALENT_REGISTRY:
                if hasattr(TALENT_REGISTRY[tid], "on_before_status_add"):
                    res = TALENT_REGISTRY[tid].on_before_status_add(self, name, amount)
                    if isinstance(res, tuple):
                        allowed, msg = res
                    else:
                        allowed, msg = res, None
                    if not allowed:
                        return False, msg

        # 2. Проверка через пассивки
        from logic.character_changing.passives import PASSIVE_REGISTRY
        for pid in self.passives:
            if pid in PASSIVE_REGISTRY:
                if hasattr(PASSIVE_REGISTRY[pid], "on_before_status_add"):
                    res = PASSIVE_REGISTRY[pid].on_before_status_add(self, name, amount)
                    if isinstance(res, tuple):
                        allowed, msg = res
                    else:
                        allowed, msg = res, None
                    if not allowed:
                        return False, msg

        if delay > 0:
            self.delayed_queue.append({
                "name": name, "amount": amount, "duration": duration, "delay": delay
            })
            return True, "Delayed"

        if name not in self._status_effects:
            self._status_effects[name] = []

        POOL_STATUSES = ["smoke", "charge", "satiety", "tremor", "self_control", "poise", "adaptation"]

        if name in POOL_STATUSES and self._status_effects[name]:
            # Если статус уже есть, просто увеличиваем количество в первом слоте
            # Это предотвращает создание [1, 1, 1, 1...] для дыма
            self._status_effects[name][0]["amount"] += amount
            # Обновляем длительность (берем максимум, для дыма это обычно 99)
            self._status_effects[name][0]["duration"] = max(self._status_effects[name][0]["duration"], duration)
        else:
            # Обычное поведение: добавляем новый отдельный стак (нужно для Силы/Стойкости с разной длительностью)
            self._status_effects[name].append({"amount": amount, "duration": duration})
        # ===================================================
        # === ХУК: on_status_applied ===
        if trigger_events:
            for tid in self.talents:
                if tid in TALENT_REGISTRY and hasattr(TALENT_REGISTRY[tid], "on_status_applied"):
                    TALENT_REGISTRY[tid].on_status_applied(self, name, amount, duration=duration)

            for pid in self.passives:
                if pid in PASSIVE_REGISTRY and hasattr(PASSIVE_REGISTRY[pid], "on_status_applied"):
                    PASSIVE_REGISTRY[pid].on_status_applied(self, name, amount, duration=duration)

        return True, None

    def get_status(self, name: str) -> int:
        self._ensure_status_storage()
        if name not in self._status_effects: return 0
        return sum(i["amount"] for i in self._status_effects[name])

    def remove_status(self, name: str, amount: int = None):
        self._ensure_status_storage()
        if name not in self._status_effects: return

        if amount is None:
            del self._status_effects[name]
            return

        items = sorted(self._status_effects[name], key=lambda x: x["duration"])
        rem = amount
        new_items = []

        for item in items:
            if rem <= 0:
                new_items.append(item)
                continue
            if item["amount"] > rem:
                item["amount"] -= rem
                rem = 0
                new_items.append(item)
            else:
                rem -= item["amount"]

        if not new_items:
            del self._status_effects[name]
        else:
            self._status_effects[name] = new_items