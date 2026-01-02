import streamlit as st


def reset_editor_state():
    """Сбрасывает все поля редактора в дефолтные значения."""
    # 1. Очищаем старые ключи
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith(("ed_", "ce_", "d_", "de_"))]
    for k in keys_to_clear:
        del st.session_state[k]

    # 2. Устанавливаем дефолты
    st.session_state["ed_name"] = "New Card"
    st.session_state["ed_desc"] = ""
    st.session_state["ed_tier"] = 1
    st.session_state["ed_type"] = "melee"
    st.session_state["ed_num_dice"] = 2
    st.session_state["ce_type"] = "None"

    # Сбрасываем список скриптов
    st.session_state["ed_script_list"] = []

    # Сбрасываем ID
    if "ed_loaded_id" in st.session_state:
        del st.session_state["ed_loaded_id"]


def load_card_to_state(card):
    """
    Разбирает объект Card и заполняет session_state редактора.
    """
    if card is None:
        reset_editor_state()
        return

    # Сначала чистим мусор от предыдущей карты
    reset_editor_state()

    # --- 1. Основные параметры ---
    st.session_state["ed_name"] = card.name
    st.session_state["ed_desc"] = card.description
    st.session_state["ed_tier"] = card.tier
    st.session_state["ed_type"] = card.card_type
    st.session_state["ed_num_dice"] = len(card.dice_list)
    st.session_state["ed_loaded_id"] = card.id  # Запоминаем ID для перезаписи

    script_list = []
    if card.scripts:
        for trigger, effects in card.scripts.items():
            for effect in effects:
                script_list.append({
                    "trigger": trigger,
                    "data": effect
                })

    st.session_state["ed_script_list"] = script_list

    # Загрузка эффектов On Use
    if "on_use" in card.scripts and card.scripts["on_use"]:
        script = card.scripts["on_use"][0]
        sid = script.get("script_id")
        p = script.get("params", {})

        # --- RESTORE HP ---
        if sid == "restore_hp":
            st.session_state["ce_type"] = "Restore HP"
            st.session_state["ce_restore_mode"] = "Flat"
            st.session_state["ce_restore_val"] = p.get("amount", 5)
        elif sid == "restore_hp_percent":
            st.session_state["ce_type"] = "Restore HP"
            st.session_state["ce_restore_mode"] = "%"
            st.session_state["ce_restore_val"] = p.get("percent", 0.05) * 100.0

        # --- RESTORE SP ---
        elif sid == "restore_sp":
            st.session_state["ce_type"] = "Restore SP"
            st.session_state["ce_restore_mode"] = "Flat"
            st.session_state["ce_restore_val"] = p.get("amount", 5)
        elif sid == "restore_sp_percent":
            st.session_state["ce_type"] = "Restore SP"
            st.session_state["ce_restore_mode"] = "%"
            st.session_state["ce_restore_val"] = p.get("percent", 0.05) * 100.0

        # --- ДРУГИЕ ---
        elif sid == "apply_status":
            st.session_state["ce_type"] = "Apply Status"
            st.session_state["ce_st_name"] = p.get("status", "bleed")
            st.session_state["ce_st_stack"] = p.get("stack", 1)
            st.session_state["ce_st_dur"] = p.get("duration", 1)
            st.session_state["ce_st_del"] = p.get("delay", 0)
            st.session_state["ce_st_tgt"] = p.get("target", "target")

        elif sid == "steal_status":
            st.session_state["ce_type"] = "Steal Status"
            st.session_state["ce_steal_st"] = p.get("status", "smoke")

        elif sid == "self_harm_percent":
            st.session_state["ce_type"] = "Self Harm (%)"
            st.session_state["ce_sh_pct"] = p.get("percent", 0.025) * 100.0

    # --- 3. Кубики ---
    for i, d in enumerate(card.dice_list):
        # Базовые параметры кубика
        st.session_state[f"d_t_{i}"] = d.dtype.name.capitalize()
        st.session_state[f"d_min_{i}"] = d.min_val
        st.session_state[f"d_max_{i}"] = d.max_val
        st.session_state[f"de_type_{i}"] = "None"

        # Ищем скрипт кубика
        found_script = None
        found_trigger = "on_hit"

        # Проверяем все возможные триггеры
        for trig in ["on_hit", "on_clash_win", "on_clash_lose", "on_play", "on_roll"]:
            if trig in d.scripts and d.scripts[trig]:
                found_script = d.scripts[trig][0]
                found_trigger = trig
                break

        if found_script:
            st.session_state[f"de_trig_{i}"] = found_trigger
            sid = found_script.get("script_id")
            p = found_script.get("params", {})

            prefix = f"de_{i}"  # Префикс для полей статусов

            if sid == "restore_hp":
                st.session_state[f"de_type_{i}"] = "Restore HP"
                st.session_state[f"de_h_amt_{i}"] = p.get("amount", 2)

            elif sid == "apply_status":
                st.session_state[f"de_type_{i}"] = "Apply Status"
                st.session_state[f"{prefix}_st_name"] = p.get("status", "bleed")
                st.session_state[f"{prefix}_st_stack"] = p.get("stack", 1)
                st.session_state[f"{prefix}_st_tgt"] = p.get("target", "target")
                st.session_state[f"{prefix}_min_roll"] = p.get("min_roll", 0)

            elif sid == "apply_status_by_roll":  # Зиккурат
                st.session_state[f"de_type_{i}"] = "Status = Roll Value"
                st.session_state[f"de_rv_n_{i}"] = p.get("status", "barrier")
                st.session_state[f"de_rv_t_{i}"] = p.get("target", "self")

            elif sid == "add_hp_damage":
                st.session_state[f"de_type_{i}"] = "Add HP Damage (%)"
                st.session_state[f"de_hp_pct_{i}"] = p.get("percent", 0.05) * 100.0

            elif sid == "add_luck_bonus_roll":  # Серия ударов
                st.session_state[f"de_type_{i}"] = "Luck Scaling Roll"
                st.session_state[f"de_luck_s_{i}"] = p.get("step", 10)
                st.session_state[f"de_luck_l_{i}"] = p.get("limit", 7)

            elif sid == "steal_status":
                st.session_state[f"de_type_{i}"] = "Steal Status"
                st.session_state[f"de_steal_{i}"] = p.get("status", "smoke")

            elif sid == "multiply_status":
                st.session_state[f"de_type_{i}"] = "Multiply Status"
                st.session_state[f"de_mul_n_{i}"] = p.get("status", "smoke")
                st.session_state[f"de_mul_v_{i}"] = p.get("multiplier", 2.0)
                st.session_state[f"de_mul_t_{i}"] = p.get("target", "target")

            elif sid == "deal_custom_damage":
                st.session_state[f"de_type_{i}"] = "Custom Damage"
                st.session_state[f"de_cd_t_{i}"] = p.get("type", "stagger")
                st.session_state[f"de_cd_s_{i}"] = p.get("scale", 1.0)
                st.session_state[f"de_cd_p_{i}"] = p.get("prevent_standard", False)