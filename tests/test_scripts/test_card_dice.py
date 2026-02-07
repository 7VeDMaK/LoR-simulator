import copy
from typing import TYPE_CHECKING

from core.enums import DiceType
from core.logging import logger, LogLevel

if TYPE_CHECKING:
    from logic.context import RollContext


def consume_evade_for_haste(ctx: 'RollContext', params: dict):
    unit = ctx.source
    if not hasattr(unit, "stored_dice") or not isinstance(unit.stored_dice, list) or not unit.stored_dice: return
    evades = [d for d in unit.stored_dice if d.dtype == DiceType.EVADE]
    others = [d for d in unit.stored_dice if d.dtype != DiceType.EVADE]
    count = len(evades)
    if count > 0:
        unit.stored_dice = others
        unit.add_status("haste", count, duration=1)
        if ctx.log: ctx.log.append(f"⚡ **{unit.name}** consumed {count} Evades -> +{count} Haste")
        logger.log(f"⚡ Consumed {count} Evades -> Haste", LogLevel.VERBOSE, "Scripts")


def repeat_dice_by_status(ctx: 'RollContext', params: dict):
    unit = ctx.source
    card = unit.current_card
    if not card: return
    status_name = params.get("status", "haste")
    limit = int(params.get("max", 4))
    die_idx = int(params.get("die_index", 0))
    val = unit.get_status(status_name)
    count = min(val, limit)
    if count > 0 and card.dice_list and len(card.dice_list) > die_idx:
        base_die = card.dice_list[die_idx]
        new_dice = []
        for _ in range(count):
            new_dice.append(copy.deepcopy(base_die))
        card.dice_list.extend(new_dice)
        if ctx.log: ctx.log.append(f"♻️ **{unit.name}** repeats dice {count} times (Status: {status_name})")
        logger.log(f"♻️ Dice Repeated {count} times due to {status_name}", LogLevel.VERBOSE, "Scripts")


def adaptive_damage_type(ctx: 'RollContext', params: dict):
    """
    Меняет тип урона (кубика или всех кубиков карты) на тот,
    к которому у цели наивысшая уязвимость.
    """
    if not ctx.target: return

    # Получаем резисты цели
    res = ctx.target.hp_resists

    # Ищем максимальный множитель (Больше множитель = Больше урона = Слабость)
    best_type = DiceType.SLASH
    max_mult = res.slash

    if res.pierce > max_mult:
        max_mult = res.pierce
        best_type = DiceType.PIERCE

    if res.blunt > max_mult:
        max_mult = res.blunt
        best_type = DiceType.BLUNT

    applied = False

    # 1. Если вызвано на конкретном кубике (on_roll)
    if ctx.dice:
        if ctx.dice.dtype != best_type:
            ctx.dice.dtype = best_type
            applied = True

    # 2. Если вызвано на карте (on_use), меняем все кубики карты
    elif ctx.source.current_card:
        for d in ctx.source.current_card.dice_list:
            if d.dtype != best_type:
                d.dtype = best_type
                applied = True

    if applied:
        msg = f"🔄 **Adaptive**: Dmg Type -> {best_type.name} (Res: {max_mult}x)"
        if ctx.log is not None:
            ctx.log.append(msg)
        logger.log(f"🔄 Adaptive: Switched to {best_type.name} vs {ctx.target.name}", LogLevel.VERBOSE, "Scripts")