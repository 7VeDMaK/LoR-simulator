import streamlit as st
from ui.components import render_unit_stats
# Импортируем обновленные функции логики
from ui.simulator.simulator_logic import (
    roll_phase, execute_combat_auto, reset_game,
    sync_state_from_widgets, precalculate_interactions
)
from ui.simulator.simulator_components import render_slot_strip, render_active_abilities, render_inventory


def render_simulator_page():
    # Инициализация фазы
    if 'phase' not in st.session_state: st.session_state['phase'] = 'roll'

    # === ОБНОВЛЕННЫЕ СТИЛИ (CSS) ===
    st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }

        /* Стили для карточек боя */
        .clash-card-left { text-align: right; padding-right: 10px; }
        .clash-card-right { text-align: left; padding-left: 10px; }

        /* === НАСТРОЙКА КАРТИНОК (АВАТАРОК) === */
        /* Картинка растягивается на всю ширину своей колонки */
        [data-testid="stImage"] img {
            width: 100% !important;
            height: auto !important;
            max-height: 250px;            
            object-fit: cover;            
            border-radius: 8px;
            margin: 0 auto;
        }

        /* Центрирование внутри колонки */
        [data-testid="stImage"] {
            display: flex;
            justify_content: center;
            align-items: flex-start;
        }
    </style>
    """, unsafe_allow_html=True)

    st.header("⚔️ Mass Battle Simulator")

    # Сайдбар с кнопкой сброса
    with st.sidebar:
        st.divider()
        st.button("🔄 Reset Battle", on_click=reset_game, type="secondary", width='stretch')

    # Получаем команды
    team_left = st.session_state.get('team_left', [])
    team_right = st.session_state.get('team_right', [])

    if not team_left or not team_right:
        st.warning("Teams are empty. Please configure teams in the sidebar.")
        return

    # 1. Пересчет статов (визуальный) для всех юнитов
    for u in team_left + team_right:
        u.recalculate_stats()

    # 2. Синхронизация состояния виджетов и прекалькуляция (только в фазе планирования)
    if st.session_state['phase'] == 'planning':
        sync_state_from_widgets(team_left, team_right)
        precalculate_interactions(team_left, team_right)

    # === ОСНОВНАЯ РАЗМЕТКА (2 КОЛОНКИ) ===
    col_left_main, col_right_main = st.columns(2, gap="large")

    # --- LEFT TEAM ---
    with col_left_main:
        st.subheader(f"Left Team ({len(team_left)})")
        for i, unit in enumerate(team_left):
            with st.container(border=True):
                c_stats, c_img = st.columns([2, 1.2])
                with c_stats:
                    render_unit_stats(unit)
                with c_img:
                    img = unit.avatar if unit.avatar else "https://placehold.co/150?text=U"
                    st.image(img, width='stretch')

                render_active_abilities(unit, f"l_abil_{i}")
                render_inventory(unit, f"l_inv_{i}")

                if st.session_state['phase'] == 'planning':
                    st.divider()
                    if unit.active_slots:
                        for s_i in range(len(unit.active_slots)):
                            # ПЕРЕДАЕМ team_left как my_team
                            render_slot_strip(unit, team_right, team_left, s_i, f"l_{i}")
                    else:
                        st.caption("No active slots")

    # --- RIGHT TEAM ---
    with col_right_main:
        st.subheader(f"Right Team ({len(team_right)})")
        for i, unit in enumerate(team_right):
            with st.container(border=True):
                c_stats, c_img = st.columns([2, 1.2])
                with c_stats:
                    render_unit_stats(unit)
                with c_img:
                    img = unit.avatar if unit.avatar else "https://placehold.co/150?text=E"
                    st.image(img, width='stretch')

                render_active_abilities(unit, f"r_abil_{i}")
                render_inventory(unit, f"l_inv_{i}")

                if st.session_state['phase'] == 'planning':
                    st.divider()
                    if unit.active_slots:
                        for s_i in range(len(unit.active_slots)):
                            # ПЕРЕДАЕМ team_right как my_team
                            render_slot_strip(unit, team_left, team_right, s_i, f"r_{i}")
                    else:
                        st.caption("No active slots")

    st.divider()

    # === ЦЕНТРАЛЬНЫЕ КНОПКИ УПРАВЛЕНИЯ ===
    _, c_center, _ = st.columns([1, 2, 1])
    with c_center:
        if st.session_state['phase'] == 'roll':
            st.button("🎲 ROLL INITIATIVE (ALL)", type="primary", on_click=roll_phase, width='stretch')
        else:
            st.button("⚔️ FIGHT! (Execute Turn)", type="primary", on_click=execute_combat_auto,
                      width='stretch')

    # === ЛОГИ БОЯ ===
    st.subheader("📜 Battle Report")

    if st.session_state.get('turn_message'):
        st.info(st.session_state['turn_message'])

    logs = st.session_state.get('battle_logs', [])

    if logs:
        for log in logs:
            if "left" in log and "right" in log:
                with st.container(border=True):
                    l = log['left']
                    r = log['right']

                    c_vis_l, c_vis_c, c_vis_r = st.columns([5, 1, 5])

                    with c_vis_l:
                        st.markdown(
                            f"<div style='text-align:right'>"
                            f"<b>{l['unit']}</b> <span style='color:gray'>({l['card']})</span><br>"
                            f"{l['dice']} <span style='font-size:1.2em; font-weight:bold'>{l['val']}</span> "
                            f"<span style='font-size:0.8em'>[{l['range']}]</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                    with c_vis_c:
                        st.markdown("<div style='text-align:center; padding-top:10px; color:gray'>VS</div>",
                                    unsafe_allow_html=True)

                    with c_vis_r:
                        st.markdown(
                            f"<b>{r['unit']}</b> <span style='color:gray'>({r['card']})</span><br>"
                            f"<span style='font-size:0.8em'>[{r['range']}]</span> "
                            f"<span style='font-size:1.2em; font-weight:bold'>{r['val']}</span> {r['dice']}",
                            unsafe_allow_html=True
                        )

                    st.divider()

                    st.caption(f"Round: {log.get('round', '?')} | Result: {log.get('outcome', '-')}")

                    if 'details' in log:
                        for d in log['details']:
                            st.markdown(f"• {d}")

            else:
                st.caption(f"ℹ️ {log.get('round', '')}: {log.get('details', '')}")