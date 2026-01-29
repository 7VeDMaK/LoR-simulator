import streamlit as st
import os
from core.unit.unit_library import UnitLibrary

AVATARS_DIR = "data/avatars"


def save_avatar_file(uploaded, unit_name):
    """
    Сохраняет загруженный файл в папку data/avatars.
    """
    os.makedirs(AVATARS_DIR, exist_ok=True)
    safe_name = "".join(c for c in unit_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
    ext = uploaded.name.split('.')[-1]
    path = f"{AVATARS_DIR}/{safe_name}.{ext}"

    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())

    return path


def get_available_avatars():
    """Сканирует папку и возвращает список картинок"""
    if not os.path.exists(AVATARS_DIR):
        return ["default.png"]
    files = [f for f in os.listdir(AVATARS_DIR) if f.endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    return sorted(files)


def render_avatar_section(unit, is_edit_mode: bool):
    """Отображает аватар и панель управления им"""

    # --- Отображение ---
    avatar_path = unit.avatar if unit.avatar and os.path.exists(unit.avatar) else None

    if avatar_path:
        st.image(avatar_path, width='stretch')
    else:
        st.markdown(
            f"""<div style="background-color: #222; height: 200px; display: flex; 
            align-items: center; justify-content: center; border-radius: 10px; border: 1px dashed #555;">
                <span style="font-size: 40px; color: #555;">👤</span>
            </div>""",
            unsafe_allow_html=True
        )

    # --- Редактирование ---
    if is_edit_mode:
        st.markdown("---")
        st.markdown("**Изменить аватар:**")
        tab_upload, tab_select = st.tabs(["📤 Загрузить", "📂 Выбрать"])

        # 1. Загрузка
        with tab_upload:
            upl = st.file_uploader("Файл картинки", type=['png', 'jpg', 'jpeg', 'webp'], label_visibility="collapsed",
                                   key=f"upl_sidebar_{unit.name}")
            if upl:
                new_path = save_avatar_file(upl, unit.name)
                unit.avatar = new_path
                UnitLibrary.save_unit(unit)
                st.toast("Аватар обновлен!", icon="🖼️")
                st.rerun()

        # 2. Выбор
        with tab_select:
            avatar_options = get_available_avatars()
            current_avatar_name = os.path.basename(unit.avatar) if unit.avatar else "default.png"

            idx = 0
            if current_avatar_name in avatar_options:
                idx = avatar_options.index(current_avatar_name)

            selected_avatar = st.selectbox("Список файлов", avatar_options, index=idx, label_visibility="collapsed")
            new_path_from_list = os.path.join(AVATARS_DIR, selected_avatar)

            if unit.avatar != new_path_from_list:
                unit.avatar = new_path_from_list
                UnitLibrary.save_unit(unit)
                st.rerun()