import streamlit as st
from ui.editor.config import SCRIPT_SCHEMAS
from ui.editor.forms import render_dynamic_form, clean_editor_params  # [NEW]
from ui.editor.callbacks import edit_global_script, delete_global_script
from ui.profile_new.tabs.build_parts.formatting import _translate_script_effect


def render_global_effects():
    """Секция редактирования глобальных эффектов."""
    st.markdown("### 🌍 Глобальные Эффекты")

    with st.expander("➕ Добавить эффект карты", expanded=False):
        c1, c2 = st.columns([1, 2])
        trigger = c1.selectbox("Триггер", ["on_use", "on_play", "on_combat_start", "on_round_start", "on_combat_end"],
                               key="glob_trigger")

        script_names = list(SCRIPT_SCHEMAS.keys())
        script_name = c2.selectbox("Скрипт", script_names, key="glob_script_select")

        schema = SCRIPT_SCHEMAS[script_name]
        params = render_dynamic_form("glob", script_name)

        if st.button("Добавить", key="add_glob_btn"):
            # [FIX] Очищаем параметры от мусора
            cleaned_params = clean_editor_params(params)

            effect_data = {
                "script_id": schema["id"],
                "params": cleaned_params
            }
            st.session_state["ed_script_list"].append({
                "trigger": trigger,
                "data": effect_data
            })
            st.success("Эффект добавлен!")
            st.rerun()

    # === СПИСОК ЭФФЕКТОВ ===
    if st.session_state["ed_script_list"]:
        st.caption("Список активных эффектов:")

        for i, item in enumerate(st.session_state["ed_script_list"]):
            trigger = item["trigger"]
            data = item["data"]

            pretty_html = _translate_script_effect(data)
            # Показываем, что реально записано (уже очищенное)
            tech_str = f"{data['script_id']} {data['params']}"

            c_info, c_edit, c_del = st.columns([8, 1, 1])

            with c_info:
                st.markdown(f"""
                <div style="
                    background-color: #262730; 
                    border: 1px solid #444; 
                    border-radius: 5px; 
                    padding: 8px; 
                    margin-bottom: 5px;
                ">
                    <div style="font-weight: bold; color: #ffbd45; margin-bottom: 4px;">⚡ {trigger.upper().replace('_', ' ')}</div>
                    <div style="font-size: 1.05em; margin-bottom: 4px;">{pretty_html}</div>
                    <div style="font-family: monospace; color: #666; font-size: 0.8em;">🔧 {tech_str}</div>
                </div>
                """, unsafe_allow_html=True)

            c_edit.button("✏️", key=f"edit_g_{i}", on_click=edit_global_script, args=(i,), help="Редактировать")
            c_del.button("❌", key=f"del_g_{i}", on_click=delete_global_script, args=(i,), help="Удалить")

    else:
        st.info("Нет глобальных эффектов.")