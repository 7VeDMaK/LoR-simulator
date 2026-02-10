from core.logging import logger, LogLevel
from logic.context import RollContext
# Импортируем логику из новых файлов
from logic.mechanics.rolling.rolling_calc import calculate_base_roll, apply_roll_modifiers
from logic.mechanics.scripts import process_card_scripts


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
    roll, base_val, log_prefix, final_is_disadvantage = calculate_base_roll(
        source, base_min, base_max, is_disadvantage
    )

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
        logger.log("🔒 Roll is Unchangeable", LogLevel.VERBOSE, "Roll")

        process_card_scripts("on_roll", ctx)
        process_card_scripts("on_play", ctx)
        if hasattr(ctx, 'get_formatted_roll_log'):
            ctx.log.insert(0, ctx.get_formatted_roll_log())
        return ctx

    # === 4. МОДИФИКАТОРЫ (ОБНОВЛЕНО) ===
    # Вынесено в rolling_calc.py
    apply_roll_modifiers(ctx, source, die)

    if hasattr(source, "trigger_mechanics"):
        source.trigger_mechanics("on_roll", ctx)

    process_card_scripts("on_roll", ctx)
    process_card_scripts("on_play", ctx)

    # === 6. ФИНАЛИЗАЦИЯ ЛОГА ===
    if hasattr(ctx, 'get_formatted_roll_log'):
        formula_text = ctx.get_formatted_roll_log()
        ctx.log.insert(0, formula_text)
        logger.log(f"🎲 Final: {ctx.final_value} ({formula_text})", LogLevel.VERBOSE, "Roll")

    return ctx