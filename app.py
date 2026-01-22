import copy
import streamlit as st

# Импортируем менеджер состояния
from logic.state_manager import StateManager

from core.unit.unit import Unit
from core.unit.unit_library import UnitLibrary
from ui.cheat_sheet import render_cheat_sheet_page
from ui.checks import render_checks_page
from ui.editor.editor import render_editor_page
from ui.leveling import render_leveling_page
from ui.profile.main import render_profile_page
from ui.simulator.simulator import render_simulator_page
from ui.styles import apply_styles
from ui.tree_view import render_skill_tree_page

# Применяем стили
apply_styles()

# --- 0. МЕНЕДЖЕР СТЕЙТОВ (ВЫБОР ФАЙЛА) ---
st.sidebar.title("Navigation")

# Инициализация переменной текущего файла
if "current_state_file" not in st.session_state:
    st.session_state["current_state_file"] = "default"

with st.sidebar.expander("💾 Менеджер Сейвов", expanded=False):
    # 1. Список доступных сейвов
    available_states = StateManager.get_available_states()
    if not available_states:
        available_states = ["default"]

    # Индекс текущего файла в списке
    curr_idx = 0
    if st.session_state["current_state_file"] in available_states:
        curr_idx = available_states.index(st.session_state["current_state_file"])

    # 2. Селектор для выбора файла загрузки
    selected_state = st.selectbox(
        "Текущий файл:",
        available_states,
        index=curr_idx,
        key="state_file_selector"
    )

    # Если пользователь сменил файл в селекторе -> Перезагружаем приложение с новыми данными
    if selected_state != st.session_state["current_state_file"]:
        st.session_state["current_state_file"] = selected_state
        # Сбрасываем флаг загрузки, чтобы блок init (ниже) загрузил данные из нового файла
        st.session_state['teams_loaded'] = False
        st.rerun()

    # 3. Создание нового сейва
    new_state_name = st.text_input("Новое сохранение", placeholder="Название...")
    if st.button("➕ Создать", key="create_state_btn"):
        if new_state_name and new_state_name not in available_states:
            if StateManager.create_new_state(new_state_name):
                st.session_state["current_state_file"] = new_state_name
                st.session_state['teams_loaded'] = False  # Загружаем "чистый" стейт
                st.rerun()
        elif new_state_name in available_states:
            st.error("Такое имя уже есть!")

    # 4. Удаление текущего сейва (кроме default)
    if st.session_state["current_state_file"] != "default":
        if st.button("🗑️ Удалить текущий", type="primary"):
            StateManager.delete_state(st.session_state["current_state_file"])
            st.session_state["current_state_file"] = "default"
            st.session_state['teams_loaded'] = False
            st.rerun()

st.sidebar.divider()

# --- 1. ИНИЦИАЛИЗАЦИЯ РОСТЕРА ---
if 'roster' not in st.session_state:
    st.session_state['roster'] = UnitLibrary.load_all() or {"Roland": Unit("Roland")}

roster_keys = sorted(list(st.session_state['roster'].keys()))
if not roster_keys: st.stop()


# --- 2. ФУНКЦИЯ СОХРАНЕНИЯ (CALLBACK) ---
def update_and_save_state():
    """
    Сохраняет полное состояние сессии через StateManager в ТЕКУЩИЙ ВЫБРАННЫЙ файл.
    Вызывается при любом изменении в UI (on_change).
    """
    current_file = st.session_state.get("current_state_file", "default")
    StateManager.save_state(st.session_state, filename=current_file)


if 'save_callback' not in st.session_state:
    st.session_state['save_callback'] = update_and_save_state

# --- 3. ЗАГРУЗКА СОСТОЯНИЯ (RESTORE) ---
# Загружаем, если это первый запуск ИЛИ если мы принудительно сбросили флаг (при смене файла)
if 'teams_loaded' not in st.session_state or not st.session_state['teams_loaded']:

    current_file = st.session_state.get("current_state_file", "default")

    # 1. Загружаем сырые данные из ВЫБРАННОГО JSON файла
    saved_data = StateManager.load_state(filename=current_file)

    # 2. Восстанавливаем команды (Юниты + их слоты/статусы/карты)
    l_data = saved_data.get("team_left_data", [])
    r_data = saved_data.get("team_right_data", [])

    team_left = []
    for d in l_data:
        try:
            u = Unit.from_dict(d)
            team_left.append(u)
        except Exception as e:
            print(f"Error loading left unit: {e}")

    team_right = []
    for d in r_data:
        try:
            u = Unit.from_dict(d)
            team_right.append(u)
        except Exception as e:
            print(f"Error loading right unit: {e}")

    # Обязательный пересчет статов после загрузки
    for u in team_left + team_right:
        u.recalculate_stats()

    st.session_state['team_left'] = team_left
    st.session_state['team_right'] = team_right

    # 3. Восстанавливаем глобальные переменные боя
    st.session_state['phase'] = saved_data.get('phase', 'roll')
    st.session_state['round_number'] = saved_data.get('round_number', 1)
    st.session_state['turn_message'] = saved_data.get('turn_message', "")
    st.session_state['battle_logs'] = saved_data.get('battle_logs', [])
    st.session_state['script_logs'] = saved_data.get('script_logs', "")

    st.session_state['turn_phase'] = saved_data.get('turn_phase', 'planning')
    st.session_state['action_idx'] = saved_data.get('action_idx', 0)

    # Восстанавливаем сет выполненных слотов (из списка)
    st.session_state['executed_slots'] = set()
    for item in saved_data.get('executed_slots', []):
        st.session_state['executed_slots'].add(tuple(item))  # (name, idx)

    # 4. Восстанавливаем Очередь Действий (Actions)
    raw_actions = saved_data.get('turn_actions', [])
    if raw_actions:
        st.session_state['turn_actions'] = StateManager.restore_actions(
            raw_actions, team_left, team_right
        )
    else:
        st.session_state['turn_actions'] = []

    # 5. Восстанавливаем селекторы UI
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

    # Восстанавливаем навигацию
    st.session_state['nav_page'] = saved_data.get("page", "⚔️ Simulator")

    # Ставим флаг, что загрузка завершена для текущей сессии
    st.session_state['teams_loaded'] = True

