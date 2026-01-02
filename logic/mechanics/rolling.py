import random
from core.enums import DiceType
from logic.context import RollContext
from logic.statuses.status_manager import STATUS_REGISTRY
from logic.passives import PASSIVE_REGISTRY
from logic.talents import TALENT_REGISTRY
from logic.mechanics.scripts import process_card_scripts
# Импортируем функцию для чтения новой структуры модов
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

    # === 1. БАЗОВЫЙ БРОСОК (Advantage / Disadvantage) ===
    has_advantage = source.get_status("advantage") > 0
    roll = 0
    base_val = 0
    log_prefix = ""

    # Флаг итоговой помехи для контекста
    final_is_disadvantage = False

    if is_disadvantage and has_advantage:
        # Взаимопоглощение -> Обычный бросок
        roll = safe_randint(die.min_val, die.max_val)
        base_val = roll
        log_prefix = "⚖️ **Advantage + Disadvantage** -> Normal"
        source.remove_status("advantage", 1)

    elif is_disadvantage:
        # Помеха (Худший из 2)
        r1 = safe_randint(die.min_val, die.max_val)
        r2 = safe_randint(die.min_val, die.max_val)
        roll = min(r1, r2)
        base_val = roll
        log_prefix = f"📉 **Помеха!** ({r1}, {r2})"
        final_is_disadvantage = True

    elif has_advantage:
        # Преимущество (Лучший из 2)
        r1 = safe_randint(die.min_val, die.max_val)
        r2 = safe_randint(die.min_val, die.max_val)
        roll = max(r1, r2)
        base_val = roll
        log_prefix = f"🍀 **Преимущество!** ({r1}, {r2})"
        source.remove_status("advantage", 1)

    else:
        # Обычный
        roll = safe_randint(die.min_val, die.max_val)
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

    # === 2. НЕИЗМЕНЯЕМОСТЬ ===
    if source.current_card and "unchangeable" in source.current_card.flags:
        ctx.log.append("🔒 Unchangeable (Mods ignored)")
        process_card_scripts("on_roll", ctx)
        process_card_scripts("on_play", ctx)
        if hasattr(ctx, 'get_formatted_roll_log'):
            ctx.log.insert(0, ctx.get_formatted_roll_log())
        return ctx

    # === 3. МОДИФИКАТОРЫ (ОБНОВЛЕНО) ===
    mods = source.modifiers

    # Атака
    if die.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
        # Общая сила (от стата Strength)
        p_atk = get_modded_value(0, "power_attack", mods)
        if p_atk: ctx.modify_power(p_atk, "Сила")

        # === ИСПРАВЛЕНИЕ: БОНУС ОРУЖИЯ ===
        # Определяем тип текущего оружия
        current_weapon_id = getattr(source, "weapon_id", "none")
        weapon_type = "light"  # По дефолту (кулаки)

        if current_weapon_id in WEAPON_REGISTRY:
            weapon_type = WEAPON_REGISTRY[current_weapon_id].weapon_type

        # Карта маппинга типа оружия на ключ модификатора
        # Эти ключи заполняются в formulas.py -> apply_skill_effects
        type_to_mod = {
            "light": "power_light",  # Навык Легкого оружия
            "medium": "power_medium",  # Навык Среднего оружия
            "heavy": "power_heavy",  # Навык Тяжелого оружия
            "ranged": "power_ranged"  # Навык Огнестрела
        }

        target_mod_key = type_to_mod.get(weapon_type, "power_light")

        # Берем значение только ОДНОГО нужного навыка
        w_bonus = get_modded_value(0, target_mod_key, mods)

        if w_bonus != 0:
            # Красивое название для лога
            ru_names = {
                "light": "Легкое ор.",
                "medium": "Среднее ор.",
                "heavy": "Тяжелое ор.",
                "ranged": "Огнестрел"
            }
            reason = ru_names.get(weapon_type, "Оружие")
            ctx.modify_power(w_bonus, reason)
        # =================================

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

    # === 4. СОБЫТИЯ ON_ROLL ===
    for status_id, stack in list(source.statuses.items()):
        if status_id in STATUS_REGISTRY: STATUS_REGISTRY[status_id].on_roll(ctx, stack)

    for pid in source.passives:
        if pid in PASSIVE_REGISTRY: PASSIVE_REGISTRY[pid].on_roll(ctx)

    if source.weapon_id in WEAPON_REGISTRY:
        wep = WEAPON_REGISTRY[source.weapon_id]
        if wep.passive_id and wep.passive_id in PASSIVE_REGISTRY:
            PASSIVE_REGISTRY[wep.passive_id].on_roll(ctx)

    for pid in source.talents:
        if pid in TALENT_REGISTRY: TALENT_REGISTRY[pid].on_roll(ctx)

    process_card_scripts("on_roll", ctx)
    process_card_scripts("on_play", ctx)

    # === 5. ФИНАЛИЗАЦИЯ ЛОГА ===
    if hasattr(ctx, 'get_formatted_roll_log'):
        ctx.log.insert(0, ctx.get_formatted_roll_log())

    return ctx