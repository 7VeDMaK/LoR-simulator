import random
from core.enums import DiceType
from logic.context import RollContext
from logic.mechanics.scripts import process_card_scripts
# Импортируем функцию для чтения модов
from logic.calculations.formulas import get_modded_value
from logic.weapon_definitions import WEAPON_REGISTRY


def safe_randint(min_val: int, max_val: int) -> int:
    """
    Безопасный рандом: если min > max, меняет их местами.
    """
    if min_val > max_val:
        return random.randint(max_val, min_val)
    return random.randint(min_val, max_val)


def create_roll_context(source, target, die, is_disadvantage=False) -> RollContext:
    if not die: return None

    # === [ОПТИМИЗАЦИЯ] 1. Модификация границ кубика ===
    # Позволяет эффектам менять мин/макс значения ПЕРЕД броском
    base_min = die.min_val
    base_max = die.max_val

    if hasattr(source, "apply_mechanics_filter"):
        base_min = source.apply_mechanics_filter("modify_dice_min", base_min, die=die)
        base_max = source.apply_mechanics_filter("modify_dice_max", base_max, die=die)

    # === 2. БАЗОВЫЙ БРОСОК (Advantage / Disadvantage) ===
    has_advantage = source.get_status("advantage") > 0
    roll = 0
    base_val = 0
    log_prefix = ""

    # Флаг итоговой помехи для контекста
    final_is_disadvantage = False

    if is_disadvantage and has_advantage:
        # Взаимопоглощение -> Обычный бросок
        roll = safe_randint(base_min, base_max)
        base_val = roll
        log_prefix = "⚖️ **Advantage + Disadvantage** -> Normal"
        source.remove_status("advantage", 1)

    elif is_disadvantage:
        # Помеха (Худший из 2)
        r1 = safe_randint(base_min, base_max)
        r2 = safe_randint(base_min, base_max)
        roll = min(r1, r2)
        base_val = roll
        log_prefix = f"📉 **Помеха!** ({r1}, {r2})"
        final_is_disadvantage = True

    elif has_advantage:
        # Преимущество (Лучший из 2)
        r1 = safe_randint(base_min, base_max)
        r2 = safe_randint(base_min, base_max)
        roll = max(r1, r2)
        base_val = roll
        log_prefix = f"🍀 **Преимущество!** ({r1}, {r2})"
        source.remove_status("advantage", 1)

    else:
        # Обычный
        roll = safe_randint(base_min, base_max)
        base_val = roll

    # Создаем контекст с base_value
    ctx = RollContext(
        source=source,
        target=target,
        dice=die,
        final_value=roll,
        base_value=base_val,
        is_disadvantage=final_is_disadvantage
    )

    if log_prefix:
        ctx.log.append(f"{log_prefix} -> Base: {base_val}")

    # === 3. НЕИЗМЕНЯЕМОСТЬ ===
    if source.current_card and "unchangeable" in source.current_card.flags:
        ctx.log.append("🔒 Unchangeable (Mods ignored)")
        process_card_scripts("on_roll", ctx)
        process_card_scripts("on_play", ctx)
        if hasattr(ctx, 'get_formatted_roll_log'):
            ctx.log.insert(0, ctx.get_formatted_roll_log())
        return ctx

    # === 4. МОДИФИКАТОРЫ (ОБНОВЛЕНО) ===
    mods = source.modifiers

    # Атака
    if die.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
        # Общая сила (от стата Strength)
        p_atk = get_modded_value(0, "power_attack", mods)
        if p_atk: ctx.modify_power(p_atk, "Сила")

        # === БОНУС ОРУЖИЯ ===
        # Определяем тип текущего оружия
        current_weapon_id = getattr(source, "weapon_id", "none")
        weapon_type = "light"  # По дефолту (кулаки)

        if current_weapon_id in WEAPON_REGISTRY:
            weapon_type = WEAPON_REGISTRY[current_weapon_id].weapon_type

        # Карта маппинга типа оружия на ключ модификатора
        type_to_mod = {
            "light": "power_light",
            "medium": "power_medium",
            "heavy": "power_heavy",
            "ranged": "power_ranged"
        }

        target_mod_key = type_to_mod.get(weapon_type, "power_light")
        w_bonus = get_modded_value(0, target_mod_key, mods)

        if w_bonus != 0:
            ru_names = {
                "light": "Легкое ор.",
                "medium": "Среднее ор.",
                "heavy": "Тяжелое ор.",
                "ranged": "Огнестрел"
            }
            reason = ru_names.get(weapon_type, "Оружие")
            ctx.modify_power(w_bonus, reason)

        # Бонус конкретного типа атаки (Slash/Pierce/Blunt)
        type_key = f"power_{die.dtype.value.lower()}"
        type_bonus = get_modded_value(0, type_key, mods)
        if type_bonus: ctx.modify_power(type_bonus, f"Bonus {die.dtype.name}")

    # Блок
    elif die.dtype == DiceType.BLOCK:
        p_blk = get_modded_value(0, "power_block", mods)
        if p_blk: ctx.modify_power(p_blk, "Стойкость")

    # Уворот
    elif die.dtype == DiceType.EVADE:
        p_evd = get_modded_value(0, "power_evade", mods)
        if p_evd: ctx.modify_power(p_evd, "Ловкость")

    # === [ОПТИМИЗАЦИЯ] 5. СОБЫТИЯ ON_ROLL ===
    # Заменяем ручной перебор на trigger_mechanics
    if hasattr(source, "trigger_mechanics"):
        source.trigger_mechanics("on_roll", ctx)

    process_card_scripts("on_roll", ctx)
    process_card_scripts("on_play", ctx)

    # === 6. ФИНАЛИЗАЦИЯ ЛОГА ===
    if hasattr(ctx, 'get_formatted_roll_log'):
        ctx.log.insert(0, ctx.get_formatted_roll_log())

    return ctx