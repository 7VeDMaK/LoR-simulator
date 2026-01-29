import streamlit as st
from logic.character_changing.talents import TALENT_REGISTRY

# Пытаемся импортировать структуру деревьев
try:
    from core.tree_data import SKILL_TREE
except ImportError:
    SKILL_TREE = {}

# Кеш для быстрого поиска
_BRANCH_CACHE = {}


def _get_branch_info(talent_id):
    """
    Возвращает строку вида '3.1 Ветка 3: Неутомимый'
    """
    if talent_id in _BRANCH_CACHE:
        return _BRANCH_CACHE[talent_id]

    if not SKILL_TREE:
        return "Неизвестная ветка"

    # SKILL_TREE = { "Branch Name": [ { "code": "1.1", "id": "xxx", ... }, ... ], ... }

    for branch_name, talents_list in SKILL_TREE.items():
        # talents_list - это список словарей
        if isinstance(talents_list, list):
            for t_data in talents_list:
                # t_data = {"code": "...", "id": "...", ...}
                if t_data.get("id") == talent_id:
                    code = t_data.get("code", "???")
                    # Формируем красивую строку
                    # Например: "3.1 (Ветка 3: Неутомимый)"
                    # Можно сократить имя ветки, если оно длинное
                    res = f"{code} [{branch_name}]"
                    _BRANCH_CACHE[talent_id] = res
                    return res

    return "Вне веток / Скрытый"


def render_talents_tab(unit, is_edit_mode: bool):
    """
    Вкладка Талантов.
    """
    raw_talents = getattr(unit, 'talents', [])

    if is_edit_mode:
        if st.button("➕ Добавить талант (Mock)", key="add_talent_top_btn"):
            st.toast("Редактор талантов в разработке")

    if not raw_talents:
        st.info("У этого персонажа нет изученных талантов.")
        return

    # === 1. ПОДГОТОВКА ДАННЫХ ===
    prepared_list = []

    for t_item in raw_talents:
        t_id = "unknown"
        t_obj = None

        if isinstance(t_item, str):
            t_id = t_item
            if t_item in TALENT_REGISTRY:
                t_obj = TALENT_REGISTRY[t_item]
            else:
                t_obj = {
                    "name": f"Unknown ID: {t_item}",
                    "description": "Талант не найден в реестре.",
                }
        else:
            t_obj = t_item
            t_id = getattr(t_obj, "id", "unknown")

        prepared_list.append((t_id, t_obj))

    # Сортируем список: сначала по ветке (через кеш или поиск), потом по имени
    # Это чтобы таланты одной ветки шли подряд
    prepared_list.sort(key=lambda x: _get_branch_info(x[0]))

    # Layout
    col_list, col_details = st.columns([1, 2])

    with col_list:
        st.markdown("### Список")

        # Генерируем список имен для выбора
        t_options = []
        for t_id, t_obj in prepared_list:
            if isinstance(t_obj, dict):
                name = t_obj.get('name', 'Unknown')
            else:
                name = getattr(t_obj, 'name', 'Unnamed Talent')

            # Добавляем код ветки в название в списке для наглядности
            # Например: "[3.1] Big Guy"
            branch_short = _get_branch_info(t_id).split(' ')[0]  # Берем только код "3.1"
            t_options.append(f"[{branch_short}] {name}")

        # Radio button
        selected_option = st.radio("Select Talent", t_options, label_visibility="collapsed", key="talents_list_radio")

        sel_idx = 0
        if selected_option in t_options:
            sel_idx = t_options.index(selected_option)

    with col_details:
        st.markdown("### Описание")
        if prepared_list:
            sel_id, sel_obj = prepared_list[sel_idx]
            _render_talent_details(sel_obj, sel_id, is_edit_mode)


def _render_talent_details(talent, talent_id, is_edit_mode):
    # Универсальный доступ
    if isinstance(talent, dict):
        name = talent.get('name', 'Unknown')
        desc = talent.get('description', '')
    else:
        name = getattr(talent, 'name', 'Unknown')
        desc = getattr(talent, 'description', '')

    branch_info = _get_branch_info(talent_id)

    st.info(f"🌟 **{name}**\n\n📌 {branch_info}")

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