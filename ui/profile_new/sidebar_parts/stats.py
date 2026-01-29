import streamlit as st
from core.unit.unit_library import UnitLibrary


def render_vital_stats(unit, is_edit_mode: bool):
    """
    Рендер полосок здоровья/рассудка в одну строку.
    """

    # === 1. КНОПКА ВОССТАНОВЛЕНИЯ ===
    if is_edit_mode:
        if st.button("💖 Full Heal", use_container_width=True, help="Восстановить HP/SP/Stagger до максимума"):
            unit.current_hp = unit.max_hp
            unit.current_sp = unit.max_sp
            unit.current_stagger = unit.max_stagger
            UnitLibrary.save_unit(unit)
            st.toast("Состояние восстановлено!")
            st.rerun()
        # Дивайдер убран, просто небольшой отступ через caption или margin
        st.caption("")

        # === 2. СЕТКА 3 КОЛОНКИ ===
    c_hp, c_sp, c_stg = st.columns(3)

    def _render_cell(col, label, cur_attr, max_attr, color):
        cur_val = getattr(unit, cur_attr)
        max_val = getattr(unit, max_attr)

        with col:
            if is_edit_mode:
                new_val = st.number_input(
                    label,
                    min_value=-100,
                    max_value=9999,
                    value=int(cur_val),
                    key=f"inp_{cur_attr}_{unit.name}"
                )
                st.markdown(
                    f"<div style='text-align:center; font-size:12px; color:{color};'>Max: {max_val}</div>",
                    unsafe_allow_html=True
                )
                if new_val != cur_val:
                    setattr(unit, cur_attr, new_val)
                    UnitLibrary.save_unit(unit)
            else:
                st.metric(label, f"{cur_val} / {max_val}")

    _render_cell(c_hp, "HP", "current_hp", "max_hp", "#ff4b4b")
    _render_cell(c_sp, "SP", "current_sp", "max_sp", "#4ecdc4")
    _render_cell(c_stg, "Stagger", "current_stagger", "max_stagger", "#feca57")