import streamlit as st


def render_equipment_tab(unit, is_edit_mode: bool):
    """
    Вкладка экипировки: Оружие, Броня, Аугментации.
    """
    # Меню выбора типа внутри вкладки
    eq_type = st.radio(
        "Тип снаряжения:",
        ["⚔️ Оружие", "🛡️ Броня", "⚙️ Аугментации"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.divider()

    if "Оружие" in eq_type:
        _render_weapon_section(unit, is_edit_mode)
    elif "Броня" in eq_type:
        _render_armor_section(unit, is_edit_mode)
    elif "Аугментации" in eq_type:
        _render_augs_section(unit, is_edit_mode)


def _render_weapon_section(unit, is_edit_mode):
    st.subheader("Активное оружие")

    # Безопасное получение данных
    weapon = getattr(unit, 'equipped_weapon', None)

    if not weapon:
        st.info("Оружие не экипировано (Кулаки).")
        if is_edit_mode:
            st.button("➕ Экипировать (Mock)", key="equip_w_btn")
        return

    # Данные (поддержка словаря или объекта)
    w_name = weapon.get('name', 'Unknown') if isinstance(weapon, dict) else weapon.name
    w_desc = weapon.get('description', '') if isinstance(weapon, dict) else getattr(weapon, 'description', '')

    c1, c2 = st.columns([1, 4])
    with c1:
        st.markdown("## ⚔️")
    with c2:
        st.markdown(f"#### {w_name}")
        st.markdown(w_desc)

    if is_edit_mode:
        st.button("Снять оружие", key="unequip_w")


def _render_armor_section(unit, is_edit_mode):
    st.subheader("Активная броня")

    armor = getattr(unit, 'equipped_armor', None)

    if not armor:
        st.info("Базовая одежда.")
        if is_edit_mode:
            st.button("➕ Экипировать (Mock)", key="equip_a_btn")
        return

    a_name = armor.get('name', 'Suit') if isinstance(armor, dict) else armor.name
    st.success(f"🛡️ **{a_name}**")


def _render_augs_section(unit, is_edit_mode):
    st.subheader("Аугментации")

    augs = getattr(unit, 'augmentations', [])

    if not augs:
        st.info("Нет аугментаций.")
        if is_edit_mode:
            st.button("➕ Установить (Mock)", key="add_aug_btn")
        return

    # Список слева, детали справа
    c1, c2 = st.columns([1, 2])

    with c1:
        aug_names = [a.get('name', f"Aug {i}") if isinstance(a, dict) else a.name for i, a in enumerate(augs)]
        sel_aug = st.radio("Список", aug_names, label_visibility="collapsed")
        sel_idx = aug_names.index(sel_aug) if sel_aug in aug_names else 0

    with c2:
        if augs:
            a = augs[sel_idx]
            name = a.get('name') if isinstance(a, dict) else a.name
            desc = a.get('description', '') if isinstance(a, dict) else getattr(a, 'description', '')

            st.markdown(f"**{name}**")
            st.info(desc)

            if is_edit_mode:
                st.button(f"Удалить {name}", key=f"del_aug_{sel_idx}")