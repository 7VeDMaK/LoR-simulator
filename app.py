# app.py
import streamlit as st
import os
import json
import copy

from core.unit.unit import Unit
from core.unit.unit_library import UnitLibrary
from ui.cheat_sheet import render_cheat_sheet_page
from ui.checks import render_checks_page
from ui.leveling import render_leveling_page
from ui.profile.main import render_profile_page
from ui.styles import apply_styles
from ui.simulator.simulator import render_simulator_page
from ui.editor.editor import render_editor_page
from ui.tree_view import render_skill_tree_page

apply_styles()

STATE_FILE = "data/simulator_state.json"


def load_from_disk():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content: return json.loads(content)
        except Exception as e:
            print(f"Error loading: {e}")
    return {}


def save_to_disk(data):
    try:
        os.makedirs("data", exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"Error saving: {e}")


if 'persistent_state' not in st.session_state:
    st.session_state['persistent_state'] = load_from_disk()


def update_and_save_state():
    p_state = st.session_state['persistent_state']

    # 1. Навигация
    p_state["page"] = st.session_state.get("nav_page", "⚔️ Simulator")

    # Сохраняем селекторы
    keys_map = {
        "profile_selected_unit": "profile_unit",
        "leveling_selected_unit": "leveling_unit",
        "tree_selected_unit": "tree_unit",
        "checks_selected_unit": "checks_unit"
    }

    for session_key, json_key in keys_map.items():
        if session_key in st.session_state:
            p_state[json_key] = st.session_state[session_key]

    save_to_disk(p_state)


if 'save_callback' not in st.session_state:
    st.session_state['save_callback'] = update_and_save_state

if 'roster' not in st.session_state:
    st.session_state['roster'] = UnitLibrary.load_all() or {"Roland": Unit("Roland")}

roster_keys = sorted(list(st.session_state['roster'].keys()))
if not roster_keys: st.stop()

p_state = st.session_state['persistent_state']


def restore_widget(session_key, json_key):
    if session_key not in st.session_state and json_key in p_state:
        val = p_state[json_key]
        if val in roster_keys:
            st.session_state[session_key] = val


if 'nav_page' not in st.session_state:
    st.session_state['nav_page'] = p_state.get("page", "⚔️ Simulator")

# --- ГЛОБАЛЬНЫЕ ОБЪЕКТЫ ---
if 'team_left' not in st.session_state: st.session_state['team_left'] = []
if 'team_right' not in st.session_state: st.session_state['team_right'] = []
if 'battle_logs' not in st.session_state: st.session_state['battle_logs'] = []
if 'script_logs' not in st.session_state: st.session_state['script_logs'] = ""

# --- ОТРИСОВКА ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to",
                        ["⚔️ Simulator", "👤 Profile", "🌳 Skill Tree", "📈 Leveling", "🛠️ Card Editor", "🎲 Checks",
                         "📚 Cheat Sheet"],
                        key="nav_page", on_change=update_and_save_state)

# === СТРАНИЦА: SIMULATOR ===
if "Simulator" in page:
    st.sidebar.divider()
    st.sidebar.subheader("⚔️ Team Builder")

    current_phase = st.session_state.get('phase', 'roll')
    is_team_locked = current_phase != 'roll'

    unit_to_add_name = st.sidebar.selectbox(
        "Выберите персонажа",
        roster_keys,
        key="sim_unit_add_sel",
        disabled=is_team_locked
    )
    # 2. Кнопки добавления
    c_add_l, c_add_r = st.sidebar.columns(2)

    if c_add_l.button("⬅️ Add Left", use_container_width=True, disabled=is_team_locked):
        if unit_to_add_name:
            base_unit = st.session_state['roster'][unit_to_add_name]
            new_unit = copy.deepcopy(base_unit)

            count = len([u for u in st.session_state['team_left'] if u.name.startswith(base_unit.name)])
            if count > 0:
                new_unit.name = f"{base_unit.name} {count + 1}"

            st.session_state['team_left'].append(new_unit)
            # Сброс логов при изменении состава
            st.session_state['battle_logs'] = []
            st.rerun()

    if c_add_r.button("Add Right ➡️", use_container_width=True, disabled=is_team_locked):
        if unit_to_add_name:
            base_unit = st.session_state['roster'][unit_to_add_name]
            new_unit = copy.deepcopy(base_unit)

            count = len([u for u in st.session_state['team_right'] if u.name.startswith(base_unit.name)])
            if count > 0:
                new_unit.name = f"{base_unit.name} {count + 1}"

            st.session_state['team_right'].append(new_unit)
            st.session_state['battle_logs'] = []
            st.rerun()

    st.sidebar.markdown("---")

    # --- LEFT TEAM ---
    st.sidebar.markdown(f"**Left Team ({len(st.session_state['team_left'])})**")
    if st.session_state['team_left']:
        for i, u in enumerate(st.session_state['team_left']):
            c_name, c_del = st.sidebar.columns([4, 1])
            c_name.caption(f"{i + 1}. {u.name} (Lvl {u.level})")
            if c_del.button("❌", key=f"del_l_{i}", disabled=is_team_locked):
                st.session_state['team_left'].pop(i)
                st.rerun()
    else:
        st.sidebar.caption("Пусто")

    # --- RIGHT TEAM ---
    st.sidebar.markdown(f"**Right Team ({len(st.session_state['team_right'])})**")
    if st.session_state['team_right']:
        for i, u in enumerate(st.session_state['team_right']):
            c_name, c_del = st.sidebar.columns([4, 1])
            c_name.caption(f"{i + 1}. {u.name} (Lvl {u.level})")
            if c_del.button("❌", key=f"del_r_{i}", disabled=is_team_locked):
                st.session_state['team_right'].pop(i)
                st.rerun()
    else:
        st.sidebar.caption("Пусто")

    # Кнопка очистки
    if st.sidebar.button("🗑️ Очистить все команды", use_container_width=True, disabled=is_team_locked):
        st.session_state['team_left'] = []
        st.session_state['team_right'] = []
        st.session_state['battle_logs'] = []
        st.rerun()

    render_simulator_page()

# === ОСТАЛЬНЫЕ СТРАНИЦЫ ===
elif "Profile" in page:
    restore_widget("profile_selected_unit", "profile_unit")
    render_profile_page()

elif "Checks" in page:
    restore_widget("checks_selected_unit", "checks_unit")
    render_checks_page()

elif "Leveling" in page:
    restore_widget("leveling_selected_unit", "leveling_unit")
    render_leveling_page()

elif "Skill Tree" in page:
    restore_widget("tree_selected_unit", "tree_unit")
    render_skill_tree_page()

elif "Cheat Sheet" in page:
    render_cheat_sheet_page()

else:
    render_editor_page()