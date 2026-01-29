import streamlit as st
import os

# Путь к папке с аватарами
AVATARS_DIR = "data/avatars"


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


def render_sidebar(unit, is_edit_mode: bool):
    """
    Рисует 'Паспорт' персонажа.
    """
    # --- 1. АВАТАР ---
    # Получаем список файлов для выбора, если мы в режиме редактора
    if is_edit_mode:
        avatar_options = _get_available_avatars()
        # Пытаемся найти текущий аватар в списке
        current_avatar_name = os.path.basename(unit.avatar) if unit.avatar else "default.png"

        # Если такого файла нет в списке (например, путь сломан), берем первый
        idx = 0
        if current_avatar_name in avatar_options:
            idx = avatar_options.index(current_avatar_name)

        selected_avatar = st.selectbox("Выберите аватар", avatar_options, index=idx)

        # Обновляем путь в юните
        new_path = os.path.join(AVATARS_DIR, selected_avatar)
        if unit.avatar != new_path:
            unit.avatar = new_path
            st.rerun()  # Перезагрузка для отображения новой картинки

    # Отображение картинки
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

    st.divider()

    # --- 2. ИНФОРМАЦИЯ (ИМЯ / РАНГ / УРОВЕНЬ) ---
    if is_edit_mode:
        # Логика смены имени
        new_name = st.text_input("Имя", value=unit.name)
        if new_name != unit.name and new_name:
            _handle_rename(unit, new_name)

        c1, c2 = st.columns(2)
        with c1:
            new_lvl = st.number_input("Ур.", value=unit.level, min_value=1, step=1)
            if new_lvl != unit.level: unit.level = new_lvl
        with c2:
            new_rank = st.number_input("Ранг", value=unit.rank, min_value=1, max_value=9, step=1)
            if new_rank != unit.rank: unit.rank = new_rank
    else:
        st.markdown(f"### {unit.name}")
        st.caption(f"Rank: {unit.rank} | Level: {unit.level}")

    st.divider()

    # --- 3. ВИТАЛЬНЫЕ ПОКАЗАТЕЛИ ---
    _draw_bar("HP", unit.current_hp, unit.max_hp, "#d64545")
    _draw_bar("SP", unit.current_sp, unit.max_sp, "#e3d856")
    _draw_bar("Stagger", unit.current_stagger, unit.max_stagger, "#aaaaaa")

    st.divider()

    # --- 4. РЕЗИСТЫ (HP) ---
    st.write("**Resistances (HP)**")

    # Получаем реальные данные из unit.resistances
    # Структура предполагается: unit.resistances['hp']['slash'] и т.д.
    hp_res = unit.resistances.get('hp', {}) if hasattr(unit, 'resistances') else {}

    r_slash = hp_res.get('slash', 1.0)
    r_pierce = hp_res.get('pierce', 1.0)
    r_blunt = hp_res.get('blunt', 1.0)

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        new_s = _render_resist_cell("Slash", "🗡️", r_slash, is_edit_mode)
        if is_edit_mode and new_s != r_slash:
            unit.resistances['hp']['slash'] = new_s

    with rc2:
        new_p = _render_resist_cell("Pierce", "🏹", r_pierce, is_edit_mode)
        if is_edit_mode and new_p != r_pierce:
            unit.resistances['hp']['pierce'] = new_p

    with rc3:
        new_b = _render_resist_cell("Blunt", "🔨", r_blunt, is_edit_mode)
        if is_edit_mode and new_b != r_blunt:
            unit.resistances['hp']['blunt'] = new_b


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def _handle_rename(unit, new_name):
    """
    Меняет имя юнита и обновляет ключ в глобальном ростере (session_state).
    """
    if 'roster' in st.session_state:
        roster = st.session_state['roster']
        old_name = unit.name

        # Если имя свободно
        if new_name not in roster:
            # Удаляем старый ключ, добавляем новый
            roster[new_name] = roster.pop(old_name)
            unit.name = new_name

            # Обновляем выбор в селекторе header.py
            if 'selected_unit_id' in st.session_state:
                st.session_state['selected_unit_id'] = new_name

            st.toast(f"Renamed to {new_name}")
            st.rerun()
        else:
            st.error(f"Name '{new_name}' already exists!")


def _get_available_avatars():
    """Сканирует папку и возвращает список картинок"""
    if not os.path.exists(AVATARS_DIR):
        return ["default.png"]

    files = [f for f in os.listdir(AVATARS_DIR) if f.endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    return sorted(files)


def _draw_bar(label, current, maximum, color):
    pct = max(0.0, min(1.0, current / maximum if maximum > 0 else 0))
    st.markdown(f"**{label}:** {current} / {maximum}")
    st.markdown(
        f"""<div style="width: 100%; background-color: #333; border-radius: 4px; height: 8px; margin-bottom: 8px;">
            <div style="width: {pct * 100}%; background-color: {color}; height: 8px; border-radius: 4px;"></div>
        </div>""", unsafe_allow_html=True
    )


def _render_resist_cell(label, icon, value, is_edit_mode):
    st.markdown(f"<div style='text-align: center; font-size: 20px;'>{icon}</div>", unsafe_allow_html=True)

    if is_edit_mode:
        # Возвращаем новое значение при редактировании
        return st.number_input(label, value=float(value), step=0.1, label_visibility="collapsed",
                               key=f"res_input_{label}")
    else:
        color = "#fff"
        if value < 1.0:
            color = "#aaffaa"  # Green (Resist)
        elif value > 1.0:
            color = "#ffaaaa"  # Red (Weak)
        elif value == 1.0:
            color = "#ffffff"  # Normal

        st.markdown(f"<div style='text-align: center; color: {color}; font-weight: bold;'>{value}</div>",
                    unsafe_allow_html=True)
        return value