import streamlit as st


def _draw_bar(label, current, maximum, color):
    """Рисует красивый прогресс-бар"""
    pct = max(0.0, min(1.0, current / maximum if maximum > 0 else 0))
    st.markdown(f"**{label}:** {current} / {maximum}")
    st.markdown(
        f"""<div style="width: 100%; background-color: #333; border-radius: 4px; height: 8px; margin-bottom: 8px;">
            <div style="width: {pct * 100}%; background-color: {color}; height: 8px; border-radius: 4px;"></div>
        </div>""", unsafe_allow_html=True
    )


def render_vital_stats(unit, is_edit_mode: bool):
    """
    Отображает HP, SP, Stagger.
    В режиме редактирования позволяет менять Max и Current значения.
    """

    if is_edit_mode:
        st.caption("Изменение характеристик (Current / Max)")

        # --- HP ---
        c1, c2 = st.columns([1, 1])
        with c1:
            unit.current_hp = st.number_input("Cur HP", value=unit.current_hp, step=1)
        with c2:
            unit.max_hp = st.number_input("Max HP", value=unit.max_hp, step=1)

        # --- SP ---
        c3, c4 = st.columns([1, 1])
        with c3:
            unit.current_sp = st.number_input("Cur SP", value=unit.current_sp, step=1)
        with c4:
            unit.max_sp = st.number_input("Max SP", value=unit.max_sp, step=1)

        # --- Stagger ---
        c5, c6 = st.columns([1, 1])
        with c5:
            unit.current_stagger = st.number_input("Cur Stagger", value=unit.current_stagger, step=1)
        with c6:
            unit.max_stagger = st.number_input("Max Stagger", value=unit.max_stagger, step=1)

    else:
        # Режим просмотра (бары)
        _draw_bar("HP", unit.current_hp, unit.max_hp, "#d64545")
        _draw_bar("SP", unit.current_sp, unit.max_sp, "#e3d856")
        _draw_bar("Stagger", unit.current_stagger, unit.max_stagger, "#aaaaaa")