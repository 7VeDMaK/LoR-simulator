import streamlit as st
import os


def render_profile_controls():
    """
    Рисует настройки в глобальном сайдбаре (слева).
    """
    with st.sidebar:
        st.markdown("---")
        st.header("⚙️ Настройки")
        # Этот переключатель теперь будет под меню навигации
        is_edit_mode = st.toggle("✏️ Режим редактирования", value=False, key="profile_edit_mode_global")

        if is_edit_mode:
            st.warning("Включен режим изменения данных")

    return is_edit_mode


def render_sidebar(unit, is_edit_mode: bool):
    """
    Рисует 'Паспорт' персонажа (Левая колонка профиля).
    """
    # 1. АВАТАР
    avatar_path = unit.avatar if unit.avatar and os.path.exists(unit.avatar) else None

    if avatar_path:
        st.image(avatar_path, use_column_width=True)
    else:
        st.markdown(
            f"""<div style="background-color: #222; height: 200px; display: flex; 
            align-items: center; justify-content: center; border-radius: 10px; border: 1px dashed #555;">
                <span style="font-size: 40px; color: #555;">👤</span>
            </div>""",
            unsafe_allow_html=True
        )

    st.divider()

    # 2. ИНФОРМАЦИЯ (Имя, Ранг, Уровень)
    if is_edit_mode:
        new_name = st.text_input("Имя", value=unit.name)
        if new_name != unit.name:
            unit.name = new_name

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

    # 3. ШКАЛЫ (HP/SP/Stagger)
    # Можно сделать редактируемыми базовые значения в режиме редактора, но пока оставим просмотр
    _draw_bar("HP", unit.current_hp, unit.max_hp, "#d64545")
    _draw_bar("SP", unit.current_sp, unit.max_sp, "#e3d856")
    _draw_bar("Stagger", unit.current_stagger, unit.max_stagger, "#aaaaaa")

    st.divider()

    # 4. РЕЗИСТЫ (HP Only)
    st.write("**Resistances (HP)**")
    rc1, rc2, rc3 = st.columns(3)

    # Заглушки значений (подключи реальные данные из unit.resistances)
    r_slash = 1.0
    r_pierce = 0.5
    r_blunt = 2.0

    with rc1:
        _render_resist_cell("Slash", "🗡️", r_slash, is_edit_mode)
    with rc2:
        _render_resist_cell("Pierce", "🏹", r_pierce, is_edit_mode)
    with rc3:
        _render_resist_cell("Blunt", "🔨", r_blunt, is_edit_mode)


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
        st.number_input(label, value=value, step=0.1, label_visibility="collapsed", key=f"res_{label}")
    else:
        color = "#fff"
        if value < 1.0:
            color = "#aaffaa"  # Green
        elif value > 1.0:
            color = "#ffaaaa"  # Red
        st.markdown(f"<div style='text-align: center; color: {color}; font-weight: bold;'>{value}</div>",
                    unsafe_allow_html=True)