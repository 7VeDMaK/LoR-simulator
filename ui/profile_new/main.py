import streamlit as st
from core.unit.unit_library import UnitLibrary
from core.unit.unit import Unit
from ui.profile.header import render_header

# Импорты компонентов
from ui.profile_new.sidebar import render_sidebar
from ui.profile_new.tabs.build import render_build_tab
from ui.profile_new.tabs.passives import render_passives_tab


def render_profile_page_v2():
    # 1. Загрузка данных
    if 'roster' not in st.session_state or not st.session_state['roster']:
        st.session_state['roster'] = UnitLibrary.load_all() or {"New Unit": Unit("New Unit")}

    roster = st.session_state['roster']

    # 2. Шапка выбора персонажа
    unit, u_key = render_header(roster)
    if unit is None:
        return

    unit.recalculate_stats()

    # 3. Панель управления (Toggle Edit Mode)
    # Используем колонки, чтобы чекбокс был аккуратно справа или слева
    c1, c2 = st.columns([0.8, 0.2])
    with c2:
        is_edit_mode = st.toggle("✏️ Режим редактирования", value=False, key="profile_edit_mode")

    st.divider()

    # 4. Основная разметка
    col_left, col_right = st.columns([1, 2.5], gap="medium")

    # === ЛЕВАЯ КОЛОНКА (ПАСПОРТ) ===
    with col_left:
        # Передаем флаг редактирования внутрь
        render_sidebar(unit, is_edit_mode)

    # === ПРАВАЯ КОЛОНКА (ВКЛАДКИ) ===
    with col_right:
        # Вынесли Пассивки в отдельную вкладку
        tab_deck, tab_passives, tab_stats, tab_bio = st.tabs([
            "⚔️ Колода",
            "🧬 Пассивки",
            "📊 Параметры",
            "🎨 Внешность"
        ])

        with tab_deck:
            render_build_tab(unit, is_edit_mode)

        with tab_passives:
            render_passives_tab(unit, is_edit_mode)

        with tab_stats:
            st.info("Тут будут Атрибуты (Сила/Ловкость) и дерево прокачки")
            # Если нужно редактирование статов:
            # if is_edit_mode: ...

        with tab_bio:
            st.info("Тут настройки скинов и биографии")