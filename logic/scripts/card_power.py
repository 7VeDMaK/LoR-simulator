from typing import TYPE_CHECKING

from core.logging import logger, LogLevel
from logic.scripts.utils import _check_conditions, _resolve_value

if TYPE_CHECKING:
    from logic.context import RollContext


def modify_roll_power(ctx: 'RollContext', params: dict):
    if not _check_conditions(ctx.source, params): return
    amount = _resolve_value(ctx.source, ctx.target, params)
    if amount == 0: return

    reason = params.get("reason", "Bonus")
    if reason == "Bonus" and params.get("stat"):
        reason = f"{params['stat'].title()} scale"

    ctx.modify_power(amount, reason)
    logger.log(f"Modify Power: {amount} ({reason}) for {ctx.source.name}", LogLevel.VERBOSE, "Scripts")


def convert_status_to_power(ctx: 'RollContext', params: dict):
    status_id = params.get("status")
    factor = params.get("factor", 1.0)
    stack_count = ctx.source.get_status(status_id)
    if stack_count <= 0: return
    bonus = int(stack_count * factor)
    ctx.modify_power(bonus, f"Consumed {status_id.capitalize()}")
    ctx.source.remove_status(status_id, stack_count)
    logger.log(f"🔋 Converted {stack_count} {status_id} -> +{bonus} Power", LogLevel.VERBOSE, "Scripts")


def lima_ram_logic(ctx: 'RollContext', params: dict):
    unit = ctx.source
    haste = unit.get_status("haste")
    base_bonus = 0
    if haste >= 20:
        base_bonus = 5
    elif haste >= 14:
        base_bonus = 4
    elif haste >= 9:
        base_bonus = 3
    elif haste >= 5:
        base_bonus = 2
    elif haste >= 2:
        base_bonus = 1
    lvl_mult = int(unit.level / 3)
    final_bonus = base_bonus * lvl_mult
    if final_bonus > 0:
        ctx.modify_power(final_bonus, f"Ram (Haste {haste} * Lvl {unit.level}/3)")
    if haste > 0:
        unit.remove_status("haste", 999)
        if ctx.log: ctx.log.append(f"📉 **{unit.name}** consumed all Haste")
        logger.log(f"📉 Ram Logic: {final_bonus} Power, Haste Consumed", LogLevel.VERBOSE, "Scripts")


def apply_card_power_bonus(ctx: 'RollContext', params: dict):
    unit = ctx.source
    card = unit.current_card if unit else None
    if not unit or not card:
        return

    if unit.memory.get("card_power_bonus_card_id") != card.id:
        return

    base = int(unit.memory.get("card_power_bonus_base", 0))
    mult = int(unit.memory.get("card_power_bonus_mult", 1))
    reason = unit.memory.get("card_power_bonus_reason", params.get("reason", "Bonus"))

    bonus = int(base * mult)
    if bonus == 0:
        return

    ctx.modify_power(bonus, reason)
    logger.log(
        f"Modify Power (Card Bonus): +{bonus} {reason} for {unit.name}",
        LogLevel.VERBOSE,
        "Scripts"
    )


def set_card_power_multiplier(ctx: 'RollContext', params: dict):
    unit = ctx.source
    card = unit.current_card if unit else None
    if not unit or not card:
        return

    condition = params.get("condition", "")
    if condition in ["last_clash_win", "last_clash_lose", "last_clash_draw"]:
        if not unit.memory.get(condition):
            if ctx.log is not None:
                ctx.log.append(f"⚠️ Power Mult not triggered ({condition})")
            return
        unit.memory[condition] = False

    mult = float(params.get("multiplier", 2.0))
    if mult <= 1.0:
        return

    reason = params.get("reason", "Power Mult")

    unit.memory["card_power_mult_card_id"] = card.id
    unit.memory["card_power_mult"] = mult
    unit.memory["card_power_mult_reason"] = reason

    if ctx.log is not None:
        ctx.log.append(f"⚔️ Power Mult: {card.name} x{mult:.2f}")
    logger.log(
        f"⚔️ Card Power Mult: {unit.name} {card.id} mult={mult:.2f}",
        LogLevel.VERBOSE,
        "Scripts"
    )


def apply_card_power_multiplier(ctx: 'RollContext', params: dict):
    unit = ctx.source
    card = unit.current_card if unit else None
    if not unit or not card:
        return

    if unit.memory.get("card_power_mult_card_id") != card.id:
        return

    mult = float(unit.memory.get("card_power_mult", 1.0))
    if mult <= 1.0:
        return

    reason = unit.memory.get("card_power_mult_reason", params.get("reason", "Power Mult"))

    base_val = ctx.final_value
    bonus = int(base_val * (mult - 1.0))
    if bonus == 0:
        return

    ctx.modify_power(bonus, reason)
    logger.log(
        f"Modify Power (Card Mult): x{mult:.2f} for {unit.name}",
        LogLevel.VERBOSE,
        "Scripts"
    )


def multiply_roll_power(ctx: 'RollContext', params: dict):
    if not _check_conditions(ctx.source, params):
        return

    mult = float(params.get("multiplier", 2.0))
    if mult <= 1.0:
        return

    base_val = ctx.final_value
    bonus = int(base_val * (mult - 1.0))
    if bonus == 0:
        return

    reason = params.get("reason", f"Power x{mult:.2f}")
    ctx.modify_power(bonus, reason)
    logger.log(
        f"Modify Power (Multiply): x{mult:.2f} for {ctx.source.name}",
        LogLevel.VERBOSE,
        "Scripts"
    )