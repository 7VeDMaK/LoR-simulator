import streamlit as st

from core.library import Library


def reset_editor_state(default_file=None):
    """
    Сбрасывает редактор.
    :param default_file: Если указан, новая карта будет привязана к этому файлу.
    """
    # 1. Очистка (как было)
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith(("ed_", "d_", "de_"))]
    for k in keys_to_clear:
        del st.session_state[k]

    # 2. Дефолтные значения
    st.session_state["ed_name"] = "New Card"
    st.session_state["ed_desc"] = ""
    st.session_state["ed_tier"] = 1
    st.session_state["ed_type"] = "Melee"
    st.session_state["ed_num_dice"] = 1
    st.session_state["ed_num_dice_input"] = 1
    st.session_state["ed_flags"] = []

    # [FIX] Логика выбора файла
    if default_file:
        st.session_state["ed_source_file"] = default_file
    else:
        # Пытаемся взять первый попавшийся или custom
        all_files = Library.get_all_source_files()
        if "custom_cards.json" in all_files:
            st.session_state["ed_source_file"] = "custom_cards.json"
        elif all_files:
            st.session_state["ed_source_file"] = all_files[0]
        else:
            st.session_state["ed_source_file"] = "default.json"

    st.session_state["ed_script_list"] = []

    # ID не должно быть при создании новой
    if "ed_loaded_id" in st.session_state:
        del st.session_state["ed_loaded_id"]


def load_card_to_state(card):
    """
    Загружает объект Card в переменные сессии редактора.
    Использует упрощенную логику списков для скриптов.
    """
    if card is None:
        reset_editor_state()
        return

    # Сначала чистим всё, чтобы убрать мусор
    reset_editor_state()

    # --- 1. Основные параметры ---
    st.session_state["ed_name"] = card.name
    st.session_state["ed_desc"] = card.description
    st.session_state["ed_tier"] = card.tier
    st.session_state["ed_loaded_id"] = card.id
    st.session_state["ed_flags"] = card.flags if card.flags else []
    source = Library.get_source(card.id)
    if source:
        st.session_state["ed_source_file"] = source
    else:
        st.session_state["ed_source_file"] = "custom_cards.json"
    # Приводим тип карты к красивому виду (например, "melee" -> "Melee")
    # Список валидных типов для селекта в редакторе
    valid_types = ["Melee", "Offensive", "Ranged", "Mass Summation", "Mass Individual", "On Play", "Item"]

    ctype_title = str(card.card_type).title()
    # Если вдруг в файле что-то странное, ставим дефолт
    if ctype_title not in valid_types:
        # Пытаемся найти частичное совпадение (например "Mass" -> "Mass Summation")
        found = False
        for vt in valid_types:
            if vt.lower() == str(card.card_type).lower():
                st.session_state["ed_type"] = vt
                found = True
                break
        if not found:
            st.session_state["ed_type"] = "Melee"
    else:
        st.session_state["ed_type"] = ctype_title

    st.session_state["ed_num_dice"] = len(card.dice_list)
    st.session_state["ed_num_dice_input"] = len(card.dice_list)

    # --- 2. Глобальные скрипты (On Use / On Play) ---
    # Новый редактор ожидает список словарей: [{'trigger': '...', 'data': {...}}, ...]
    global_scripts = []
    if card.scripts:
        for trigger, effects_list in card.scripts.items():
            for effect in effects_list:
                global_scripts.append({
                    "trigger": trigger,
                    "data": effect  # effect уже содержит {"script_id": "...", "params": {...}}
                })

    st.session_state["ed_script_list"] = global_scripts

    # --- 3. Кубики (Dice) ---
    for i, d in enumerate(card.dice_list):
        # Базовые параметры кубика
        # .name у Enum возвращает "SLASH", .capitalize() -> "Slash"
        st.session_state[f"d_t_{i}"] = d.dtype.name.capitalize()
        st.session_state[f"d_min_{i}"] = d.min_val
        st.session_state[f"d_max_{i}"] = d.max_val
        st.session_state[f"d_cnt_{i}"] = getattr(d, 'is_counter', False)

        # Скрипты кубика
        # Сохраняем в ключ, который ожидает редактор: ed_dice_scripts_{i}
        dice_scripts = []
        if d.scripts:
            for trigger, effects_list in d.scripts.items():
                for effect in effects_list:
                    dice_scripts.append({
                        "trigger": trigger,
                        "data": effect
                    })

        st.session_state[f"ed_dice_scripts_{i}"] = dice_scripts