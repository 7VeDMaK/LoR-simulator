import streamlit as st
from core.unit.unit_library import UnitLibrary
from core.unit.unit import Unit
from ui.profile.header import render_header

# === ИМПОРТЫ ===
from ui.profile_new.sidebar import render_sidebar, render_profile_controls
from ui.profile_new.tabs.build import render_build_tab
from ui.profile_new.tabs.passives import render_passives_tab
from ui.profile_new.tabs.equipment import render_equipment_tab
from ui.profile_new.tabs.talents import render_talents_tab
from ui.profile_new.tabs.stats import render_stats_tab
# Импортируем новую вкладку
from ui.profile_new.tabs.visuals import render_visuals_tab


def render_profile_page_v2():
    # 1. Init Roster
    if 'roster' not in st.session_state or not st.session_state['roster']:
        st.session_state['roster'] = UnitLibrary.load_all() or {"New Unit": Unit("New Unit")}

    roster = st.session_state['roster']

    # 2. Global Controls (Sidebar)
    is_edit_mode = render_profile_controls()

    # 3. Header (Unit Select)
    unit, u_key = render_header(roster)
    if unit is None:
        return

    # Пересчет статов
    unit.recalculate_stats()
    st.markdown("---")

    # 4. Layout
    col_left, col_right = st.columns([1, 2.5], gap="medium")

    # === LEFT: PASSPORT ===
    with col_left:
        render_sidebar(unit, is_edit_mode)

    # === RIGHT: TABS ===
    with col_right:
        tabs = st.tabs([
            "⚔️ Колода",
            "🛠️ Снаряжение",
            "🧬 Пассивки",
            "🌟 Таланты",
            "📊 Параметры",
            "📝 Инфо"  # <--- Переименовали последнюю вкладку
        ])

        # TAB 1: Deck
        with tabs[0]:
            render_build_tab(unit, is_edit_mode)

        # TAB 2: Equipment
        with tabs[1]:
            render_equipment_tab(unit, is_edit_mode)

        # TAB 3: Passives
        with tabs[2]:
            render_passives_tab(unit, is_edit_mode)

        # TAB 4: Talents
        with tabs[3]:
            render_talents_tab(unit, is_edit_mode)

        # TAB 5: Stats
        with tabs[4]:
            render_stats_tab(unit, is_edit_mode)

        # TAB 6: Visuals / Info (НОВАЯ ФУНКЦИЯ)
        with tabs[5]:
            render_visuals_tab(unit, is_edit_mode)