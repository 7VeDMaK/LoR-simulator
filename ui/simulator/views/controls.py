import streamlit as st

from ui.simulator.logic.precalculate_speed_rolls import precalculate_interactions
from ui.simulator.logic.simulator_logic import sync_state_from_widgets
from ui.simulator.logic.step_func import roll_phase, execute_combat_auto


def _ensure_stats_calculated(units):
    """Пересчитывает статы только если они еще не посчитаны в этом раунде"""
    current_round = st.session_state.get('round_number', 1)
    
    for u in units:
        # Проверяем, были ли статы уже пересчитаны в этом раунде
        last_calc_round = getattr(u, '_last_stats_calc_round', -1)
        if last_calc_round != current_round:
            u.recalculate_stats()
            u._last_stats_calc_round = current_round


def render_top_controls(team_left, team_right):
    col_counter, col_ctrl = st.columns([1, 4])

    with col_counter:
        st.markdown(f"""
        <div class="turn-counter-static">
            <div class="counter-label">SCENE</div>
            <div class="counter-value">{st.session_state['round_number']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_ctrl:
        if not team_left or not team_right:
            st.warning("⚠️ Команды пусты. Добавьте персонажей в боковом меню.")
            return

        # Оптимизация: пересчитываем только если нужно
        _ensure_stats_calculated(team_left + team_right)

        btn_col1, _ = st.columns([3, 1])

        with btn_col1:
            if st.session_state['phase'] == 'roll':
                st.info("🎲 Фаза: **Бросок Инициативы**. Определите скорость персонажей.")
                if st.button("🎲 БРОСИТЬ КУБИКИ СКОРОСТИ", type="primary", width='stretch'):
                    roll_phase()
                    st.rerun()
            else:
                st.success("⚔️ Фаза: **Столкновение**. Настройте карты и начните бой.")
                sync_state_from_widgets(team_left, team_right)
                precalculate_interactions(team_left, team_right)

                if st.button("⚔️ НАЧАТЬ РАУНД (FIGHT)", type="primary", width='stretch'):
                    execute_combat_auto()
                    st.rerun()