"""
Логика проверок навыков и характеристик (Skill Checks).

Система проверок с тремя точками интеграции механик:
1. on_check_roll - ПЕРЕД броском (advantage/disadvantage)
2. modify_skill_check_result - модификация итогового результата
3. on_skill_check - ПОСЛЕ проверки (триггеры и эффекты)
"""
import random
from core.unit.unit import Unit
from ui.checks.constants import (
    TYPE_10_ATTRS, TYPE_15_SKILLS, TYPE_WISDOM, TYPE_LUCK, TYPE_INTELLECT
)


class CheckContext:
    """Контекст для передачи флагов Advantage/Disadvantage."""
    def __init__(self):
        self.is_advantage = False
        self.is_disadvantage = False


def get_check_params(key: str) -> tuple:
    """Возвращает тип проверки, кубик и описание."""
    if key in ["speed", "medicine"]:
        return "type10", "d6", "Характеристика (1/3)"
    
    if key in TYPE_10_ATTRS:
        return "type10", "d6", "Характеристика (1/3)"
    elif key in TYPE_15_SKILLS:
        return "type15", "d6", "Навык (1 к 1)"
    elif key in TYPE_WISDOM:
        return "typeW", "d20", "Мудрость"
    elif key in TYPE_LUCK:
        return "typeL", "d12", "Удача"
    elif key in TYPE_INTELLECT:
        return "typeI", "d6", "Интеллект"
    
    return "unknown", "d6", "???"


def get_stat_value(unit: Unit, key: str) -> int:
    """Получает значение характеристики/навыка из юнита."""
    if key == "luck":
        return unit.resources.get("luck", 0)

    # Проверяем модификаторы
    val_data = None
    if key in unit.modifiers:
        val_data = unit.modifiers[key]
    elif f"total_{key}" in unit.modifiers:
        val_data = unit.modifiers[f"total_{key}"]
    
    if key == "intellect" and "total_intellect" in unit.modifiers:
        val_data = unit.modifiers["total_intellect"]

    if val_data is not None:
        if isinstance(val_data, dict):
            return int(val_data.get("flat", 0))
        return int(val_data)

    # Проверяем базовые атрибуты и навыки
    if key in unit.attributes:
        return unit.attributes[key]
    if key in unit.skills:
        return unit.skills[key]
    if key == "intellect":
        return unit.base_intellect

    return 0


def calculate_pre_roll_stats(unit, stat_key: str, stat_value: int, difficulty: int, bonus: int) -> tuple:
    """
    Рассчитывает ожидаемый шанс успеха и матожидание результата.
    Используется для отображения информации перед броском.
    УЧИТЫВАЕТ модификаторы от пассивок и талантов для точного прогноза.
    """
    check_type, _, _ = get_check_params(stat_key)

    # Определяем базовые параметры броска
    params = {
        "die_min": 1,
        "die_max": 6,
        "base_bonus": 0,
        "stat_bonus": 0
    }
    
    if check_type == "type10":
        params["die_max"] = 6
        params["stat_bonus"] = stat_value // 3
    elif check_type == "type15":
        params["die_max"] = 6
        params["stat_bonus"] = stat_value
    elif check_type == "typeW":
        params["die_max"] = 20
        params["stat_bonus"] = stat_value
    elif check_type == "typeL":
        params["die_max"] = 12
        params["stat_bonus"] = stat_value
    elif check_type == "typeI":
        params["die_max"] = 6
        params["stat_bonus"] = 4 + int(stat_value)

    # Применяем модификаторы от талантов к параметрам
    if hasattr(unit, "mechanics"):
        for mechanic in unit.mechanics:
            if hasattr(mechanic, "modify_check_parameters"):
                params = mechanic.modify_check_parameters(unit, stat_key.lower(), params)

    # Подсчет шанса успеха
    target_roll = difficulty - params["base_bonus"] - params["stat_bonus"] - bonus
    success_count = 0
    total_faces = params["die_max"] - params["die_min"] + 1

    for roll_value in range(params["die_min"], params["die_max"] + 1):
        # Для d20 и d12: 1 = автопровал, макс = автоуспех
        if check_type in ["typeW", "typeL"]:
            if roll_value == 1:
                continue
            if roll_value == params["die_max"]:
                success_count += 1
                continue
        
        if roll_value >= target_roll:
            success_count += 1

    chance = (success_count / total_faces) * 100.0
    expected_roll = (params["die_min"] + params["die_max"]) / 2
    expected_total = expected_roll + params["base_bonus"] + params["stat_bonus"] + bonus

    # ===== ПРИМЕНЯЕМ МОДИФИКАТОРЫ ОТ ПАССИВОК К МАТОЖИДАНИЮ =====
    if hasattr(unit, "mechanics"):
        for mechanic in unit.mechanics:
            if hasattr(mechanic, "modify_skill_check_result"):
                expected_total = mechanic.modify_skill_check_result(unit, stat_key.lower(), int(expected_total))

    return chance, expected_total, difficulty


