import random
from typing import Dict, Any

from core.logging import logger, LogLevel  # [LOG] Импорт логгера
from core.unit.unit import Unit


class CheckSystem:
    # Таблицы сложности (порог, описание)
    # Сортируем в обратном порядке для упрощения поиска (от большего к меньшему)
    DIFFICULTY_STD = [
        (21, "Невозможно для человека"), (17, "Нечеловеческий уровень"),
        (13, "Тяжело (профессионал)"), (9, "Средне (специалист)"),
        (5, "Легко"), (0, "Элементарно")
    ]
    DIFFICULTY_WIS = [
        (45, "Божественный уровень"), (36, "Нечеловеческий уровень"),
        (28, "Специалист"), (20, "Хорошо образованный"),
        (13, "Подстегнутый в сфере"), (7, "Обычный человек"), (0, "Элементарно")
    ]

    # Карта влияния статусов на характеристики: {stat: [(status, sign)]}
    STATUS_MAP = {
        "strength": [("attack_power_up", 1)],
        "endurance": [("endurance", 1)],
        "agility": [("haste", 1), ("bind", -1)],
        "speed": [("haste", 1), ("bind", -1)]
    }

    @staticmethod
    def get_difficulty_desc(value: int, is_wisdom: bool = False) -> str:
        table = CheckSystem.DIFFICULTY_WIS if is_wisdom else CheckSystem.DIFFICULTY_STD
        # Ищем первое значение, которое меньше или равно value
        for threshold, desc in table:
            if value >= threshold: return desc
        return "Неизвестно"

    @staticmethod
    def perform_check(unit: Unit, stat_key: str, difficulty: int = 0) -> Dict[str, Any]:
        key = stat_key.lower()

        # [LOG] Старт проверки
        logger.log(f"🎲 Checking {key} for {unit.name} (DC: {difficulty})...", LogLevel.VERBOSE, "Check")

        # 1. Получаем базовое значение
        # Ищем в modifiers -> attributes -> skills -> 0
        base_val = unit.modifiers.get(f"total_{key}",
                                      unit.attributes.get(key, unit.skills.get(key, 0)))

        # 2. Настройка параметров броска
        is_wis = (key == "wisdom")
        die_max = 20 if is_wis else 6
        bonus_divisor = 1 if is_wis else 3
        dc_mult = 1.3 if key == "engineering" else 1.0

        # 3. Расчеты
        roll = random.randint(1, die_max)
        stat_bonus = base_val // bonus_divisor

        # Расчет бонусов от статусов через карту
        status_bonus = 0
        for status, sign in CheckSystem.STATUS_MAP.get(key, []):
            status_bonus += unit.get_status(status) * sign

        total = roll + stat_bonus + status_bonus
        final_dc = int(difficulty * dc_mult) if difficulty > 0 else 0

        # [LOG] Детали расчета
        logger.log(f"Calc: [{roll}] (Die) + {stat_bonus} (Stat) + {status_bonus} (Buffs) = {total}", LogLevel.VERBOSE,
                   "Check")

        # 4. Формирование результата
        is_success = total >= final_dc if final_dc > 0 else None

        outcome = "RESULT"
        if final_dc > 0:
            outcome = "✅ УСПЕХ" if is_success else "❌ ПРОВАЛ"
            # Криты только для Мудрости (d20)
            if is_wis:
                if roll == 20:
                    outcome = "🌟 КРИТИЧЕСКИЙ УСПЕХ"
                elif roll == 1:
                    outcome = "💀 КРИТИЧЕСКИЙ ПРОВАЛ"

            # [LOG] Итог с DC
            logger.log(f"🎲 Check {key}: {outcome} ({total} vs {final_dc})", LogLevel.NORMAL, "Check")
        else:
            # [LOG] Итог без DC
            desc = CheckSystem.get_difficulty_desc(total, is_wis)
            logger.log(f"🎲 Check {key} Result: {total} ({desc})", LogLevel.NORMAL, "Check")

        formula = f"[{roll}] + {stat_bonus}"
        if status_bonus: formula += f" + {status_bonus} (Buffs)"
        if key == "engineering": formula += " (Engi Penalty)"

        return {
            "type": f"{key.capitalize()} (d{die_max})",
            "die": f"1d{die_max}",
            "roll": roll,
            "stat_val": base_val,
            "bonus": stat_bonus,
            "status_bonus": status_bonus,
            "total": total,
            "success": is_success,
            "dc": final_dc,
            "outcome": outcome,
            "formula": formula,
            "level_desc": CheckSystem.get_difficulty_desc(total, is_wis)
        }