import streamlit as st

from logic.clash import ClashSystem
from logic.statuses.status_manager import StatusManager
from logic.state_manager import StateManager
from ui.simulator.logic.simulator_logic import get_teams, set_cooldowns, capture_output


def roll_phase():
    """
    Фаза броска скорости.
    """
    # 1. Сначала выполняем логику начала раунда и бросков
    l_team, r_team = get_teams()
    all_units = l_team + r_team

    # === TRIGGERS (События начала) ===
    for u in all_units:
        u.recalculate_stats()
        set_cooldowns(u)

        opponents = r_team if u in l_team else l_team
        my_allies = l_team if u in l_team else r_team

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

    # === БРОСОК КУБИКОВ ===
    for u in all_units:
        u.recalculate_stats()

        if u.is_staggered():
            u.active_slots = [{
                'speed': 0, 'card': None,
                'target_unit_idx': -1, 'target_slot_idx': -1,
                'stunned': True, 'is_aggro': False
            }]
        else:
            # Генерация случайных чисел происходит ЗДЕСЬ
            u.roll_speed_dice()

            for s in u.active_slots:
                s['target_unit_idx'] = -1;
                s['target_slot_idx'] = -1;
                s['is_aggro'] = False;
                s['force_clash'] = False

    # === SPEED ROLLED EVENTS ===
    for u in all_units:
        opponents = r_team if u in l_team else l_team
        my_allies = l_team if u in l_team else r_team

        def log_speed(msg):
            if 'battle_logs' not in st.session_state: st.session_state['battle_logs'] = []
            st.session_state['battle_logs'].append({
                "round": "Speed Roll", "rolls": "Passive", "details": f"⚡ **{u.name}**: {msg}"
            })

        if hasattr(u, "trigger_mechanics"):
            u.trigger_mechanics("on_speed_rolled", u, log_speed,
                                enemies=opponents, allies=my_allies)

    for u in all_units:
        u.recalculate_stats()

    # Переключаем фазу
    st.session_state['phase'] = 'planning'
    st.session_state['turn_message'] = "🎲 Speed Rolled (Targets Auto-Assigned)"

    # === [FIX] СОХРАНЕНИЕ ИСТОРИИ (ТЕПЕРЬ В КОНЦЕ) ===
    # Мы сохраняем состояние, когда кубики УЖЕ брошены и фаза 'planning'.
    # Это гарантирует, что при загрузке мы увидим те же самые числа.

    if 'undo_stack' not in st.session_state:
        st.session_state['undo_stack'] = []

    if not st.session_state['undo_stack']:
        # Первый раунд -> Полный слепок
        snapshot = StateManager.get_state_snapshot(st.session_state)
    else:
        # Последующие -> Динамический слепок
        snapshot = StateManager.get_dynamic_snapshot(st.session_state)

    st.session_state['undo_stack'].append(snapshot)

    # Лимит истории
    if len(st.session_state['undo_stack']) > 50:
        st.session_state['undo_stack'].pop(1)  # Не удаляем базу [0]

    # Сохраняем в файл для надежности
    StateManager.save_state(st.session_state, filename=st.session_state.get("current_state_file", "default"))


def step_start():
    l_team, r_team = get_teams()
    sys_clash = ClashSystem()

    init_logs, actions = sys_clash.prepare_turn(l_team, r_team)

    st.session_state['battle_logs'] = init_logs
    st.session_state['turn_actions'] = actions
    st.session_state['executed_slots'] = set()
    st.session_state['turn_phase'] = 'fighting'
    st.session_state['action_idx'] = 0


def step_next():
    actions = st.session_state.get('turn_actions', [])
    idx = st.session_state.get('action_idx', 0)

    if idx < len(actions):
        sys_clash = ClashSystem()
        act = actions[idx]
        logs = sys_clash.execute_single_action(act, st.session_state['executed_slots'])
        st.session_state['battle_logs'].extend(logs)
        st.session_state['action_idx'] += 1

    StateManager.save_state(st.session_state, filename=st.session_state.get("current_state_file", "default"))

    if st.session_state['action_idx'] >= len(actions):
        step_finish()


def step_finish():
    l_team, r_team = get_teams()
    sys_clash = ClashSystem()
    end_logs = sys_clash.finalize_turn(l_team + r_team)
    st.session_state['battle_logs'].extend(end_logs)
    finish_round_logic()


def execute_combat_auto():
    l_team, r_team = get_teams()
    sys_clash = ClashSystem()

    with capture_output() as captured:
        logs = sys_clash.resolve_turn(l_team, r_team)

    st.session_state['battle_logs'] = logs
    st.session_state['script_logs'] = captured.getvalue()
    finish_round_logic()


def finish_round_logic():
    l_team, r_team = get_teams()
    all_units = l_team + r_team
    msg = []

    def log_collector(message):
        msg.append(message)

    for u in all_units:
        if u.active_slots and u.active_slots[0].get('stunned'):
            u.current_stagger = u.max_stagger
            msg.append(f"✨ {u.name} recovered!")

        my_allies = l_team if u in l_team else r_team

        if hasattr(u, "trigger_mechanics"):
            u.trigger_mechanics("on_round_end", u, log_collector, allies=my_allies)

        status_logs = StatusManager.process_turn_end(u)
        msg.extend(status_logs)

        u.tick_cooldowns()
        u.active_slots = []
        if hasattr(u, 'stored_dice') and u.stored_dice:
            u.stored_dice = []
            msg.append(f"{u.name}: Stored evade dice burned.")

    st.session_state['round_number'] = st.session_state.get('round_number', 1) + 1
    st.session_state['turn_message'] = " ".join(msg) if msg else "Round Complete."
    st.session_state['phase'] = 'roll'
    st.session_state['turn_phase'] = 'done'


def reset_game():
    l_team, r_team = get_teams()
    all_units = l_team + r_team

    for u in all_units:
        u.memory.pop("battle_initialized", None)
        saved_stats = u.memory.get('start_of_battle_stats')

        if saved_stats:
            u.current_hp = saved_stats['hp']
            u.current_sp = saved_stats['sp']
            u.current_stagger = saved_stats['stagger']
        else:
            u.current_hp = u.max_hp
            u.current_stagger = u.max_stagger
            u.current_sp = u.max_sp

        u.active_buffs = {}
        u.card_cooldowns = {}
        u.cooldowns = {}
        u.recalculate_stats()
        u._status_effects = {}
        u.delayed_queue = []
        u.active_slots = []
        u.overkill_damage = 0
        u.stored_dice = []
        u.death_count = 0

    st.session_state['battle_logs'] = []
    st.session_state['undo_stack'] = []  # Очищаем стек при сбросе
    st.session_state['script_logs'] = ""
    st.session_state['turn_message'] = "Game Reset to Pre-Battle State. Press 'Roll Initiative'."
    st.session_state['phase'] = 'roll'
    st.session_state['round_number'] = 1