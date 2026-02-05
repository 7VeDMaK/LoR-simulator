from core.enums import DiceType
from core.logging import logger, LogLevel
from logic.calculations.base_calc import get_modded_value
from logic.mechanics.rolling.rolling_utils import safe_randint
from logic.weapon_definitions import WEAPON_REGISTRY


def calculate_base_roll(source, base_min, base_max, is_disadvantage):
    """
    Выполняет базовый бросок кубика с учетом Преимущества и Помехи.
    Возвращает: (roll, base_val, log_prefix, final_is_disadvantage)
    """
    has_advantage = source.get_status("advantage") > 0
    roll = 0
    base_val = 0
    log_prefix = ""
    final_is_disadvantage = False

    if is_disadvantage and has_advantage:
        # Взаимопоглощение -> Обычный бросок
        roll = safe_randint(base_min, base_max)
        base_val = roll
        log_prefix = "⚖️ **Advantage + Disadvantage** -> Normal"
        source.remove_status("advantage", 1)
        logger.log(f"⚖️ {source.name}: Adv cancels Disadv. Rolled {roll}", LogLevel.VERBOSE, "Roll")

    elif is_disadvantage:
        # Помеха (Худший из 2)
        r1 = safe_randint(base_min, base_max)
        r2 = safe_randint(base_min, base_max)
        roll = min(r1, r2)
        base_val = roll
        log_prefix = f"📉 **Помеха!** ({r1}, {r2})"
        final_is_disadvantage = True
        logger.log(f"📉 {source.name}: Disadvantage ({r1}, {r2}) -> {roll}", LogLevel.VERBOSE, "Roll")

    elif has_advantage:
        # Преимущество (Лучший из 2)
        r1 = safe_randint(base_min, base_max)
        r2 = safe_randint(base_min, base_max)
        roll = max(r1, r2)
        base_val = roll
        log_prefix = f"🍀 **Преимущество!** ({r1}, {r2})"
        source.remove_status("advantage", 1)
        logger.log(f"🍀 {source.name}: Advantage ({r1}, {r2}) -> {roll}", LogLevel.VERBOSE, "Roll")

    else:
        # Обычный
        roll = safe_randint(base_min, base_max)
        base_val = roll
        logger.log(f"🎲 {source.name}: Rolled {roll} [{base_min}-{base_max}]", LogLevel.VERBOSE, "Roll")

    return roll, base_val, log_prefix, final_is_disadvantage


def apply_roll_modifiers(ctx, source, die):
    """
    Применяет модификаторы (статы, оружие, пассивки) к контексту броска.
    """
    mods = source.modifiers
    skip_standard_stats = False

    # [NEW] Проверка хука override_roll_base_stat
    if hasattr(source, "apply_mechanics_filter"):
        # Пытаемся получить подмену стата
        override_val, override_reason = source.apply_mechanics_filter(
            "override_roll_base_stat",
            (0, ""),
            dice=die
        )

        if override_val != 0:
            # Применяем кастомный стат (например, Удача)
            ctx.modify_power(override_val, override_reason)
            # Отключаем стандартные бонусы от характеристик (Сила, Стойкость и т.д.)
            skip_standard_stats = True
            logger.log(f"⚡ Stat Override: Used {override_reason} (+{override_val}), standard stats skipped.", LogLevel.VERBOSE, "Roll")

    # Атака
    if die.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
        # Общая сила (от стата Strength) - применяем только если нет оверрайда
        if not skip_standard_stats:
            p_atk = get_modded_value(0, "power_attack", mods)
            if p_atk:
                ctx.modify_power(p_atk, "Сила")
                logger.log(f"💪 Power Atk Bonus: {p_atk:+}", LogLevel.VERBOSE, "Roll")

        # === БОНУС ОРУЖИЯ ===
        current_weapon_id = getattr(source, "weapon_id", "none")
        weapon_type = "light"  # По дефолту

        if current_weapon_id in WEAPON_REGISTRY:
            weapon_type = WEAPON_REGISTRY[current_weapon_id].weapon_type

        type_to_mod = {
            "light": "power_light",
            "medium": "power_medium",
            "heavy": "power_heavy",
            "ranged": "power_ranged",
            "gun": "power_ranged"  # gun использует тот же модификатор что и ranged
        }

        target_mod_key = type_to_mod.get(weapon_type, "power_light")
        w_bonus = get_modded_value(0, target_mod_key, mods)

        if w_bonus != 0:
            ru_names = {
                "light": "Легкое ор.",
                "medium": "Среднее ор.",
                "heavy": "Тяжелое ор.",
                "ranged": "Огнестрел",
                "gun": "Огнестрел"  # gun отображается как Огнестрел
            }
            reason = ru_names.get(weapon_type, "Оружие")
            ctx.modify_power(w_bonus, reason)
            logger.log(f"⚔️ Weapon Bonus ({weapon_type}): {w_bonus:+}", LogLevel.VERBOSE, "Roll")

        # Бонус конкретного типа атаки (Slash/Pierce/Blunt)
        type_key = f"power_{die.dtype.value.lower()}"
        type_bonus = get_modded_value(0, type_key, mods)
        if type_bonus:
            ctx.modify_power(type_bonus, f"Bonus {die.dtype.name}")
            logger.log(f"⚔️ Type Bonus ({die.dtype.name}): {type_bonus:+}", LogLevel.VERBOSE, "Roll")

    # Блок
    elif die.dtype == DiceType.BLOCK:
        if not skip_standard_stats:
            p_blk = get_modded_value(0, "power_block", mods)
            if p_blk:
                ctx.modify_power(p_blk, "Стойкость")
                logger.log(f"🛡️ Block Bonus: {p_blk:+}", LogLevel.VERBOSE, "Roll")

    # Уворот
    elif die.dtype == DiceType.EVADE:
        if not skip_standard_stats:
            p_evd = get_modded_value(0, "power_evade", mods)
            if p_evd:
                ctx.modify_power(p_evd, "Ловкость")
                logger.log(f"💨 Evade Bonus: {p_evd:+}", LogLevel.VERBOSE, "Roll")

    # --- ГЛОБАЛЬНЫЙ БОНУС (Power All) ---
    power_all = mods.get("power_all", {}).get("flat", 0)
    if power_all != 0:
        ctx.modify_power(power_all, "Power All")