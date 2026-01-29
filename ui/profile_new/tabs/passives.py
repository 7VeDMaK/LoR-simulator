import streamlit as st


def render_passives_tab(unit, is_edit_mode: bool):
    passives = unit.passives if hasattr(unit, 'passives') else []

    if is_edit_mode:
        st.warning(
            "⚠️ Редактирование пассивок (добавление/удаление) через это меню пока в разработке. Используйте Editor.")

    if not passives:
        st.info("Нет активных пассивных способностей.")
        return

    # Layout: Список слева (Radio), Детали справа
    col_list, col_details = st.columns([1, 2])

    with col_list:
        st.markdown("### Список")
        # Получаем список имен
        p_names = [p.get('name', '???') if isinstance(p, dict) else p.name for p in passives]

        # Radio button работает как селектор
        selected_name = st.radio("Select Passive", p_names, label_visibility="collapsed")

        # Находим индекс
        sel_idx = 0
        if selected_name in p_names:
            sel_idx = p_names.index(selected_name)

    with col_details:
        st.markdown("### Описание")
        if passives:
            p = passives[sel_idx]
            _render_passive_details(p, is_edit_mode)


def _render_passive_details(passive, is_edit_mode):
    # Универсальный доступ (словарь или объект)
    name = passive.get('name') if isinstance(passive, dict) else passive.name
    desc = passive.get('description', '') if isinstance(passive, dict) else getattr(passive, 'description', '')
    cost = passive.get('cost', 0) if isinstance(passive, dict) else getattr(passive, 'cost', 0)

    # Красивая карточка
    st.info(f"**{name}** (Cost: {cost})")

    if is_edit_mode:
        st.text_area("Описание", value=desc, height=150)
        if st.button("Сохранить описание (Mock)", key=f"save_{name}"):
            st.toast("Сохранение описания...")
    else:
        st.markdown(desc)