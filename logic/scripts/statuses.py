import random
from typing import TYPE_CHECKING

from core.logging import logger, LogLevel
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
        # Проверка по базовому броску (натуральному)
        if ctx.base_value < min_roll:
            logger.log(f"Apply Status {status_name} failed: Roll {ctx.base_value} < {min_roll}", LogLevel.VERBOSE,
                       "Scripts")
            return

    # Подготовка параметров для расчета
    calc_params = params.copy()
    if "stack" in params and "base" not in params:
        calc_params["base"] = params["stack"]

    targets = _get_targets(ctx, target_mode)
    if status_name == "smoke": duration = 99

    # [FIX] Импортируем список негативных статусов для проверки
    from logic.statuses.status_constants import NEGATIVE_STATUSES

    for u in targets:
        # [FIX] Ликорис блокирует ТОЛЬКО негативные статусы
        if u.get_status("red_lycoris") > 0 and status_name in NEGATIVE_STATUSES:
            ctx.log.append(f"🚫 {u.name} Immune to {status_name} (Lycoris)")
            continue

        if status_name == "mental_protection":
            current = u.get_status("mental_protection")
            if current >= 2:
                ctx.log.append(f"🧀 {u.name}: Mental Protection maxed (2)")
                continue

        # ВАЖНО: Считаем стаки для КОНКРЕТНОГО юнита u
        stack = _resolve_value(ctx.source, u, calc_params)

        if stack <= 0: continue

        success, msg = u.add_status(status_name, stack, duration=duration, delay=delay)

        if success:
            if msg == "Delayed":
                ctx.log.append(f"⏰ **{u.name}**: {status_name.capitalize()} (Delayed {delay} turns)")
                logger.log(f"⏰ Status Delayed: {status_name} on {u.name} for {delay}t", LogLevel.VERBOSE, "Scripts")
            else:
                ctx.log.append(f"🧪 **{u.name}**: +{stack} {status_name.capitalize()}")
                logger.log(f"🧪 Applied {stack} {status_name} to {u.name}", LogLevel.VERBOSE, "Scripts")
        elif msg:
            ctx.log.append(f"🛡️ {msg}")
            logger.log(f"🛡️ Status Blocked: {msg}", LogLevel.VERBOSE, "Scripts")


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
        logger.log(f"✋ {thief.name} stole {current} {status_name} from {victim.name}", LogLevel.VERBOSE, "Scripts")


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
            logger.log(f"✖️ Multiplied {status_name} on {u.name} by {multiplier}", LogLevel.VERBOSE, "Scripts")


def remove_status_script(ctx: 'RollContext', params: dict):
    """Снимает указанный статус с цели."""
    if not _check_conditions(ctx.source, params): return

    status_name = params.get("status")
    target_mode = params.get("target", "target")

    amount = _resolve_value(ctx.source, ctx.target, params)

    targets = _get_targets(ctx, target_mode)

    for u in targets:
        current = u.get_status(status_name)
        if current > 0:
            to_remove = min(current, amount)
            u.remove_status(status_name, to_remove)

            ctx.log.append(f"🧹 **{u.name}**: Снято {to_remove} {status_name}")
            logger.log(f"🧹 Removed {to_remove} {status_name} from {u.name}", LogLevel.VERBOSE, "Scripts")


def remove_all_positive(context: 'RollContext', params: dict):
    """Снимает все положительные эффекты."""
    target_mode = params.get("target", "self")
    targets = _get_targets(context, target_mode)

    # Список положительных статусов
    POSITIVE_BUFFS = [
        "attack_power_up", "endurance", "haste", "protection", "barrier",
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
            logger.log(f"🧹 Removed positive buffs from {u.name}: {removed_list}", LogLevel.NORMAL, "Scripts")


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
        logger.log(f"🎲 Applied {amount} {status} (Roll-based) to {u.name}", LogLevel.VERBOSE, "Scripts")


def remove_random_status(ctx: 'RollContext', params: dict):
    """Снимает случайный статус с цели, игнорируя уникальные."""
    target = ctx.target
    if not target or not hasattr(target, "statuses"): return

    status_dict = target.statuses
    if not status_dict: return

    # Список статусов, которые нельзя снимать (уникальные, ресурсы, механики)
    IGNORED_STATUSES = [
        "slot_lock",  # Механика карты
        "adaptation",  # Уникальный статус (Хаски/Рейн)
        "red_lycoris",  # Уникальный статус
        "ammo",  # Ресурс
        "charge",  # Ресурс
        "bullet_time",  # Спец. эффект (Лима)
        "no_glasses",  # Спец. эффект (Лима)
        "mental_protection"  # Защита Эдама
    ]

    # Фильтруем статусы
    active_statuses = [s for s in status_dict.keys() if s not in IGNORED_STATUSES]

    if not active_statuses: return

    chosen_status = random.choice(active_statuses)
    amount = int(params.get("amount", 1))

    target.remove_status(chosen_status, amount)

    if ctx.log is not None:
        ctx.log.append(f"🧪 **Purge**: Снято {amount} {chosen_status} с {target.name}")
        logger.log(f"🧪 Random Purge: Removed {amount} {chosen_status} from {target.name}", LogLevel.VERBOSE, "Scripts")


def apply_slot_debuff(ctx: 'RollContext', params: dict):
    """Накладывает дебафф на количество слотов."""
    target = ctx.target
    if not target: return

    duration = int(params.get("duration", 1))
    # Накладываем статус "slot_lock"
    target.add_status("slot_lock", 1, duration=duration)

    if ctx.log:
        ctx.log.append(f"🔒 **Purge**: {target.name} will lose 1 Slot next turn")
        logger.log(f"🔒 Slot Lock applied to {target.name} for {duration} turns", LogLevel.NORMAL, "Scripts")


def consume_status_apply(ctx: 'RollContext', params: dict):
    """
    Если у цели есть статус X, снимает его и накладывает статус(ы) Y.
    Поддерживает наложение нескольких статусов сразу (списком).
    """
    target = ctx.target
    if not target: return

    req_status = params.get("consume_status")
    req_amount = int(params.get("consume_amount", 1))

    current_val = target.get_status(req_status)

    if current_val >= req_amount:
        # 1. Снимаем статус (Плата)
        target.remove_status(req_status, req_amount)
        if ctx.log:
            ctx.log.append(f"🌀 Consumed {req_amount} {req_status} from {target.name}")

        # 2. Определяем, что накладывать (один статус или список)
        raw_apply = params.get("apply_status")
        # Превращаем в список, даже если это одна строка
        apply_stats_list = raw_apply if isinstance(raw_apply, list) else [raw_apply]

        apply_amt = int(params.get("apply_amount", 1))
        apply_dur = int(params.get("duration", 1))

        # Выбор целей
        from logic.scripts.utils import _get_targets
        dest_mode = params.get("apply_target", "target")
        destinations = _get_targets(ctx, dest_mode)

        if dest_mode == "all_allies":
            destinations = [u for u in destinations if u != ctx.source]

        # 3. Накладываем ВСЕ статусы из списка
        for stat in apply_stats_list:
            if not stat: continue  # защита от пустых строк
            for u in destinations:
                u.add_status(stat, apply_amt, duration=apply_dur)
                if ctx.log:
                    ctx.log.append(f"✨ Effect: +{apply_amt} {stat.capitalize()} to {u.name}")

        from core.logging import logger, LogLevel
        logger.log(f"Conditional Effect: {req_status} -> {apply_stats_list}", LogLevel.VERBOSE, "Scripts")