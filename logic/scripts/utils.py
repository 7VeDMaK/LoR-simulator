import random
import streamlit as st
from typing import TYPE_CHECKING

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
    limit = params.get("max", None)
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
    if limit is not None:
        final_stat_val = min(final_stat_val, int(limit))
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