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
STATUS_LIST = sorted(list(STATUS_REGISTRY.keys()))
TARGET_OPTS = ["self", "target", "all"]
STAT_OPTS = ["None", "strength", "endurance", "agility", "intellect", "eloquence", "luck", "max_hp", "current_hp",
             "max_sp", "current_sp", "charge", "smoke"]

SCRIPT_SCHEMAS = {
    # --- БОЕВЫЕ МОДИФИКАТОРЫ ---
    "Modify Roll Power": {
        "id": "modify_roll_power",
        "params": [
            {"key": "base", "label": "База (Flat)", "type": "int", "default": 0},
            {"key": "stat", "label": "Скалирование от...", "type": "select", "opts": STAT_OPTS, "default": "None"},
            {"key": "scale_from_target", "label": "Брать стат у Цели?", "type": "bool", "default": False},
            {"key": "factor", "label": "Множитель стата (x)", "type": "float", "default": 1.0},
            {"key": "diff", "label": "Разница с врагом?", "type": "bool", "default": False,
             "help": "(Мой стат - Стат врага)"},
            {"key": "reason", "label": "Название в логе", "type": "text", "default": "Bonus"}
        ]
    },

    # --- ЛЕЧЕНИЕ / РЕСУРСЫ ---
    "Restore Resource": {
        "id": "restore_resource",
        "params": [
            {"key": "type", "label": "Ресурс", "type": "select", "opts": ["hp", "sp", "stagger"], "default": "hp"},
            {"key": "base", "label": "База", "type": "int", "default": 5},
            {"key": "stat", "label": "Скалирование от...", "type": "select", "opts": STAT_OPTS, "default": "None"},
            {"key": "scale_from_target", "label": "Брать стат у Цели?", "type": "bool", "default": False},
            {"key": "factor", "label": "Множитель стата", "type": "float", "default": 0.5},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target", "all_allies"],
             "default": "self"}
        ]
    },

    # --- УРОН ЭФФЕКТОМ ---
    "Deal Effect Damage": {
        "id": "deal_effect_damage",
        "params": [
            {"key": "type", "label": "Тип урона", "type": "select", "opts": ["hp", "stagger", "sp"], "default": "hp"},
            {"key": "base", "label": "База", "type": "int", "default": 0},
            {"key": "stat", "label": "Скалирование от...", "type": "select", "opts": STAT_OPTS,
             "default": "current_hp"},
            {"key": "scale_from_target", "label": "Брать стат у Цели?", "type": "bool", "default": False},
            {"key": "factor", "label": "Множитель (для %)", "type": "float", "default": 0.05},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target", "all"], "default": "self"}
        ]
    },

    # --- СТАТУСЫ ---
    "Apply Status": {
        "id": "apply_status",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "bleed"},
            {"key": "base", "label": "Базовое кол-во", "type": "int", "default": 1},
            {"key": "stat", "label": "Скейл от (опц.)", "type": "select", "opts": STAT_OPTS, "default": "None"},
            {"key": "scale_from_target", "label": "Брать стат у Цели?", "type": "bool", "default": False},
            {"key": "factor", "label": "Множитель скейла", "type": "float", "default": 1.0},
            {"key": "duration", "label": "Длительность", "type": "int", "default": 1},
            {"key": "delay", "label": "Задержка (Delay)", "type": "int", "default": 0},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["target", "self", "all_allies"],
             "default": "target"}
        ]
    },

    "Steal Status": {
        "id": "steal_status",
        "params": [{"key": "status", "label": "Статус", "type": "status_select", "default": "smoke"}]
    },
    "Multiply Status": {
        "id": "multiply_status",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "smoke"},
            {"key": "multiplier", "label": "Множитель", "type": "float", "default": 2.0}
        ]
    },
    "Remove Status": {
        "id": "remove_status",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "bleed"},
            {"key": "base", "label": "Сколько снять", "type": "int", "default": 999},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"], "default": "self"}
        ]
    },
    "Remove All Positive": {
        "id": "remove_all_positive",
        "params": [
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"], "default": "self"}
        ]
    },
    "Self Harm Percent": {
        "id": "self_harm_percent",
        "params": [
            {"key": "percent", "label": "Процент (0.1 = 10%)", "type": "float", "default": 0.1}
        ]
    },
    "Add HP Damage": {
        "id": "add_hp_damage",
        "params": [
            {"key": "percent", "label": "Процент от Макс HP цели", "type": "float", "default": 0.05}
        ]
    },
    "Apply Status By Roll": {
        "id": "apply_status_by_roll",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "protection"},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"], "default": "self"}
        ]
    },
    "Add Luck Bonus": {
        "id": "add_luck_bonus_roll",
        "params": [
            {"key": "step", "label": "Шаг удачи", "type": "int", "default": 10},
            {"key": "limit", "label": "Лимит бонуса", "type": "int", "default": 999}
        ]
    },
    "Scale Roll By Luck": {
        "id": "scale_roll_by_luck",
        "params": [
            {"key": "step", "label": "Шаг удачи", "type": "int", "default": 10},
            {"key": "limit", "label": "Лимит повторов", "type": "int", "default": 7}
        ]
    },
    "Add Power By Luck": {
        "id": "add_power_by_luck",
        "params": [
            {"key": "step", "label": "Шаг удачи", "type": "int", "default": 5},
            {"key": "limit", "label": "Лимит силы", "type": "int", "default": 15}
        ]
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
            # Streamlit берет значение из st.session_state[widget_key], если оно там есть
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
                idx = STATUS_LIST.index(default) if default in STATUS_LIST else 0
                val = st.selectbox(label, STATUS_LIST, index=idx, key=widget_key, help=help_text)
                result_params[key] = val

    return result_params


# ==========================================
# 🔙 CALLBACKS (ДЛЯ БЕЗОПАСНОГО ИЗМЕНЕНИЯ STATE)
# ==========================================

def edit_global_script(index):
    """Callback для редактирования глобального скрипта."""
    g_scripts = st.session_state["ed_script_list"]
    if index >= len(g_scripts): return

    item = g_scripts[index]
    trig = item['trigger']
    sid = item['data'].get('script_id')
    p = item['data'].get('params', {})

    schema_name = next((k for k, v in SCRIPT_SCHEMAS.items() if v["id"] == sid), None)
    if schema_name:
        # Устанавливаем селекторы
        st.session_state["ce_trig"] = trig
        st.session_state["ce_schema"] = schema_name

        # Устанавливаем параметры в форму
        prefix = "global"
        for param_key, param_val in p.items():
            widget_key = f"{prefix}_{schema_name}_{param_key}"
            st.session_state[widget_key] = param_val

        # Удаляем из списка (чтобы "вернуть" в редактор)
        g_scripts.pop(index)


def delete_global_script(index):
    """Callback для удаления глобального скрипта."""
    st.session_state["ed_script_list"].pop(index)


def edit_dice_script(dice_idx, script_idx):
    """Callback для редактирования скрипта кубика."""
    key = f"ed_dice_scripts_{dice_idx}"
    d_scripts = st.session_state[key]
    if script_idx >= len(d_scripts): return

    item = d_scripts[script_idx]
    t = item['trigger']
    d_sid = item['data'].get('script_id')
    d_p = item['data'].get('params', {})

    schema_name = next((k for k, v in SCRIPT_SCHEMAS.items() if v["id"] == d_sid), None)
    if schema_name:
        # Селекторы для конкретного кубика
        st.session_state[f"de_trig_sel_{dice_idx}"] = t
        st.session_state[f"de_schema_sel_{dice_idx}"] = schema_name

        # Параметры
        prefix = f"dice_{dice_idx}"
        for param_key, param_val in d_p.items():
            widget_key = f"{prefix}_{schema_name}_{param_key}"
            st.session_state[widget_key] = param_val

        # Удаляем
        d_scripts.pop(script_idx)


def delete_dice_script(dice_idx, script_idx):
    """Callback для удаления скрипта кубика."""
    st.session_state[f"ed_dice_scripts_{dice_idx}"].pop(script_idx)


# ==========================================
# 🖥️ ОСНОВНОЙ РЕНДЕР
# ==========================================

def render_editor_page():
    st.markdown("### 🛠️ Универсальный Редактор Карт")

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
    with st.expander("✨ Эффекты карты (Global Scripts)", expanded=True):
        ce_col1, ce_col2 = st.columns([1, 2])
        ce_trigger = ce_col1.selectbox("Триггер", ["on_use", "on_combat_end"], key="ce_trig")
        ce_schema_name = ce_col2.selectbox("Эффект", list(SCRIPT_SCHEMAS.keys()), key="ce_schema")

        current_params = _render_dynamic_form("global", ce_schema_name)

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
            c_txt.markdown(f"`{trig}` : **{_format_script_text(sid, p)}**")

            # Используем callbacks (on_click) для безопасного редактирования
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
                # База
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

                st.caption("Эффекты кубика:")
                d_scripts_list = st.session_state[dice_script_key]
                if not d_scripts_list:
                    st.caption("Нет")

                final_dice_scripts_dict = {}

                for idx, ds in enumerate(d_scripts_list):
                    t = ds['trigger']
                    d_sid = ds['data'].get('script_id')
                    d_p = ds['data'].get('params', {})

                    c_d_txt, c_d_edit, c_d_del = st.columns([4, 0.5, 0.5])
                    c_d_txt.markdown(f"- `{t}` : {_format_script_text(d_sid, d_p)}")

                    # Callbacks для кубиков
                    c_d_edit.button("✏️", key=f"edit_de_{i}_{idx}", on_click=edit_dice_script, args=(i, idx),
                                    help="Редактировать")
                    c_d_del.button("❌", key=f"del_de_{i}_{idx}", on_click=delete_dice_script, args=(i, idx),
                                   help="Удалить")

                    if t not in final_dice_scripts_dict: final_dice_scripts_dict[t] = []
                    final_dice_scripts_dict[t].append(ds['data'])

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