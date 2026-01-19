import streamlit as st

from logic.clash import ClashSystem
from logic.statuses.status_manager import StatusManager
from ui.simulator.logic.simulator_logic import get_teams, set_cooldowns, capture_output


def roll_phase():
    """
        Фаза броска скорости.
        Порядок:
        1. Combat/Round Start (Баффы скорости)
        2. Recalc (Применение скорости)
        3. Roll Speed (Генерация слотов)
        4. Speed Rolled Events (Баффы от слотов)
        5. Recalc (Применение баффов от слотов)
        """
    l_team, r_team = get_teams()
    all_units = l_team + r_team

    # === 1. TRIGGERS (События начала) ===
    for u in all_units:
        u.recalculate_stats()
        set_cooldowns(u)

        # B. Round Start (Каждый раунд)
        opponents = r_team if u in l_team else l_team
        my_allies = l_team if u in l_team else r_team

        # Логгер для событий начала раунда
        def log_round(msg):
            if 'battle_logs' not in st.session_state: st.session_state['battle_logs'] = []
            st.session_state['battle_logs'].append({
                "round": "Round Start",
                "rolls": "Event",
                "details": f"🔄 **{u.name}**: {msg}"
            })

        if hasattr(u, "trigger_mechanics"):
            u.trigger_mechanics("on_round_start", u, log_round,
                                enemies=opponents, allies=my_allies)

    for u in all_units:
        u.recalculate_stats()

        if u.is_staggered():
            u.active_slots = [{
                'speed': 0, 'card': None,
                'target_unit_idx': -1, 'target_slot_idx': -1,
                'stunned': True, 'is_aggro': False
            }]
        else:
            u.roll_speed_dice()
            # Init fields
            for s in u.active_slots:
                s['target_unit_idx'] = -1;
                s['target_slot_idx'] = -1;
                s['is_aggro'] = False;
                s['force_clash'] = False

            # === 3. SPEED ROLLED EVENTS (Баффы от слотов) ===
    for u in all_units:
        opponents = r_team if u in l_team else l_team
        my_allies = l_team if u in l_team else r_team

        def log_speed(msg):
            if 'battle_logs' not in st.session_state: st.session_state['battle_logs'] = []
            st.session_state['battle_logs'].append({
                "round": "Speed Roll", "rolls": "Passive", "details": f"⚡ **{u.name}**: {msg}"
            })

        # Запускаем новый триггер
        if hasattr(u, "trigger_mechanics"):
            u.trigger_mechanics("on_speed_rolled", u, log_speed,
                                enemies=opponents, allies=my_allies)

        for u in all_units:
            u.recalculate_stats()

    st.session_state['phase'] = 'planning'
    st.session_state['turn_message'] = "🎲 Speed Rolled (Targets Auto-Assigned)"


def step_start():
    """Начало пошагового боя."""
    l_team, r_team = get_teams()
    sys_clash = ClashSystem()

    # Подготовка хода (расчет инициативы, событий начала боя)
    init_logs, actions = sys_clash.prepare_turn(l_team, r_team)

    st.session_state['battle_logs'] = init_logs
    st.session_state['turn_actions'] = actions
    # Множество отыгранных слотов: (unit_name, slot_idx)
    st.session_state['executed_slots'] = set()
    st.session_state['turn_phase'] = 'fighting'
    st.session_state['action_idx'] = 0


def step_next():
    """Выполнение следующего действия в очереди."""
    actions = st.session_state.get('turn_actions', [])
    idx = st.session_state.get('action_idx', 0)

    if idx < len(actions):
        sys_clash = ClashSystem()
        act = actions[idx]
        # Выполняем действие
        logs = sys_clash.execute_single_action(act, st.session_state['executed_slots'])
        st.session_state['battle_logs'].extend(logs)
        st.session_state['action_idx'] += 1

    # Если действия кончились, завершаем раунд
    if st.session_state['action_idx'] >= len(actions):
        step_finish()


