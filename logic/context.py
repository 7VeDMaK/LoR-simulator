from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from core.dice import Dice
from core.unit.unit import Unit


@dataclass
class RollContext:
    """
    Контекст броска кубика.
    """
    source: 'Unit'
    target: Optional['Unit']
    dice: Optional['Dice']
    final_value: int

    # --- [NEW] Базовое значение броска (чистый рандом) ---
    base_value: int = 0

    # Старый лог (для текстовых сообщений, не связанных с математикой броска)
    log: List[str] = field(default_factory=list)

    # === НОВЫЙ СПИСОК МОДИФИКАТОРОВ ===
    # Хранит кортежи (значение, причина), например: (5, "Сила")
    modifiers_list: List[Tuple[int, str]] = field(default_factory=list)

    # === НОВЫЕ ПОЛЯ ДЛЯ КРИТОВ ===
    damage_multiplier: float = 1.0
    is_critical: bool = False
    is_disadvantage: bool = False

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
            parts.append(f"{sign} {abs(amount)} ({reason})")

        formula = " ".join(parts)

        # Добавляем информацию о диапазоне кубика
        range_info = f"[{self.dice.min_val}-{self.dice.max_val}]"

        return f"🎲 Roll {range_info}: {formula} = **{self.final_value}**"