# --- 4. ОТРИСОВКА ИНТЕРФЕЙСА ---
# (навигация была выше, в сайдбаре)

pages = ["⚔️ Simulator", "👤 Profile", "🌳 Skill Tree", "📈 Leveling", "🛠️ Card Editor", "🎲 Checks", "📚 Cheat Sheet"]

# Навигация с коллбэком сохранения
page = st.sidebar.radio("Go to", pages, key="nav_page", on_change=update_and_save_state)

# === СТРАНИЦА: SIMULATOR ===
if "Simulator" in page:
    st.sidebar.divider()
    st.sidebar.subheader("⚔️ Team Builder")

    current_phase = st.session_state.get('phase', 'roll')
    is_team_locked = current_phase != 'roll'

    if is_team_locked:
        st.sidebar.info("🔒 Идет бой. Изменение команд заблокировано.")

    # 1. Выбор юнита для добавления
    unit_to_add_name = st.sidebar.selectbox(
        "Выберите персонажа",
        roster_keys,
        key="sim_unit_add_sel",
        disabled=is_team_locked
    )

    as_template = st.sidebar.checkbox(
        "Добавить как копию (Шаблон)",
        value=False,
        help="Вкл: создает независимую копию. Выкл: добавляет ссылку на оригинал.",
        disabled=is_team_locked
    )


    def add_unit_to_team(target_list_key):
        if not unit_to_add_name: return
        base_unit = st.session_state['roster'][unit_to_add_name]
        unit_to_add = None

        if as_template:
            unit_to_add = copy.deepcopy(base_unit)
            existing_names = [u.name for u in st.session_state['team_left'] + st.session_state['team_right']]
            count = 0
            for name in existing_names:
                if name.startswith(base_unit.name):
                    count += 1
            if count > 0:
                unit_to_add.name = f"{base_unit.name} {count + 1}"
        else:
            all_current_units = st.session_state['team_left'] + st.session_state['team_right']
            if any(u is base_unit for u in all_current_units):
                st.sidebar.error(f"❌ {base_unit.name} уже в команде! (Используйте режим копии для дублей)")
                return
            unit_to_add = base_unit

        # Инициализация боевой памяти
        unit_to_add.memory['start_of_battle_stats'] = {
            'hp': unit_to_add.current_hp,
            'sp': unit_to_add.current_sp,
            'stagger': unit_to_add.current_stagger
        }

        st.session_state[target_list_key].append(unit_to_add)
        st.session_state['battle_logs'] = []
        update_and_save_state()


    c_add_l, c_add_r = st.sidebar.columns(2)

    if c_add_l.button("⬅️ Add Left", width='stretch', disabled=is_team_locked):
        add_unit_to_team('team_left')
        st.rerun()

    if c_add_r.button("Add Right ➡️", width='stretch', disabled=is_team_locked):
        add_unit_to_team('team_right')
        st.rerun()

    st.sidebar.markdown("---")


    def remove_unit(team_key, idx):
        st.session_state[team_key].pop(idx)
        update_and_save_state()
        st.rerun()


    st.sidebar.markdown(f"**Left Team ({len(st.session_state['team_left'])})**")
    if st.session_state['team_left']:
        for i, u in enumerate(st.session_state['team_left']):
            c_name, c_del = st.sidebar.columns([4, 1])
            c_name.caption(f"{i + 1}. {u.name} (Lvl {u.level})")
            if c_del.button("❌", key=f"del_l_{i}", disabled=is_team_locked):
                remove_unit('team_left', i)
    else:
        st.sidebar.caption("Пусто")

    st.sidebar.markdown(f"**Right Team ({len(st.session_state['team_right'])})**")
    if st.session_state['team_right']:
        for i, u in enumerate(st.session_state['team_right']):
            c_name, c_del = st.sidebar.columns([4, 1])
            c_name.caption(f"{i + 1}. {u.name} (Lvl {u.level})")
            if c_del.button("❌", key=f"del_r_{i}", disabled=is_team_locked):
                remove_unit('team_right', i)
    else:
        st.sidebar.caption("Пусто")

    if st.sidebar.button("🗑️ Очистить все команды", width='stretch', disabled=is_team_locked):
        st.session_state['team_left'] = []
        st.session_state['team_right'] = []
        st.session_state['battle_logs'] = []
        update_and_save_state()
        st.rerun()

    render_simulator_page()

# === ОСТАЛЬНЫЕ СТРАНИЦЫ ===
elif "Profile" in page:
    render_profile_page()

elif "Checks" in page:
    render_checks_page()

elif "Leveling" in page:
    render_leveling_page()

elif "Skill Tree" in page:
    render_skill_tree_page()

elif "Cheat Sheet" in page:
    render_cheat_sheet_page()

else:
    render_editor_page()