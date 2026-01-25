import random

from core.unit.unit import Unit
from ui.checks.constants import (
    TYPE_10_ATTRS, TYPE_15_SKILLS, TYPE_WISDOM, TYPE_LUCK, TYPE_INTELLECT
)


class CheckContext:
    """Контекст для перехвата броска (механики Adv/Dis)."""
    def __init__(self):
        self.is_advantage = False
        self.is_disadvantage = False
        self.log = []

def get_check_params(key):
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
    if key == "luck":
        return unit.resources.get("luck", 0)

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

    if key in unit.attributes: return unit.attributes[key]
    if key in unit.skills: return unit.skills[key]
    if key == "intellect": return unit.base_intellect

    return 0

def calculate_pre_roll_stats(unit, stat_key, stat_value, difficulty, bonus):
    """
    Рассчитывает шансы и матожидание.
    """
    check_type, _, _ = get_check_params(stat_key)

    die_min = 1
    die_max = 6
    base_add = 0
    stat_bonus = 0
    final_dc = difficulty
    is_talent_active = False

    # Специфичные таланты
    # Без Ошибок (5 + 1d15 для всех проверок)
    if "no_mistakes" in unit.talents:
        die_max = 15
        base_add = 5        
        if check_type == "type10":
            stat_bonus = stat_value // 3
        elif check_type == "type15":
            stat_bonus = stat_value
        elif check_type == "typeW":
            stat_bonus = stat_value
        elif check_type == "typeL":
            stat_bonus = stat_value
        elif check_type == "typeI":
            stat_bonus = 4 + int(stat_value)
        else:
            stat_bonus = 0
        is_talent_active = True

    elif stat_key == "eloquence" and "speech_master" in unit.talents:
        die_max = 10
        base_add = 10
        stat_bonus = stat_value
        is_talent_active = True

    elif stat_key == "engineering" and "bright_talent" in unit.talents:
        die_max = 10
        base_add = 10
        stat_bonus = stat_value
        if difficulty > 0: final_dc = int(difficulty * 1.3)
        is_talent_active = True

    if not is_talent_active:
        if check_type == "type10":
            die_max = 6
            stat_bonus = stat_value // 3
        elif check_type == "type15":
            die_max = 6
            stat_bonus = stat_value
            if stat_key == "engineering" and difficulty > 0: final_dc = int(difficulty * 1.3)
        elif check_type == "typeW":
            die_max = 20
            stat_bonus = stat_value
        elif check_type == "typeL":
            die_max = 12
            stat_bonus = stat_value
        elif check_type == "typeI":
            die_max = 6
            stat_bonus = 4 + int(stat_value)

    target_roll = final_dc - (base_add + stat_bonus + bonus)
    success_count = 0
    total_faces = die_max - die_min + 1

    for r in range(die_min, die_max + 1):
        if not is_talent_active and check_type in ["typeW", "typeL"]:
            if r == 1: continue
            if r == die_max: success_count += 1; continue
        if r >= target_roll: success_count += 1

    chance = (success_count / total_faces) * 100.0
    ev_roll = (die_min + die_max) / 2
    ev_total = ev_roll + base_add + stat_bonus + bonus

    return chance, ev_total, final_dc