def perform_check_logic(unit, stat_key: str, stat_value: int, difficulty: int, bonus: int) -> dict:
    """
    Выполняет проверку навыка/характеристики.
    
    ПОРЯДОК ВЫПОЛНЕНИЯ:
    1. on_check_roll → механики устанавливают advantage/disadvantage
    2. Бросок кубика с учетом adv/dis
    3. Расчет базового результата (бросок + модификатор стата + бонус)
    4. modify_skill_check_result → механики модифицируют итоговый результат
    5. Определение успеха/провала
    6. on_skill_check → триггеры после проверки
    
    Returns:
        dict: результат проверки с полями roll, die, stat_bonus, total, is_success и т.д.
    """
    stat_key = stat_key.lower()
    check_type, die_type, _ = get_check_params(stat_key)

    result = {
        "roll": 0,
        "die": die_type,
        "stat_bonus": 0,
        "total": 0,
        "final_difficulty": difficulty,
        "is_success": False,
        "is_crit": False,
        "is_fumble": False,
        "msg": "",
        "formula_text": ""
    }

    # ===== ТОЧКА 1: on_check_roll =====
    ctx = CheckContext()
    if hasattr(unit, "trigger_mechanics"):
        unit.trigger_mechanics("on_check_roll", unit, attribute=stat_key, context=ctx)

    # Обработка advantage/disadvantage
    is_adv = ctx.is_advantage
    is_dis = ctx.is_disadvantage
    if is_adv and is_dis:  # Взаимопоглощение
        is_adv = is_dis = False

    # ===== ОПРЕДЕЛЕНИЕ БАЗОВЫХ ПАРАМЕТРОВ БРОСКА =====
    # Создаем параметры броска по умолчанию
    params = {
        "die_min": 1,
        "die_max": 6,
        "base_bonus": 0,
        "stat_bonus": 0
    }

    # Устанавливаем параметры в зависимости от типа проверки
    if check_type == "type10":
        params["die_max"] = 6
        params["stat_bonus"] = stat_value // 3
    elif check_type == "type15":
        params["die_max"] = 6
        params["stat_bonus"] = stat_value
    elif check_type == "typeI":
        params["die_max"] = 6
        params["stat_bonus"] = 4 + int(stat_value)
    elif check_type == "typeW":
        params["die_max"] = 20
        params["stat_bonus"] = stat_value
    elif check_type == "typeL":
        params["die_max"] = 12
        params["stat_bonus"] = stat_value

    # ===== ТОЧКА 1.5: modify_check_parameters =====
    # Таланты могут изменить тип кубика и бонусы
    if hasattr(unit, "mechanics"):
        for mechanic in unit.mechanics:
            if hasattr(mechanic, "modify_check_parameters"):
                old_params = params.copy()
                params = mechanic.modify_check_parameters(unit, stat_key, params)
                # Отладка: показываем изменения
                if params != old_params:
                    print(f"[DEBUG] {getattr(mechanic, 'name', 'Unknown')} изменил параметры: {old_params} -> {params}")

    # ===== БРОСОК КУБИКА =====
    def roll_dice(min_val: int, max_val: int) -> tuple:
        """Бросает кубик с учетом advantage/disadvantage."""
        r1 = random.randint(min_val, max_val)
        if not is_adv and not is_dis:
            return r1, ""
        
        r2 = random.randint(min_val, max_val)
        if is_adv:
            return max(r1, r2), f"(Adv: {r1}, {r2})"
        else:
            return min(r1, r2), f"(Dis: {r1}, {r2})"

    # ===== ВЫПОЛНЕНИЕ БРОСКА С УЧЕТОМ ПАРАМЕТРОВ =====
    val, tag = roll_dice(params["die_min"], params["die_max"])
    result["roll"] = val
    
    # Формируем название кубика
    die_name = f"d{params['die_max']}"
    result["die"] = f"{die_name} {tag}" if tag else die_name
    
    # Устанавливаем бонусы
    result["stat_bonus"] = params["stat_bonus"]
    
    # Формируем текст формулы
    formula_parts = []
    
    # Базовый бонус от таланта (если есть)
    if params["base_bonus"] != 0:
        formula_parts.append(f"`{params['base_bonus']} (Талант)`")
    
    # Бонус от характеристики
    if check_type == "type10":
        formula_parts.append(f"`{result['stat_bonus']} (Стат // 3)`")
    elif check_type == "typeI":
        formula_parts.append(f"`{result['stat_bonus']} (4 + Инт)`")
    elif check_type == "type15":
        formula_parts.append(f"`{result['stat_bonus']} (Навык)`")
    elif check_type == "typeW":
        formula_parts.append(f"`{result['stat_bonus']} (Мудр)`")
    elif check_type == "typeL":
        formula_parts.append(f"`{result['stat_bonus']} (Удача)`")
    
    result["formula_text"] = " + ".join(formula_parts) if formula_parts else "`0`"
    
    # Проверка на критические броски (только для d20 и d12)
    if check_type == "typeW" and params["die_max"] == 20:
        if val == 20:
            result["is_crit"] = True
        if val == 1:
            result["is_fumble"] = True
    
    if check_type == "typeL" and params["die_max"] == 12:
        if val == 12:
            result["is_crit"] = True
        if val == 1:
            result["is_fumble"] = True

    # ===== БАЗОВЫЙ РЕЗУЛЬТАТ =====
    result["total"] = val + params["base_bonus"] + result["stat_bonus"] + bonus

    # ===== ТОЧКА 2: modify_skill_check_result =====
    # Отслеживаем модификаторы для отображения пользователю
    modifiers_applied = []
    
    if hasattr(unit, "mechanics"):
        for mechanic in unit.mechanics:
            if hasattr(mechanic, "modify_skill_check_result"):
                old_total = result["total"]
                result["total"] = mechanic.modify_skill_check_result(unit, stat_key, result["total"])
                
                # Записываем изменение, если оно произошло
                if result["total"] != old_total:
                    diff = result["total"] - old_total
                    mechanic_name = getattr(mechanic, "name", getattr(mechanic, "id", "Unknown"))
                    sign = "+" if diff > 0 else ""
                    modifiers_applied.append(f"`{sign}{diff} ({mechanic_name})`")

    # Добавляем модификаторы к формуле
    if bonus != 0:
        result["formula_text"] += f" + `{bonus} (Бонус)`"
    
    if modifiers_applied:
        result["formula_text"] += " + " + " + ".join(modifiers_applied)

    # ===== ОПРЕДЕЛЕНИЕ УСПЕХА =====
    if difficulty > 0:
        if result["is_crit"]:
            result["is_success"] = True
            result["msg"] = "КРИТИЧЕСКИЙ УСПЕХ!"
        elif result["is_fumble"]:
            result["is_success"] = False
            result["msg"] = "КРИТИЧЕСКИЙ ПРОВАЛ!"
        else:
            result["is_success"] = result["total"] >= result["final_difficulty"]
            result["msg"] = "УСПЕХ" if result["is_success"] else "ПРОВАЛ"
    else:
        result["msg"] = "РЕЗУЛЬТАТ"
        result["is_success"] = True

    # ===== ТОЧКА 3: on_skill_check =====
    if hasattr(unit, "trigger_mechanics"):
        unit.trigger_mechanics("on_skill_check", unit, check_result=result["total"], stat_key=stat_key)

    return result