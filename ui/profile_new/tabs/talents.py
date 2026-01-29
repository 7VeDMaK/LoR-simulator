import streamlit as st


def render_talents_tab(unit, is_edit_mode: bool):
    """
    Вкладка Талантов.
    """
    # Получаем список талантов (или пустой, если их нет)
    talents = getattr(unit, 'talents', [])

    # Кнопка добавления (в режиме редактирования)
    if is_edit_mode:
        if st.button("➕ Добавить талант (Mock)", key="add_talent_top_btn"):
            st.toast("Редактор талантов в разработке")

    if not talents:
        st.info("У этого персонажа нет изученных талантов.")
        return

    # Разметка: Список (слева) | Детали (справа)
    col_list, col_details = st.columns([1, 2])

    with col_list:
        st.markdown("### Список")
        # Генерируем список имен для выбора
        t_names = [t.get('name', 'Unknown') if isinstance(t, dict) else t.name for t in talents]

        # Используем radio как селектор
        selected_name = st.radio("Select Talent", t_names, label_visibility="collapsed", key="talents_list_radio")

        # Определяем индекс выбранного
        sel_idx = 0
        if selected_name in t_names:
            sel_idx = t_names.index(selected_name)

    with col_details:
        st.markdown("### Описание")
        if talents:
            t = talents[sel_idx]
            _render_talent_details(t, is_edit_mode)


def _render_talent_details(talent, is_edit_mode):
    # Универсальный доступ к данным (dict или object)
    name = talent.get('name') if isinstance(talent, dict) else talent.name
    desc = talent.get('description', '') if isinstance(talent, dict) else getattr(talent, 'description', '')
    lvl_req = talent.get('level_req', 1) if isinstance(talent, dict) else getattr(talent, 'level_req', 1)

    # Красивая шапка
    st.info(f"🌟 **{name}** (Level Req: {lvl_req})")

    if is_edit_mode:
        st.text_area("Описание эффекта", value=desc, height=150, key=f"desc_talent_{name}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Сохранить", key=f"save_t_{name}"):
                st.toast(f"Описание {name} сохранено (в памяти)")
        with c2:
            if st.button("🗑️ Удалить", key=f"del_t_{name}"):
                st.toast(f"Талант {name} удален (Mock)")
    else:
        st.markdown(desc)