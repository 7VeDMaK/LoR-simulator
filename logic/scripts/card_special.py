import copy
import uuid
from typing import TYPE_CHECKING

import streamlit as st

from core.logging import logger, LogLevel

if TYPE_CHECKING:
    from logic.context import RollContext


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
    other_allies = [u for u in my_team if u is not source and not u.is_dead()]

    if other_allies:
        for ally in other_allies:
            ally.add_status(status, 1, duration=duration)

        if ctx.log is not None:
            ctx.log.append(f"🙌 **Axis Team**: +1 {status.capitalize()} to {len(other_allies)} allies")
        logger.log(f"🙌 Axis Team Buff: Applied 1 {status} to allies of {source.name}", LogLevel.VERBOSE, "Scripts")
    else:
        source.add_status(status, 2, duration=duration)
        if ctx.log is not None:
            ctx.log.append(f"👤 **Axis Solo**: +2 {status.capitalize()} to Self")
        logger.log(f"👤 Axis Solo Buff: Applied 2 {status} to {source.name}", LogLevel.VERBOSE, "Scripts")


def summon_ally(ctx: 'RollContext', params: dict):
    """
    Призывает копию юнита из библиотеки (Roster) на сторону кастующего.
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
        for u in roster.values():
            if u.name == unit_name:
                template_unit = u
                break

    if not template_unit:
        if ctx.log is not None: ctx.log.append(f"🚫 Summon Error: '{unit_name}' not found")
        return

    # 3. Создаем копию
    new_unit = copy.deepcopy(template_unit)
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

def set_memory_flag(ctx: 'RollContext', params: dict):
    """
    Устанавливает флаг в память юнита (для пассивок или проверок).
    params: { "flag": "wethermon_failed", "value": true }
    """
    flag = params.get("flag")
    value = params.get("value", True)
    if flag:
        ctx.source.memory[flag] = value
        # Для удобства отладки можно писать и в ctx.log, но сейчас пишем только в logger
        logger.log(f"🚩 Memory: Set {flag}={value} for {ctx.source.name}", LogLevel.VERBOSE, "Scripts")


def _get_team_lists(source):
    if 'team_left' in st.session_state and source in st.session_state['team_left']:
        return st.session_state['team_left'], st.session_state['team_right']
    if 'team_right' in st.session_state and source in st.session_state['team_right']:
        return st.session_state['team_right'], st.session_state['team_left']
    return None, None


def apply_marked_flesh(ctx: 'RollContext', params: dict):
    """Накладывает marked_flesh на цель с наименьшим HP среди врагов."""
    source = ctx.source
    if not source:
        return

    my_team, enemy_team = _get_team_lists(source)
    if not enemy_team:
        return

    candidates = [u for u in enemy_team if not u.is_dead()]
    if not candidates:
        return

    target = min(candidates, key=lambda u: u.current_hp)

    # Снимаем старую метку
    for u in enemy_team:
        if u.get_status("marked_flesh") > 0:
            u.remove_status("marked_flesh", 999)

    duration = int(params.get("duration", 99))
    target.add_status("marked_flesh", 1, duration=duration)
    target.memory["marked_flesh_by"] = source.name
    target.memory.pop("marked_flesh_transferred", None)
    source.memory["marked_flesh_target_name"] = target.name

    if ctx.log is not None:
        ctx.log.append(f"🩸 **Marked Flesh**: {target.name} selected")
    logger.log(
        f"🩸 Marked Flesh applied: {source.name} -> {target.name}",
        LogLevel.NORMAL,
        "Scripts"
    )


def set_card_power_bonus(ctx: 'RollContext', params: dict):
    """Запоминает бонус к мощности для текущей карты на этот ход."""
    unit = ctx.source
    card = unit.current_card if unit else None
    if not unit or not card:
        return

    base = int(params.get("base", 1))
    reason = params.get("reason", "Bonus")
    condition = params.get("condition", "")
    multiplier = int(params.get("multiplier", 2))
    else_multiplier = int(params.get("else_multiplier", 1))

    condition_met = False
    if condition == "last_clash_win":
        condition_met = bool(unit.memory.get("last_clash_win"))
        if condition_met:
            unit.memory["last_clash_win"] = False
    elif condition == "only_card_this_turn":
        active_cards = [s for s in unit.active_slots if s.get("card")]
        condition_met = (len(active_cards) == 1)
    elif condition == "always":
        condition_met = True

    mult = multiplier if condition_met else else_multiplier

    unit.memory["card_power_bonus_card_id"] = card.id
    unit.memory["card_power_bonus_base"] = base
    unit.memory["card_power_bonus_mult"] = mult
    unit.memory["card_power_bonus_reason"] = reason

    if ctx.log is not None:
        tag = "x" + str(mult)
        ctx.log.append(f"⚔️ Power Bonus: {card.name} {tag}")
    logger.log(
        f"⚔️ Card Power Bonus: {unit.name} {card.id} base={base} mult={mult}",
        LogLevel.VERBOSE,
        "Scripts"
    )