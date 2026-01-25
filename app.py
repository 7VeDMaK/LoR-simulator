import streamlit as st

# Модули управления приложением
from ui.app_modules.state_controller import render_save_manager_sidebar, load_initial_state, update_and_save_state
from ui.app_modules.team_builder import render_team_builder_sidebar
from ui.cheat_sheet import render_cheat_sheet_page
from ui.checks import render_checks_page
from ui.editor.editor import render_editor_page
from ui.leveling import render_leveling_page
from ui.profile.main import render_profile_page
from ui.relationships import render_relationships_page
# Страницы
from ui.simulator.simulator import render_simulator_page
from ui.styles import apply_styles
from ui.tree_view import render_skill_tree_page

# 1. Применяем CSS
apply_styles()

# 2. Сайдбар: Менеджер сохранений
render_save_manager_sidebar()

# 3. Загрузка данных (если нужно)
load_initial_state()

# 4. Навигация
pages = [
    "⚔️ Simulator",
    "👤 Profile",
    "🌳 Skill Tree",
    "📈 Leveling",
    "🛠️ Card Editor",
    "🎲 Checks",
    "❤️ Relationships",  # <--- НОВЫЙ ПУНКТ
    "📚 Cheat Sheet"
]
page = st.sidebar.radio("Go to", pages, key="nav_page", on_change=update_and_save_state)

# 5. Маршрутизация
if "Simulator" in page:
    render_team_builder_sidebar() # Доп. панель только для симулятора
    render_simulator_page()

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

elif "Relationships" in page:
    render_relationships_page()

else:
    render_editor_page()