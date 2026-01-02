# app.py
import streamlit as st

from core.unit.unit import Unit
from core.unit.unit_library import UnitLibrary
from ui.checks import render_checks_page
from ui.leveling import render_leveling_page
from ui.profile.main import render_profile_page
from ui.styles import apply_styles
from ui.simulator.simulator import render_simulator_page
from ui.editor.editor import render_editor_page
from ui.tree_view import render_skill_tree_page

# Применяем CSS и конфиг
apply_styles()

# --- INIT ROSTER (ЗАГРУЗКА ИЗ ФАЙЛОВ) ---
if 'roster' not in st.session_state:
    loaded_roster = UnitLibrary.load_all()

    # Если папка пуста, создаем тестового Роланда
    if not loaded_roster:
        roland = Unit("Roland")
        # Настраиваем статы
        roland.attributes["endurance"] = 5
        roland.attributes["strength"] = 5
        roland.base_hp = 75  # База 20 + 75 = 95 (+ выносливость)

        # ВАЖНО: Пересчитываем статы и лечим его полностью при создании
        roland.recalculate_stats()
        roland.current_hp = roland.max_hp  # <--- Вот это фиксит проблему "20 хп"
        roland.current_sp = roland.max_sp

        UnitLibrary.save_unit(roland)
        loaded_roster = UnitLibrary.load_all()

    st.session_state['roster'] = loaded_roster

# --- SYNC SIMULATOR WITH ROSTER ---
# Проверяем валидность ключей (вдруг файл удалили, а сессия осталась)
roster_keys = list(st.session_state['roster'].keys())
if not roster_keys:
    st.error("Roster is empty! Please create a character in Profile tab.")
    st.stop()

# Дефолтный выбор бойцов
if 'team_left_names' not in st.session_state:
    st.session_state['team_left_names'] = [roster_keys[0]]
if 'team_right_names' not in st.session_state:
    st.session_state['team_right_names'] = [roster_keys[-1] if len(roster_keys) > 1 else roster_keys[0]]

# Объекты команд
if 'team_left' not in st.session_state: st.session_state['team_left'] = []
if 'team_right' not in st.session_state: st.session_state['team_right'] = []

# Логи
if 'battle_logs' not in st.session_state: st.session_state['battle_logs'] = []
if 'script_logs' not in st.session_state: st.session_state['script_logs'] = ""
if 'turn_message' not in st.session_state: st.session_state['turn_message'] = ""

# --- NAVIGATION ---
st.sidebar.title("Navigation")
# Добавляем "Skill Tree" в список
page = st.sidebar.radio("Go to",
                        ["⚔️ Simulator",
                         "👤 Profile",
                         "🌳 Skill Tree",
                         "📈 Leveling",
                         "🛠️ Card Editor",
                         "🎲 Checks"])

if "Simulator" in page:
    st.sidebar.divider()
    st.sidebar.markdown("**Team Setup**")

    # Мультивыбор для левой и правой команды
    left_sel = st.sidebar.multiselect("Left Team", roster_keys, default=st.session_state['team_left_names'])
    right_sel = st.sidebar.multiselect("Right Team", roster_keys, default=st.session_state['team_right_names'])

    # Кнопка обновления команд (чтобы не пересоздавать объекты каждый раз при клике)
    if st.sidebar.button("Apply Teams", type="primary"):
        st.session_state['team_left_names'] = left_sel
        st.session_state['team_right_names'] = right_sel

        # Пересоздаем объекты (загружаем свежие из библиотеки)
        st.session_state['team_left'] = [st.session_state['roster'][n] for n in left_sel]
        st.session_state['team_right'] = [st.session_state['roster'][n] for n in right_sel]

        # Сброс логов при смене команд
        st.session_state['battle_logs'] = []
        st.rerun()

    # Если объектов еще нет (первый запуск), создаем их
    if not st.session_state['team_left'] and left_sel:
        st.session_state['team_left'] = [st.session_state['roster'][n] for n in left_sel]
    if not st.session_state['team_right'] and right_sel:
        st.session_state['team_right'] = [st.session_state['roster'][n] for n in right_sel]

    # Для обратной совместимости некоторых старых функций (пока что) можно оставить attacker/defender как первых членов
    if st.session_state['team_left']: st.session_state['attacker'] = st.session_state['team_left'][0]
    if st.session_state['team_right']: st.session_state['defender'] = st.session_state['team_right'][0]

    render_simulator_page()

elif "Profile" in page:
    render_profile_page()
elif "Checks" in page:          # <--- Обработка новой страницы
    render_checks_page()
elif "Leveling" in page:      # <--- Добавляем блок
    render_leveling_page()
elif "Skill Tree" in page:
    render_skill_tree_page()
else:
    render_editor_page()