"""
Game Master Panel - панель для контроля боя в реальном времени
"""
import streamlit as st
from logic.statuses.status_definitions import STATUS_REGISTRY
from core.unit.unit_library import UnitLibrary
import copy
# Критические эффекты, требующие немедленного обновления UI
CRITICAL_EFFECTS = {
    'arrested', 'paralysis', 'bind', 'stagger_resist', 
    'invisibility', 'taunt', 'smoke', 'weakness',
    'fragile', 'vulnerable', 'barrier'
}

def _render_add_units_tab(team_left, team_right, all_units):
    """Вспомогательная функция для рендеринга таба добавления юнитов"""
    st.markdown("### ➕ Добавление персонажа в бой")
    
    # Загружаем библиотеку юнитов
    if 'unit_roster' not in st.session_state:
        st.session_state['unit_roster'] = UnitLibrary.load_all()
    
    roster = st.session_state.get('unit_roster', {})
    
    if not roster:
        st.warning("⚠️ Библиотека персонажей пуста. Создайте персонажей в редакторе профилей.")
        if st.button("🔄 Перезагрузить библиотеку"):
            st.session_state['unit_roster'] = UnitLibrary.load_all()
            st.rerun()
        return
    
    # Получаем список доступных юнитов (исключая уже добавленных)
    current_unit_names = [u.name for u in all_units]
    available_units = {name: unit for name, unit in roster.items() if name not in current_unit_names}
    
    if not available_units:
        st.info("ℹ️ Все персонажи из библиотеки уже добавлены в бой.")
        if st.button("🔄 Перезагрузить библиотеку"):
            st.session_state['unit_roster'] = UnitLibrary.load_all()
            st.rerun()
    else:
        # Выбор персонажа
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_unit_to_add = st.selectbox(
                "Выберите персонажа для добавления:",
                options=sorted(available_units.keys()),
                key="gm_unit_to_add"
            )
        
        with col2:
            target_team = st.radio(
                "Команда:",
                options=["Левая", "Правая"],
                key="gm_target_team",
                horizontal=False
            )
        
        # Показываем информацию о выбранном юните
        if selected_unit_to_add:
            unit_to_add = available_units[selected_unit_to_add]
            
            with st.expander("📋 Информация о персонаже", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("HP", f"{unit_to_add.max_hp}")
                with col2:
                    st.metric("SP", f"{unit_to_add.max_sp}")
                with col3:
                    st.metric("Выносливость", f"{unit_to_add.max_stagger}")
                
                st.caption(f"**Уровень:** {unit_to_add.level} | **Ранг:** {unit_to_add.rank}")
            
            st.divider()
            
            # Кнопка добавления
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button(
                    f"➕ Добавить {selected_unit_to_add} в {'левую' if target_team == 'Левая' else 'правую'} команду",
                    type="primary",
                    use_container_width=True
                ):
                    # Создаем копию юнита (чтобы не изменять оригинал из библиотеки)
                    new_unit = copy.deepcopy(unit_to_add)
                    
                    # Добавляем в выбранную команду
                    if target_team == "Левая":
                        team_left.append(new_unit)
                        st.session_state['team_left'] = team_left
                    else:
                        team_right.append(new_unit)
                        st.session_state['team_right'] = team_right
                    
                    st.toast(f"✅ {selected_unit_to_add} добавлен в {'левую' if target_team == 'Левая' else 'правую'} команду!")
                    st.rerun()
            
            with col2:
                if st.button("🔄 Обновить список", use_container_width=True):
                    st.session_state['unit_roster'] = UnitLibrary.load_all()
                    st.rerun()
    
    st.divider()
    
    # Удаление юнитов из боя
    st.markdown("### 🗑️ Удаление персонажей из боя")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🟦 Левая команда**")
        if team_left:
            for idx, unit in enumerate(team_left):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"• {unit.name}")
                with col_b:
                    if st.button("❌", key=f"gm_remove_left_{idx}"):
                        team_left.pop(idx)
                        st.session_state['team_left'] = team_left
                        st.toast(f"🗑️ {unit.name} удален из левой команды")
                        st.rerun()
        else:
            st.caption("Команда пуста")
    
    with col2:
        st.markdown("**🟥 Правая команда**")
        if team_right:
            for idx, unit in enumerate(team_right):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"• {unit.name}")
                with col_b:
                    if st.button("❌", key=f"gm_remove_right_{idx}"):
                        team_right.pop(idx)
                        st.session_state['team_right'] = team_right
                        st.toast(f"🗑️ {unit.name} удален из правой команды")
                        st.rerun()
        else:
            st.caption("Команда пуста")


