# app.py
import streamlit as st
import os
import json

from core.unit.unit import Unit
from core.unit.unit_library import UnitLibrary
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

    # 2. Сохраняем ТОЛЬКО те виджеты, которые реально существуют сейчас
    if "team_left_names" in st.session_state:
        p_state["left"] = st.session_state["team_left_names"]
    if "team_right_names" in st.session_state:
        p_state["right"] = st.session_state["team_right_names"]

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

# --- ВОССТАНОВЛЕНИЕ (Функция-помощник) ---
p_state = st.session_state['persistent_state']


def restore_widget(session_key, json_key):
    # Восстанавливаем, только если ключа еще нет в сессии
    if session_key not in st.session_state and json_key in p_state:
        val = p_state[json_key]
        if val in roster_keys:
            st.session_state[session_key] = val


# Восстанавливаем страницу навигации сразу
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
                        ["⚔️ Simulator", "👤 Profile", "🌳 Skill Tree", "📈 Leveling", "🛠️ Card Editor", "🎲 Checks"],
                        key="nav_page", on_change=update_and_save_state)

# === СТРАНИЦА: SIMULATOR ===
if "Simulator" in page:
    # 1. Восстанавливаем ТОЛЬКО для этой страницы
    if 'team_left_names' not in st.session_state:
        valid = [n for n in p_state.get("left", []) if n in roster_keys]
        st.session_state['team_left_names'] = valid if valid else [roster_keys[0]]

    if 'team_right_names' not in st.session_state:
        valid = [n for n in p_state.get("right", []) if n in roster_keys]
        st.session_state['team_right_names'] = valid if valid else [
            roster_keys[-1] if len(roster_keys) > 1 else roster_keys[0]]

    # 2. Рендер
    st.sidebar.divider()
    st.sidebar.markdown("**Team Setup**")
    left_sel = st.sidebar.multiselect("Left Team", roster_keys, key="team_left_names")
    right_sel = st.sidebar.multiselect("Right Team", roster_keys, key="team_right_names")

    if st.sidebar.button("Apply Teams", type="primary"):
        st.session_state['team_left'] = [st.session_state['roster'][n] for n in left_sel]
        st.session_state['team_right'] = [st.session_state['roster'][n] for n in right_sel]
        st.session_state['battle_logs'] = []
        update_and_save_state()
        st.rerun()

    if not st.session_state['team_left'] and left_sel:
        st.session_state['team_left'] = [st.session_state['roster'][n] for n in left_sel]
    if not st.session_state['team_right'] and right_sel:
        st.session_state['team_right'] = [st.session_state['roster'][n] for n in right_sel]

    if st.session_state['team_left']: st.session_state['attacker'] = st.session_state['team_left'][0]
    if st.session_state['team_right']: st.session_state['defender'] = st.session_state['team_right'][0]

    render_simulator_page()

# === СТРАНИЦА: PROFILE ===
elif "Profile" in page:
    restore_widget("profile_selected_unit", "profile_unit")
    render_profile_page()

# === СТРАНИЦА: CHECKS ===
elif "Checks" in page:
    restore_widget("checks_selected_unit", "checks_unit")
    render_checks_page()

# === СТРАНИЦА: LEVELING ===
elif "Leveling" in page:
    restore_widget("leveling_selected_unit", "leveling_unit")
    render_leveling_page()

# === СТРАНИЦА: SKILL TREE ===
elif "Skill Tree" in page:
    restore_widget("tree_selected_unit", "tree_unit")
    render_skill_tree_page()

else:
    render_editor_page()