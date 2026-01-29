import streamlit as st
# Импортируем реестр пассивок, чтобы находить их по ID
from logic.character_changing.passives import PASSIVE_REGISTRY


def render_passives_tab(unit, is_edit_mode: bool):
    # Получаем список ID пассивок (строки)
    raw_passives = unit.passives if hasattr(unit, 'passives') else []

    if is_edit_mode:
        st.warning(
            "⚠️ Редактирование пассивок (добавление/удаление) через это меню пока в разработке. Используйте Editor.")

    if not raw_passives:
        st.info("Нет активных пассивных способностей.")
        return

    # === 1. ПРЕОБРАЗОВАНИЕ ID В ОБЪЕКТЫ ===
    passives_list = []
    for p_item in raw_passives:
        # Если это строка (ID), ищем в реестре
        if isinstance(p_item, str):
            if p_item in PASSIVE_REGISTRY:
                passives_list.append(PASSIVE_REGISTRY[p_item])
            else:
                # Если ID нет в базе, создаем заглушку (словарь)
                passives_list.append({
                    "name": f"Unknown ID: {p_item}",
                    "description": "Пассивка не найдена в реестре.",
                    "cost": 0
                })
        # Если это уже объект или словарь (легаси или кастом)
        else:
            passives_list.append(p_item)

    # Layout: Список слева (Radio), Детали справа
    col_list, col_details = st.columns([1, 2])

    with col_list:
        st.markdown("### Список")

        # Собираем имена для радио-кнопки
        p_names = []
        for p in passives_list:
            if isinstance(p, dict):
                p_names.append(p.get('name', '???'))
            else:
                # Проверяем атрибут name, если его нет — fallback
                p_names.append(getattr(p, 'name', 'Unnamed Passive'))

        # Radio button работает как селектор
        selected_name = st.radio("Select Passive", p_names, label_visibility="collapsed")

        # Находим индекс выбранного элемента
        sel_idx = 0
        if selected_name in p_names:
            sel_idx = p_names.index(selected_name)

    with col_details:
        st.markdown("### Описание")
        if passives_list:
            p = passives_list[sel_idx]
            _render_passive_details(p, is_edit_mode)


def _render_passive_details(passive, is_edit_mode):
    # Универсальный доступ (словарь или объект)
    if isinstance(passive, dict):
        name = passive.get('name', 'Unknown')
        desc = passive.get('description', '')
    else:
        name = getattr(passive, 'name', 'Unknown')
        desc = getattr(passive, 'description', '')

    # Красивая карточка
    st.info(f"**{name}**")

    if is_edit_mode:
        st.text_area("Описание", value=desc, height=150, key=f"desc_{name}")
        if st.button("Сохранить описание (Mock)", key=f"save_{name}"):
            st.toast("Сохранение описания... (Функция не реализована)", icon="⚠️")
    else:
        st.markdown(desc)