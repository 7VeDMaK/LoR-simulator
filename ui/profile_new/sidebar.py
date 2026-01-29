import streamlit as st
from ui.profile_new.sidebar_parts.avatar import render_avatar_section
from ui.profile_new.sidebar_parts.info import render_basic_info
from ui.profile_new.sidebar_parts.stats import render_vital_stats


def render_sidebar(unit, is_edit_mode: bool):
    """
    Рисует 'Паспорт' персонажа.
    Порядок: Аватар -> Статы (HP) -> Инфо.
    Без дивайдеров.
    """
    # 1. Аватар
    render_avatar_section(unit, is_edit_mode)

    # 2. Показатели (HP/SP/Stagger) - ВТОРЫМ, как просили
    render_vital_stats(unit, is_edit_mode)

    # 3. Основная инфа (Имя, Ранг, Уровень и т.д.)
    render_basic_info(unit, is_edit_mode)