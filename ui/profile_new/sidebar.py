import streamlit as st
import os


def render_sidebar(unit, is_edit_mode: bool):
    # --- 1. АВАТАР ---
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
        if is_edit_mode:
            st.caption("Загрузка аватара пока в разработке...")

    st.divider()

    # --- 2. ОСНОВНАЯ ИНФО (ИМЯ / РАНГ / УРОВЕНЬ) ---
    if is_edit_mode:
        # Редактирование
        new_name = st.text_input("Имя", value=unit.name)
        if new_name != unit.name:
            unit.name = new_name
            # Тут можно добавить авто-сейв или кнопку сохранения

        c1, c2 = st.columns(2)
        with c1:
            new_lvl = st.number_input("Уровень", value=unit.level, min_value=1, step=1)
            if new_lvl != unit.level: unit.level = new_lvl
        with c2:
            new_rank = st.number_input("Ранг", value=unit.rank, min_value=1, max_value=9, step=1)
            if new_rank != unit.rank: unit.rank = new_rank

    else:
        # Просмотр
        st.markdown(f"### {unit.name}")
        st.caption(f"Rank: {unit.rank} | Level: {unit.level}")

    st.divider()

    # --- 3. VITALS (HP/SP/Stagger Bar) ---
    # Эти параметры обычно расчетные, поэтому их редактирование - это редактирование "Базовых" статов
    # Для простоты здесь оставим только просмотр текущих значений

    _draw_bar("HP", unit.current_hp, unit.max_hp, "#d64545")  # Red
    _draw_bar("SP", unit.current_sp, unit.max_sp, "#e3d856")  # Yellow
    _draw_bar("Stagger", unit.current_stagger, unit.max_stagger, "#aaaaaa")  # Grey

    st.divider()

    # --- 4. РЕЗИСТЫ (Только HP, с иконками) ---
    st.write("**Resistances (HP)**")

    # Сетка 3 колонки под 3 типа урона
    rc1, rc2, rc3 = st.columns(3)

    # Получаем значения резистов (заглушки или реальные данные)
    # В будущем тут будет unit.resistances.hp.slash и т.д.
    res_slash = 1.0
    res_pierce = 0.5
    res_blunt = 2.0

    with rc1:
        _render_resist_cell("Slash", "🗡️", res_slash, is_edit_mode)
    with rc2:
        _render_resist_cell("Pierce", "🏹", res_pierce, is_edit_mode)
    with rc3:
        _render_resist_cell("Blunt", "🔨", res_blunt, is_edit_mode)


def _draw_bar(label, current, maximum, color):
    pct = max(0.0, min(1.0, current / maximum if maximum > 0 else 0))
    st.markdown(f"**{label}:** {current} / {maximum}")

    # Кастомный HTML бар, так как st.progress имеет мало настроек цветов
    st.markdown(
        f"""
        <div style="width: 100%; background-color: #333; border-radius: 4px; height: 10px;">
            <div style="width: {pct * 100}%; background-color: {color}; height: 10px; border-radius: 4px;"></div>
        </div>
        <div style="margin-bottom: 10px;"></div>
        """,
        unsafe_allow_html=True
    )


def _render_resist_cell(label, icon, value, is_edit_mode):
    # Центрируем контент
    st.markdown(f"<div style='text-align: center; font-size: 24px;'>{icon}</div>", unsafe_allow_html=True)

    if is_edit_mode:
        # Если редактируем - числовое поле
        st.number_input(label, value=value, step=0.1, label_visibility="collapsed", key=f"res_{label}")
    else:
        # Если смотрим - текст с цветовым кодированием
        color = "#fff"
        res_text = "Normal"
        if value < 1.0:
            color = "#aaffaa"  # Greenish
            res_text = "Resist"
        elif value > 1.0:
            color = "#ffaaaa"  # Reddish
            res_text = "Weak"

        st.markdown(
            f"<div style='text-align: center; color: {color}; font-weight: bold;'>{value}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='text-align: center; font-size: 10px; color: #888;'>{res_text}</div>",
            unsafe_allow_html=True
        )