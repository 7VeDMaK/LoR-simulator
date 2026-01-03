import random
from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from logic.context import RollContext


# ==========================================
# 🧮 УНИВЕРСАЛЬНЫЙ КАЛЬКУЛЯТОР (CORE)
# ==========================================

def _get_unit_stat(unit, stat_name: str) -> int:
    """
    Умное получение значения стата.
    """
    if not unit or not stat_name: return 0
    key = stat_name.lower()

    # 1. Динамические параметры
    if key in ["hp", "current_hp"]: return unit.current_hp
    if key in ["sp", "current_sp"]: return unit.current_sp
    if key in ["stagger", "current_stagger"]: return unit.current_stagger

    if key == "max_hp": return unit.max_hp
    if key == "max_sp": return unit.max_sp
    if key == "max_stagger": return unit.max_stagger

    # 2. Ресурсы
    if key in unit.resources: return unit.resources[key]
    if key == "luck": return unit.skills.get("luck", 0)

    # 3. Атрибуты и Навыки (через modifiers)
    val_data = unit.modifiers.get(key)
    if val_data is None:
        val_data = unit.modifiers.get(f"total_{key}")

    if val_data is not None:
        if isinstance(val_data, dict): return int(val_data.get("flat", 0))
        return int(val_data)

    if key in unit.attributes: return unit.attributes[key]
    if key in unit.skills: return unit.skills[key]

    return 0


def _resolve_value(source, target, params: dict) -> int:
    """
    Универсальная формула вычисления значения.
    Поддерживает scale_from_target для расчета от статов цели.
    """
    # 1. Базовое значение
    base = int(params.get("base", params.get("amount", 0)))

    # 2. Стат для скалирования
    stat_key = params.get("stat")
    if not stat_key or stat_key == "None":
        return base

    # 3. Определение источника стата
    # Если scale_from_target=True, берем стат у TARGET (того, на кого применяется эффект)
    scale_from_target = params.get("scale_from_target", False)

    primary_unit = target if scale_from_target else source
    secondary_unit = source if scale_from_target else target

    # Защита на случай, если юнита нет (например target умер или None)
    if not primary_unit:
        return base

    primary_val = _get_unit_stat(primary_unit, stat_key)
    final_stat_val = primary_val

    # 4. Разница (если включено)
    # Если scale_from_target=True, то diff будет (Target - Source)
    if params.get("diff", False) and secondary_unit:
        secondary_val = _get_unit_stat(secondary_unit, stat_key)
        final_stat_val = primary_val - secondary_val

    # 5. Множитель
    factor = float(params.get("factor", 1.0))

    total = base + (final_stat_val * factor)
    return int(total)


def _get_targets(ctx, target_mode: str):
    """Определяет список целей."""
    if target_mode == "self":
        return [ctx.source] if ctx.source else []
    elif target_mode == "target":
        return [ctx.target] if ctx.target else []
    elif target_mode == "all":
        res = []
        if ctx.source: res.append(ctx.source)
        if ctx.target: res.append(ctx.target)
        return res
    elif target_mode == "all_allies":
        source = ctx.source
        my_team = []
        if 'team_left' in st.session_state and source in st.session_state['team_left']:
            my_team = st.session_state['team_left']
        elif 'team_right' in st.session_state and source in st.session_state['team_right']:
            my_team = st.session_state['team_right']

        if not my_team: return [source]
        return [u for u in my_team if not u.is_dead()]

    return []


# ==========================================
# 📜 СКРИПТЫ
# ==========================================

def modify_roll_power(ctx: 'RollContext', params: dict):
    if not _check_conditions(ctx.source, params): return
    amount = _resolve_value(ctx.source, ctx.target, params)
    if amount == 0: return

    reason = params.get("reason", "Bonus")
    if reason == "Bonus" and params.get("stat"):
        reason = f"{params['stat'].title()} scale"

    ctx.modify_power(amount, reason)

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


def apply_status(ctx: 'RollContext', params: dict):
    if not _check_conditions(ctx.source, params): return
    status_name = params.get("status")
    if not status_name: return

    target_mode = params.get("target", "target")
    duration = int(params.get("duration", 1))
    min_roll = int(params.get("min_roll", 0))

    if min_roll > 0 and ctx.final_value < min_roll:
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

        # ВАЖНО: Считаем стаки для КОНКРЕТНОГО юнита u
        # Если scale_from_target=True, то стат возьмется у u
        stack = _resolve_value(ctx.source, u, calc_params)

        if stack <= 0: continue

        success, msg = u.add_status(status_name, stack, duration=duration)
        if success:
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

