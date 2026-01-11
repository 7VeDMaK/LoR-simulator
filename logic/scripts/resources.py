from typing import TYPE_CHECKING
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
                healed = u.heal_hp(amount)
                ctx.log.append(f"💚 **{u.name}**: +{healed} HP")
            else:
                u.current_hp = max(0, u.current_hp + amount)
                ctx.log.append(f"💔 **{u.name}**: {amount} HP")

        elif res_type == "sp":
            if amount >= 0:
                recovered = u.restore_sp(amount)
                ctx.log.append(f"🧠 **{u.name}**: +{recovered} SP")
            else:
                u.take_sanity_damage(abs(amount))
                ctx.log.append(f"🤯 **{u.name}**: {amount} SP")

        elif res_type == "stagger":
            old = u.current_stagger
            u.current_stagger = min(u.max_stagger, u.current_stagger + amount)
            diff = u.current_stagger - old
            ctx.log.append(f"🛡️ **{u.name}**: +{diff} Stagger")