import streamlit as st
import io
import os

from core.logging import logger
from core.unit.unit import Unit
from core.unit.unit_library import UnitLibrary
from ui.profile.abilities import render_abilities
from ui.profile.header import render_header, render_basic_info
from ui.profile.stats import render_stats
from ui.profile_new.tabs.equipment import render_equipment_tab


def render_profile_page():
    if 'roster' not in st.session_state or not st.session_state['roster']:
        st.session_state['roster'] = UnitLibrary.load_all() or {"New Unit": Unit("New Unit")}

    roster = st.session_state['roster']

    unit, u_key = render_header(roster)
    if unit is None:
        return

    logger.clear()
    unit.recalculate_stats()
    calculation_logs = logger.get_logs()

    col_l, col_r = st.columns([1, 2.5], gap="medium")

    with col_l:
        render_basic_info(unit, u_key)

    with col_r:
        render_equipment_tab(unit, u_key)
        render_stats(unit, u_key)

    st.markdown("---")
    render_abilities(unit, u_key)

    with st.expander("📜 Лог расчета характеристик", expanded=False):
        if calculation_logs:
            for l in calculation_logs:
                if "Stats" in str(l) or "Talent" in str(l):
                    st.caption(f"• {l}")
                elif "ERROR" in str(l):
                    st.error(f"• {l}")
                else:
                    st.text(f"• {l}")
        else:
            st.info("Нет записей. Проверьте уровень логирования или наличие пассивок.")