def _check_conditions(unit, params) -> bool:
    """Проверяет вероятность и требования к статам."""
    # 1. Вероятность (0.01 = 1%)
    prob = float(params.get("probability", 1.0))
    if prob < 1.0 and random.random() > prob:
        return False

    # 2. Требование стата (например, Agility > 10 для Сакуры)
    req_stat = params.get("req_stat")
    if req_stat:
        req_val = int(params.get("req_val", 0))
        unit_val = _get_unit_stat(unit, req_stat)
        if unit_val < req_val:
            return False

    return True


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


# === Обновляем логику SP урона в deal_effect_damage (для Эдама) ===
def deal_effect_damage(ctx: 'RollContext', params: dict):
    if not _check_conditions(ctx.source, params): return

    dmg_type = params.get("type", "hp")
    targets = _get_targets(ctx, params.get("target", "target"))

    for u in targets:
        amount = _resolve_value(ctx.source, u, params)
        if amount <= 0: continue

        if dmg_type == "hp":
            u.current_hp = max(0, u.current_hp - amount)
            ctx.log.append(f"💔 **{u.name}**: -{amount} HP (Effect)")
        elif dmg_type == "stagger":
            u.current_stagger = max(0, u.current_stagger - amount)
            ctx.log.append(f"😵 **{u.name}**: -{amount} Stagger")
        elif dmg_type == "sp":
            # === ЛОГИКА ЭДАМА (Mental Protection) ===
            ment_prot = u.get_status("mental_protection")
            if ment_prot > 0:
                # 1 стак = 25%, 2 стака = 50% (макс)
                pct_red = min(0.50, ment_prot * 0.25)
                reduction = int(amount * pct_red)
                amount -= reduction
                ctx.log.append(f"🧀 **Edam**: Blocked {reduction} SP dmg")

            u.take_sanity_damage(amount)
            ctx.log.append(f"🤯 **{u.name}**: -{amount} SP")


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


# === НОВЫЕ СКРИПТЫ ДЛЯ КАРТЫ "ИЗНИЧТОЖЕНИЕ" И ДРУГИХ ===

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


def add_luck_bonus_roll(ctx: 'RollContext', params: dict):
    """Добавляет бонус к броску на основе Удачи (Luck)."""
    if not _check_conditions(ctx.source, params): return
    step = int(params.get("step", 10))
    limit = int(params.get("limit", 999))

    # Берем удачу из ресурсов (обычно там хранится текущая удача)
    luck = ctx.source.resources.get("luck", 0)

    if step <= 0: step = 1
    bonus = luck // step
    bonus = min(bonus, limit)

    if bonus > 0:
        ctx.modify_power(bonus, f"Luck ({luck})")

def scale_roll_by_luck(ctx: 'RollContext', params: dict):
    """
    Серия ударов: Бросок повторяется за каждые X удачи.
    Реализация: Увеличивает итоговое значение броска.
    """
    step = int(params.get("step", 10))  # Каждые 10 удачи
    limit = int(params.get("limit", 7))  # Лимит повторов

    # Берем Удачу из ресурсов (второй стат)
    luck = ctx.source.resources.get("luck", 0)

    if step <= 0: step = 1

    # Считаем множитель (сколько раз добавить значение)
    # Если 10 удачи -> 1 доп раз. Итого 2x.
    repeats = luck // step
    repeats = min(repeats, limit)

    if repeats > 0:
        base_val = ctx.final_value
        bonus = base_val * repeats
        ctx.modify_power(bonus, f"Luck x{repeats}")

def add_power_by_luck(ctx: 'RollContext', params: dict):
    """
    Удар фортуны: Каждые X удачи добавляют 1 к силе.
    """
    step = int(params.get("step", 5))  # Каждые 5 удачи
    limit = int(params.get("limit", 15))  # Лимит

    luck = ctx.source.resources.get("luck", 0)

    if step <= 0: step = 1

    bonus = luck // step
    bonus = min(bonus, limit)

    if bonus > 0:
        ctx.modify_power(bonus, f"Fortune ({bonus})")

SCRIPTS_REGISTRY = {
    "modify_roll_power": modify_roll_power,
    "deal_effect_damage": deal_effect_damage,
    "restore_resource": restore_resource,
    "apply_status": apply_status,
    "steal_status": steal_status,
    "multiply_status": multiply_status,
    "remove_status": remove_status_script, # <--- NEW
    "remove_all_positive": remove_all_positive,

    "self_harm_percent": self_harm_percent,
    "add_hp_damage": add_hp_damage,
    "apply_status_by_roll": apply_status_by_roll,
    "add_luck_bonus_roll": add_luck_bonus_roll,

    "scale_roll_by_luck": scale_roll_by_luck,
    "add_power_by_luck": add_power_by_luck,
}