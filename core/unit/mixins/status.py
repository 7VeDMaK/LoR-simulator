from typing import Dict, TYPE_CHECKING

import streamlit as st

from core.logging import logger, LogLevel

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

        if hasattr(self, "iter_mechanics"):
            for mech in self.iter_mechanics():
                if hasattr(mech, "on_before_status_add"):
                    res = mech.on_before_status_add(self, name, amount)

                    # Обработка результата (bool или tuple)
                    if isinstance(res, tuple):
                        allowed, msg = res
                    else:
                        allowed, msg = res, None

                    if not allowed:
                        # Логируем блокировку (VERBOSE)
                        logger.log(f"🚫 {self.name}: Status {name} blocked ({msg})", LogLevel.VERBOSE, "Status")
                        return False, msg
        # =========================================================================

        if delay > 0:
            self.delayed_queue.append({
                "name": name, "amount": amount, "duration": duration, "delay": delay
            })
            logger.log(f"⏰ {self.name}: {name} delayed for {delay} turns", LogLevel.NORMAL, "Status")
            return True, "Delayed"

        if name not in self._status_effects:
            self._status_effects[name] = []

        POOL_STATUSES = ["smoke", "charge", "satiety", "tremor", "self_control", "poise", "adaptation", "exhaustion"]

        if name in POOL_STATUSES and self._status_effects[name]:
            # Если статус уже есть, просто увеличиваем количество в первом слоте
            self._status_effects[name][0]["amount"] += amount
            # Обновляем длительность (берем максимум)
            self._status_effects[name][0]["duration"] = max(self._status_effects[name][0]["duration"], duration)
        else:
            # Обычное поведение: добавляем новый отдельный стак
            self._status_effects[name].append({"amount": amount, "duration": duration})

        # Логируем наложение (NORMAL)
        logger.log(f"🧪 {self.name}: +{amount} {name} ({duration}t)", LogLevel.NORMAL, "Status")

        # === [ОПТИМИЗАЦИЯ] 2. ХУК: on_status_applied ===
        if trigger_events:
            # A. ЛОКАЛЬНЫЙ ХУК (Для самого себя)
            if hasattr(self, "trigger_mechanics"):
                self.trigger_mechanics("on_status_applied", self, name, amount, duration=duration)

            # B. [NEW] ГЛОБАЛЬНЫЙ ХУК (Для наблюдателей, например Аксис)
            # Мы оповещаем всех остальных юнитов в бою, что на 'self' наложился статус
            try:
                # Получаем списки команд из сессии (безопасный доступ)
                team_l = st.session_state.get('team_left', [])
                team_r = st.session_state.get('team_right', [])
                all_units = team_l + team_r

                for observer in all_units:
                    # Пропускаем себя (локальный хук уже сработал) и мертвых
                    if observer is self or observer.is_dead():
                        continue

                    if hasattr(observer, "trigger_mechanics"):
                        # Вызываем событие у наблюдателя
                        # Аргументы: (unit=observer, target=self, status_id=name, ...)
                        observer.trigger_mechanics(
                            "on_status_applied_global",
                            observer,
                            target=self,
                            status_id=name,
                            amount=amount,
                            duration=duration
                        )
            except Exception as e:
                # Заглушка на случай ошибок доступа к session_state вне контекста
                pass
        # ==============================================

        return True, None

    def get_status(self, name: str) -> int:
        self._ensure_status_storage()
        if name not in self._status_effects: return 0
        return sum(i["amount"] for i in self._status_effects[name])

    def remove_status(self, name: str, amount: int = None):
        self._ensure_status_storage()
        if name not in self._status_effects: return

        current_val = self.get_status(name)

        if amount is None:
            del self._status_effects[name]
            logger.log(f"🧹 {self.name}: Cleared all {name} ({current_val})", LogLevel.NORMAL, "Status")
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

        # Логируем фактическое снятие
        removed = current_val - self.get_status(name)
        if removed > 0:
            logger.log(f"🧹 {self.name}: Removed {removed} {name}", LogLevel.NORMAL, "Status")

            if hasattr(self, "trigger_mechanics"):
                self.trigger_mechanics("on_status_removed", self, name, removed)