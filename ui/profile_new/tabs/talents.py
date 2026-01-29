import streamlit as st
from core.unit.unit_library import UnitLibrary
# Импорт реестра и дерева для инфо
from logic.character_changing.talents import TALENT_REGISTRY

try:
    from core.tree_data import SKILL_TREE
except ImportError:
    SKILL_TREE = {}

# Кеш для быстрого поиска ветки
_BRANCH_CACHE = {}


def _get_branch_info(talent_id):
    """
    Возвращает строку вида '3.1 [Ветка 3: Неутомимый]'
    """
    if talent_id in _BRANCH_CACHE:
        return _BRANCH_CACHE[talent_id]

    if not SKILL_TREE:
        return "Неизвестная ветка"

    for branch_name, talents_list in SKILL_TREE.items():
        if isinstance(talents_list, list):
            for t_data in talents_list:
                if t_data.get("id") == talent_id:
                    code = t_data.get("code", "???")
                    res = f"{code} [{branch_name}]"
                    _BRANCH_CACHE[talent_id] = res
                    return res

    return "Вне веток / Скрытый"


def render_talents_tab(unit, is_edit_mode: bool):
    """
    Вкладка Талантов.
    """
    # Инициализация, если списка нет
    if not hasattr(unit, 'talents') or unit.talents is None:
        unit.talents = []

    raw_talents = unit.talents

    # === 1. ДОБАВЛЕНИЕ ТАЛАНТА (EDIT MODE) ===
    if is_edit_mode:
        # Собираем ID, которые уже есть
        current_ids = set()
        for t in raw_talents:
            if isinstance(t, str):
                current_ids.add(t)
            elif hasattr(t, 'id'):
                current_ids.add(t.id)

        # Формируем список доступных для добавления
        available_opts = []
        for tid, t_obj in TALENT_REGISTRY.items():
            if tid not in current_ids:
                # Добавляем инфо о ветке для удобства поиска
                branch_info = _get_branch_info(tid)
                label = f"[{branch_info}] {t_obj.name}"
                available_opts.append((label, tid))

        # Сортируем: сначала по коду ветки (чтобы шли по порядку), потом по имени
        # Хитрость: сортируем по label, так как он начинается с "[1.1 ..."
        available_opts.sort(key=lambda x: x[0])

        # UI добавления
        c_add, _ = st.columns([1, 2])
        with c_add:
            with st.popover("➕ Добавить талант", use_container_width=True):
                options_map = {label: tid for label, tid in available_opts}

                sel_label = st.selectbox(
                    "Выберите талант из списка",
                    options=[""] + list(options_map.keys()),
                    label_visibility="collapsed"
                )

                if sel_label and sel_label in options_map:
                    tid_to_add = options_map[sel_label]
                    if st.button(f"Добавить: {TALENT_REGISTRY[tid_to_add].name}", type="primary"):
                        unit.talents.append(tid_to_add)
                        UnitLibrary.save_unit(unit)
                        st.rerun()

        st.divider()

    if not raw_talents:
        st.info("У этого персонажа нет изученных талантов.")
        return

    # === 2. ПОДГОТОВКА ДАННЫХ ДЛЯ ОТОБРАЖЕНИЯ ===
    prepared_list = []

    for index, t_item in enumerate(raw_talents):
        t_data = {"original": t_item, "index": index}

        if isinstance(t_item, str):
            t_id = t_item
            if t_item in TALENT_REGISTRY:
                t_obj = TALENT_REGISTRY[t_item]
                t_data.update({
                    "name": t_obj.name,
                    "desc": t_obj.description,
                    "id": t_id,
                    "obj": t_obj
                })
            else:
                t_data.update({
                    "name": f"Unknown ID: {t_item}",
                    "desc": "Талант не найден в реестре.",
                    "id": t_id,
                    "obj": None
                })
        else:
            # Legacy object
            t_obj = t_item
            t_id = getattr(t_obj, "id", "unknown")
            t_name = getattr(t_obj, "name", "Unnamed")
            t_desc = getattr(t_obj, "description", "")
            t_data.update({
                "name": t_name,
                "desc": t_desc,
                "id": t_id,
                "obj": t_obj
            })

        prepared_list.append(t_data)

    # Сортируем список отображения по веткам
    prepared_list.sort(key=lambda x: _get_branch_info(x["id"]))

    # Layout
    col_list, col_details = st.columns([1, 2])

    with col_list:
        st.markdown("### Список")

        # Генерируем красивые имена для списка
        t_options = []
        for item in prepared_list:
            branch_short = _get_branch_info(item["id"]).split(' ')[0]  # Только код "1.1"
            t_options.append(f"[{branch_short}] {item['name']}")

        # Radio button
        selected_option = st.radio("Select Talent", t_options, label_visibility="collapsed", key="talents_list_radio")

        sel_idx = 0
        if selected_option in t_options:
            sel_idx = t_options.index(selected_option)

    with col_details:
        st.markdown("### Описание")
        if prepared_list:
            sel_data = prepared_list[sel_idx]
            _render_talent_details(unit, sel_data, is_edit_mode)


def _render_talent_details(unit, t_data, is_edit_mode):
    name = t_data["name"]
    desc = t_data["desc"]
    t_id = t_data["id"]

    branch_info = _get_branch_info(t_id)

    st.info(f"🌟 **{name}**\n\n📌 {branch_info}")

    if is_edit_mode:
        # Только просмотр описания (disabled=True)
        st.text_area("Описание", value=desc, height=150, disabled=True, key=f"desc_talent_{name}")

        c_del, _ = st.columns([1, 3])
        with c_del:
            if st.button("🗑️ Удалить", key=f"del_t_{t_data['index']}"):
                val_to_remove = t_data["original"]
                if val_to_remove in unit.talents:
                    unit.talents.remove(val_to_remove)
                    UnitLibrary.save_unit(unit)
                    st.toast(f"Талант {name} удален")
                    st.rerun()
    else:
        st.markdown(desc)