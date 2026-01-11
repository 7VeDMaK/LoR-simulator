import streamlit as st
from ui.editor.config import SCRIPT_SCHEMAS

def edit_global_script(index):
    """Callback для редактирования глобального скрипта."""
    g_scripts = st.session_state["ed_script_list"]
    if index >= len(g_scripts): return

    item = g_scripts[index]
    trig = item['trigger']
    sid = item['data'].get('script_id')
    p = item['data'].get('params', {})

    schema_name = next((k for k, v in SCRIPT_SCHEMAS.items() if v["id"] == sid), None)
    if schema_name:
        # Устанавливаем селекторы
        st.session_state["ce_trig"] = trig
        st.session_state["ce_schema"] = schema_name

        # Устанавливаем параметры в форму
        prefix = "global"
        for param_key, param_val in p.items():
            widget_key = f"{prefix}_{schema_name}_{param_key}"
            st.session_state[widget_key] = param_val

        # Удаляем из списка (чтобы "вернуть" в редактор)
        g_scripts.pop(index)


def delete_global_script(index):
    """Callback для удаления глобального скрипта."""
    st.session_state["ed_script_list"].pop(index)


def edit_dice_script(dice_idx, script_idx):
    """Callback для редактирования скрипта кубика."""
    key = f"ed_dice_scripts_{dice_idx}"
    d_scripts = st.session_state[key]
    if script_idx >= len(d_scripts): return

    item = d_scripts[script_idx]
    t = item['trigger']
    d_sid = item['data'].get('script_id')
    d_p = item['data'].get('params', {})

    schema_name = next((k for k, v in SCRIPT_SCHEMAS.items() if v["id"] == d_sid), None)
    if schema_name:
        # Селекторы для конкретного кубика
        st.session_state[f"de_trig_sel_{dice_idx}"] = t
        st.session_state[f"de_schema_sel_{dice_idx}"] = schema_name

        # Параметры
        prefix = f"dice_{dice_idx}"
        for param_key, param_val in d_p.items():
            widget_key = f"{prefix}_{schema_name}_{param_key}"
            st.session_state[widget_key] = param_val

        # Удаляем
        d_scripts.pop(script_idx)


def delete_dice_script(dice_idx, script_idx):
    """Callback для удаления скрипта кубика."""
    st.session_state[f"ed_dice_scripts_{dice_idx}"].pop(script_idx)

