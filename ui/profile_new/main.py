import streamlit as st
from core.unit.unit_library import UnitLibrary
from core.unit.unit import Unit
from ui.profile.header import render_header

# === ИМПОРТЫ ===
# 1. Сайдбар и контролы
from ui.profile_new.sidebar import render_sidebar, render_profile_controls

# 2. Вкладки (убедись, что все файлы созданы)
from ui.profile_new.tabs.build import render_build_tab
from ui.profile_new.tabs.passives import render_passives_tab
from ui.profile_new.tabs.equipment import render_equipment_tab  # Наш новый файл


# from ui.profile_new.tabs.talents import render_talents_tab # Раскомментируй, если создал talents.py

def render_profile_page_v2():
    # 1. Загрузка Ростера
    if 'roster' not in st.session_state or not st.session_state['roster']:
        st.session_state['roster'] = UnitLibrary.load_all() or {"New Unit": Unit("New Unit")}

    roster = st.session_state['roster']

    # 2. РИСУЕМ КОНТРОЛЫ В ГЛОБАЛЬНОМ САЙДБАРЕ
    # Эта функция сама вызовет with st.sidebar: ...
    is_edit_mode = render_profile_controls()

    # 3. Шапка профиля
    unit, u_key = render_header(roster)
    if unit is None:
        return

    unit.recalculate_stats()
    st.markdown("---")

    # 4. Основная сетка страницы
    col_left, col_right = st.columns([1, 2.5], gap="medium")

    # === ЛЕВАЯ КОЛОНКА (ПАСПОРТ) ===
    with col_left:
        # Передаем режим, полученный из сайдбара
        render_sidebar(unit, is_edit_mode)

    # === ПРАВАЯ КОЛОНКА (ВКЛАДКИ) ===
    with col_right:
        # Список вкладок
        tabs = st.tabs([
            "⚔️ Колода",
            "🛠️ Снаряжение",  # <--- Вкладка экипировки
            "🧬 Пассивки",
            "📊 Параметры",
            "🎨 Внешность"
        ])

        # TAB 1: Колода
        with tabs[0]:
            render_build_tab(unit, is_edit_mode)

        # TAB 2: Экипировка (Оружие/Броня/Аугментации)
        with tabs[1]:
            render_equipment_tab(unit, is_edit_mode)

        # TAB 3: Пассивки
        with tabs[2]:
            render_passives_tab(unit, is_edit_mode)

        # TAB 4: Параметры (Заглушка или старый код)
        with tabs[3]:
            st.info("Атрибуты (Сила/Ловкость) и Таланты")
            # render_talents_tab(unit, is_edit_mode)

        # TAB 5: Внешность
        with tabs[4]:
            st.info("Настройки скинов и биографии")