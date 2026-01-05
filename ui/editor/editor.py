import streamlit as st
import uuid

from core.card import Card
from core.dice import Dice
from core.enums import DiceType
from core.library import Library
from ui.editor.editor_loader import load_card_to_state
from ui.components import _format_script_text

# Импорты из новых модулей
from ui.editor.config import SCRIPT_SCHEMAS
from ui.editor.forms import render_dynamic_form
from ui.editor.callbacks import (
    edit_global_script, delete_global_script,
    edit_dice_script, delete_dice_script
)

def render_editor_page():
    st.markdown("### 🛠️ Универсальный Редактор Карт")

    if "ed_script_list" not in st.session_state: st.session_state["ed_script_list"] = []
    if "ed_flags" not in st.session_state: st.session_state["ed_flags"] = []

    # ... (Загрузка и Основные параметры без изменений) ...
    # ЗАГРУЗКА
    all_cards = Library.get_all_cards()
    all_cards.sort(key=lambda x: x.name)
    card_options = {"(Создать новую)": None}
    for c in all_cards:
        card_options[f"{c.name} ({c.id[:4]}..)"] = c
    c_load_sel, c_load_btn = st.columns([3, 1])
    selected_option = c_load_sel.selectbox("Шаблон", list(card_options.keys()), label_visibility="collapsed")
    if c_load_btn.button("📥 Загрузить", use_container_width=True):
        load_card_to_state(card_options[selected_option])
        st.rerun()

    # ПАРАМЕТРЫ
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        name = c1.text_input("Название карты", key="ed_name")
        tier = c2.selectbox("Tier (Ранг)", [1, 2, 3, 4, 5], key="ed_tier")
        ctype = c3.selectbox("Тип", ["Melee", "Offensive", "Ranged", "Mass Summation", "Mass Individual", "On Play", "Item"], key="ed_type")
        flags = st.multiselect("Флаги", ["friendly", "offensive", "unchangeable", "exhaust"], key="ed_flags")
        desc = st.text_area("Описание", key="ed_desc", height=68)

    # --- 2. ЭФФЕКТЫ КАРТЫ (ГЛОБАЛЬНЫЕ) ---
    with st.expander("✨ Эффекты карты (Global Scripts)", expanded=True):
        ce_col1, ce_col2 = st.columns([1, 2])
        ce_trigger = ce_col1.selectbox("Триггер", ["on_use", "on_combat_end"], key="ce_trig")
        ce_schema_name = ce_col2.selectbox("Эффект", list(SCRIPT_SCHEMAS.keys()), key="ce_schema")

        current_params = render_dynamic_form("global", ce_schema_name)

        if st.button("➕ Добавить эффект карты"):
            script_id = SCRIPT_SCHEMAS[ce_schema_name]["id"]
            st.session_state["ed_script_list"].append({
                "trigger": ce_trigger,
                "data": {"script_id": script_id, "params": current_params}
            })
            st.rerun()

        st.divider()
        st.caption("Список эффектов карты:")
        g_scripts = st.session_state["ed_script_list"]

        if not g_scripts:
            st.caption("Пусто")

        for i, item in enumerate(g_scripts):
            trig = item['trigger']
            sid = item['data'].get('script_id')
            p = item['data'].get('params', {})

            c_txt, c_edit, c_del = st.columns([4, 0.5, 0.5])
            # [FIX] Разрешаем HTML для иконок в редакторе
            c_txt.markdown(f"`{trig}` : **{_format_script_text(sid, p)}**", unsafe_allow_html=True)

            c_edit.button("✏️", key=f"edit_g_{i}", on_click=edit_global_script, args=(i,), help="Редактировать")
            c_del.button("❌", key=f"del_g_{i}", on_click=delete_global_script, args=(i,), help="Удалить")

    # --- 3. КУБИКИ (DICE) ---
    st.divider()
    st.markdown("**Настройка кубиков**")

    def_dice = 0 if ctype == "Item" else 1
    if "ed_num_dice" not in st.session_state: st.session_state["ed_num_dice"] = def_dice
    num_dice = st.number_input("Кол-во кубиков", 0, 5, key="ed_num_dice")

    dice_objects = []

    if num_dice > 0:
        tabs = st.tabs([f"Dice {i + 1}" for i in range(num_dice)])

        for i, tab in enumerate(tabs):
            with tab:
                d_c1, d_c2, d_c3, d_c4 = st.columns([1.5, 1, 1, 1])
                dtype_str = d_c1.selectbox("Тип", ["Slash", "Pierce", "Blunt", "Block", "Evade"], key=f"d_t_{i}")
                d_min = d_c2.number_input("Min", -99, 999, 2, key=f"d_min_{i}")
                d_max = d_c3.number_input("Max", -99, 999, 5, key=f"d_max_{i}")
                d_counter = d_c4.checkbox("Counter?", key=f"d_cnt_{i}")

                st.divider()
                st.caption("Добавить эффект к кубику:")

                dice_script_key = f"ed_dice_scripts_{i}"
                if dice_script_key not in st.session_state:
                    st.session_state[dice_script_key] = []

                de_c1, de_c2 = st.columns([1, 2])
                de_trig = de_c1.selectbox("Условие", ["on_hit", "on_clash_win", "on_clash_lose", "on_roll", "on_play"], key=f"de_trig_sel_{i}")
                de_schema = de_c2.selectbox("Эффект", list(SCRIPT_SCHEMAS.keys()), key=f"de_schema_sel_{i}")

                de_params = render_dynamic_form(f"dice_{i}", de_schema)

                if st.button(f"➕ Добавить к Dice {i + 1}", key=f"add_de_{i}"):
                    s_id = SCRIPT_SCHEMAS[de_schema]["id"]
                    st.session_state[dice_script_key].append({
                        "trigger": de_trig,
                        "data": {"script_id": s_id, "params": de_params}
                    })
                    st.rerun()

                st.caption("Эффекты кубика:")
                d_scripts_list = st.session_state[dice_script_key]
                if not d_scripts_list: st.caption("Нет")

                final_dice_scripts_dict = {}

                for idx, ds in enumerate(d_scripts_list):
                    t = ds['trigger']
                    d_sid = ds['data'].get('script_id')
                    d_p = ds['data'].get('params', {})

                    c_d_txt, c_d_edit, c_d_del = st.columns([4, 0.5, 0.5])
                    # [FIX] Разрешаем HTML
                    c_d_txt.markdown(f"- `{t}` : {_format_script_text(d_sid, d_p)}", unsafe_allow_html=True)

                    c_d_edit.button("✏️", key=f"edit_de_{i}_{idx}", on_click=edit_dice_script, args=(i, idx), help="Редактировать")
                    c_d_del.button("❌", key=f"del_de_{i}_{idx}", on_click=delete_dice_script, args=(i, idx), help="Удалить")

                    if t not in final_dice_scripts_dict: final_dice_scripts_dict[t] = []
                    final_dice_scripts_dict[t].append(ds['data'])

                new_die = Dice(d_min, d_max, DiceType[dtype_str.upper()], is_counter=d_counter, scripts=final_dice_scripts_dict)
                dice_objects.append(new_die)

    # --- 4. СОХРАНЕНИЕ ---
    st.divider()
    c_save, c_del, _ = st.columns([1, 1, 2])

    if c_save.button("💾 Сохранить Карту", type="primary"):
        if not name:
            st.error("Введите имя!")
        else:
            cid = st.session_state.get("ed_loaded_id")
            if not cid:
                cid = name.lower().replace(" ", "_") + "_" + str(uuid.uuid4())[:4]

            final_global_scripts = {}
            for gs in st.session_state["ed_script_list"]:
                trig = gs["trigger"]
                if trig not in final_global_scripts: final_global_scripts[trig] = []
                final_global_scripts[trig].append(gs["data"])

            new_card = Card(
                id=cid,
                name=name,
                tier=tier,
                card_type=ctype,
                description=desc,
                dice_list=dice_objects,
                scripts=final_global_scripts,
                flags=st.session_state["ed_flags"]
            )
            Library.save_card(new_card)
            st.toast(f"Карта {name} сохранена!", icon="✅")

    if st.session_state.get("ed_loaded_id"):
        if c_del.button("🗑️ Удалить"):
            Library.delete_card(st.session_state["ed_loaded_id"])
            st.toast("Удалено!", icon="🗑️")
            from ui.editor.editor_loader import reset_editor_state
            reset_editor_state()
            st.rerun()