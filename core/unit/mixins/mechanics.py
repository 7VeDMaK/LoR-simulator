from core.logging import logger, LogLevel
from logic.statuses.status_definitions import STATUS_REGISTRY


class MechanicsIteratorMixin:  # <--- Имя класса должно совпадать с импортом в unit.py
    """
    Миксин, предоставляющий единый интерфейс для доступа ко всем
    источникам механик (Пассивки, Таланты, Аугментации, Статусы, Оружие).
    """

    @property
    def mechanics(self):
        """Возвращает список всех активных механик юнита."""
        return list(self._iter_all_mechanics())

    def _iter_all_mechanics(self):  # <--- Переименовано для совместимости с checks.py
        """
        Генератор, возвращающий все активные объекты эффектов на юните.
        Порядок: Статусы -> Пассивки -> Таланты -> Аугментации -> Оружие.
        """
        # Локальные импорты для предотвращения циклической зависимости
        from logic.character_changing.passives import PASSIVE_REGISTRY
        from logic.character_changing.talents import TALENT_REGISTRY
        from logic.character_changing.augmentations.augmentations import AUGMENTATION_REGISTRY
        from logic.weapon_definitions import WEAPON_REGISTRY

        # 1. Статусы (У них приоритет, т.к. они часто меняют логику статов)
        if hasattr(self, "statuses"):
            for status_id, stack in self.statuses.items():
                if status_id in STATUS_REGISTRY:
                    yield STATUS_REGISTRY[status_id]

        # 2. Пассивки
        if hasattr(self, "passives"):
            for pid in self.passives:
                if pid in PASSIVE_REGISTRY: yield PASSIVE_REGISTRY[pid]

        # 3. Таланты
        if hasattr(self, "talents"):
            for tid in self.talents:
                if tid in TALENT_REGISTRY: yield TALENT_REGISTRY[tid]

        # 4. Аугментации
        if hasattr(self, "augmentations"):
            for aid in self.augmentations:
                if aid in AUGMENTATION_REGISTRY: yield AUGMENTATION_REGISTRY[aid]

        # 5. Пассивка оружия
        if hasattr(self, "weapon_id") and self.weapon_id in WEAPON_REGISTRY:
            wep = WEAPON_REGISTRY[self.weapon_id]
            if wep.passive_id and wep.passive_id in PASSIVE_REGISTRY:
                yield PASSIVE_REGISTRY[wep.passive_id]

    def trigger_mechanics(self, method_name, *args, **kwargs):
        """
        Запускает метод method_name у всех механик, если он существует.
        Пример: unit.trigger_mechanics("on_combat_start", unit, log_func)
        """
        from logic.character_changing.passives import PASSIVE_REGISTRY
        from logic.character_changing.talents import TALENT_REGISTRY
        from logic.character_changing.augmentations.augmentations import AUGMENTATION_REGISTRY
        from logic.weapon_definitions import WEAPON_REGISTRY

        # === 1. СТАТУСЫ (Передаем stack) ===
        if hasattr(self, "statuses"):
            for status_id, stack in self.statuses.items():
                if status_id in STATUS_REGISTRY:
                    mech = STATUS_REGISTRY[status_id]
                    if hasattr(mech, method_name):
                        getattr(mech, method_name)(*args, stack=stack, **kwargs)

        # === 2. ОСТАЛЬНЫЕ МЕХАНИКИ (Без stack) ===
        other_mechanics = []

        # Пассивки
        if hasattr(self, "passives"):
            for pid in self.passives:
                if pid in PASSIVE_REGISTRY: other_mechanics.append(PASSIVE_REGISTRY[pid])

        # Таланты
        if hasattr(self, "talents"):
            for tid in self.talents:
                if tid in TALENT_REGISTRY: other_mechanics.append(TALENT_REGISTRY[tid])

        # Аугментации
        if hasattr(self, "augmentations"):
            for aid in self.augmentations:
                if aid in AUGMENTATION_REGISTRY: other_mechanics.append(AUGMENTATION_REGISTRY[aid])

        # Оружие
        if hasattr(self, "weapon_id") and self.weapon_id in WEAPON_REGISTRY:
            wep = WEAPON_REGISTRY[self.weapon_id]
            if wep.passive_id and wep.passive_id in PASSIVE_REGISTRY:
                other_mechanics.append(PASSIVE_REGISTRY[wep.passive_id])

        # Запуск для остальных
        for mech in other_mechanics:
            if hasattr(mech, method_name):
                getattr(mech, method_name)(*args, **kwargs)

    def apply_mechanics_filter(self, method_name, initial_value, *args, **kwargs):
        """
        Прогоняет значение через цепочку модификаторов.
        Пример: damage = unit.apply_mechanics_filter("modify_incoming_damage", damage, dmg_type)
        """
        value = initial_value

        # Используем переименованный метод _iter_all_mechanics
        for mech in self._iter_all_mechanics():
            if hasattr(mech, method_name):
                old_val = value

                # Примечание: тут мы не передаем stack явно, так как генератор не возвращает stack.
                # Но статусы в своих методах (например, modify_incoming_damage) обычно делают:
                # if stack == 0: stack = unit.get_status(self.id)
                # Так что это будет работать корректно.

                value = getattr(mech, method_name)(self, value, *args, **kwargs)

                # Логируем, если значение изменилось
                if value != old_val:
                    mech_id = getattr(mech, 'id', 'Unknown')
                    logger.log(f"Filter change by {mech_id}: {old_val} -> {value}", LogLevel.VERBOSE, "Filter")

        return value

    def trigger_hooks(self, hook_name: str, **kwargs):
        """
        Вызывает метод hook_name у всех активных механик.
        Пример: unit.trigger_hooks('on_luck_check', result=15)
        """
        for mechanic in self._iter_all_mechanics():
            # Проверяем, есть ли у механики нужный метод (например, on_luck_check)
            hook_method = getattr(mechanic, hook_name, None)

            if callable(hook_method):
                try:
                    # Вызываем метод, передавая self (юнита) первым аргументом
                    hook_method(self, **kwargs)
                except Exception as e:
                    logger.log(f"Error in hook '{hook_name}' for {mechanic.id}: {e}", LogLevel.ERROR, "System")