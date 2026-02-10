from typing import TYPE_CHECKING

from core.logging import logger, LogLevel
from logic.scripts.utils import _check_conditions, _resolve_value, _get_targets

if TYPE_CHECKING:
    from logic.context import RollContext


def deal_effect_damage(ctx: 'RollContext', params: dict):
    if not _check_conditions(ctx.source, params): return

    dmg_type = params.get("type", "hp")
    targets = _get_targets(ctx, params.get("target", "target"))

    stat_key = params.get("stat", "None")

    for u in targets:
        if stat_key == "roll":
            # Берем значение броска
            base = int(params.get("base", 0))
            factor = float(params.get("factor", 1.0))
            amount = int(base + (ctx.final_value * factor))
        else:
            # Стандартный резолв от статов
            amount = _resolve_value(ctx.source, u, params)

        if amount <= 0: continue

        if dmg_type == "hp":
            u.current_hp = max(0, u.current_hp - amount)
            ctx.log.append(f"💔 **{u.name}**: -{amount} HP (Effect)")
            logger.log(f"💔 Effect Dmg: {u.name} takes {amount} HP", LogLevel.MINIMAL, "Scripts")
        elif dmg_type == "stagger":
            u.current_stagger = max(0, u.current_stagger - amount)
            ctx.log.append(f"😵 **{u.name}**: -{amount} Stagger")
            logger.log(f"😵 Effect Stagger: {u.name} takes {amount}", LogLevel.MINIMAL, "Scripts")
        elif dmg_type == "sp":
            # Логика Эдама (Mental Protection)
            ment_prot = u.get_status("mental_protection")
            if ment_prot > 0:
                pct_red = min(0.50, ment_prot * 0.25)
                reduction = int(amount * pct_red)
                amount -= reduction
                ctx.log.append(f"🧀 **Edam**: Blocked {reduction} SP dmg")

            u.take_sanity_damage(amount)
            ctx.log.append(f"🤯 **{u.name}**: -{amount} SP")
            logger.log(f"🤯 Effect SP: {u.name} takes {amount}", LogLevel.MINIMAL, "Scripts")


def nullify_hp_damage(ctx: 'RollContext', params: dict):
    """Обнуляет множитель урона, предотвращая нанесение стандартного HP урона."""
    ctx.damage_multiplier = 0.0
    logger.log(f"🚫 HP Damage Nullified for {ctx.source.name}", LogLevel.VERBOSE, "Scripts")


def multiply_damage(ctx: 'RollContext', params: dict):
    """Умножает итоговый урон (HP) без изменения броска."""
    if not _check_conditions(ctx.source, params):
        return

    mult = float(params.get("multiplier", 2.0))
    if mult <= 0:
        return

    ctx.damage_multiplier *= mult
    if ctx.log is not None:
        ctx.log.append(f"💥 Damage x{mult:.2f}")
    logger.log(
        f"💥 Damage multiplied x{mult:.2f} for {ctx.source.name}",
        LogLevel.VERBOSE,
        "Scripts"
    )


def self_harm_percent(ctx: 'RollContext', params: dict):
    """Наносит урон самому себе в % от Макс ХП."""
    if not _check_conditions(ctx.source, params): return
    percent = float(params.get("percent", 0.0))
    damage = int(ctx.source.max_hp * percent)

    if damage > 0:
        ctx.source.current_hp = max(0, ctx.source.current_hp - damage)
        ctx.log.append(f"🩸 **Self Harm**: -{damage} HP ({percent * 100}%)")
        logger.log(f"🩸 Self Harm: {ctx.source.name} takes {damage} HP", LogLevel.MINIMAL, "Scripts")


def add_hp_damage(ctx: 'RollContext', params: dict):
    """Наносит дополнительный урон цели в % от её Макс ХП."""
    if not _check_conditions(ctx.source, params): return
    target = ctx.target
    if not target: return

    percent = float(params.get("percent", 0.0))
    damage = int(target.max_hp * percent)

    if damage > 0:
        target.current_hp = max(0, target.current_hp - damage)
        ctx.log.append(f"💔 **Decay**: -{damage} HP ({percent * 100}%)")
        logger.log(f"💔 Decay: {target.name} takes {damage} HP", LogLevel.MINIMAL, "Scripts")


def deal_damage_by_roll(ctx: 'RollContext', params: dict):
    """
    Наносит урон (HP/Stagger) равный значению броска.
    params: { "target": "self", "type": "hp" }
    """
    from logic.scripts.utils import _get_targets

    target_mode = params.get("target", "self")
    dmg_type = params.get("type", "hp")
    targets = _get_targets(ctx, target_mode)
    amount = ctx.final_value  # Значение броска

    if amount <= 0: return

    for u in targets:
        if dmg_type == "hp":
            u.take_damage(amount)
            if ctx.log is not None:
                ctx.log.append(f"🩸 **Roll Dmg**: {u.name} takes {amount} HP")
        elif dmg_type == "stagger":
            u.take_damage(amount, damage_type="stagger")  # Предполагаем наличие метода или меняем поле напрямую
            # Если метода нет: u.current_stagger = max(0, u.current_stagger - amount)
            if ctx.log is not None:
                ctx.log.append(f"😵 **Roll Stagger**: {u.name} takes {amount} Stagger")


def deal_damage_by_clash_diff(ctx: 'RollContext', params: dict):
    """
    Наносит урон, равный разнице в клэше.
    params: { "target": "self" }
    """
    from logic.scripts.utils import _get_targets

    # 1. Вычисляем разницу
    diff = getattr(ctx, "clash_diff", 0)
    if diff == 0 and hasattr(ctx, "target_die_result"):
        diff = max(0, ctx.final_value - ctx.target_die_result)

    if diff <= 0: return

    # 2. Наносим урон
    targets = _get_targets(ctx, params.get("target", "self"))
    for u in targets:
        u.take_damage(diff)
        if ctx.log is not None:
            ctx.log.append(f"⚖️ **Clash Diff**: {u.name} takes {diff} damage!")