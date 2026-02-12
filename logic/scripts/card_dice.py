import copy
from typing import TYPE_CHECKING

from core.dice import Dice
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


def break_target_dice(ctx: 'RollContext', params: dict):
    """
    Ломает текущий кубик оппонента (например, при победе в Clash).
    params:
        "probability": 1.0 (шанс срабатывания)
    """
    # Проверяем, есть ли контекст оппонента (это бывает только в Clash)
    if ctx.opponent_ctx and ctx.opponent_ctx.dice:
        ctx.opponent_ctx.dice.is_broken = True
        ctx.log.append("💥 **Break**: Кубик врага сломан!")
        logger.log(f"💥 Target Dice Broken by {ctx.source.name}", LogLevel.VERBOSE, "Scripts")


def add_preset_dice(ctx: 'RollContext', params: dict):
    """
    Добавляет в карту новые кубики, описанные в JSON.
    Params:
      - dice: list of dicts [{"min": 4, "max": 8, "type": "Slash"}, ...]
    """
    card = ctx.source.current_card
    if not card: return

    dice_defs = params.get("dice", [])

    added_count = 0
    for d_def in dice_defs:
        min_v = d_def.get("min", 1)
        max_v = d_def.get("max", 1)
        dtype_str = d_def.get("type", "Slash").upper()

        # Преобразуем строку в Enum
        try:
            dtype = DiceType[dtype_str]
        except KeyError:
            dtype = DiceType.SLASH

        new_die = Dice(min_v, max_v, dtype)
        card.dice_list.append(new_die)
        added_count += 1

    if added_count > 0 and ctx.log:
        ctx.log.append(f"🎲 **Bonus**: Added {added_count} extra dice!")


def unity_chain_reaction(ctx: 'RollContext', params: dict):
    """
    Unity: Реализует механику цепной реакции.
    1. Добавляет в текущую карту все кубики, сохраненные в цепи ранее в этом ходу.
    2. Сохраняет первый "родной" кубик этой карты в цепь для следующих карт.
    """
    unit = ctx.source
    card = unit.current_card
    if not card or not card.dice_list:
        return

    # Инициализация памяти цепи, если её нет
    if "unity_chain" not in unit.memory:
        unit.memory["unity_chain"] = []

    # 1. ЗАПОМИНАЕМ РОДНОЙ КУБИК (До модификаций)
    # Берем первый кубик карты как "вклад" в общее дело.
    # Важно сделать глубокую копию сейчас, пока мы не добавили в начало чужие кубики.
    original_die = card.dice_list[0]
    die_to_store = copy.deepcopy(original_die)

    # 2. ЗАБИРАЕМ КУБИКИ ИЗ ПАМЯТИ (Наследие)
    chain_dice = unit.memory["unity_chain"]

    if chain_dice:
        # Создаем копии накопленных кубиков
        inherited_dice = [copy.deepcopy(d) for d in chain_dice]

        # Вставляем их в НАЧАЛО списка кубиков карты
        # Теперь порядок: [Наследие А], [Наследие Б], [Родной куб], [Родной куб 2]...
        card.dice_list[0:0] = inherited_dice

        if ctx.log:
            ctx.log.append(f"🔗 **Unity**: Активирована цепь! Добавлено {len(inherited_dice)} кубиков.")

    # 3. ОБНОВЛЯЕМ ПАМЯТЬ (Для следующих карт)
    # Добавляем наш родной кубик в конец цепи
    unit.memory["unity_chain"].append(die_to_store)