import math

from collections import defaultdict


def init_modifiers():
    """
    Создает динамическое хранилище модификаторов.
    Вместо фиксированного списка ключей, мы используем defaultdict.

    Структура: { "stat_name": { "flat": 0.0, "pct": 0.0 } }
    При обращении к несуществующему ключу (например, mods["fire_dmg"]),
    он автоматически создастся.
    """
    # Лямбда-функция создает структуру для каждого нового стата
    return defaultdict(lambda: {"flat": 0.0, "pct": 0.0})


def init_bonuses(unit):
    """
    Собирает временные бонусы к базовым атрибутам.
    Тоже делаем динамическим, чтобы не падало при новых статах.
    """
    return defaultdict(int)


def get_word(value, positive="Повышает", negative="Понижает"):
    return positive if value >= 0 else negative


def safe_int_div(val, div):
    return int(val / div)


def get_modded_value(base_val, stat_name, mods):
    """
    Универсальная формула: (Base + Flat) * (1 + Pct / 100)
    """
    flat = mods[stat_name]["flat"]
    pct = mods[stat_name]["pct"]
    total = (base_val + flat) * (1 + pct / 100.0)
    return int(total)


def calculate_totals(unit, bonuses, mods):
    # 1. Атрибуты
    attrs = {}
    for k in unit.attributes:
        val = unit.attributes[k] + bonuses[k]
        attrs[k] = val
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
    mods["intellect"]["flat"] = base_int

    return attrs, skills


def apply_attribute_effects(attrs, mods, logs):
    # --- СИЛА ---
    sila = attrs["strength"]
    mod_sila_5 = safe_int_div(sila, 5)
    if mod_sila_5 != 0:
        mods["power_attack"]["flat"] += mod_sila_5
        logs.append(f"Сила {sila}: Мощь атаки {mod_sila_5:+}")

    # --- СТОЙКОСТЬ ---
    stoyk = attrs["endurance"]
    mod_stoyk_5 = safe_int_div(stoyk, 5)
    if mod_stoyk_5 != 0:
        mods["power_block"]["flat"] += mod_stoyk_5
        logs.append(f"Стойкость {stoyk}: Мощь блока {mod_stoyk_5:+}")

    # --- ЛОВКОСТЬ ---
    lovkost = attrs["agility"]
    mod_lov = safe_int_div(lovkost, 3)
    mod_lov_5 = safe_int_div(lovkost, 5)

    if mod_lov != 0:
        mods["initiative"]["flat"] += mod_lov
        logs.append(f"Ловкость {lovkost}: Инициатива {mod_lov:+}")
    if mod_lov_5 != 0:
        mods["power_evade"]["flat"] += mod_lov_5
        logs.append(f"Ловкость {lovkost}: Уклонение {mod_lov_5:+}")

    # --- ПСИХИКА ---
    # Влияет на пулы (см. ниже)


def apply_skill_effects(skills, mods, logs):
    # --- СИЛА УДАРА ---
    su = skills["strike_power"]
    mod_su = safe_int_div(su, 3)
    if mod_su != 0:
        mods["damage_deal"]["flat"] += mod_su
        logs.append(f"Сила удара {su}: Урон {mod_su:+}")

    # --- МЕДИЦИНА ---
    med = skills["medicine"]
    mod_med = safe_int_div(med, 3)
    if mod_med != 0:
        eff_pct = mod_med * 10
        mods["heal_efficiency"]["pct"] += eff_pct
        logs.append(f"Медицина {med}: Лечение {eff_pct:+}%")

    # --- АКРОБАТИКА / ЩИТЫ ---
    acro = skills["acrobatics"]
    mod_acro = int(acro * 0.8)
    if mod_acro != 0:
        mods["power_evade"]["flat"] += mod_acro
        logs.append(f"Акробатика {acro}: Уклонение {mod_acro:+}")

    shields = skills["shields"]
    mod_shields = int(shields * 0.8)
    if mod_shields != 0:
        mods["power_block"]["flat"] += mod_shields
        logs.append(f"Щиты {shields}: Блок {mod_shields:+}")

    # --- ОРУЖИЕ ---
    weapon_map = {
        "light_weapon": "power_light",
        "medium_weapon": "power_medium",
        "heavy_weapon": "power_heavy",
        "firearms": "power_ranged"
    }
    for key, target_stat in weapon_map.items():
        val = skills[key]
        mod_w = safe_int_div(val, 3)
        if mod_w != 0:
            mods[target_stat]["flat"] += mod_w
            logs.append(f"{key} {val}: {target_stat} {mod_w:+}")

    # --- КРЕПКАЯ КОЖА ---
    skin = skills["tough_skin"]
    mod_skin = int(skin * 1.2)
    if mod_skin != 0:
        mods["damage_take"]["flat"] -= mod_skin
        logs.append(f"Крепкая кожа {skin}: Поглощение {mod_skin}")


