import streamlit as st
import uuid

from core.card import Card
from core.dice import Dice
from core.enums import DiceType
from core.library import Library
from logic.statuses.status_manager import STATUS_REGISTRY
from ui.editor.editor_loader import load_card_to_state
from ui.components import _format_script_text

# ==========================================
# ⚙️ СХЕМЫ СКРИПТОВ (КОНФИГУРАЦИЯ)
# ==========================================
# Здесь мы описываем интерфейс для каждого типа скрипта.
# Типы полей: 'int', 'float', 'text', 'select', 'status_select', 'bool'

STATUS_LIST = sorted(list(STATUS_REGISTRY.keys()))
TARGET_OPTS = ["self", "target", "all"]

SCRIPT_SCHEMAS = {
    # --- ЛЕЧЕНИЕ / РЕСУРСЫ ---
    "Restore HP": {
        "id": "restore_hp",
        "params": [
            {"key": "amount", "label": "Количество", "type": "int", "default": 5},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"], "default": "self"}
        ]
    },
    "Restore SP": {
        "id": "restore_sp",
        "params": [
            {"key": "amount", "label": "Количество", "type": "int", "default": 5,
             "help": "Отрицательное = Урон рассудку"},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"], "default": "self"}
        ]
    },
    "Self Harm (%)": {
        "id": "self_harm_percent",
        "params": [
            {"key": "percent", "label": "Процент HP (0.1 = 10%)", "type": "float", "default": 0.05}
        ]
    },
    "Add HP Damage (%)": {
        "id": "add_hp_damage",
        "params": [
            {"key": "percent", "label": "Процент от Макс HP", "type": "float", "default": 0.05}
        ]
    },

    # --- СТАТУСЫ ---
    "Apply Status": {
        "id": "apply_status",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "bleed"},
            {"key": "stack", "label": "Кол-во (Stack)", "type": "int", "default": 1},
            {"key": "duration", "label": "Длительность", "type": "int", "default": 1},
            {"key": "target", "label": "Цель", "type": "select", "opts": TARGET_OPTS, "default": "target"},
            {"key": "min_roll", "label": "Мин. бросок (0=всегда)", "type": "int", "default": 0},
            {"key": "delay", "label": "Задержка (Delay)", "type": "int", "default": 0}
        ]
    },
    "Apply Status (Roll)": {
        "id": "apply_status_by_roll",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "barrier"},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"], "default": "self"}
        ]
    },
    "Steal Status": {
        "id": "steal_status",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "smoke"}
        ]
    },
    "Multiply Status": {
        "id": "multiply_status",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "smoke"},
            {"key": "multiplier", "label": "Множитель (x)", "type": "float", "default": 2.0},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"], "default": "target"}
        ]
    },

    # --- УНИКАЛЬНЫЕ / ПРОЧЕЕ ---
    "Luck Scaling Roll": {
        "id": "add_luck_bonus_roll",
        "params": [
            {"key": "step", "label": "Удачи за бросок", "type": "int", "default": 10},
            {"key": "limit", "label": "Лимит бросков", "type": "int", "default": 5}
        ]
    },
    "Custom Damage": {
        "id": "deal_custom_damage",
        "params": [
            {"key": "type", "label": "Тип", "type": "select", "opts": ["hp", "stagger"], "default": "stagger"},
            {"key": "scale", "label": "Множитель (x)", "type": "float", "default": 1.0},
            {"key": "target", "label": "Цель", "type": "select", "opts": TARGET_OPTS, "default": "target"},
            {"key": "prevent_standard", "label": "Отменить обычный урон?", "type": "bool", "default": False}
        ]
    },
    "Pat Shoulder (Buff)": {
        "id": "pat_shoulder",
        "params": [
            {"key": "mode", "label": "Режим", "type": "select", "opts": ["off", "def"], "default": "off"},
            {"key": "amount", "label": "Сила баффа", "type": "int", "default": 6}
        ]
    },
    "Eloquence Clash": {
        "id": "eloquence_clash",
        "params": []  # Нет параметров
    }
}


