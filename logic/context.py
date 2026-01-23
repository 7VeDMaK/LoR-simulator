from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from core.dice import Dice
from core.unit.unit import Unit
from core.enums import DiceType
from core.logging import logger, LogLevel  # [NEW] Для логов


@dataclass
class RollContext:
    """
    Контекст броска кубика.
    """
    source: 'Unit'
    target: Optional['Unit']
    dice: Optional['Dice']
    final_value: int = 0  # Default 0, так как вычисляется

    # --- [NEW] Базовое значение броска (чистый рандом) ---
    base_value: int = 0

    # Флаг конвертации типа урона (для пассивок типа Банганранга)
    convert_hp_to_sp: bool = False

    # Ссылка на контекст оппонента (заполняется в clash.py)
    opponent_ctx: Optional['RollContext'] = None

    # Старый лог (для текстовых сообщений, не связанных с математикой броска)
    log: List[str] = field(default_factory=list)

    # === НОВЫЙ СПИСОК МОДИФИКАТОРОВ ===
    # Хранит кортежи (значение, причина), например: (5, "Сила")
    modifiers_list: List[Tuple[int, str]] = field(default_factory=list)

    # === НОВЫЕ ПОЛЯ ДЛЯ КРИТОВ И ПРОЧЕГО ===
    damage_multiplier: float = 1.0
    is_critical: bool = False
    is_disadvantage: bool = False

    # =========================================================================
    # ОСНОВНЫЕ МЕТОДЫ БРОСКА
    # =========================================================================

    def roll(self, stack=0):
        """
        Основной метод совершения броска.
        1. Кидает кубик (RNG).
        2. Считает статы и модификаторы.
        3. Вызывает хуки пассивок.
        """
        if self.dice:
            # 1. Чистый рандом
            self.base_value = self.dice.roll()
            self.final_value = self.base_value

        # 2. Расчет силы (Статы + Отключение кубиков)
        self.calculate_power(stack)

        # 3. Хуки после расчета (on_roll), которые могут еще изменить final_value
        self._trigger_on_roll(stack)

        # Гарантируем, что результат не отрицательный (если только это не -9999 от отключения)
        # Но для UI лучше показать 0, если отключено.
        if self.final_value < 0:
            self.final_value = 0

        return self.final_value

    def calculate_power(self, stack=0):
        """
        Применение характеристик и проверка условий отключения кубиков.
        """
        if not self.dice: return

        # --- 1. ПРОВЕРКА ОТКЛЮЧЕНИЯ (Logic moved from formulas.py) ---
        # Проверяем флаги в модификаторах юнита
        disable_block = self.source.modifiers.get("disable_block", {}).get("flat", 0) > 0
        disable_evade = self.source.modifiers.get("disable_evade", {}).get("flat", 0) > 0

        # Если Блок отключен -> Штраф -9999 (чтобы результат стал 0)
        if self.dice.dtype == DiceType.BLOCK and disable_block:
            self.modify_power(-9999, "Block Disabled 🚫")
            logger.log(f"🚫 Block disabled for {self.source.name}", LogLevel.VERBOSE, "Combat")
            return  # Прерываем, статы не добавляем

        # Если Уклонение отключено
        if self.dice.dtype == DiceType.EVADE and disable_evade:
            self.modify_power(-9999, "Evade Disabled 🚫")
            logger.log(f"🚫 Evade disabled for {self.source.name}", LogLevel.VERBOSE, "Combat")
            return

        # --- 2. ДОБАВЛЕНИЕ СТАТОВ (Stats Logic) ---
        stat_bonus = 0
        reason = "Stat"

        if self.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            # Атака -> Сила + Мод. Атаки
            base_str = self.source.stats.get("strength", 0)
            mod_atk = self.source.modifiers.get("power_attack", {}).get("flat", 0)
            stat_bonus = base_str + mod_atk
            reason = "Strength"

        elif self.dice.dtype == DiceType.BLOCK:
            # Блок -> Стойкость + Мод. Блока
            base_end = self.source.stats.get("endurance", 0)
            mod_blk = self.source.modifiers.get("power_block", {}).get("flat", 0)
            stat_bonus = base_end + mod_blk
            reason = "Endurance"

        elif self.dice.dtype == DiceType.EVADE:
            # Уклонение -> Акробатика (Навык) + Мод. Уклонения
            # (Или Ловкость, зависит от вашей системы, здесь берем Акробатику как навык)
            base_acro = self.source.skills.get("acrobatics", 0)
            mod_evd = self.source.modifiers.get("power_evade", {}).get("flat", 0)
            stat_bonus = base_acro + mod_evd
            reason = "Acrobatics"

        if stat_bonus != 0:
            self.modify_power(stat_bonus, reason)

        # --- 3. ГЛОБАЛЬНЫЙ БОНУС (Power All) ---
        power_all = self.source.modifiers.get("power_all", {}).get("flat", 0)
        if power_all != 0:
            self.modify_power(power_all, "Power All")

    def _trigger_on_roll(self, stack):
        """
        Вызов хуков on_roll у всех пассивок, талантов и статусов.
        """
        # 1. Пассивки и Таланты (Active Objects)
        # В `collectors.py` мы должны были собрать активные объекты в список,
        # или перебирать их здесь. Для надежности переберем реестры по ID.

        # Собираем все ID способностей
        all_ability_ids = self.source.passives + self.source.talents

        # Импортируем реестры внутри метода во избежание циклического импорта
        from logic.character_changing.passives import PASSIVE_REGISTRY
        from logic.character_changing.talents import TALENT_REGISTRY

        for pid in all_ability_ids:
            obj = None
            if pid in PASSIVE_REGISTRY:
                obj = PASSIVE_REGISTRY[pid]
            elif pid in TALENT_REGISTRY:
                obj = TALENT_REGISTRY[pid]

            if obj and hasattr(obj, "on_roll"):
                obj.on_roll(self, stack=stack)

        # 2. Статусы
        from logic.statuses.status_manager import STATUS_REGISTRY
        for status_id, amount in self.source.statuses.items():
            if amount > 0 and status_id in STATUS_REGISTRY:
                st_obj = STATUS_REGISTRY[status_id]
                if hasattr(st_obj, "on_roll"):
                    st_obj.on_roll(self, stack=stack)

    # =========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # =========================================================================

    def modify_power(self, amount: int, reason: str):
        """Изменяет значение кубика и сохраняет модификатор."""
        if amount == 0:
            return
        self.final_value += amount
        # Сохраняем в список для красивого вывода
        self.modifiers_list.append((amount, reason))

    def get_formatted_roll_log(self) -> str:
        """Формирует итоговую строку броска: Roll: 5 + 2 (Str) + 1 (Buff) = 8"""
        if not self.dice:
            return f"Value: {self.final_value}"

        parts = [str(self.base_value)]

        for amount, reason in self.modifiers_list:
            sign = "+" if amount >= 0 else "-"
            # Если это огромное число отключения, пишем красиво
            if abs(amount) >= 999:
                parts.append(f"(DISABLED)")
            else:
                parts.append(f"{sign} {abs(amount)} ({reason})")

        formula = " ".join(parts)

        # Добавляем информацию о диапазоне кубика
        range_info = f"[{self.dice.min_val}-{self.dice.max_val}]"

        return f"🎲 Roll {range_info}: {formula} = **{self.final_value}**"