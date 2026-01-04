import math


def get_word(value, positive="Повышает", negative="Понижает"):
    return positive if value >= 0 else negative


def safe_int_div(val, div):
    """
    Деление с отбрасыванием дробной части через int(),
    чтобы -4 / 3 давало -1 (как в ТЗ), а не -2 (как // в Python).
    """
    return int(val / div)


def get_modded_value(base_val, stat_name, mods):
    """
    Универсальная формула: (Base + Flat) * (1 + Pct / 100)
    Округляет результат до целого.
    """
    flat = mods[stat_name]["flat"]
    pct = mods[stat_name]["pct"]

    total = (base_val + flat) * (1 + pct / 100.0)
    return int(total)


def calculate_totals(unit, bonuses, mods):
    """Суммирует базу и бонусы, заполняет mods['total_X']."""

    # 1. Атрибуты
    attrs = {}
    for k in unit.attributes:
        val = unit.attributes[k] + bonuses[k]
        attrs[k] = val
        # Записываем в новую структуру
        mods[k]["flat"] = val

    # 2. Навыки
    skills = {}
    for k in unit.skills:
        val = unit.skills[k] + bonuses[k]
        skills[k] = val
        mods[k]["flat"] = val

    # 3. Интеллект
    base_int = unit.base_intellect + bonuses["bonus_intellect"] + (attrs["wisdom"] // 3)
    mods["total_intellect"]["flat"] = base_int
    mods["intellect"]["flat"] = base_int  # Для совместимости

    return attrs, skills


def apply_attribute_effects(attrs, mods, logs):
    """Бонусы от Атрибутов (восстановлена полная логика логов)."""

    # --- СИЛА ---
    sila = attrs["strength"]
    mod_sila = safe_int_div(sila, 3)
    mod_sila_5 = safe_int_div(sila, 5)

    if mod_sila != 0:
        word = get_word(mod_sila)
        logs.append(f"{word} значение броска силы на {abs(mod_sila)}")

    if mod_sila_5 != 0:
        word = get_word(mod_sila_5)
        mods["power_attack"]["flat"] += mod_sila_5
        logs.append(f"{word} значение куба ⚔️ атаки на {abs(mod_sila_5)}")

    # --- СТОЙКОСТЬ ---
    stoyk = attrs["endurance"]
    mod_stoyk_5 = safe_int_div(stoyk, 5)

    if mod_stoyk_5 != 0:
        word = get_word(mod_stoyk_5)
        mods["power_block"]["flat"] += mod_stoyk_5
        logs.append(f"{word} значение куба 🛡️ блока на {abs(mod_stoyk_5)}")

    # --- ЛОВКОСТЬ ---
    lovkost = attrs["agility"]
    mod_lov = safe_int_div(lovkost, 3)
    mod_lov_5 = safe_int_div(lovkost, 5)

    if mod_lov != 0:
        word = get_word(mod_lov)
        mods["initiative"]["flat"] += mod_lov
        logs.append(f"{word} значение броска ловкости и 👢 инициативу на {abs(mod_lov)}")

    if mod_lov_5 != 0:
        word = get_word(mod_lov_5)
        mods["power_evade"]["flat"] += mod_lov_5
        logs.append(f"{word} значение куба 💨 уклонения на {abs(mod_lov_5)}")

    # --- МУДРОСТЬ ---
    mudrost = attrs["wisdom"]
    if abs(mudrost) >= 3:
        word = "Повышает" if mudrost > 0 else "Понижает"
        logs.append(f'{word} "интеллект" персонажа на основе его опыта')

    # --- ПСИХИКА ---
    psy = attrs["psych"]
    mod_psy = safe_int_div(psy, 3)
    if mod_psy != 0:
        word = get_word(mod_psy)
        logs.append(f"{word} значение бросков против необъяснимого на {abs(mod_psy)}")


def apply_skill_effects(skills, mods, logs):
    """Бонусы от Навыков (восстановлена полная логика логов)."""

    # --- СИЛА УДАРА ---
    su = skills["strike_power"]
    mod_su = safe_int_div(su, 3)
    if mod_su != 0:
        word = get_word(mod_su)
        mods["damage_deal"]["flat"] += mod_su
        logs.append(f"Ваш показатель 💥 урона при ударе {word.lower()}ся на {abs(mod_su)}")

    # --- МЕДИЦИНА ---
    med = skills["medicine"]
    mod_med = safe_int_div(med, 3)
    if mod_med != 0:
        heal_eff = mod_med * 10
        word = get_word(mod_med, "повышается", "понижается")

        # В новой системе проценты храним в 'pct' (10 = 10%)
        # Если в damage.py heal_efficiency используется как множитель (1.5), то тут надо адаптировать.
        # Обычно get_modded_value берет (1 + pct/100). Значит 10 -> 1.1x.
        mods["heal_efficiency"]["pct"] += heal_eff

        logs.append(f"Ваш бросок 💚 медицины {word} на {abs(mod_med)}, эффективность лечения — {abs(heal_eff)}%")

    # --- АКРОБАТИКА ---
    acro = skills["acrobatics"]
    mod_acro = safe_int_div(acro, 3)
    if mod_acro != 0:
        val = int(mod_acro * 0.8)
        if val != 0:
            word = get_word(val)
            mods["power_evade"]["flat"] += val
            logs.append(f"{word} значение куба 💨 уклонения на {abs(val)} (Акробатика)")

    # --- ЩИТЫ ---
    shields = skills["shields"]
    mod_shields = safe_int_div(shields, 3)
    if mod_shields != 0:
        val = int(mod_shields * 0.8)
        if val != 0:
            word = get_word(val)
            mods["power_block"]["flat"] += val
            logs.append(f"{word} значение куба 🛡️ щита на {abs(val)}")

    # --- ОРУЖИЕ ---
    weapon_map = {
        "light_weapon": "лёгкого оружия",
        "medium_weapon": "среднего оружия",
        "heavy_weapon": "тяжёлого оружия",
        "firearms": "огнестрельного оружия"
    }

    # Словарь сопоставления навыка с ключом мода
    mod_key_map = {
        "light_weapon": "power_light",
        "medium_weapon": "power_medium",
        "heavy_weapon": "power_heavy",
        "firearms": "power_ranged"
    }

    for key, name_ru in weapon_map.items():
        val = skills[key]
        mod_w = safe_int_div(val, 3)
        if mod_w != 0:
            word = get_word(mod_w)

            target_stat = mod_key_map.get(key)
            mods[target_stat]["flat"] += mod_w

            logs.append(f"{word} значение куба ⚔️ удара атакующими картами {name_ru} на {abs(mod_w)}")

    # --- КРЕПКАЯ КОЖА ---
    skin = skills["tough_skin"]
    mod_skin = safe_int_div(skin, 3)
    if mod_skin != 0:
        val = int(mod_skin * 1.2)
        if val > 0:
            mods["damage_take"][
                "flat"] += val  # Внимание: тут логика damage.py должна вычитать это значение (Absorption)
            logs.append(f"Понижает 🧱 получаемый урон на {val}")
        elif val < 0:
            mods["damage_take"]["flat"] += val
            logs.append(f"Повышает 🧱 получаемый урон на {abs(val)}")

    # --- СОЦИАЛЬНЫЕ И КРАФТ ---
    simple_skills = [
        ("eloquence", "значение броска при убеждении/торговле"),
        ("forging", "бросок качества создаваемого предмета"),
        ("engineering", "качество предметов и бросок инженерии"),
        ("programming", "успешность взлома и контроля механизмов")
    ]
    for key, desc in simple_skills:
        val = skills[key]
        if val != 0:
            word = get_word(val)
            logs.append(f"{word} {desc} на {abs(val)}")


def calculate_speed_dice(unit, speed_val, mods):
    """Считает кубики скорости."""
    dice_count = 1
    if speed_val >= 10: dice_count += 1
    if speed_val >= 20: dice_count += 1
    if speed_val >= 30: dice_count += 1

    final_dice = []
    # Берем инициативу из mods (flat)
    global_init = mods["initiative"]["flat"]

    for i in range(dice_count):
        skill_bonus = 0
        if i == 3 and speed_val >= 30:
            skill_bonus = 5
        else:
            points = max(0, min(10, speed_val - (i * 10)))
            skill_bonus = points // 2

        d_min = unit.base_speed_min + global_init + skill_bonus
        d_max = unit.base_speed_max + global_init + skill_bonus
        final_dice.append((d_min, d_max))

    unit.computed_speed_dice = final_dice
    unit.speed_dice_count = dice_count


def calculate_pools(unit, attrs, skills, mods, logs):
    """
    Расчет HP, SP и Stagger (с логами).
    """
    # --- 1. HP ---
    base_h = unit.base_hp
    rolls_h = 0

    if "severe_training" in unit.passives:
        rolls_h = len(unit.level_rolls) * 10
        logs.append(f"🏋️ Суровые тренировки: +10 HP за уровень")
    elif "accelerated_learning" in unit.passives:
        rolls_h = len(unit.level_rolls) * 10
        logs.append(f"🎓 Ускоренное обучение: +10 HP за каждые 3 уровня")
    else:
        rolls_h = sum(5 + v.get("hp", 0) for v in unit.level_rolls.values())

    endurance_val = attrs["endurance"]
    hp_flat_attr = 5 * (endurance_val // 3)
    hp_pct_attr = min(abs(endurance_val) * 2, 100)
    if endurance_val < 0: hp_pct_attr = -hp_pct_attr

    # Логи HP
    if endurance_val != 0:
        word = get_word(endurance_val)
        logs.append(f"{word} максимальный показатель ❤️ здоровья на {abs(hp_pct_attr)}% от основного")
    if hp_flat_bonus := hp_flat_attr:  # walrus для краткости
        action = "получает дополнительные" if hp_flat_bonus > 0 else "теряет"
        logs.append(f"Персонаж {action} {abs(hp_flat_bonus)} ❤️ здоровья")

        # === [ВАЖНО] СБОР ВСЕХ МОДИФИКАТОРОВ В MODS ===
        # Добавляем Flat (база + роллы + статы + ИМПЛАНТЫ)
    mods["hp"]["flat"] += base_h + rolls_h + hp_flat_attr + unit.implants_hp_flat

    # Добавляем Percent (статы + импланты + таланты)
    mods["hp"]["pct"] += hp_pct_attr + unit.implants_hp_pct + unit.talents_hp_pct

    unit.max_hp = get_modded_value(0, "hp", mods)

    # --- 2. SP ---
    base_s = unit.base_sp
    rolls_s = 0

    if "severe_training" in unit.passives:
        rolls_s = len(unit.level_rolls) * 5
        logs.append(f"🏋️ Суровые тренировки: +5 SP за уровень")
    elif "accelerated_learning" in unit.passives:
        rolls_s = len(unit.level_rolls) * 10
        logs.append(f"🎓 Ускоренное обучение: +10 SP за каждые 3 уровня")
    else:
        rolls_s = sum(5 + v.get("sp", 0) for v in unit.level_rolls.values())

    psych_val = attrs["psych"]
    sp_flat_attr = 5 * (psych_val // 3)
    sp_pct_attr = min(abs(psych_val) * 2, 100)
    if psych_val < 0: sp_pct_attr = -sp_pct_attr

    # Логи SP
    if psych_val != 0:
        word = get_word(psych_val)
        logs.append(f"{word} максимальный показатель 🧠 рассудка на {abs(sp_pct_attr)}% от основного")
    if sp_flat_bonus := sp_flat_attr:
        action = "получает дополнительные" if sp_flat_bonus > 0 else "теряет"
        logs.append(f"Персонаж {action} {abs(sp_flat_bonus)} 🧠 рассудка")

    # Сбор SP
    mods["sp"]["flat"] += base_s + rolls_s + sp_flat_attr + unit.implants_sp_flat
    mods["sp"]["pct"] += sp_pct_attr + unit.implants_sp_pct + unit.talents_sp_pct

    unit.max_sp = get_modded_value(0, "sp", mods)

    # --- 3. STAGGER ---
    adapt_lvl = unit.get_status("adaptation")
    if adapt_lvl > 0:
        eff_lvl = min(adapt_lvl, 5)
        # Damage Threshold
        mods["damage_threshold"]["flat"] = 1 + (eff_lvl * 10)
        # Stagger Take reduction (-50% at max)
        mods["stagger_take"]["pct"] -= 50
        logs.append(f"🧬 Адаптация (Ур. {eff_lvl}): Игнор < {1 + eff_lvl * 10}, StaggerResist +50%")

    base_stg = unit.max_hp // 2
    stg_pct = min(skills["willpower"], 50)

    # Логи Stagger
    if stg_pct != 0:
        word = get_word(stg_pct)
        logs.append(f"{word} 😵 выдержку на {abs(stg_pct)}%")

    # Сбор Stagger
    mods["stagger"]["flat"] += base_stg + unit.implants_stagger_flat
    mods["stagger"]["pct"] += stg_pct + unit.implants_stagger_pct

    unit.max_stagger = get_modded_value(0, "stagger", mods)

def finalize_state(unit, mods, logs):
    """Финальные проверки."""
    unit.current_hp = min(unit.current_hp, unit.max_hp)
    unit.current_sp = min(unit.current_sp, unit.max_sp)
    unit.current_stagger = min(unit.current_stagger, unit.max_stagger)

    if mods["disable_block"]["flat"] > 0:
        mods["power_block"]["flat"] = -999
        logs.append("🚫 Блок отключен")

    if mods["disable_evade"]["flat"] > 0:
        mods["power_evade"]["flat"] = -999
        logs.append("🚫 Уклонение отключено")