def step_finish():
    """Завершение фазы боя."""
    l_team, r_team = get_teams()
    sys_clash = ClashSystem()

    # События конца хода (End of Combat Events)
    end_logs = sys_clash.finalize_turn(l_team + r_team)
    st.session_state['battle_logs'].extend(end_logs)

    finish_round_logic()


def execute_combat_auto():
    """Автоматический расчет всего раунда."""
    l_team, r_team = get_teams()
    sys_clash = ClashSystem()

    with capture_output() as captured:
        logs = sys_clash.resolve_turn(l_team, r_team)

    st.session_state['battle_logs'] = logs
    st.session_state['script_logs'] = captured.getvalue()

    finish_round_logic()


def finish_round_logic():
    """
    Общая логика завершения раунда (очистка, кулдауны, реген).
    """
    l_team, r_team = get_teams()
    all_units = l_team + r_team
    msg = []

    def log_collector(message):
        msg.append(message)

    for u in all_units:
        # 1. Восстановление Stagger после стана
        if u.active_slots and u.active_slots[0].get('stunned'):
            u.current_stagger = u.max_stagger
            msg.append(f"✨ {u.name} recovered!")

        # Контекст союзников
        my_allies = l_team if u in l_team else r_team

        # 2. ЗАПУСК СОБЫТИЙ (Passives, Talents, Augmentations, Weapons, Statuses)
        # trigger_mechanics сам найдет все механики и вызовет у них on_round_end
        if hasattr(u, "trigger_mechanics"):
            u.trigger_mechanics("on_round_end", u, log_collector, allies=my_allies)

        # 3. Жизненный цикл статусов (снижение длительности)
        # Получаем логи (например, от активации Delayed статусов) и добавляем в общий список
        status_logs = StatusManager.process_turn_end(u)
        msg.extend(status_logs)

        # 4. Техническая очистка
        u.tick_cooldowns()
        u.active_slots = []
        if hasattr(u, 'stored_dice') and u.stored_dice:
            u.stored_dice = []
            msg.append(f"{u.name}: Stored evade dice burned.") # Опционально логировать
    st.session_state['round_number'] = st.session_state.get('round_number', 1) + 1
    st.session_state['turn_message'] = " ".join(msg) if msg else "Round Complete."
    st.session_state['phase'] = 'roll'
    st.session_state['turn_phase'] = 'done'


def reset_game():
    """
    Сброс боя. Восстанавливает состояние персонажей до того момента,
    как они вступили в бой (start_of_battle_stats).
    """
    l_team, r_team = get_teams()
    all_units = l_team + r_team

    for u in all_units:
        # 1. Чистим память боя
        u.memory.pop("battle_initialized", None)  # Чтобы сработал on_combat_start заново

        # Сохраняем временные ключи, которые нужны (например, сам снимок)
        saved_stats = u.memory.get('start_of_battle_stats')

        # 2. Восстанавливаем статы из снимка
        if saved_stats:
            u.current_hp = saved_stats['hp']
            u.current_sp = saved_stats['sp']
            u.current_stagger = saved_stats['stagger']
        else:
            # Если снимка нет (легаси), сбрасываем в макс (как было раньше)
            u.current_hp = u.max_hp
            u.current_stagger = u.max_stagger
            u.current_sp = u.max_sp

        # 3. Очистка эффектов
        u.active_buffs = {}
        u.card_cooldowns = {}
        u.cooldowns = {}
        u.recalculate_stats()
        u._status_effects = {}
        u.delayed_queue = []
        u.active_slots = []
        u.overkill_damage = 0
        u.stored_dice = []


    st.session_state['battle_logs'] = []
    st.session_state['script_logs'] = ""
    st.session_state['turn_message'] = "Game Reset to Pre-Battle State. Press 'Roll Initiative'."
    st.session_state['phase'] = 'roll'
    st.session_state['round_number'] = 1