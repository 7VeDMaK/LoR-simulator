import streamlit as st
from core.unit.unit_library import UnitLibrary
# Импортируем реестр пассивок для выбора
from logic.character_changing.passives import PASSIVE_REGISTRY


def render_passives_tab(unit, is_edit_mode: bool):
    # Убедимся, что список инициализирован
    if not hasattr(unit, 'passives') or unit.passives is None:
        unit.passives = []

    raw_passives = unit.passives

    # === 1. ДОБАВЛЕНИЕ ПАССИВКИ (EDIT MODE) ===
    if is_edit_mode:
        # Собираем список ID, которые уже есть у персонажа
        current_ids = set()
        for p in raw_passives:
            if isinstance(p, str):
                current_ids.add(p)
            elif hasattr(p, 'id'):
                current_ids.add(p.id)

        # Формируем список доступных для добавления
        available_opts = []
        for pid, p_obj in PASSIVE_REGISTRY.items():
            if pid not in current_ids:
                available_opts.append((pid, p_obj))

        # Сортируем по имени
        available_opts.sort(key=lambda x: x[1].name)

        # UI добавления
        c_add, _ = st.columns([1, 2])
        with c_add:
            with st.popover("➕ Добавить пассивку", use_container_width=True):
                # Формируем строки для селектора
                options_map = {f"{p_obj.name}": pid for pid, p_obj in available_opts}

                sel_label = st.selectbox(
                    "Выберите способность из реестра",
                    options=[""] + list(options_map.keys()),
                    label_visibility="collapsed"
                )

                if sel_label and sel_label in options_map:
                    pid_to_add = options_map[sel_label]
                    if st.button(f"Добавить: {PASSIVE_REGISTRY[pid_to_add].name}", type="primary"):
                        unit.passives.append(pid_to_add)
                        UnitLibrary.save_unit(unit)
                        st.rerun()

        st.divider()

    if not raw_passives:
        st.info("Нет активных пассивных способностей.")
        return

    # === 2. ПРЕОБРАЗОВАНИЕ ID В ОБЪЕКТЫ ===
    passives_list = []
    for index, p_item in enumerate(raw_passives):
        # Сохраняем оригинальный индекс или значение для удаления
        p_data = {"original": p_item, "index": index}

        if isinstance(p_item, str):
            if p_item in PASSIVE_REGISTRY:
                # Если нашли в реестре
                p_obj = PASSIVE_REGISTRY[p_item]
                p_data["obj"] = p_obj
                p_data["name"] = p_obj.name
            else:
                # Если ID нет в базе
                p_data["obj"] = None
                p_data["name"] = f"Unknown ID: {p_item}"
                p_data["desc"] = "Пассивка не найдена в реестре."
        else:
            # Если это уже объект/словарь
            p_data["obj"] = p_item
            if isinstance(p_item, dict):
                p_data["name"] = p_item.get('name', '???')
            else:
                p_data["name"] = getattr(p_item, 'name', 'Unnamed')

        passives_list.append(p_data)

    # === 3. ОТОБРАЖЕНИЕ (Master-Detail) ===
    col_list, col_details = st.columns([1, 2])

    with col_list:
        st.markdown("### Список")

        p_names = [p["name"] for p in passives_list]

        # Radio button как селектор
        selected_name = st.radio("Select Passive", p_names, label_visibility="collapsed", key="passive_list_radio")

        sel_idx = 0
        if selected_name in p_names:
            sel_idx = p_names.index(selected_name)

    with col_details:
        st.markdown("### Описание")
        if passives_list:
            selected_data = passives_list[sel_idx]
            _render_passive_details(unit, selected_data, is_edit_mode)


def _render_passive_details(unit, p_data, is_edit_mode):
    """
    Рисует детали пассивки и кнопку удаления.
    """
    p_obj = p_data.get("obj")

    # Извлекаем данные
    if p_obj:
        # Это реальный объект или словарь
        if isinstance(p_obj, dict):
            name = p_obj.get('name', 'Unknown')
            desc = p_obj.get('description', '')
        else:
            name = getattr(p_obj, 'name', 'Unknown')
            desc = getattr(p_obj, 'description', '')
    else:
        # Это заглушка (Unknown ID)
        name = p_data["name"]
        desc = p_data.get("desc", "")
        cost = 0

    # Карточка
    st.info(f"🧬 **{name}**")

    # Контент
    if is_edit_mode:
        st.text_area("Описание (ReadOnly из кода)", value=desc, height=150, disabled=True, key=f"desc_view_{name}")

        # КНОПКА УДАЛЕНИЯ
        c_del, _ = st.columns([1, 3])
        with c_del:
            if st.button("🗑️ Удалить", key=f"del_passive_{p_data['index']}"):
                # Удаляем по индексу или значению
                val_to_remove = p_data["original"]
                if val_to_remove in unit.passives:
                    unit.passives.remove(val_to_remove)
                    UnitLibrary.save_unit(unit)
                    st.toast(f"Пассивка {name} удалена")
                    st.rerun()
    else:
        st.markdown(desc)