def perform_check_logic(unit, stat_key, stat_value, difficulty, bonus):
    """
    Выполняет физический бросок с учетом Преимущества и Помехи.
    """
    stat_key = stat_key.lower()
    check_type, die_type, _ = get_check_params(stat_key)

    result = {
        "roll": 0, "die": die_type, "stat_bonus": 0, "total": 0,
        "final_difficulty": difficulty, "is_success": False,
        "is_crit": False, "is_fumble": False, "msg": "", "formula_text": ""
    }

    # === 1. ИНИЦИАЛИЗАЦИЯ КОНТЕКСТА И ХУКИ ===
    ctx = CheckContext()

    # Вызываем событие on_check_roll у всех механик юнита
    if hasattr(unit, "trigger_mechanics"):
        unit.trigger_mechanics("on_check_roll", unit, attribute=stat_key, context=ctx)

    is_adv = ctx.is_advantage
    is_dis = ctx.is_disadvantage

    # Взаимопоглощение
    if is_adv and is_dis:
        is_adv = False
        is_dis = False

    # === 2. ФУНКЦИЯ БРОСКА С ADV/DIS ===
    def roll_with_mechanic(min_val, max_val):
        r1 = random.randint(min_val, max_val)
        if not is_adv and not is_dis:
            return r1, [r1], ""

        r2 = random.randint(min_val, max_val)
        rolls = [r1, r2]

        if is_adv:
            final = max(r1, r2)
            tag = f"(Adv: {r1}, {r2})"
        else:  # is_dis
            final = min(r1, r2)
            tag = f"(Dis: {r1}, {r2})"

        return final, rolls, tag

    # === 3. ТАЛАНТЫ (ПЕРЕОПРЕДЕЛЕНИЕ - HIGHEST PRIORITY) ===
    # Без Ошибок (5 + 1d15 для всех проверок)
    if "no_mistakes" in unit.talents:
        val, logs, tag = roll_with_mechanic(1, 15)

        result["die"] = f"d15 {tag}" if tag else "d15"
        result["roll"] = val
        
        # Определяем бонус от характеристики/навыка в зависимости от типа
        if check_type == "type10":
            stat_modifier = stat_value // 3
            stat_label = "Стат // 3"
        elif check_type == "type15":
            stat_modifier = stat_value
            stat_label = "Навык"
        elif check_type == "typeW":
            stat_modifier = stat_value
            stat_label = "Мудр"
        elif check_type == "typeL":
            stat_modifier = stat_value
            stat_label = "Удача"
        elif check_type == "typeI":
            stat_modifier = 4 + int(stat_value)
            stat_label = "4 + Инт"
        else:
            stat_modifier = 0
            stat_label = ""
        
        result["stat_bonus"] = 5 + stat_modifier
        
        # Формируем текст формулы
        formula_parts = ["`5 (No Mistakes)`"]
        if stat_modifier != 0:
            formula_parts.append(f"`{stat_modifier} ({stat_label})`")
        if bonus != 0:
            formula_parts.append(f"`{bonus} (Bonus)`")
        result["formula_text"] = " + ".join(formula_parts)
        
        result["total"] = 5 + val + stat_modifier + bonus

        if difficulty > 0:
            result["is_success"] = result["total"] >= difficulty
            result["msg"] = "УСПЕХ" if result["is_success"] else "ПРОВАЛ"
        else:
            result["msg"] = "РЕЗУЛЬТАТ"
            result["is_success"] = True
        return result

    # Мастер речи (d10)
    if stat_key == "eloquence" and "speech_master" in unit.talents:
        val, logs, tag = roll_with_mechanic(1, 10)

        result["die"] = f"d10 {tag}"
        result["roll"] = val
        result["stat_bonus"] = stat_value
        result["formula_text"] = f"`10 (Talent)` + `{stat_value} (Skill)`"
        result["total"] = result["roll"] + 10 + stat_value + bonus

        if difficulty > 0:
            result["is_success"] = result["total"] >= difficulty
            result["msg"] = "УСПЕХ" if result["is_success"] else "ПРОВАЛ"
        else:
            result["msg"] = "РЕЗУЛЬТАТ"
            result["is_success"] = True
        return result

    # Яркий талант (Инженерия)
    elif stat_key == "engineering" and "bright_talent" in unit.talents:
        val, logs, tag = roll_with_mechanic(1, 10)

        result["die"] = f"d10 {tag}"
        result["roll"] = val
        result["stat_bonus"] = stat_value
        result["formula_text"] = f"`10 (Talent)` + `{stat_value} (Skill)`"

        if difficulty > 0:
            result["final_difficulty"] = int(difficulty * 1.3)

        result["total"] = result["roll"] + 10 + stat_value + bonus

        if difficulty > 0:
            result["is_success"] = result["total"] >= result["final_difficulty"]
            result["msg"] = "УСПЕХ" if result["is_success"] else "ПРОВАЛ"
        else:
            result["msg"] = "РЕЗУЛЬТАТ"
            result["is_success"] = True
        return result

    # === 4. СТАНДАРТНАЯ ЛОГИКА ===
    if check_type in ["type10", "type15", "typeI"]:
        val, logs, tag = roll_with_mechanic(1, 6)
        result["roll"] = val
        result["die"] = f"d6 {tag}" if tag else "d6"

        if check_type == "type10":
            result["stat_bonus"] = stat_value // 3
            result["formula_text"] = f"`{result['stat_bonus']} (Стат // 3)`"
        elif check_type == "typeI":
            result["stat_bonus"] = 4 + int(stat_value)
            result["formula_text"] = f"`{result['stat_bonus']} (4 + Инт)`"
        else:  # type15
            result["stat_bonus"] = stat_value
            result["formula_text"] = f"`{result['stat_bonus']} (Навык)`"
            if stat_key == "engineering" and difficulty > 0:
                result["final_difficulty"] = int(difficulty * 1.3)

    elif check_type == "typeW":
        val, logs, tag = roll_with_mechanic(1, 20)
        result["roll"] = val
        result["die"] = f"d20 {tag}" if tag else "d20"
        result["stat_bonus"] = stat_value
        result["formula_text"] = f"`{result['stat_bonus']} (Мудр)`"

        if val == 20: result["is_crit"] = True
        if val == 1: result["is_fumble"] = True

    elif check_type == "typeL":
        val, logs, tag = roll_with_mechanic(1, 12)
        result["roll"] = val
        result["die"] = f"d12 {tag}" if tag else "d12"
        result["stat_bonus"] = stat_value
        result["formula_text"] = f"`{result['stat_bonus']} (Удача)`"

        if val == 12: result["is_crit"] = True
        if val == 1: result["is_fumble"] = True

    # === ИТОГ ===
    result["total"] = result["roll"] + result["stat_bonus"] + bonus

    # === МОДИФИКАТОРЫ ОТ ПАССИВОК ===
    passive_modifier = 0
    if hasattr(unit, "trigger_mechanics"):
        # Собираем модификаторы от всех пассивок
        for mechanic in getattr(unit, "mechanics", []):
            if hasattr(mechanic, "modify_skill_check_result"):
                mod = mechanic.modify_skill_check_result(unit, stat_key, result["total"])
                if mod != 0:
                    passive_modifier += mod
    
    if passive_modifier != 0:
        result["total"] += passive_modifier
        result["passive_modifier"] = passive_modifier

    if difficulty > 0:
        if result["is_crit"]:
            result["is_success"] = True; result["msg"] = "КРИТИЧЕСКИЙ УСПЕХ!"
        elif result["is_fumble"]:
            result["is_success"] = False; result["msg"] = "КРИТИЧЕСКИЙ ПРОВАЛ!"
        else:
            result["is_success"] = result["total"] >= result["final_difficulty"]
            result["msg"] = "УСПЕХ" if result["is_success"] else "ПРОВАЛ"
    else:
        result["msg"] = "РЕЗУЛЬТАТ"
        result["is_success"] = True

    if hasattr(unit, "trigger_mechanics"):
        unit.trigger_mechanics("on_skill_check", unit, check_result=result["total"], stat_key=stat_key)

    return result