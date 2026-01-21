import random
from core.logging import logger, LogLevel


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

        # [LOG] Старт фазы
        logger.log(f"🎲 Rolling Speed Dice for {self.name}", LogLevel.VERBOSE, "System")

        # Проверка на смерть теперь через общий метод
        if self.is_dead():
            logger.log(f"{self.name} is dead, skipping roll.", LogLevel.VERBOSE, "System")
            return

        slot_penalty = self.get_status("slot_lock")
        if slot_penalty > 0:
            logger.log(f"{self.name} has slot penalty: -{slot_penalty}", LogLevel.NORMAL, "Status")

        total_potential_slots = len(self.computed_speed_dice)

        slots_to_roll = max(1, total_potential_slots - slot_penalty)

        speed_modifier = 0
        active_mechanics = list(self._iter_all_mechanics())

        for effect in active_mechanics:
            if hasattr(effect, "get_speed_dice_value_modifier"):
                speed_modifier += effect.get_speed_dice_value_modifier(self)

        speed_rolls = []
        for i, (d_min, d_max) in enumerate(self.computed_speed_dice):
            if i >= slots_to_roll: break  # Пропускаем заблокированные слоты

            val = max(1, random.randint(int(d_min), int(d_max)) + speed_modifier)
            self.active_slots.append({
                'speed': val, 'card': None, 'target_slot': None, 'is_aggro': False
            })
            speed_rolls.append(val)

        extra_dice_count = 0

        # А. Сбор бонусов к количеству кубиков
        for effect in active_mechanics:
            if hasattr(effect, "get_speed_dice_bonus"):
                bonus = effect.get_speed_dice_bonus(self)
                if bonus > 0:
                    extra_dice_count += bonus
                    # [LOG] Логируем источник бонуса
                    logger.log(f"Extra Speed Die from {getattr(effect, 'id', 'Unknown')}", LogLevel.NORMAL, "Effect")

        # Б. Добавление бонусных кубиков
        if extra_dice_count > 0:
            if self.computed_speed_dice:
                d_min, d_max = self.computed_speed_dice[0]
            else:
                d_min, d_max = self.base_speed_min, self.base_speed_max

            for _ in range(extra_dice_count):
                # [FIX] Используем тот же модификатор
                val = max(1, random.randint(d_min, d_max) + speed_modifier)
                self.active_slots.append({
                    'speed': val, 'card': None, 'target_slot': None,
                    'is_aggro': False, 'source_effect': 'Bonus 🌟'
                })
                speed_rolls.append(f"{val} (Bonus)")

        # [LOG] Итоговые роллы
        logger.log(f"{self.name} speed rolls: {speed_rolls} (Mod: {speed_modifier})", LogLevel.NORMAL, "Speed")

        for slot in self.active_slots:
            for effect in active_mechanics:
                if hasattr(effect, "modify_active_slot"):
                    effect.modify_active_slot(self, slot)

    def is_staggered(self) -> bool:
        if self.current_stagger > 0:
            return False

        # Проверяем иммунитет к оглушению
        for effect in self._iter_all_mechanics():
            attr = getattr(effect, "prevents_stagger", None)
            if callable(attr):
                if attr(self):
                    # [LOG] Важная информация о спасении
                    logger.log(f"{self.name} stagger prevented by {getattr(effect, 'id', 'Effect')}", LogLevel.NORMAL,
                               "Immunity")
                    return False
            elif attr:
                logger.log(f"{self.name} stagger prevented by {getattr(effect, 'id', 'Effect')}", LogLevel.NORMAL,
                           "Immunity")
                return False

        return True

    def is_dead(self) -> bool:
        """Проверяет, мертв ли юнит, учитывая бессмертие."""
        if self.current_hp > 0:
            return False

        # Проверяем иммунитет к смерти
        for effect in self._iter_all_mechanics():
            attr = getattr(effect, "prevents_death", None)
            if callable(attr):
                if attr(self):
                    # [LOG] Спасение от смерти
                    logger.log(f"{self.name} death prevented by {getattr(effect, 'id', 'Effect')}", LogLevel.NORMAL,
                               "Immunity")
                    return False
            elif attr:
                logger.log(f"{self.name} death prevented by {getattr(effect, 'id', 'Effect')}", LogLevel.NORMAL,
                           "Immunity")
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
        old_cds_len = len(self.cooldowns) + len(self.active_buffs)

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
                new_timers = [t - 1 for t in timers if t > 1]

                if new_timers:
                    new_card_cds[cid] = new_timers

        self.card_cooldowns = new_card_cds
        # =================================================

        if self.is_dead():
            self.active_buffs.clear()
            self.card_cooldowns.clear()
            logger.log(f"{self.name} died, Cooldowns/Buffs cleared.", LogLevel.NORMAL, "System")

        # [LOG] Пишем в Verbose, чтобы не спамить каждый ход, если ничего не изменилось
        # (Или можно добавить проверку, если что-то изменилось)
        logger.log(f"{self.name} cooldowns ticked.", LogLevel.VERBOSE, "System")