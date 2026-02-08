import streamlit as st
from ui.editor.config import SCRIPT_SCHEMAS


def edit_global_script(index):
    """Callback для редактирования глобального скрипта."""
    g_scripts = st.session_state.get("ed_script_list", [])
    if index >= len(g_scripts): return

    item = g_scripts[index]
    trig = item['trigger']
    data = item['data']
    sid = data.get('script_id')
    params = data.get('params', {})

    # Ищем имя схемы по ID скрипта
    schema_name = next((k for k, v in SCRIPT_SCHEMAS.items() if v["id"] == sid), None)

    if schema_name:
        # Устанавливаем селекторы
        st.session_state["glob_trigger"] = trig
        st.session_state["glob_script_select"] = schema_name

        # Устанавливаем параметры в форму
        # Ключи виджетов строятся как f"{prefix}_{schema_name}_{param_key}"
        prefix = "glob"
        for p_key, p_val in params.items():
            widget_key = f"{prefix}_{schema_name}_{p_key}"
            # Важно: streamlit session_state хранит значения виджетов
            st.session_state[widget_key] = p_val

        # Удаляем из списка (чтобы пользователь мог "пересохранить" его)
        g_scripts.pop(index)


def delete_global_script(index):
    """Callback для удаления."""
    st.session_state["ed_script_list"].pop(index)


def edit_dice_script(dice_idx, script_idx):
    """Callback для редактирования скрипта кубика."""
    key = f"ed_dice_scripts_{dice_idx}"
    d_scripts = st.session_state.get(key, [])
    if script_idx >= len(d_scripts): return

    item = d_scripts[script_idx]
    trig = item['trigger']
    data = item['data']
    sid = data.get('script_id')
    params = data.get('params', {})

    schema_name = next((k for k, v in SCRIPT_SCHEMAS.items() if v["id"] == sid), None)

    if schema_name:
        # Устанавливаем селекторы
        st.session_state[f"d_trig_{dice_idx}"] = trig
        st.session_state[f"d_script_{dice_idx}"] = schema_name

        # Параметры
        prefix = f"d_{dice_idx}"
        for p_key, p_val in params.items():
            widget_key = f"{prefix}_{schema_name}_{p_key}"
            st.session_state[widget_key] = p_val

        # Удаляем из списка
        d_scripts.pop(script_idx)


def delete_dice_script(dice_idx, script_idx):
    """Callback для удаления."""
    st.session_state[f"ed_dice_scripts_{dice_idx}"].pop(script_idx)