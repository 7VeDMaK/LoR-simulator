from core.logging import logger, LogLevel
from logic.character_changing.passives import PASSIVE_REGISTRY
from logic.statuses.status_definitions import STATUS_REGISTRY
from logic.weapon_definitions import WEAPON_REGISTRY


def collect_ability_bonuses(unit, source_list, registry, prefix_icon, mods, bonuses):
    """
    Сбор бонусов от списков способностей (Пассивки, Таланты, Аугментации).
    """
    for pid in source_list:
        if pid in registry:
            obj = registry[pid]
            if hasattr(obj, "on_calculate_stats"):
                bonus_dict = obj.on_calculate_stats(unit)
                if bonus_dict:
                    _apply_smart_bonuses(obj.name, bonus_dict, mods, bonuses, prefix_icon)


def collect_weapon_bonuses(unit, mods, bonuses):
    """
    Сбор бонусов от оружия (базовые статы + встроенная пассивка).
    """
    if unit.weapon_id in WEAPON_REGISTRY:
        wep = WEAPON_REGISTRY[unit.weapon_id]
        if wep.id != "none":
            # Логируем название оружия
            logger.log(f"⚔️ Weapon equipped: {wep.name}", LogLevel.VERBOSE, "Stats")

            # 1. Обычные статы оружия
            _apply_smart_bonuses("Weapon", wep.stats, mods, bonuses, None)

            # 2. Статы от пассивки оружия
            if wep.passive_id and wep.passive_id in PASSIVE_REGISTRY:
                p_obj = PASSIVE_REGISTRY[wep.passive_id]
                if hasattr(p_obj, "on_calculate_stats"):
                    bonus_dict = p_obj.on_calculate_stats(unit)
                    if bonus_dict:
                        _apply_smart_bonuses(f"{p_obj.name} (Wep)", bonus_dict, mods, bonuses, "⚔️")


def collect_status_bonuses(unit, mods, bonuses):
    """
    Сбор бонусов от активных статусов.
    """
    for status_id, stack in unit.statuses.items():
        if status_id in STATUS_REGISTRY and stack > 0:
            st_obj = STATUS_REGISTRY[status_id]
            if hasattr(st_obj, 'on_calculate_stats'):
                try:
                    # Передаем stack, так как многие статусы скейлятся от стаков
                    bonus_dict = st_obj.on_calculate_stats(unit, stack)
                except TypeError:
                    # Фолбек для старых статусов, которые не принимают stack
                    bonus_dict = st_obj.on_calculate_stats(unit)

                if bonus_dict:
                    _apply_smart_bonuses(st_obj.id, bonus_dict, mods, bonuses, None)


def _apply_smart_bonuses(source_name, bonus_dict, mods, bonuses, icon):
    """
    Вспомогательная функция распределения бонусов (Flat vs Percent, Mods vs Bonuses).
    """
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
        is_attribute = stat_name in ["strength", "endurance", "agility", "wisdom", "psych",
                                     "strike_power", "medicine", "willpower", "luck", "acrobatics", "shields",
                                     "tough_skin", "speed", "light_weapon", "medium_weapon", "heavy_weapon",
                                     "firearms", "eloquence", "forging", "engineering", "programming"]

        if is_attribute and mode == "flat":
            bonuses[stat_name] += val
            if icon:
                logger.log(f"{icon} {source_name}: {stat_name} {val:+}", LogLevel.VERBOSE, "Stats")
        else:
            # [FIX] Убрали проверку "if stat_name in mods", так как mods это defaultdict
            mods[stat_name][mode] += val

            # Красивый лог
            if icon:
                sign = "+" if val >= 0 else ""
                suffix = "%" if mode == "pct" else ""
                logger.log(f"{icon} {source_name}: {stat_name.upper()} {sign}{val}{suffix}", LogLevel.VERBOSE,
                           "Stats")