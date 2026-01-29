import streamlit as st
import os

# Импортируем разбитые части
from ui.profile_new.sidebar_parts.controls import render_profile_controls
from ui.profile_new.sidebar_parts.avatar import render_avatar_section
from ui.profile_new.sidebar_parts.info import render_basic_info
from ui.profile_new.sidebar_parts.stats import render_vital_stats


# from ui.profile_new.sidebar_parts.resistances import render_resistances  <-- Больше не нужно

def render_sidebar(unit, is_edit_mode: bool):
    """
    Рисует 'Паспорт' персонажа, собирая компоненты из подмодулей.
    """
    # 1. Аватар
    render_avatar_section(unit, is_edit_mode)

    st.divider()

    # 2. Основная инфа (Имя, Уровень)
    render_basic_info(unit, is_edit_mode)

    st.divider()

    # 3. Показатели (HP/SP/Stagger)
    render_vital_stats(unit, is_edit_mode)

    # Раздел с резистами удален, так как перенесен в Equipment Tab