# ==========================================
# 🛠️ ГЕНЕРАТОР UI
# ==========================================

def _render_dynamic_form(prefix: str, schema_name: str) -> dict:
    """
    Рисует инпуты на основе выбранной схемы и возвращает готовый словарь params.
    """
    if schema_name not in SCRIPT_SCHEMAS:
        return {}

    schema = SCRIPT_SCHEMAS[schema_name]
    params_def = schema["params"]
    result_params = {}

    if not params_def:
        st.caption("Нет настроек.")
        return {}

    # Разбиваем на колонки для компактности (по 3 в ряд)
    cols = st.columns(3)

    for i, p_def in enumerate(params_def):
        col = cols[i % 3]

        key = p_def["key"]
        label = p_def["label"]
        p_type = p_def["type"]
        default = p_def["default"]
        help_text = p_def.get("help", None)

        widget_key = f"{prefix}_{schema_name}_{key}"

        with col:
            if p_type == "int":
                val = st.number_input(label, value=default, step=1, key=widget_key, help=help_text)
                result_params[key] = int(val)
            elif p_type == "float":
                val = st.number_input(label, value=float(default), step=0.1, format="%.2f", key=widget_key,
                                      help=help_text)
                result_params[key] = float(val)
            elif p_type == "text":
                val = st.text_input(label, value=str(default), key=widget_key, help=help_text)
                result_params[key] = val
            elif p_type == "bool":
                val = st.checkbox(label, value=bool(default), key=widget_key, help=help_text)
                result_params[key] = val
            elif p_type == "select":
                opts = p_def["opts"]
                val = st.selectbox(label, opts, index=opts.index(default) if default in opts else 0, key=widget_key,
                                   help=help_text)
                result_params[key] = val
            elif p_type == "status_select":
                # Специальный селект для статусов
                idx = STATUS_LIST.index(default) if default in STATUS_LIST else 0
                val = st.selectbox(label, STATUS_LIST, index=idx, key=widget_key, help=help_text)
                result_params[key] = val

    return result_params


# ==========================================
# 🖥️ ОСНОВНОЙ РЕНДЕР
# ==========================================

