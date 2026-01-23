import copy
import uuid
from typing import TYPE_CHECKING

from core.enums import DiceType
from core.logging import logger, LogLevel
from logic.scripts.utils import _check_conditions, _resolve_value, _get_targets
import streamlit as st

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
            # [CHANGE] VERBOSE -> MINIMAL
            logger.log(f"💔 Effect Dmg: {u.name} takes {amount} HP", LogLevel.MINIMAL, "Scripts")
        elif dmg_type == "stagger":
            u.current_stagger = max(0, u.current_stagger - amount)
            ctx.log.append(f"😵 **{u.name}**: -{amount} Stagger")
            # [CHANGE] VERBOSE -> MINIMAL
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
            # [CHANGE] VERBOSE -> MINIMAL
            logger.log(f"🤯 Effect SP: {u.name} takes {amount}", LogLevel.MINIMAL, "Scripts")


def nullify_hp_damage(ctx: 'RollContext', params: dict):
    """Обнуляет множитель урона, предотвращая нанесение стандартного HP урона."""
    ctx.damage_multiplier = 0.0
    logger.log(f"🚫 HP Damage Nullified for {ctx.source.name}", LogLevel.VERBOSE, "Scripts")


def self_harm_percent(ctx: 'RollContext', params: dict):
    """Наносит урон самому себе в % от Макс ХП."""
    if not _check_conditions(ctx.source, params): return
    percent = float(params.get("percent", 0.0))
    damage = int(ctx.source.max_hp * percent)

    if damage > 0:
        ctx.source.current_hp = max(0, ctx.source.current_hp - damage)
        ctx.log.append(f"🩸 **Self Harm**: -{damage} HP ({percent * 100}%)")
        # [CHANGE] VERBOSE -> MINIMAL
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
        # [CHANGE] VERBOSE -> MINIMAL
        logger.log(f"💔 Decay: {target.name} takes {damage} HP", LogLevel.MINIMAL, "Scripts")


def convert_status_to_power(ctx: 'RollContext', params: dict):
    status_id = params.get("status")
    factor = params.get("factor", 1.0)
    stack_count = ctx.source.get_status(status_id)
    if stack_count <= 0: return
    bonus = int(stack_count * factor)
    ctx.modify_power(bonus, f"Consumed {status_id.capitalize()}")
    ctx.source.remove_status(status_id, stack_count)
    logger.log(f"🔋 Converted {stack_count} {status_id} -> +{bonus} Power", LogLevel.VERBOSE, "Scripts")


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


def apply_axis_team_buff(ctx: 'RollContext', params: dict):
    """
    Накладывает 1 статус всем союзникам (КРОМЕ СЕБЯ).
    Если других союзников нет, накладывает 2 статуса СЕБЕ.
    """
    source = ctx.source
    status = params.get("status")
    duration = int(params.get("duration", 1))

    # 1. Определяем команду
    my_team = []
    if 'team_left' in st.session_state and source in st.session_state['team_left']:
        my_team = st.session_state['team_left']
    elif 'team_right' in st.session_state and source in st.session_state['team_right']:
        my_team = st.session_state['team_right']

    # 2. Ищем других живых союзников
    # (u is not source) исключает самого Аксиса
    other_allies = [u for u in my_team if u is not source and not u.is_dead()]

    if other_allies:
        # Условие: Есть союзники -> Баффаем их по 1
        for ally in other_allies:
            ally.add_status(status, 1, duration=duration)

        if ctx.log is not None:
            ctx.log.append(f"🙌 **Axis Team**: +1 {status.capitalize()} to {len(other_allies)} allies")

        logger.log(f"🙌 Axis Team Buff: Applied 1 {status} to allies of {source.name}", LogLevel.VERBOSE, "Scripts")
    else:
        # Условие: Нет союзников -> Баффаем себя на 2
        source.add_status(status, 2, duration=duration)

        if ctx.log is not None:
            ctx.log.append(f"👤 **Axis Solo**: +2 {status.capitalize()} to Self")

        logger.log(f"👤 Axis Solo Buff: Applied 2 {status} to {source.name}", LogLevel.VERBOSE, "Scripts")


def adaptive_damage_type(ctx: 'RollContext', params: dict):
    """
    Меняет тип урона (кубика или всех кубиков карты) на тот,
    к которому у цели наивысшая уязвимость (наибольший множитель резиста).
    """
    if not ctx.target: return

    # Получаем резисты цели
    res = ctx.target.hp_resists

    # Ищем максимальный множитель (Больше множитель = Больше урона = Слабость)
    # Приоритет при равенстве: Slash -> Pierce -> Blunt (можно любой)
    best_type = DiceType.SLASH
    max_mult = res.slash

    if res.pierce > max_mult:
        max_mult = res.pierce
        best_type = DiceType.PIERCE

    if res.blunt > max_mult:
        max_mult = res.blunt
        best_type = DiceType.BLUNT

    # Применяем изменение
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


def summon_ally(ctx: 'RollContext', params: dict):
    """
    Призывает копию юнита из библиотеки (Roster) на сторону кастующего.
    Параметры:
    - unit_name: Имя юнита в файле (например, "Ex Machina")
    """
    source = ctx.source
    unit_name = params.get("unit_name")

    if not unit_name:
        if ctx.log is not None: ctx.log.append("🚫 Summon Error: No unit name")
        return

    # 1. Определяем команду
    target_team_list = None
    if 'team_left' in st.session_state and source in st.session_state['team_left']:
        target_team_list = st.session_state['team_left']
    elif 'team_right' in st.session_state and source in st.session_state['team_right']:
        target_team_list = st.session_state['team_right']

    if target_team_list is None: return

    # Лимит на команду (5 юнитов)
    if len(target_team_list) >= 5:
        if ctx.log is not None: ctx.log.append("🚫 Summon Failed: Team Full")
        logger.log(f"🚫 Summon failed for {source.name}: Team is full", LogLevel.NORMAL, "Summon")
        return

    # 2. Ищем шаблон в Ростере
    roster = st.session_state.get('roster', {})
    template_unit = roster.get(unit_name)

    if not template_unit:
        # Попытка найти по частичному совпадению (если файл называется Ex_Machina.json, а имя внутри Ex Machina)
        for u in roster.values():
            if u.name == unit_name:
                template_unit = u
                break

    if not template_unit:
        if ctx.log is not None: ctx.log.append(f"🚫 Summon Error: '{unit_name}' not found")
        return

    # 3. Создаем копию
    new_unit = copy.deepcopy(template_unit)

    # Уникальное имя, чтобы не путать
    unique_suffix = str(uuid.uuid4())[:4]
    new_unit.name = f"{template_unit.name} ({unique_suffix})"

    # Инициализация боя
    new_unit.recalculate_stats()
    new_unit.current_hp = new_unit.max_hp
    new_unit.current_sp = new_unit.max_sp
    new_unit.current_stagger = new_unit.max_stagger

    new_unit.memory['start_of_battle_stats'] = {
        'hp': new_unit.max_hp,
        'sp': new_unit.max_sp,
        'stagger': new_unit.max_stagger
    }

    # 4. Добавляем в команду
    target_team_list.append(new_unit)

    msg = f"🤖 **Summon**: {new_unit.name} прибыл!"
    if ctx.log is not None: ctx.log.append(msg)
    logger.log(f"🤖 Summoned {new_unit.name} for {source.name}", LogLevel.NORMAL, "Summon")