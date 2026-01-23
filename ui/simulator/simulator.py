import streamlit as st

# [NEW] Импорт логгера
from core.logging import logger, LogLevel
from logic.revival import render_death_overlay
from logic.state_manager import StateManager
# Импортируем логику возрождения
from ui.components import render_unit_stats
# Импортируем логику симулятора
from ui.simulator.components.simulator_components import render_slot_strip, render_active_abilities, render_inventory
from ui.simulator.logic.precalculate_speed_rolls import precalculate_interactions
from ui.simulator.logic.simulator_logic import sync_state_from_widgets
from ui.simulator.logic.step_func import reset_game, roll_phase, execute_combat_auto


def render_simulator_page():
    # Инициализация фазы
    if 'phase' not in st.session_state: st.session_state['phase'] = 'roll'
    if 'round_number' not in st.session_state: st.session_state['round_number'] = 1

    # Инициализация стека истории
    if 'undo_stack' not in st.session_state: st.session_state['undo_stack'] = []

    # === CSS СТИЛИ ДЛЯ ЛОГОВ И СЧЕТЧИКА ===
    st.markdown(f"""
        <style>
            /* Контейнер счетчика раундов */
            .turn-counter-static {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                margin: 0 auto 10px auto; 
                padding: 5px 20px;
                width: fit-content;
                min-width: 120px;
                background: linear-gradient(135deg, rgba(35, 37, 46, 1) 0%, rgba(20, 20, 25, 1) 100%);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }}
            .counter-label {{
                font-family: sans-serif; font-size: 10px; letter-spacing: 2px;
                text-transform: uppercase; color: #8d99ae; margin-bottom: 2px;
            }}
            .counter-value {{
                font-family: 'Courier New', monospace; font-size: 24px;
                font-weight: 700; color: #edf2f4; text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
                line-height: 1;
            }}

            /* Стили логов */
            .log-container {{
                background-color: #0e1117;
                border: 1px solid #30333d;
                border-radius: 5px;
                padding: 10px;
                max-height: 500px;
                overflow-y: auto;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
            }}
            .log-entry {{
                padding: 3px 0;
                border-bottom: 1px solid #1c1f26;
                display: flex;
                align-items: baseline;
            }}
            .log-time {{ color: #6c757d; margin-right: 10px; min-width: 70px; font-size: 0.9em; }}

            /* Категории */
            .cat-Combat {{ color: #ff6b6b; font-weight: bold; }} 
            .cat-Status {{ color: #4ecdc4; }} 
            .cat-Effect {{ color: #feca57; }} 
            .cat-Stats {{ color: #54a0ff; }} 
            .cat-System {{ color: #8395a7; }} 
            .cat-Clash {{ color: #ff9ff3; font-weight: bold; }} 
            .cat-Damage {{ color: #ff4757; font-weight: bold; text-decoration: underline; }} 

            .log-cat {{ margin-right: 10px; min-width: 80px; text-transform: uppercase; font-size: 0.85em; }}

            /* Уровни важности */
            .lvl-NORMAL {{ color: #e9ecef; }}
            .lvl-MINIMAL {{ color: #ffffff; font-weight: bold; border-left: 2px solid #fff; padding-left: 5px; }}
            .lvl-VERBOSE {{ color: #636e72; font-style: italic; }}
        </style>
        """, unsafe_allow_html=True)

    # === САЙДБАР ===
    with st.sidebar:
        st.divider()
        st.subheader("⚙️ Управление боем")

        # --- 1. СБРОС ---
        if st.button("🔄 Сброс боя (Reset)", type="secondary", width='stretch', help="Полный сброс к началу"):
            reset_game()
            logger.clear()
            st.rerun()

        # --- 2. МАШИНА ВРЕМЕНИ (TIMELINE) ---
        undo_stack = st.session_state.get('undo_stack', [])

        # Список доступных точек возврата
        if undo_stack:
            with st.expander("🕰️ История ходов", expanded=True):
                # undo_stack[i] - это состояние ПЕРЕД началом раунда (i+1)
                available_rounds = list(range(1, len(undo_stack) + 1))

                target_round = st.selectbox(
                    "Вернуться к началу раунда:",
                    options=available_rounds,
                    index=len(available_rounds) - 1,  # По умолчанию последний доступный
                    format_func=lambda x: f"Раунд {x}",
                    key="timeline_selector"
                )

                if st.button("⏪ Загрузить состояние", type="primary", width='stretch'):
                    # 1. Находим индекс в стеке. Раунд 1 лежит по индексу 0.
                    stack_index = target_round - 1

                    if 0 <= stack_index < len(undo_stack):
                        snapshot = undo_stack[stack_index]

                        # 2. Восстанавливаем состояние (Keyframe + Delta)
                        if snapshot.get("type") == "dynamic":
                            # Для восстановления динамики нужна База (Round 1 / Index 0)
                            base_snapshot = undo_stack[0]
                            if base_snapshot.get("type") != "full":
                                st.error("❌ Ошибка истории: Базовый снимок поврежден!")
                            else:
                                StateManager.restore_from_dynamic_snapshot(st.session_state, snapshot, base_snapshot)
                                st.toast(f"Раунд {target_round} восстановлен (Delta)! 🕰️")
                        else:
                            # Это полный снимок (Full Keyframe)
                            StateManager.restore_state_from_snapshot(st.session_state, snapshot)
                            st.toast(f"Раунд {target_round} восстановлен (Full)! 🕰️")

                        # 3. Обрезаем историю БУДУЩЕГО (мы изменили временную линию)
                        st.session_state['undo_stack'] = undo_stack[:stack_index + 1]

                        st.rerun()
        else:
            st.caption("История ходов пуста (Раунд 1)")

        st.divider()

        # --- ВЫБОР РЕЖИМА ЛОГИРОВАНИЯ ---
        st.markdown("**📜 Уровень Логирования**")
        log_mode = st.radio(
            "Детализация:",
            ["Минимальный", "Обычный", "Подробный"],
            index=1,  # Обычный по умолчанию
            key="sim_log_mode",
            help="Влияет на то, сколько информации будет показано в консоли событий."
        )

        # Маппинг для конвертации
        log_level_map = {
            "Минимальный": LogLevel.MINIMAL,
            "Обычный": LogLevel.NORMAL,
            "Подробный": LogLevel.VERBOSE
        }
        current_log_level = log_level_map[log_mode]

    # === ВЕРХНЯЯ ЧАСТЬ: СЧЕТЧИК И ФАЗЫ ===
    col_counter, col_ctrl = st.columns([1, 4])

    with col_counter:
        st.markdown(f"""
        <div class="turn-counter-static">
            <div class="counter-label">SCENE</div>
            <div class="counter-value">{st.session_state['round_number']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_ctrl:
        # Получаем команды
        team_left = st.session_state.get('team_left', [])
        team_right = st.session_state.get('team_right', [])

        if not team_left or not team_right:
            st.warning("⚠️ Команды пусты. Добавьте персонажей в боковом меню.")
            return

        # 1. Пересчет статов (чтобы UI был свежим)
        for u in team_left + team_right:
            u.recalculate_stats()

        # 2. Логика фаз и Кнопка действия
        btn_col1, btn_col2 = st.columns([3, 1])

        with btn_col1:
            if st.session_state['phase'] == 'roll':
                st.info("🎲 Фаза: **Бросок Инициативы**. Определите скорость персонажей.")
                if st.button("🎲 БРОСИТЬ КУБИКИ СКОРОСТИ", type="primary", width='stretch'):
                    roll_phase()
                    st.rerun()
            else:
                # Фаза планирования/боя
                st.success("⚔️ Фаза: **Столкновение**. Настройте карты и начните бой.")

                # Синхронизация виджетов с данными (чтобы при нажатии Fight данные не потерялись)
                sync_state_from_widgets(team_left, team_right)
                precalculate_interactions(team_left, team_right)

                if st.button("⚔️ НАЧАТЬ РАУНД (FIGHT)", type="primary", width='stretch'):
                    execute_combat_auto()
                    st.rerun()

    st.divider()

    # === ОСНОВНАЯ ЗОНА: КОМАНДЫ ===
    col_left_main, col_right_main = st.columns(2, gap="large")

    # --- ЛЕВАЯ КОМАНДА ---
    with col_left_main:
        st.markdown(f"### 🟦 Left Team ({len(team_left)})")
        for i, unit in enumerate(team_left):
            with st.container(border=True):
                # Шапка юнита
                c_stats, c_img = st.columns([2, 1.2])
                with c_stats:
                    render_unit_stats(unit)
                with c_img:
                    # Аватар
                    img = unit.avatar if unit.avatar else "https://placehold.co/150?text=Unit"
                    st.image(img, width='stretch')

                # Активные способности и инвентарь
                render_active_abilities(unit, f"l_abil_{i}")
                render_inventory(unit, f"l_inv_{i}")
                if st.session_state['phase'] == 'planning':
                    st.divider()

                    # === [NEW] ПРОВЕРКА НА СМЕРТЬ ===
                    # Если HP или SP <= 0 (и есть overkill), считаем его мертвым
                    is_dead_mechanic = (unit.current_hp <= 0 or unit.current_sp <= 0 or unit.overkill_damage > 0)

                    if is_dead_mechanic:
                        render_death_overlay(unit, f"death_{i}_{unit.name}")
                    elif unit.active_slots:
                        for s_i in range(len(unit.active_slots)):
                            render_slot_strip(unit, team_right, team_left, s_i, f"l_{i}")
                    else:
                        if unit.is_staggered():
                            st.error("😵 STAGGERED")
                        else:
                            st.caption("No active slots")

    # --- ПРАВАЯ КОМАНДА ---
    with col_right_main:
        st.markdown(f"### 🟥 Right Team ({len(team_right)})")
        for i, unit in enumerate(team_right):
            with st.container(border=True):
                c_stats, c_img = st.columns([2, 1.2])
                with c_stats:
                    render_unit_stats(unit)
                with c_img:
                    img = unit.avatar if unit.avatar else "https://placehold.co/150?text=Enemy"
                    st.image(img, width='stretch')

                render_active_abilities(unit, f"r_abil_{i}")
                render_inventory(unit, f"r_inv_{i}")

                if st.session_state['phase'] == 'planning':
                    st.divider()

                    # === [NEW] ПРОВЕРКА НА СМЕРТЬ ===
                    is_dead_mechanic = (unit.current_hp <= 0 or unit.current_sp <= 0 or unit.overkill_damage > 0)

                    if is_dead_mechanic:
                        render_death_overlay(unit, f"death_r_{i}_{unit.name}")
                    elif unit.active_slots:
                        for s_i in range(len(unit.active_slots)):
                            render_slot_strip(unit, team_left, team_right, s_i, f"r_{i}")
                    else:
                        if unit.is_staggered():
                            st.error("😵 STAGGERED")
                        else:
                            st.caption("No active slots")

    st.divider()

    # === ЗОНА ЛОГОВ (2 ЧАСТИ) ===

    tab_visual, tab_system = st.tabs(["📜 Visual Report (Cards)", f"🛠️ System Log ({log_mode})"])

    # 1. VISUAL REPORT (Карточки столкновений)
    # Показывает красивые плашки Clash/OneSided из logic/battle_flow
    with tab_visual:
        visual_logs = st.session_state.get('battle_logs', [])

        if not visual_logs:
            st.caption("Нет данных о столкновениях в этом раунде.")
        else:
            for log in visual_logs:
                # Если это полноценный отчет о столкновении (словарь с left/right)
                if "left" in log and "right" in log:
                    with st.container(border=True):
                        l = log['left']
                        r = log['right']

                        # Определяем цвет рамки по исходу (победа/поражение)
                        outcome = log.get('outcome', '-')

                        c_vis_l, c_vis_c, c_vis_r = st.columns([5, 1, 5])

                        # ЛЕВО
                        with c_vis_l:
                            st.markdown(
                                f"<div style='text-align:right'><b>{l['unit']}</b> <span style='color:gray; font-size:0.8em'>({l['card']})</span><br>"
                                f"{l['dice']} <span style='font-size:1.4em; font-weight:bold; color:#4ecdc4'>{l['val']}</span> <span style='font-size:0.8em; color:gray'>[{l['range']}]</span></div>",
                                unsafe_allow_html=True)

                        # VS
                        with c_vis_c:
                            st.markdown(
                                "<div style='text-align:center; font-weight:bold; padding-top:10px; color:#555'>VS</div>",
                                unsafe_allow_html=True)

                        # ПРАВО
                        with c_vis_r:
                            st.markdown(
                                f"<b>{r['unit']}</b> <span style='color:gray; font-size:0.8em'>({r['card']})</span><br>"
                                f"<span style='font-size:1.4em; font-weight:bold; color:#ff6b6b'>{r['val']}</span> {r['dice']} <span style='font-size:0.8em; color:gray'>[{r['range']}]</span>",
                                unsafe_allow_html=True)

                        # Итог и Детали
                        st.caption(f"🏁 {outcome}")
                        if 'details' in log and log['details']:
                            with st.expander("Подробности"):
                                for d in log['details']:
                                    st.markdown(f"- {d}")

                # Если это просто текстовое событие (например, начало раунда)
                else:
                    # Фильтруем простые события, если выбран Minimal, чтобы не засорять визуал
                    if current_log_level > LogLevel.MINIMAL:
                        st.caption(f"ℹ️ {log.get('round', '')}: {log.get('details', '')}")

    # 2. SYSTEM LOG (Текстовая консоль)
    with tab_system:
        # Получаем отфильтрованные логи
        system_logs = logger.get_logs_for_ui(current_log_level)

        # Доп. фильтр по категориям
        if system_logs:
            all_cats = sorted(list(set(l['category'] for l in system_logs)))
            selected_cats = st.multiselect("Фильтр категорий", all_cats, default=all_cats, key="log_cat_filter")
        else:
            selected_cats = []

        # Начинаем контейнер
        log_html = '<div class="log-container">'

        if not system_logs:
            log_html += '<div class="log-entry">Нет логов для отображения.</div>'

        for entry in system_logs:
            if entry['category'] in selected_cats:
                # CSS классы
                lvl_class = f"lvl-{entry['level'].name}"
                cat_class = f"cat-{entry['category']}"

                # Собираем строку лога
                row = (
                    f'<div class="log-entry {lvl_class}">'
                    f'<span class="log-time">[{entry["time"]}]</span>'
                    f'<span class="log-cat {cat_class}">[{entry["category"]}]</span>'
                    f'<span class="log-msg">{entry["message"]}</span>'
                    f'</div>'
                )
                log_html += row

        log_html += '</div>'
        st.markdown(log_html, unsafe_allow_html=True)