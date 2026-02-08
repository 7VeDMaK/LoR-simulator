import streamlit as st

from core.dice import Dice
from core.enums import DiceType
from ui.editor.config import SCRIPT_SCHEMAS
from ui.editor.forms import render_dynamic_form
from ui.icons import get_icon_html
from ui.editor.callbacks import edit_dice_script, delete_dice_script
from ui.profile_new.tabs.build_parts.formatting import _translate_script_effect


def render_dice_editor(card_type):
    """
    Отрисовывает табы с кубиками и возвращает список объектов Dice.
    """
    st.subheader("🎲 Кубики")

    def_dice = 0 if card_type == "Item" else 1
    # Инициализация количества при первом запуске
    if "ed_num_dice" not in st.session_state:
        st.session_state["ed_num_dice"] = def_dice

    col_n, _ = st.columns([1, 3])

    # Виджет сам обновляет st.session_state["ed_num_dice_input"],
    # но нам нужно синхронизировать его с нашей логической переменной ed_num_dice
    num_dice = col_n.number_input(
        "Кол-во кубиков", 0, 10,
        key="ed_num_dice_input",
        value=st.session_state["ed_num_dice"]
    )
    st.session_state["ed_num_dice"] = num_dice

    dice_objects = []

    if num_dice > 0:
        tabs = st.tabs([f"Кубик #{i + 1}" for i in range(num_dice)])

        for i, tab in enumerate(tabs):
            with tab:
                d_c1, d_c2, d_c3, d_c4 = st.columns([1.5, 1, 1, 1])

                # --- [FIX] Убраны лишние присваивания в session_state ---

                # 1. Тип кубика
                # Если ключа нет в стейте, ставим дефолт
                if f"d_t_{i}" not in st.session_state:
                    st.session_state[f"d_t_{i}"] = "Slash"

                # Получаем индекс для selectbox
                types = ["Slash", "Pierce", "Blunt", "Block", "Evade"]
                curr_t = st.session_state.get(f"d_t_{i}", "Slash")
                try:
                    t_idx = types.index(curr_t)
                except ValueError:
                    t_idx = 0

                dtype_str = d_c1.selectbox("Тип", types, key=f"d_t_{i}", index=t_idx)

                with d_c1:
                    st.caption(f"Иконка: {get_icon_html(dtype_str, 20)}", unsafe_allow_html=True)

                # 2. Мин/Макс/Counter
                # Для number_input value берется из key автоматически, если он есть в session_state.
                # Мы просто задаем дефолты через value на случай, если ключа еще нет.
                d_min = d_c2.number_input("Min", 0, 999, key=f"d_min_{i}", value=st.session_state.get(f"d_min_{i}", 4))
                d_max = d_c3.number_input("Max", 0, 999, key=f"d_max_{i}", value=st.session_state.get(f"d_max_{i}", 8))
                d_counter = d_c4.checkbox("Counter?", key=f"d_cnt_{i}", value=st.session_state.get(f"d_cnt_{i}", False))

                # --- ВАЖНО: Мы удалили строки вида st.session_state[...] = ... после виджетов ---

                st.divider()

                # === Dice Scripts ===
                st.markdown("**📜 Эффекты кубика**")

                dice_script_key = f"ed_dice_scripts_{i}"
                if dice_script_key not in st.session_state:
                    st.session_state[dice_script_key] = []

                # Форма добавления
                with st.expander(f"➕ Добавить эффект на Кубик #{i + 1}", expanded=False):
                    de_c1, de_c2 = st.columns([1, 2])
                    de_trig = de_c1.selectbox("Условие",
                                              ["on_hit", "on_clash_win", "on_clash_lose", "on_roll", "on_clash",
                                               "on_play"],
                                              key=f"de_trig_sel_{i}")
                    de_schema = de_c2.selectbox("Эффект", list(SCRIPT_SCHEMAS.keys()), key=f"de_schema_sel_{i}")

                    de_params = render_dynamic_form(f"dice_{i}", de_schema)

                    if st.button(f"Добавить", key=f"add_de_{i}"):
                        from ui.editor.forms import clean_editor_params
                        cleaned = clean_editor_params(de_params)

                        s_id = SCRIPT_SCHEMAS[de_schema]["id"]
                        st.session_state[dice_script_key].append({
                            "trigger": de_trig,
                            "data": {"script_id": s_id, "params": cleaned}
                        })
                        st.success("Добавлено!")
                        st.rerun()

                # Список эффектов
                d_scripts_list = st.session_state[dice_script_key]
                final_dice_scripts_dict = {}

                if d_scripts_list:
                    for idx, ds in enumerate(d_scripts_list):
                        trigger = ds['trigger']
                        data = ds['data']

                        pretty_html = _translate_script_effect(data)
                        tech_str = f"{data.get('script_id')} {data.get('params')}"

                        c_del, c_info, c_edit = st.columns([1, 10, 1])

                        if c_del.button("🗑️", key=f"del_de_{i}_{idx}"):
                            delete_dice_script(i, idx)
                            st.rerun()

                        with c_info:
                            st.markdown(f"""
                            <div style="
                                background-color: #262730; 
                                border: 1px solid #555; 
                                border-radius: 5px; 
                                padding: 6px; 
                                margin-bottom: 4px;
                            ">
                                <div style="font-weight: bold; color: #8ecae6; font-size: 0.9em;">🎲 {trigger.upper().replace('_', ' ')}</div>
                                <div style="font-size: 1em; margin: 2px 0;">{pretty_html}</div>
                                <div style="font-family: monospace; color: #777; font-size: 0.75em;">{tech_str}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        # Кнопка редактирования
                        if c_edit.button("✏️", key=f"edit_de_{i}_{idx}"):
                            edit_dice_script(i, idx)
                            st.rerun()

                        # Собираем словарь для объекта Dice
                        if trigger not in final_dice_scripts_dict:
                            final_dice_scripts_dict[trigger] = []
                        final_dice_scripts_dict[trigger].append(data)
                else:
                    st.caption("Нет эффектов.")

                # Создаем объект кубика
                try:
                    dtype_enum = DiceType[dtype_str.upper()]
                except KeyError:
                    dtype_enum = DiceType.SLASH

                new_die = Dice(d_min, d_max, dtype_enum, is_counter=d_counter,
                               scripts=final_dice_scripts_dict)
                dice_objects.append(new_die)

    return dice_objects