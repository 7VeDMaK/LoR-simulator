import streamlit as st

from core.library import Library
from core.unit.unit import Unit
from core.unit.unit_library import UnitLibrary
from logic.state.state_manager import StateManager


def update_and_save_state():
    """
    Callback: Сохраняет полное состояние сессии в текущий файл.
    """
    current_file = st.session_state.get("current_state_file", "default")
    StateManager.save_state(st.session_state, filename=current_file)


def render_save_manager_sidebar():
    """Отрисовывает менеджер сохранений в сайдбаре."""
    st.sidebar.title("Navigation")

    if "current_state_file" not in st.session_state:
        st.session_state["current_state_file"] = "default"

    with st.sidebar.expander("💾 Менеджер Сейвов", expanded=False):
        available_states = StateManager.get_available_states() or ["default"]

        curr_idx = 0
        if st.session_state["current_state_file"] in available_states:
            curr_idx = available_states.index(st.session_state["current_state_file"])

        selected_state = st.selectbox(
            "Текущий файл:", available_states, index=curr_idx, key="state_file_selector"
        )

        # Смена файла -> Перезагрузка
        if selected_state != st.session_state["current_state_file"]:
            st.session_state["current_state_file"] = selected_state
            st.session_state['teams_loaded'] = False
            st.rerun()

        # Создание нового
        new_state_name = st.text_input("Новое сохранение", placeholder="Название...")
        if st.button("➕ Создать", key="create_state_btn"):
            if new_state_name and new_state_name not in available_states:
                if StateManager.create_new_state(new_state_name):
                    st.session_state["current_state_file"] = new_state_name
                    st.session_state['teams_loaded'] = False
                    st.rerun()
            elif new_state_name in available_states:
                st.error("Такое имя уже есть!")

        # Удаление
        if st.session_state["current_state_file"] != "default":
            if st.button("🗑️ Удалить текущий", type="primary"):
                StateManager.delete_state(st.session_state["current_state_file"])
                st.session_state["current_state_file"] = "default"
                st.session_state['teams_loaded'] = False
                st.rerun()

    st.sidebar.divider()


def load_initial_state():
    """
    Загружает состояние из файла при старте или смене профиля.
    """
    # 0. Загрузка библиотеки карт
    if not Library.get_cards_dict():
        Library.load_all()
    
    # 1. Инициализация Ростера
    if 'roster' not in st.session_state:
        st.session_state['roster'] = UnitLibrary.load_all() or {"Roland": Unit("Roland")}

    roster_keys = sorted(list(st.session_state['roster'].keys()))
    if not roster_keys: st.stop()

    # 2. Инициализация Callback
    if 'save_callback' not in st.session_state:
        st.session_state['save_callback'] = update_and_save_state

    # 3. Восстановление данных (Restore)
    if 'teams_loaded' not in st.session_state or not st.session_state['teams_loaded']:
        current_file = st.session_state.get("current_state_file", "default")
        saved_data = StateManager.load_state(filename=current_file)

        # Восстановление команд
        l_data = saved_data.get("team_left_data", [])
        r_data = saved_data.get("team_right_data", [])

        team_left = []
        for d in l_data:
            try:
                team_left.append(Unit.from_dict(d))
            except Exception as e:
                print(f"Error loading left unit: {e}")

        team_right = []
        for d in r_data:
            try:
                team_right.append(Unit.from_dict(d))
            except Exception as e:
                print(f"Error loading right unit: {e}")

        for u in team_left + team_right: u.recalculate_stats()

        st.session_state['team_left'] = team_left
        st.session_state['team_right'] = team_right

        # Глобальные переменные
        st.session_state['phase'] = saved_data.get('phase', 'roll')
        st.session_state['round_number'] = saved_data.get('round_number', 1)
        st.session_state['turn_message'] = saved_data.get('turn_message', "")
        st.session_state['battle_logs'] = saved_data.get('battle_logs', [])
        st.session_state['script_logs'] = saved_data.get('script_logs', "")
        st.session_state['turn_phase'] = saved_data.get('turn_phase', 'planning')
        st.session_state['action_idx'] = saved_data.get('action_idx', 0)

        st.session_state['executed_slots'] = set()
        for item in saved_data.get('executed_slots', []):
            st.session_state['executed_slots'].add(tuple(item))

        # Actions
        raw_actions = saved_data.get('turn_actions', [])
        if raw_actions:
            st.session_state['turn_actions'] = StateManager.restore_actions(raw_actions, team_left, team_right)
        else:
            st.session_state['turn_actions'] = []

        # Селекторы
        selector_mapping = {
            "profile_unit": "profile_selected_unit",
            "leveling_unit": "leveling_selected_unit",
            "tree_unit": "tree_selected_unit",
            "checks_unit": "checks_selected_unit",
        }
        for json_key, session_key in selector_mapping.items():
            saved_val = saved_data.get(json_key)
            if saved_val and saved_val in roster_keys:
                st.session_state[session_key] = saved_val
            elif roster_keys and session_key not in st.session_state:
                st.session_state[session_key] = roster_keys[0]

        st.session_state['nav_page'] = saved_data.get("page", "⚔️ Simulator")
        st.session_state['teams_loaded'] = True