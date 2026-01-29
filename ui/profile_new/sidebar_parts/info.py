import streamlit as st
from core.unit.unit_library import UnitLibrary


def handle_rename(unit, new_name):
    """Меняет имя юнита и обновляет ключ в ростере."""
    if 'roster' in st.session_state:
        roster = st.session_state['roster']
        old_name = unit.name

        if new_name not in roster:
            roster[new_name] = roster.pop(old_name)
            unit.name = new_name

            UnitLibrary.delete_unit(old_name)
            UnitLibrary.save_unit(unit)

            if 'profile_selected_unit' in st.session_state:
                st.session_state['profile_selected_unit'] = new_name

            st.toast(f"Renamed to {new_name}")
            st.rerun()
        else:
            st.error(f"Name '{new_name}' already exists!")


def render_basic_info(unit, is_edit_mode: bool):
    if is_edit_mode:
        new_name = st.text_input("Имя", value=unit.name)
        if new_name != unit.name and new_name:
            handle_rename(unit, new_name)

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