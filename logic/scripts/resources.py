from typing import TYPE_CHECKING

from core.logging import logger, LogLevel
from logic.scripts.utils import _check_conditions, _resolve_value, _get_targets

if TYPE_CHECKING:
    from logic.context import RollContext

def restore_resource(ctx: 'RollContext', params: dict):
    if not _check_conditions(ctx.source, params): return
    res_type = params.get("type", "hp")
    targets = _get_targets(ctx, params.get("target", "self"))

    for u in targets:
        # Считаем лечение индивидуально (например 25% от Макс ХП цели)
        amount = _resolve_value(ctx.source, u, params)

        if res_type == "hp":
            if amount >= 0:
                healed = u.heal_hp(amount, source=ctx.source)
                ctx.log.append(f"💚 **{u.name}**: +{healed} HP")
                logger.log(f"💚 Healed {u.name} for {healed} HP", LogLevel.VERBOSE, "Scripts")
            else:
                u.current_hp = max(0, u.current_hp + amount)
                ctx.log.append(f"💔 **{u.name}**: {amount} HP")
                logger.log(f"💔 Drained {u.name} for {abs(amount)} HP", LogLevel.VERBOSE, "Scripts")

        elif res_type == "sp":
            if amount >= 0:
                recovered = u.restore_sp(amount, source=ctx.source)
                ctx.log.append(f"🧠 **{u.name}**: +{recovered} SP")
                logger.log(f"🧠 Restored {u.name} for {recovered} SP", LogLevel.VERBOSE, "Scripts")
            else:
                u.take_sanity_damage(abs(amount))
                ctx.log.append(f"🤯 **{u.name}**: {amount} SP")
                logger.log(f"🤯 Drained {u.name} for {abs(amount)} SP", LogLevel.VERBOSE, "Scripts")

        elif res_type == "stagger":
            old = u.current_stagger
            u.current_stagger = min(u.max_stagger, u.current_stagger + amount)
            diff = u.current_stagger - old
            ctx.log.append(f"🛡️ **{u.name}**: +{diff} Stagger")
            logger.log(f"🛡️ Restored {u.name} for {diff} Stagger", LogLevel.VERBOSE, "Scripts")


def restore_resource_by_roll(ctx: 'RollContext', params: dict):
    """
    Восстанавливает ресурс в зависимости от значения броска.
    params: { "type": "hp", "target": "self", "factor": 1.0 }
    """
    from logic.scripts.utils import _get_targets

    res_type = params.get("type", "hp")
    factor = float(params.get("factor", 1.0))
    targets = _get_targets(ctx, params.get("target", "self"))

    amount = int(ctx.final_value * factor)
    if amount <= 0: return

    for u in targets:
        if res_type == "hp":
            healed = u.heal_hp(amount, source=ctx.source)
            if ctx.log is not None:
                ctx.log.append(f"💚 **Roll Heal**: {u.name} +{healed} HP")
        elif res_type == "sp":
            recovered = u.restore_sp(amount)
            if ctx.log is not None:
                ctx.log.append(f"🧠 **Roll SP**: {u.name} +{recovered} SP")