def render_editor_page():
    st.markdown("### 🛠️ Универсальный Редактор Карт")

    # Инициализация сессии
    if "ed_script_list" not in st.session_state: st.session_state["ed_script_list"] = []
    if "ed_flags" not in st.session_state: st.session_state["ed_flags"] = []

    # --- 0. ЗАГРУЗКА ---
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

    # --- 1. ОСНОВНЫЕ ПАРАМЕТРЫ ---
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        name = c1.text_input("Название карты", key="ed_name")
        tier = c2.selectbox("Tier (Ранг)", [1, 2, 3, 4, 5], key="ed_tier")
        ctype = c3.selectbox("Тип",
                             ["Melee", "Offensive", "Ranged", "Mass Summation", "Mass Individual", "On Play", "Item"],
                             key="ed_type")

        flags = st.multiselect("Флаги", ["friendly", "offensive", "unchangeable", "exhaust"], key="ed_flags")
        desc = st.text_area("Описание", key="ed_desc", height=68)

    # --- 2. ЭФФЕКТЫ КАРТЫ (ГЛОБАЛЬНЫЕ) ---
    # Это скрипты, которые привязаны к карте целиком (On Use, On Combat End)

    with st.expander("✨ Эффекты карты (Global Scripts)", expanded=True):
        ce_col1, ce_col2 = st.columns([1, 2])
        ce_trigger = ce_col1.selectbox("Триггер", ["on_use", "on_combat_end"], key="ce_trig")
        ce_schema_name = ce_col2.selectbox("Эффект", list(SCRIPT_SCHEMAS.keys()), key="ce_schema")

        # Рисуем динамическую форму
        current_params = _render_dynamic_form("global", ce_schema_name)

        if st.button("➕ Добавить эффект карты"):
            script_id = SCRIPT_SCHEMAS[ce_schema_name]["id"]
            st.session_state["ed_script_list"].append({
                "trigger": ce_trigger,
                "data": {"script_id": script_id, "params": current_params}
            })
            st.rerun()

        # Список добавленных
        st.divider()
        st.caption("Список эффектов карты:")
        g_scripts = st.session_state["ed_script_list"]

        if not g_scripts:
            st.caption("Пусто")

        for i, item in enumerate(g_scripts):
            trig = item['trigger']
            sid = item['data'].get('script_id')
            p = item['data'].get('params', {})

            c_txt, c_del = st.columns([5, 0.5])
            c_txt.markdown(f"`{trig}` : **{_format_script_text(sid, p)}**")
            if c_del.button("❌", key=f"del_g_{i}"):
                g_scripts.pop(i)
                st.rerun()

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
                # База
                d_c1, d_c2, d_c3, d_c4 = st.columns([1.5, 1, 1, 1])
                dtype_str = d_c1.selectbox("Тип", ["Slash", "Pierce", "Blunt", "Block", "Evade"], key=f"d_t_{i}")
                d_min = d_c2.number_input("Min", -99, 999, 2, key=f"d_min_{i}")
                d_max = d_c3.number_input("Max", -99, 999, 5, key=f"d_max_{i}")
                d_counter = d_c4.checkbox("Counter?", key=f"d_cnt_{i}")

                st.divider()
                st.caption("Добавить эффект к кубику:")

                # Инициализация списка скриптов для кубика в сессии
                dice_script_key = f"ed_dice_scripts_{i}"
                if dice_script_key not in st.session_state:
                    st.session_state[dice_script_key] = []

                # Форма добавления скрипта кубика
                de_c1, de_c2 = st.columns([1, 2])
                de_trig = de_c1.selectbox("Условие", ["on_hit", "on_clash_win", "on_clash_lose", "on_roll", "on_play"],
                                          key=f"de_trig_sel_{i}")
                de_schema = de_c2.selectbox("Эффект", list(SCRIPT_SCHEMAS.keys()), key=f"de_schema_sel_{i}")

                de_params = _render_dynamic_form(f"dice_{i}", de_schema)

                if st.button(f"➕ Добавить к Dice {i + 1}", key=f"add_de_{i}"):
                    s_id = SCRIPT_SCHEMAS[de_schema]["id"]
                    st.session_state[dice_script_key].append({
                        "trigger": de_trig,
                        "data": {"script_id": s_id, "params": de_params}
                    })
                    st.rerun()

                # Список скриптов кубика
                st.caption("Эффекты кубика:")
                d_scripts_list = st.session_state[dice_script_key]
                if not d_scripts_list:
                    st.caption("Нет")

                final_dice_scripts_dict = {}

                for idx, ds in enumerate(d_scripts_list):
                    t = ds['trigger']
                    d_sid = ds['data'].get('script_id')
                    d_p = ds['data'].get('params', {})

                    c_d_txt, c_d_del = st.columns([5, 0.5])
                    c_d_txt.markdown(f"- `{t}` : {_format_script_text(d_sid, d_p)}")
                    if c_d_del.button("x", key=f"del_de_{i}_{idx}"):
                        d_scripts_list.pop(idx)
                        st.rerun()

                    # Сборка для создания объекта
                    if t not in final_dice_scripts_dict: final_dice_scripts_dict[t] = []
                    final_dice_scripts_dict[t].append(ds['data'])

                # Создаем объект кубика (для сохранения)
                new_die = Dice(d_min, d_max, DiceType[dtype_str.upper()], is_counter=d_counter,
                               scripts=final_dice_scripts_dict)
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

            # Сборка глобальных скриптов
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