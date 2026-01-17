import random
from core.enums import DiceType


# Импорты реестров делаем внутри методов или в начале, если нет циклических зависимостей.
# Для надежности оставим динамический импорт в методе-генераторе.

class UnitCombatMixin:
    """
    Боевая логика: броски инициативы, проверки состояния, кулдауны.
    """

    def _iter_all_mechanics(self):
        """
        Генератор, который перебирает все активные источники механик:
        Таланты, Пассивки, Аугментации и Статусы.
        Позволяет избавиться от дублирования циклов.
        """
        from logic.character_changing.talents import TALENT_REGISTRY
        from logic.character_changing.passives import PASSIVE_REGISTRY
        from logic.character_changing.augmentations.augmentations import AUGMENTATION_REGISTRY
        from logic.statuses.status_manager import STATUS_REGISTRY

        # 1. Таланты
        if hasattr(self, "talents"):
            for tid in self.talents:
                if tid in TALENT_REGISTRY: yield TALENT_REGISTRY[tid]

        # 2. Пассивки
        if hasattr(self, "passives"):
            for pid in self.passives:
                if pid in PASSIVE_REGISTRY: yield PASSIVE_REGISTRY[pid]

        # 3. Аугментации
        if hasattr(self, "augmentations"):
            for aid in self.augmentations:
                if aid in AUGMENTATION_REGISTRY: yield AUGMENTATION_REGISTRY[aid]

        # 4. Статусы (для Red Lycoris и подобных)
        # Проходимся по активным статусам юнита
        if hasattr(self, "statuses"):
            for status_id, stack in self.statuses.items():
                if status_id in STATUS_REGISTRY:
                    yield STATUS_REGISTRY[status_id]

    def roll_speed_dice(self):
        """Генерация активных слотов на раунд."""
        self.active_slots = []
        self.counter_dice = []

        # Проверка на смерть теперь через общий метод
        if self.is_dead():
            return

        slot_penalty = self.get_status("slot_lock")

        total_potential_slots = len(self.computed_speed_dice)

        # Вычитаем штраф (минимум 1 кубик всегда остается, если не стан)
        # Если хотите, чтобы можно было оставить 0 кубиков (полный стан), уберите max(1, ...)
        slots_to_roll = max(1, total_potential_slots - slot_penalty)
        # ===============================================

        # 1. Основные кубики (с учетом штрафа)
        for i, (d_min, d_max) in enumerate(self.computed_speed_dice):
            if i >= slots_to_roll: break  # Пропускаем заблокированные слоты

            mod = self.get_status("haste") - self.get_status("slow") - self.get_status("bind")
            val = max(1, random.randint(int(d_min), int(d_max)) + mod)
            self.active_slots.append({
                'speed': val, 'card': None, 'target_slot': None, 'is_aggro': False
            })

        # 2. Бонусные слоты и Модификация слотов (Все в одном цикле!)
        extra_dice_count = 0

        # Перебираем все механики ОДИН раз
        active_mechanics = list(self._iter_all_mechanics())

        # А. Сбор бонусов к количеству кубиков
        for effect in active_mechanics:
            if hasattr(effect, "get_speed_dice_bonus"):
                extra_dice_count += effect.get_speed_dice_bonus(self)

        # Б. Добавление бонусных кубиков
        if extra_dice_count > 0:
            if self.computed_speed_dice:
                d_min, d_max = self.computed_speed_dice[0]
            else:
                d_min, d_max = self.base_speed_min, self.base_speed_max

            mod = self.get_status("haste") - self.get_status("slow") - self.get_status("bind")

            for _ in range(extra_dice_count):
                val = max(1, random.randint(d_min, d_max) + mod)
                self.active_slots.append({
                    'speed': val, 'card': None, 'target_slot': None,
                    'is_aggro': False, 'source_effect': 'Bonus 🌟'
                })

        # 3. Модификация слотов (Замена хардкода Red Lycoris)
        # Эффекты могут менять свойства слотов (prevent_redirection и т.д.)
        for slot in self.active_slots:
            for effect in active_mechanics:
                if hasattr(effect, "modify_active_slot"):
                    effect.modify_active_slot(self, slot)

    def is_staggered(self) -> bool:
        if self.current_stagger > 0:
            return False

            # Проверяем иммунитет к оглушению
        for effect in self._iter_all_mechanics():
            # [FIX] Теперь корректно вызываем метод, г8если это метод, или проверяем флаг
            attr = getattr(effect, "prevents_stagger", None)
            if callable(attr):
                if attr(self): return False
            elif attr:
                return False

        return True

    def is_dead(self) -> bool:
        """Проверяет, мертв ли юнит, учитывая бессмертие."""
        if self.current_hp > 0:
            return False

            # Проверяем иммунитет к смерти
        for effect in self._iter_all_mechanics():
            # [FIX] Аналогичное исправление для смерти
            attr = getattr(effect, "prevents_death", None)
            if callable(attr):
                if attr(self): return False
            elif attr:
                return False

        return True

    def is_immune_to_surprise_attack(self) -> bool:
        """Проверяет, имеет ли юнит иммунитет к внезапным атакам."""
        for effect in self._iter_all_mechanics():
            attr = getattr(effect, "prevents_surprise_attack", None)
            if callable(attr):
                if attr(self): return True
            elif attr:
                return True
        return False

    def tick_cooldowns(self):
        # Удаляем истекшие кулдауны способностей (обычные словари)
        self.cooldowns = {k: v - 1 for k, v in self.cooldowns.items() if v > 1}
        self.active_buffs = {k: v - 1 for k, v in self.active_buffs.items() if v > 1}

        # === [FIX] ОБНОВЛЕННАЯ ЛОГИКА ДЛЯ СПИСКОВ КАРТ ===
        new_card_cds = {}
        if hasattr(self, 'card_cooldowns') and self.card_cooldowns:
            for cid, timers in self.card_cooldowns.items():
                # Если вдруг пришел int (старый формат), превращаем в список
                if isinstance(timers, int):
                    timers = [timers]

                # Уменьшаем каждый таймер на 1, оставляем только те, что > 1
                # (Если таймер стал 1, то в начале след раунда он станет 0, значит карта готова)
                new_timers = [t - 1 for t in timers if t > 1]

                if new_timers:
                    new_card_cds[cid] = new_timers

        self.card_cooldowns = new_card_cds
        # =================================================

        if self.is_dead():
            self.active_buffs.clear()
            self.card_cooldowns.clear()