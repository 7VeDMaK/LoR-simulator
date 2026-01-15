import copy
from typing import TYPE_CHECKING

from core.enums import DiceType
from logic.scripts.utils import _check_conditions, _resolve_value, _get_targets

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
        elif dmg_type == "stagger":
            u.current_stagger = max(0, u.current_stagger - amount)
            ctx.log.append(f"😵 **{u.name}**: -{amount} Stagger")
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

def nullify_hp_damage(ctx: 'RollContext', params: dict):
    """Обнуляет множитель урона, предотвращая нанесение стандартного HP урона."""
    ctx.damage_multiplier = 0.0
    # ctx.log.append("🚫 HP Damage Negated") # Можно раскомментить для дебага

def self_harm_percent(ctx: 'RollContext', params: dict):
    """Наносит урон самому себе в % от Макс ХП."""
    if not _check_conditions(ctx.source, params): return
    percent = float(params.get("percent", 0.0))
    damage = int(ctx.source.max_hp * percent)

    if damage > 0:
        ctx.source.current_hp = max(0, ctx.source.current_hp - damage)
        ctx.log.append(f"🩸 **Self Harm**: -{damage} HP ({percent * 100}%)")


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


def convert_status_to_power(ctx: 'RollContext', params: dict):
    """
    params: {
        "status": "haste",   # Какой статус поглощать
        "factor": 1.0,       # Сколько силы за 1 стак
        "max_stacks": 999    # (Опц) Лимит поглощения
    }
    """
    status_id = params.get("status")
    factor = params.get("factor", 1.0)

    # 1. Получаем текущее количество стаков у того, кто бьет (source)
    # get_status возвращает int
    stack_count = ctx.source.get_status(status_id)

    if stack_count <= 0:
        return

    # 2. Считаем бонус
    bonus = int(stack_count * factor)

    # 3. Применяем бонус к текущему броску
    ctx.modify_power(bonus, f"Consumed {status_id.capitalize()}")

    # 4. Удаляем статус (полностью или сколько поглотили)
    ctx.source.remove_status(status_id, stack_count)


# === NEW FUNCTIONS ===

def consume_evade_for_haste(ctx: 'RollContext', params: dict):
    """
    Конвертирует все запасенные кубики уклонения (Stored Evade) в статус Спешка (Haste).
    """
    unit = ctx.source
    # Проверяем, есть ли stored_dice и является ли он списком
    if not hasattr(unit, "stored_dice") or not isinstance(unit.stored_dice, list) or not unit.stored_dice:
        return

    # Фильтруем кубики
    evades = [d for d in unit.stored_dice if d.dtype == DiceType.EVADE]
    others = [d for d in unit.stored_dice if d.dtype != DiceType.EVADE]

    count = len(evades)

    if count > 0:
        # Обновляем список, удаляя уклонения
        unit.stored_dice = others

        # Накладываем статус
        unit.add_status("haste", count, duration=2)

        # Логируем (если есть куда)
        if ctx.log:
            ctx.log.append(f"⚡ **{unit.name}** consumed {count} Evades -> +{count} Haste")


def repeat_dice_by_status(ctx: 'RollContext', params: dict):
    """
    Копирует кубик карты N раз, где N = значение статуса (но не более max).
    Params:
      - status: название статуса (default: haste)
      - max: лимит повторений (default: 4)
      - die_index: индекс кубика для копирования (default: 0)
    """
    unit = ctx.source
    card = unit.current_card

    if not card: return

    status_name = params.get("status", "haste")
    limit = int(params.get("max", 4))
    die_idx = int(params.get("die_index", 0))

    val = unit.get_status(status_name)
    count = min(val, limit)

    # Проверяем, что есть что копировать
    if count > 0 and card.dice_list and len(card.dice_list) > die_idx:
        base_die = card.dice_list[die_idx]

        new_dice = []
        for _ in range(count):
            # Важно делать глубокую копию, чтобы скрипты на кубике были независимы
            new_dice.append(copy.deepcopy(base_die))

        # Добавляем кубики в конец карты
        card.dice_list.extend(new_dice)

        if ctx.log:
            ctx.log.append(f"♻️ **{unit.name}** repeats dice {count} times (Status: {status_name})")

def lima_ram_logic(ctx: 'RollContext', params: dict):
    """
    Логика карты Таран:
    Бонус = f(Haste) * (Level / 3).
    Снимает всю спешку.
    """
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

    # Множитель уровня
    # Используем integer деление, чтобы избежать float
    lvl_mult = int(unit.level / 3)

    final_bonus = base_bonus * lvl_mult

    if final_bonus > 0:
        ctx.modify_power(final_bonus, f"Ram (Haste {haste} * Lvl {unit.level}/3)")

    # Снимаем всю спешку
    if haste > 0:
        unit.remove_status("haste", 999)
        if ctx.log:
            ctx.log.append(f"📉 **{unit.name}** consumed all Haste")

