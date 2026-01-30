import streamlit as st

from core.tree_data import SKILL_TREE
from core.unit.unit_library import UnitLibrary
from logic.tree_logic import (
    can_unlock_talent,
    learn_talent,
    forget_talent,
    can_forget_talent,
    get_talent_info
)
from ui.components.text_renderer import render_styled_description


def render_skill_tree_page():
    st.title(f"🌳 Дерево Талантов")

    # 1. ВЫБОР ПЕРСОНАЖА
    if 'roster' not in st.session_state or not st.session_state['roster']:
        st.warning("Ростер пуст. Создайте персонажа в профиле.")
        return

    # [FIX 1] Сортируем список имен для стабильности
    roster_names = sorted(list(st.session_state['roster'].keys()))

    # [FIX 2] Вычисляем индекс на основе восстановленного стейта
    current_key = st.session_state.get("tree_selected_unit")
    default_index = 0

    if current_key in roster_names:
        default_index = roster_names.index(current_key)

    selected_name = st.selectbox(
        "Выберите персонажа для прокачки:",
        roster_names,
        index=default_index,  # <--- Явно задаем индекс
        key="tree_selected_unit",
        on_change=st.session_state.get('save_callback')
    )

    unit = st.session_state['roster'][selected_name]
    unit.recalculate_stats()

    # 2. ОЧКИ ТАЛАНТОВ
    bonus_slots = 0
    if "talent_slots" in unit.modifiers:
        bonus_slots = int(unit.modifiers["talent_slots"].get("flat", 0))

    max_pts = (unit.level // 3) + bonus_slots
    # Считаем только уникальные таланты (без заглушек)
    learned_ids = [t for t in unit.talents if t not in ["base_passive"]]

    # Фильтруем дубликаты (на всякий случай)
    learned_ids = list(set(learned_ids))
    spent_pts = len(learned_ids)
    available_pts = max_pts - spent_pts

    # Красивые метрики
    c1, c2, c3 = st.columns(3)
    c1.metric("Уровень", unit.level)
    c2.metric("Слоты талантов", f"{spent_pts} / {max_pts}")

    if available_pts > 0:
        c3.metric("Доступно очков", available_pts, delta=f"+{available_pts} free")
    elif available_pts < 0:
        c3.metric("Перерасход", available_pts, delta_color="inverse")
    else:
        c3.metric("Доступно очков", 0)

    st.divider()

    # 3. ОТРИСОВКА ДЕРЕВА
    branch_names = list(SKILL_TREE.keys())
    # Упрощаем названия табов (убираем "Ветка X: ")
    tab_labels = [b.split(":")[0] for b in branch_names]
    tabs = st.tabs(tab_labels)

    for i, tab in enumerate(tabs):
        b_name = branch_names[i]
        nodes = SKILL_TREE[b_name]

        with tab:
            st.caption(f"**{b_name}**")

            # Рисуем узлы
            for node in nodes:
                tid = node["id"]
                code = node["code"]
                req = node.get("req")

                obj = get_talent_info(tid)

                # Статусы
                is_learned = (tid in unit.talents) or (tid in unit.passives)
                can_learn, learn_reason = can_unlock_talent(unit, node, SKILL_TREE)

                # Иконки
                if is_learned:
                    icon = "✅"
                    color_start = ":green["
                elif can_learn and available_pts > 0:
                    icon = "🔷"  # Готов к изучению
                    color_start = ":blue["
                elif can_learn and available_pts <= 0:
                    icon = "🔒"  # Доступно, но нет очков
                    color_start = ":grey["
                else:
                    icon = "🔒"
                    color_start = ":grey["

                # Заголовок
                title_text = f"{icon} **[{code}] {obj.name if obj else '???'}**"
                if not obj: title_text += " (WIP)"

                # Связи
                if req:
                    st.markdown(f"<div style='text-align: center; color: #444; line-height: 0.5;'>│<br>▼</div>",
                                unsafe_allow_html=True)

                with st.container(border=True):
                    cols = st.columns([0.8, 0.2])
                    # Левая часть - Инфо
                    # Левая часть - Инфо
                    with cols[0]:
                        st.markdown(f"{color_start}{title_text}]")
                        if obj:
                            # Используем нашу красивую функцию
                            render_styled_description(obj.description)
                        else:
                            st.caption("Этот талант еще не реализован в коде.")

                    # Правая часть - Кнопки
                    with cols[1]:
                        if not obj:
                            st.button("⛔", key=f"btn_{unit.name}_{code}", disabled=True)

                        elif is_learned:
                            # Проверка на удаление
                            can_forget, forget_reason = can_forget_talent(unit, tid, SKILL_TREE)
                            if can_forget:
                                if st.button("❌ Сброс", key=f"forget_{unit.name}_{tid}", type="secondary",
                                             help="Вернуть очко талантов"):
                                    if forget_talent(unit, tid):
                                        UnitLibrary.save_unit(unit)
                                        st.rerun()
                            else:
                                st.button("🔗", key=f"locked_{unit.name}_{tid}", disabled=True,
                                          help=f"Нельзя сбросить: {forget_reason}")

                        elif can_learn:
                            if available_pts > 0:
                                if st.button("➕ Взять", key=f"learn_{unit.name}_{tid}", type="primary"):
                                    if learn_talent(unit, tid):
                                        UnitLibrary.save_unit(unit)
                                        st.rerun()
                            else:
                                st.button("🔒", key=f"nopoints_{unit.name}_{tid}", disabled=True,
                                          help="Нет очков талантов")

                        else:
                            st.button("🔒", key=f"closed_{unit.name}_{tid}", disabled=True, help=learn_reason)