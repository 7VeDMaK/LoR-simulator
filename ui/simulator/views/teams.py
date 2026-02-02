import streamlit as st

from logic.revival import render_death_overlay
from ui.components import render_unit_stats
from ui.simulator.components.abilities import render_active_abilities
from ui.simulator.components.inventory import render_inventory
from ui.simulator.components.slots import render_slot_strip


def render_team_column(team, label, key_prefix, opposing_team):
    st.markdown(f"### {label} ({len(team)})")
    
    # Оптимизация: кэшируем фазу чтобы не проверять каждый раз
    current_phase = st.session_state.get('phase', 'roll')
    is_planning = current_phase == 'planning'
    
    for i, unit in enumerate(team):
        with st.container(border=True):
            # Шапка
            c_stats, c_img = st.columns([2, 1.2])
            with c_stats:
                render_unit_stats(unit)
            with c_img:
                img = unit.avatar if unit.avatar else "https://placehold.co/150?text=Unit"
                st.image(img, width='stretch')

            # Способности
            render_active_abilities(unit, f"{key_prefix}_abil_{i}")
            render_inventory(unit, f"{key_prefix}_inv_{i}")

            if is_planning:
                st.divider()

                # Проверка смерти
                is_dead_mechanic = (unit.current_hp <= 0 or unit.current_sp <= 0 or unit.overkill_damage > 0)

                if is_dead_mechanic:
                    render_death_overlay(unit, f"death_{key_prefix}_{i}_{unit.name}")
                elif unit.active_slots:
                    for s_i in range(len(unit.active_slots)):
                        render_slot_strip(unit, opposing_team, team, s_i, f"{key_prefix}_{i}")
                else:
                    if unit.is_staggered():
                        st.error("😵 STAGGERED")
                    else:
                        st.caption("No active slots")


def render_teams(team_left, team_right):
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        render_team_column(team_left, "🟦 Left Team", "l", team_right)

    with col_right:
        render_team_column(team_right, "🟥 Right Team", "r", team_left)