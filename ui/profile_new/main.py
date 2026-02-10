import streamlit as st
from core.unit.unit_library import UnitLibrary
from core.unit.unit import Unit
from ui.profile.header import render_header

# Импорт логгера для управления очисткой
from core.logging import logger

# === ИМПОРТЫ ТАБОВ ===
from ui.profile_new.sidebar import render_sidebar
from ui.profile_new.sidebar_parts.controls import render_profile_controls
from ui.profile_new.tabs.build import render_build_tab
from ui.profile_new.tabs.passives import render_passives_tab
from ui.profile_new.tabs.equipment import render_equipment_tab
from ui.profile_new.tabs.talents import render_talents_tab
from ui.profile_new.tabs.stats import render_stats_tab
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

    # === ЛОГИКА ПЕРЕСЧЕТА ===
    # 1. Очищаем глобальный логгер перед расчетом, чтобы убрать старые записи и записи чужих юнитов
    if hasattr(logger, 'clear'):
        logger.clear()
    elif hasattr(logger, 'logs') and isinstance(logger.logs, list):
        logger.logs.clear()  # Fallback если нет метода clear()

    # 2. Пересчитываем статы (теперь в лог попадет только этот расчет)
    unit.recalculate_stats()

    # 3. "Фотографируем" логи именно для этого юнита и сохраняем во временное свойство
    # Это нужно, чтобы вкладка Visuals знала, что именно показывать
    unit._ui_logs = list(logger.get_logs())

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
            "📝 Инфо"
        ])

        with tabs[0]: render_build_tab(unit, is_edit_mode)
        with tabs[1]: render_equipment_tab(unit, is_edit_mode)
        with tabs[2]: render_passives_tab(unit, is_edit_mode)
        with tabs[3]: render_talents_tab(unit, is_edit_mode)
        with tabs[4]: render_stats_tab(unit, is_edit_mode, u_key)
        with tabs[5]: render_visuals_tab(unit, is_edit_mode)