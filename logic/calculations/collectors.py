from logic.passives import PASSIVE_REGISTRY
from logic.talents import TALENT_REGISTRY
from logic.statuses.status_manager import STATUS_REGISTRY
from logic.weapon_definitions import WEAPON_REGISTRY


def collect_ability_bonuses(unit, source_list, registry, prefix_icon, mods, bonuses, logs):
    for pid in source_list:
        if pid in registry:
            obj = registry[pid]
            if hasattr(obj, "on_calculate_stats"):
                bonus_dict = obj.on_calculate_stats(unit)
                if bonus_dict:
                    _apply_smart_bonuses(obj.name, bonus_dict, mods, bonuses, logs, prefix_icon)


def collect_weapon_bonuses(unit, mods, bonuses, logs):
    if unit.weapon_id in WEAPON_REGISTRY:
        wep = WEAPON_REGISTRY[unit.weapon_id]
        if wep.id != "none":
            logs.append(f"⚔️ Оружие: {wep.name}")
            # 1. Обычные статы оружия
            _apply_smart_bonuses("Оружие", wep.stats, mods, bonuses, logs, None)

            # === 2. Статы от пассивки оружия (НОВОЕ) ===
            if wep.passive_id and wep.passive_id in PASSIVE_REGISTRY:
                p_obj = PASSIVE_REGISTRY[wep.passive_id]
                if hasattr(p_obj, "on_calculate_stats"):
                    bonus_dict = p_obj.on_calculate_stats(unit)
                    if bonus_dict:
                        _apply_smart_bonuses(f"{p_obj.name}", bonus_dict, mods, bonuses, logs, "⚔️")

def collect_status_bonuses(unit, mods, bonuses, logs):
    for status_id, stack in unit.statuses.items():
        if status_id in STATUS_REGISTRY and stack > 0:
            st_obj = STATUS_REGISTRY[status_id]
            if hasattr(st_obj, 'on_calculate_stats'):
                bonus_dict = st_obj.on_calculate_stats(unit)
                if bonus_dict:
                    # Некоторые статусы возвращают сложные структуры, здесь предполагаем простой словарь
                    # Если нужно учитывать стаки, статус сам должен умножить значения внутри on_calculate_stats
                    _apply_smart_bonuses(st_obj.id, bonus_dict, mods, bonuses, logs, None)


def collect_weapon_bonuses(unit, mods, bonuses, logs):
    if unit.weapon_id in WEAPON_REGISTRY:
        wep = WEAPON_REGISTRY[unit.weapon_id]
        if wep.id != "none":
            logs.append(f"⚔️ Оружие: {wep.name}")
            _apply_smart_bonuses("Оружие", wep.stats, mods, bonuses, logs, None)


def _apply_smart_bonuses(source_name, bonus_dict, mods, bonuses, logs, icon):
    for key, val in bonus_dict.items():
        stat_name = key
        mode = "flat"  # По умолчанию добавляем как число

        # 1. Определяем режим (Процент или Флат)
        if key.endswith("_pct") or key.endswith("_percent"):
            stat_name = key.replace("_pct", "").replace("_percent", "")
            mode = "pct"
        elif key.endswith("_flat"):
            stat_name = key.replace("_flat", "")
            mode = "flat"

        # 2. Определяем куда писать: в bonuses (базовые статы) или mods (боевые/производные)
        # Базовые атрибуты обычно идут в bonuses, чтобы потом участвовать в формулах
        # === FIX: Добавлена "luck" в список, чтобы она не перезаписывалась ===
        is_attribute = stat_name in ["strength", "endurance", "agility", "wisdom", "psych",
                                     "strike_power", "medicine", "willpower", "luck", "acrobatics", "shields",
                                     "tough_skin", "speed", "light_weapon", "medium_weapon", "heavy_weapon",
                                     "firearms", "eloquence", "forging", "engineering", "programming"]

        if is_attribute and mode == "flat":
            bonuses[stat_name] += val
            if icon:
                logs.append(f"{icon} {source_name}: {stat_name} {val:+}")
        else:
            mods[stat_name][mode] += val

            # Красивый лог
            if icon:
                sign = "+" if val >= 0 else ""
                suffix = "%" if mode == "pct" else ""
                logs.append(f"{icon} {source_name}: {stat_name.upper()} {sign}{val}{suffix}")