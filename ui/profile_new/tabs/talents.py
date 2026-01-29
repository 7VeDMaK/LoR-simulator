import streamlit as st


def render_talents_tab(unit, is_edit_mode: bool):
    """
    Вкладка для отображения талантов.
    """
    # Пытаемся получить таланты, если их нет - пустой список
    talents = getattr(unit, 'talents', [])

    if not talents:
        st.info("Нет изученных талантов.")
        if is_edit_mode:
            st.button("➕ Добавить талант (Mock)", key="add_talent_btn")
        return

    # Layout: Список (слева) | Описание (справа)
    col_list, col_details = st.columns([1, 2])

    with col_list:
        st.markdown("### Список")
        # Собираем имена для радио-кнопки
        t_names = [t.get('name', '???') if isinstance(t, dict) else t.name for t in talents]

        selected_name = st.radio("Select Talent", t_names, label_visibility="collapsed", key="talents_radio")

        # Находим индекс
        sel_idx = 0
        if selected_name in t_names:
            sel_idx = t_names.index(selected_name)

    with col_details:
        st.markdown("### Описание")
        if talents:
            t = talents[sel_idx]
            _render_talent_details(t, is_edit_mode)


def _render_talent_details(talent, is_edit_mode):
    # Адаптер для словаря или объекта
    name = talent.get('name') if isinstance(talent, dict) else talent.name
    desc = talent.get('description', '') if isinstance(talent, dict) else getattr(talent, 'description', '')
    lvl_req = talent.get('level_req', 1) if isinstance(talent, dict) else getattr(talent, 'level_req', 1)

    # Заголовок таланта (можно добавить цвет или иконку 🌟)
    st.info(f"🌟 **{name}** (Lvl Req: {lvl_req})")

    if is_edit_mode:
        st.text_area("Эффект таланта", value=desc, height=150, key=f"desc_{name}")
        if st.button(f"Сохранить {name}", key=f"save_t_{name}"):
            st.toast("Сохранено (в памяти)")
    else:
        st.markdown(desc)