def calculate_speed_dice(unit, speed_val, mods):
    dice_count = 1
    if speed_val >= 10: dice_count += 1
    if speed_val >= 20: dice_count += 1
    if speed_val >= 30: dice_count += 1

    final_dice = []
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


# ==========================================
# 🔍 ПОДРОБНЫЙ РАСЧЕТ ПУЛОВ (HP, SP, Stagger)
# ==========================================
def calculate_pools(unit, attrs, skills, mods, logs):
    """
    Расчет HP, SP и Stagger с подробным логом составляющих.
    """

    # ----------------------------------------------------
    # 1. ЗДОРОВЬЕ (HP)
    # ----------------------------------------------------
    base_h = unit.base_hp

    # Роллы за уровни
    rolls_h = 0
    roll_desc = ""
    if "severe_training" in unit.passives:
        rolls_h = len(unit.level_rolls) * 10
        roll_desc = " (Training)"
    elif "accelerated_learning" in unit.passives:
        rolls_h = len(unit.level_rolls) * 10
        roll_desc = " (Accel)"
    else:
        rolls_h = sum(5 + v.get("hp", 0) for v in unit.level_rolls.values())

    # Бонус от Выносливости
    endurance_val = attrs["endurance"]
    hp_flat_attr = 5 * (endurance_val // 3)
    hp_pct_attr = min(abs(endurance_val) * 2, 100) * (1 if endurance_val >= 0 else -1)

    # Импланты
    imp_h_flat = unit.implants_hp_flat
    imp_h_pct = unit.implants_hp_pct

    # Таланты/Пассивки (Уже собраны в mods collectors.py, но там они смешались.
    # Чтобы показать красиво, вытащим текущее значение из mods, вычтем то что мы знаем)
    # Но проще просто добавить наши известные значения в mods и вывести итог.

    # Добавляем в общий котел
    mods["hp"]["flat"] += base_h + rolls_h + hp_flat_attr + imp_h_flat
    mods["hp"]["pct"] += hp_pct_attr + imp_h_pct + unit.talents_hp_pct

    # Читаем ИТОГОВЫЕ накопившиеся модификаторы
    total_flat = mods["hp"]["flat"]
    total_pct = mods["hp"]["pct"]

    # Считаем
    final_hp = int(total_flat * (1 + total_pct / 100.0))
    unit.max_hp = final_hp

    # ЛОГ
    logs.append(f"❤️ **HP Calculation**:")
    logs.append(
        f"   Base {base_h} + Rolls {rolls_h}{roll_desc} + Attr {hp_flat_attr} + Imp {imp_h_flat} + Other {total_flat - (base_h + rolls_h + hp_flat_attr + imp_h_flat)} = **Flat {total_flat}**")
    logs.append(
        f"   Attr {hp_pct_attr}% + Imp {imp_h_pct}% + Other {total_pct - (hp_pct_attr + imp_h_pct)}% = **Pct {total_pct}%**")
    logs.append(f"   Result: {total_flat} * (1 + {total_pct / 100}) = **{final_hp}**")

    # ----------------------------------------------------
    # 2. РАССУДОК (SP)
    # ----------------------------------------------------
    base_s = unit.base_sp

    rolls_s = 0
    if "severe_training" in unit.passives:
        rolls_s = len(unit.level_rolls) * 5
    elif "accelerated_learning" in unit.passives:
        rolls_s = len(unit.level_rolls) * 10
    else:
        rolls_s = sum(5 + v.get("sp", 0) for v in unit.level_rolls.values())

    psych_val = attrs["psych"]
    sp_flat_attr = 5 * (psych_val // 3)
    sp_pct_attr = min(abs(psych_val) * 2, 100) * (1 if psych_val >= 0 else -1)

    imp_s_flat = unit.implants_sp_flat
    imp_s_pct = unit.implants_sp_pct

    # Добавляем
    mods["sp"]["flat"] += base_s + rolls_s + sp_flat_attr + imp_s_flat
    mods["sp"]["pct"] += sp_pct_attr + imp_s_pct + unit.talents_sp_pct

    total_flat_s = mods["sp"]["flat"]
    total_pct_s = mods["sp"]["pct"]

    final_sp = int(total_flat_s * (1 + total_pct_s / 100.0))
    unit.max_sp = final_sp

    # ЛОГ
    logs.append(f"🧠 **SP Calculation**:")
    logs.append(
        f"   Base {base_s} + Rolls {rolls_s} + Attr {sp_flat_attr} + Imp {imp_s_flat} + Other {total_flat_s - (base_s + rolls_s + sp_flat_attr + imp_s_flat)} = **Flat {total_flat_s}**")
    logs.append(
        f"   Attr {sp_pct_attr}% + Imp {imp_s_pct}% + Other {total_pct_s - (sp_pct_attr + imp_s_pct)}% = **Pct {total_pct_s}%**")
    logs.append(f"   Result: {total_flat_s} * {1 + total_pct_s / 100} = **{final_sp}**")

    # ----------------------------------------------------
    # 3. ВЫДЕРЖКА (Stagger)
    # ----------------------------------------------------
    # Обработка Адаптации (влияет на резисты)
    adapt_lvl = unit.get_status("adaptation")
    if adapt_lvl > 0:
        eff = min(adapt_lvl, 5)
        mods["damage_threshold"]["flat"] = 1 + (eff * 10)
        mods["stagger_take"]["pct"] -= 50
        logs.append(f"🧬 Адаптация: Stagger DMG Taken -50%")

    # Базовая выдержка зависит от HP!
    base_stg = unit.max_hp // 2

    # Навык Сила Воли дает %
    stg_pct_skill = min(skills["willpower"], 50)

    imp_stg_flat = unit.implants_stagger_flat
    imp_stg_pct = unit.implants_stagger_pct

    # Добавляем
    mods["stagger"]["flat"] += base_stg + imp_stg_flat
    mods["stagger"]["pct"] += stg_pct_skill + imp_stg_pct + unit.talents_stagger_pct

    total_flat_stg = mods["stagger"]["flat"]
    total_pct_stg = mods["stagger"]["pct"]

    final_stg = int(total_flat_stg * (1 + total_pct_stg / 100.0))
    unit.max_stagger = final_stg

    # ЛОГ
    logs.append(f"😵 **Stagger Calculation**:")
    logs.append(
        f"   Base (HP/2) {base_stg} + Imp {imp_stg_flat} + Other {total_flat_stg - (base_stg + imp_stg_flat)} = **Flat {total_flat_stg}**")
    logs.append(
        f"   Willpower {stg_pct_skill}% + Imp {imp_stg_pct}% + Other {total_pct_stg - (stg_pct_skill + imp_stg_pct)}% = **Pct {total_pct_stg}%**")
    logs.append(f"   Result: {total_flat_stg} * {1 + total_pct_stg / 100} = **{final_stg}**")


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