def render_gm_panel():
    """Панель Game Master для редактирования параметров юнитов и наложения эффектов"""
    
    # Инициализация состояния GM панели
    if 'gm_panel_enabled' not in st.session_state:
        st.session_state['gm_panel_enabled'] = False
    
    st.divider()
    
    # Кнопка для включения/отключения панели
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("🎮 Game Master Panel")
    with col2:
        if st.button(
            "🔓 Открыть" if not st.session_state['gm_panel_enabled'] else "🔒 Закрыть",
            type="primary" if not st.session_state['gm_panel_enabled'] else "secondary",
            use_container_width=True
        ):
            st.session_state['gm_panel_enabled'] = not st.session_state['gm_panel_enabled']
            st.rerun()
    
    if not st.session_state['gm_panel_enabled']:
        st.caption("Панель Game Master выключена")
        return
    
    # Получаем все юниты из обеих команд
    team_left = st.session_state.get('team_left', [])
    team_right = st.session_state.get('team_right', [])
    all_units = team_left + team_right
    
    # Создаем контейнер с рамкой для GM панели
    with st.container(border=True):
        # Создаем табы для разных функций
        # Если нет юнитов, показываем только таб добавления
        if not all_units:
            st.info("ℹ️ Нет персонажей в бою. Добавьте персонажей через вкладку ниже.")
            tab_units = st.container()
            _render_add_units_tab(team_left, team_right, all_units)
            return
        
        # Выбор юнита
        unit_names = [unit.name for unit in all_units]
        selected_unit_name = st.selectbox(
            "Выберите юнита:",
            options=unit_names,
            key="gm_selected_unit"
        )
        
        # Находим выбранного юнита
        selected_unit = next((u for u in all_units if u.name == selected_unit_name), None)
        
        if not selected_unit:
            return
        
        st.markdown(f"**Редактирование:** `{selected_unit.name}`")
        st.divider()
        
        # Создаем табы для разных функций
        tab_stats, tab_effects, tab_units = st.tabs(["⚡ Параметры", "🧪 Эффекты", "➕ Добавить юнита"])
        
        # ===== ТАБ: ПАРАМЕТРЫ =====
        with tab_stats:
            st.markdown("### Основные параметры")
            
            # Здоровье
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                new_hp = st.number_input(
                    "Текущее HP:",
                    min_value=0,
                    max_value=selected_unit.max_hp,
                    value=selected_unit.current_hp,
                    step=1,
                    key=f"gm_hp_{selected_unit.name}"
                )
            with col2:
                st.metric("Max HP", selected_unit.max_hp)
            with col3:
                if st.button("💉 Применить", key=f"gm_apply_hp_{selected_unit.name}"):
                    selected_unit.current_hp = new_hp
                    st.toast(f"✅ HP обновлено: {new_hp}/{selected_unit.max_hp}")
                    # Не делаем rerun - обновление применится при следующем рендере
            
            # Рассудок
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                new_sp = st.number_input(
                    "Текущий SP:",
                    min_value=0,
                    max_value=selected_unit.max_sp,
                    value=selected_unit.current_sp,
                    step=1,
                    key=f"gm_sp_{selected_unit.name}"
                )
            with col2:
                st.metric("Max SP", selected_unit.max_sp)
            with col3:
                if st.button("🧠 Применить", key=f"gm_apply_sp_{selected_unit.name}"):
                    selected_unit.current_sp = new_sp
                    st.toast(f"✅ SP обновлено: {new_sp}/{selected_unit.max_sp}")
                    # Не делаем rerun - обновление применится при следующем рендере
            
            # Выносливость (Стаггер)
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                new_stagger = st.number_input(
                    "Текущая Выносливость:",
                    min_value=0,
                    max_value=selected_unit.max_stagger,
                    value=selected_unit.current_stagger,
                    step=1,
                    key=f"gm_stagger_{selected_unit.name}"
                )
            with col2:
                st.metric("Max Stagger", selected_unit.max_stagger)
            with col3:
                if st.button("⚡ Применить", key=f"gm_apply_stagger_{selected_unit.name}"):
                    selected_unit.current_stagger = new_stagger
                    st.toast(f"✅ Выносливость обновлена: {new_stagger}/{selected_unit.max_stagger}")
                    # Не делаем rerun
            
            st.divider()
            
            # Быстрые действия
            st.markdown("### 🎯 Быстрые действия")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("💚 Полное HP", use_container_width=True):
                    selected_unit.current_hp = selected_unit.max_hp
                    st.toast("✅ HP восстановлено полностью!")
            
            with col2:
                if st.button("💙 Полное SP", use_container_width=True):
                    selected_unit.current_sp = selected_unit.max_sp
                    st.toast("✅ SP восстановлено полностью!")
            
            with col3:
                if st.button("⚡ Полная Выносливость", use_container_width=True):
                    selected_unit.current_stagger = selected_unit.max_stagger
                    st.toast("✅ Выносливость восстановлена полностью!")
            
            with col4:
                if st.button("🔥 Все параметры", use_container_width=True):
                    selected_unit.current_hp = selected_unit.max_hp
                    selected_unit.current_sp = selected_unit.max_sp
                    selected_unit.current_stagger = selected_unit.max_stagger
                    st.toast("✅ Все параметры восстановлены!")
        
        # ===== ТАБ: ЭФФЕКТЫ =====
        with tab_effects:
            st.markdown("### 🧪 Наложение эффектов")
            
            # Получаем список всех доступных статусов
            available_statuses = sorted(STATUS_REGISTRY.keys())
            
            # Выбор эффекта
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_status = st.selectbox(
                    "Выберите эффект:",
                    options=available_statuses,
                    key="gm_status_select",
                    format_func=lambda x: x.replace('_', ' ').title()
                )
            
            with col2:
                status_amount = st.number_input(
                    "Стаки:",
                    min_value=1,
                    max_value=999,
                    value=1,
                    step=1,
                    key="gm_status_amount"
                )
            
            # Параметры эффекта
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                status_duration = st.number_input(
                    "Длительность (ходы):",
                    min_value=1,
                    max_value=99,
                    value=3,
                    step=1,
                    key="gm_status_duration"
                )
            
            with col2:
                status_delay = st.number_input(
                    "Задержка (ходы):",
                    min_value=0,
                    max_value=10,
                    value=0,
                    step=1,
                    key="gm_status_delay"
                )
            
            with col3:
                st.write("")  # Spacing
                st.write("")  # Spacing
                if st.button("➕ Наложить эффект", type="primary", use_container_width=True):
                    # Накладываем статус на юнита
                    success, msg = selected_unit.add_status(
                        selected_status,
                        status_amount,
                        duration=status_duration,
                        delay=status_delay
                    )
                    
                    if success:
                        delay_text = f" (Задержка: {status_delay} ходов)" if status_delay > 0 else ""
                        st.toast(f"✅ Наложен эффект: {selected_status} x{status_amount}{delay_text}")
                        st.rerun()
                    else:
                        st.error(f"❌ Не удалось наложить эффект: {msg or 'Неизвестная ошибка'}")
            
            st.divider()
            
            # Отображение текущих эффектов
            st.markdown("### 📋 Активные эффекты")
            current_statuses = selected_unit.statuses
            
            if current_statuses:
                for status_name, status_value in current_statuses.items():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{status_name.replace('_', ' ').title()}:** {status_value} стаков")
                    with col2:
                        if st.button("🗑️", key=f"gm_remove_{selected_unit.name}_{status_name}"):
                            # Удаляем эффект
                            if hasattr(selected_unit, '_status_effects') and status_name in selected_unit._status_effects:
                                del selected_unit._status_effects[status_name]
                                st.toast(f"✅ Эффект {status_name} удален")
                                st.rerun()
            else:
                st.caption("Нет активных эффектов")
            
            # Кнопка очистки всех эффектов
            if current_statuses:
                st.divider()
                if st.button("🧹 Очистить все эффекты", type="secondary", use_container_width=True):
                    if hasattr(selected_unit, '_status_effects'):
                        selected_unit._status_effects.clear()
                    if hasattr(selected_unit, 'delayed_queue'):
                        selected_unit.delayed_queue.clear()
                    st.toast("✅ Все эффекты очищены!")
                    st.rerun()
                    st.rerun()
        
        # ===== ТАБ: ДОБАВИТЬ ЮНИТА =====
        with tab_units:
            _render_add_units_tab(team_left, team_right, all_units)
