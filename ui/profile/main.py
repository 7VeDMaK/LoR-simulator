import streamlit as st
from core.unit.unit import Unit
from core.unit.unit_library import UnitLibrary

# Import our new components
from ui.profile.header import render_header, render_basic_info
from ui.profile.stats import render_stats
from ui.profile.equipment import render_equipment
from ui.profile.abilities import render_abilities

def render_profile_page():
    if 'roster' not in st.session_state or not st.session_state['roster']:
        st.session_state['roster'] = UnitLibrary.load_all() or {"New Unit": Unit("New Unit")}

    roster = st.session_state['roster']

    # 1. Header & Selection
    unit, u_key = render_header(roster)

    col_l, col_r = st.columns([1, 2.5], gap="medium")

    # 2. Left Column: Basic Info
    with col_l:
        render_basic_info(unit, u_key)

    # 3. Right Column: Everything else
    with col_r:
        render_equipment(unit, u_key)
        render_stats(unit, u_key)

    # STATS RECALCULATION (Always happens to show updated logs)
    logs = unit.recalculate_stats()

    st.markdown("---")

    # 4. Abilities & Deck
    render_abilities(unit, u_key)

    # 5. Calculation Log
    with st.expander("📜 Лог расчета характеристик"):
        for l in logs:
            st.caption(f"• {l}")