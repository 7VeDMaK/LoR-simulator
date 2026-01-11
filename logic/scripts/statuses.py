from typing import TYPE_CHECKING
from logic.scripts.utils import _check_conditions, _resolve_value, _get_targets

if TYPE_CHECKING:
    from logic.context import RollContext

def apply_status(ctx: 'RollContext', params: dict):
    if not _check_conditions(ctx.source, params): return
    status_name = params.get("status")
    if not status_name: return

    target_mode = params.get("target", "target")
    duration = int(params.get("duration", 1))
    delay = int(params.get("delay", 0))
    min_roll = int(params.get("min_roll", 0))
    if min_roll > 0:
        # Check against base_value (natural roll), not final_value
        if ctx.base_value < min_roll:
            return

    # Подготовка параметров для расчета
    calc_params = params.copy()
    if "stack" in params and "base" not in params:
        calc_params["base"] = params["stack"]

    targets = _get_targets(ctx, target_mode)
    if status_name == "smoke": duration = 99

    for u in targets:
        if u.get_status("red_lycoris") > 0 and status_name != "red_lycoris":
            ctx.log.append(f"🚫 {u.name} Immune to {status_name}")
            continue

        if status_name == "mental_protection":
            current = u.get_status("mental_protection")
            if current >= 2:
                ctx.log.append(f"🧀 {u.name}: Mental Protection maxed (2)")
                continue

        # ВАЖНО: Считаем стаки для КОНКРЕТНОГО юнита u
        # Если scale_from_target=True, то стат возьмется у u
        stack = _resolve_value(ctx.source, u, calc_params)

        if stack <= 0: continue

        success, msg = u.add_status(status_name, stack, duration=duration, delay=delay)

        if success:
            if msg == "Delayed":
                ctx.log.append(f"⏰ **{u.name}**: {status_name.capitalize()} (Delayed {delay} turns)")
            else:
                ctx.log.append(f"🧪 **{u.name}**: +{stack} {status_name.capitalize()}")
        elif msg:
            ctx.log.append(f"🛡️ {msg}")


def steal_status(ctx: 'RollContext', params: dict):
    status_name = params.get("status")
    thief, victim = ctx.source, ctx.target
    if not thief or not victim: return

    current = victim.get_status(status_name)
    if current > 0:
        victim.remove_status(status_name, current)
        duration = 99 if status_name == "smoke" else 1
        thief.add_status(status_name, current, duration=duration)
        ctx.log.append(f"✋ **{thief.name}** stole {current} {status_name}")


def multiply_status(ctx: 'RollContext', params: dict):
    status_name = params.get("status")
    multiplier = float(params.get("multiplier", 2.0))
    targets = _get_targets(ctx, params.get("target", "target"))

    for u in targets:
        current = u.get_status(status_name)
        if current > 0:
            add = int(current * (multiplier - 1))
            duration = 99 if status_name == "smoke" else 1
            u.add_status(status_name, add, duration=duration)
            ctx.log.append(f"✖️ **{u.name}**: {status_name} x{multiplier} (+{add})")


def remove_status_script(ctx: 'RollContext', params: dict):
    """Снимает указанный статус с цели."""
    if not _check_conditions(ctx.source, params): return

    status_name = params.get("status")
    target_mode = params.get("target", "target")

    # Считаем количество (можно скейлить)
    amount = _resolve_value(ctx.source, ctx.target, params)

    targets = _get_targets(ctx, target_mode)

    for u in targets:
        current = u.get_status(status_name)
        if current > 0:
            to_remove = min(current, amount)
            u.remove_status(status_name, to_remove)
            ctx.log.append(f"🧹 **{u.name}**: Снято {to_remove} {status_name}")


def remove_all_positive(context: 'RollContext', params: dict):
    """Снимает все положительные эффекты."""
    target_mode = params.get("target", "self")
    targets = _get_targets(context, target_mode)

    # Список положительных статусов
    POSITIVE_BUFFS = [
        "strength", "endurance", "haste", "protection", "barrier",
        "regen_hp", "regen_ganache", "mental_protection", "clarity",
        "dmg_up", "power_up", "clash_power_up", "stagger_resist",
        "bleed_resist", "ignore_satiety"
    ]

    for u in targets:
        removed_list = []
        for buff in POSITIVE_BUFFS:
            if u.get_status(buff) > 0:
                u.remove_status(buff)  # Снимаем полностью
                removed_list.append(buff)

        if removed_list:
            context.log.append(f"🧹 **Вафли**: Снято {', '.join(removed_list)}")


def apply_status_by_roll(ctx: 'RollContext', params: dict):
    """Накладывает статус в количестве, равном выпавшему значению кубика."""
    if not _check_conditions(ctx.source, params): return
    status = params.get("status")
    target_mode = params.get("target", "self")
    amount = ctx.final_value  # Значение броска

    targets = _get_targets(ctx, target_mode)
    for u in targets:
        u.add_status(status, amount)
        ctx.log.append(f"🎲 **Roll Status**: +{amount} {status}")