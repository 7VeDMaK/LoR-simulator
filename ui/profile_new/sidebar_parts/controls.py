import streamlit as st

def render_profile_controls():
    """
    Рисует настройки в глобальном сайдбаре (слева).
    """
    with st.sidebar:
        st.markdown("---")
        st.header("⚙️ Настройки")
        is_edit_mode = st.toggle("✏️ Режим редактирования", value=False, key="profile_edit_mode_global")

        if is_edit_mode:
            st.warning("Включен режим изменения данных")

    return is_edit_mode