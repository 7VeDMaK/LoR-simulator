import streamlit as st

from ui.simulator.views.controls import render_top_controls
from ui.simulator.views.gm_panel import render_gm_panel
from ui.simulator.views.logs import render_logs
from ui.simulator.views.sidebar import render_sidebar
# Импорты новых представлений
from ui.simulator.views.styles import inject_simulator_styles
from ui.simulator.views.teams import render_teams


def render_simulator_page():
    # Инициализация состояния
    if 'phase' not in st.session_state: st.session_state['phase'] = 'roll'
    if 'round_number' not in st.session_state: st.session_state['round_number'] = 1
    if 'undo_stack' not in st.session_state: st.session_state['undo_stack'] = []

    # 1. CSS
    inject_simulator_styles()

    # 2. Сайдбар
    log_level, log_mode_label = render_sidebar()

    # 3. Данные команд
    team_left = st.session_state.get('team_left', [])
    team_right = st.session_state.get('team_right', [])

    # 4. Верхняя панель управления
    render_top_controls(team_left, team_right)

    st.divider()

    # 5. Команды
    render_teams(team_left, team_right)

    # 6. Логи
    render_logs(log_level, log_mode_label)

    # 7. Game Master Panel
    render_gm_panel()