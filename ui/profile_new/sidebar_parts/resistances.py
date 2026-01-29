import streamlit as st


def _render_resist_cell(label, icon, value, is_edit_mode):
    st.markdown(f"<div style='text-align: center; font-size: 20px;'>{icon}</div>", unsafe_allow_html=True)

    if is_edit_mode:
        return st.number_input(label, value=float(value), step=0.1, label_visibility="collapsed",
                               key=f"res_input_{label}")
    else:
        color = "#fff"
        if value < 1.0:
            color = "#aaffaa"  # Green (Resist)
        elif value > 1.0:
            color = "#ffaaaa"  # Red (Weak)

        st.markdown(f"<div style='text-align: center; color: {color}; font-weight: bold;'>{value}</div>",
                    unsafe_allow_html=True)
        return value


def render_resistances(unit, is_edit_mode: bool):
    st.write("**Resistances (HP)**")

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