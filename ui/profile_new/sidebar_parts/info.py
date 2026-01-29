import streamlit as st
from core.unit.unit_library import UnitLibrary
from core.enums import UnitType


def _get_rank_info(grade):
    """
    Возвращает (Название, Цвет) на основе Градации (Grade).
    В Project Moon:
    9 = Canard (Слабый)
    1 = Grade 1 (Сильный)
    0 = Color (Легенда)
    """
    # Чем МЕНЬШЕ число, тем КРУЧЕ ранг.

    if grade >= 9:
        return "Canard (Grade 9)", "gray"
    elif grade == 8:
        return "Urban Myth (Grade 8)", "green"
    elif grade == 7:
        return "Urban Legend (Grade 7)", "green"
    elif grade == 6:
        return "Urban Plague (Grade 6)", "blue"
    elif grade == 5:
        return "Urban Nightmare (Grade 5)", "blue"
    elif grade == 4:
        return "Star of the City (Grade 4)", "orange"
    elif grade == 3:
        return "Impurity / Grade 3", "orange"
    elif grade == 2:
        return "Grade 2", "red"
    elif grade == 1:
        return "Grade 1", "red"
    else:
        # 0 и отрицательные числа
        return "Color Fixer", "red"


def render_basic_info(unit, is_edit_mode: bool):
    """
    Рендер основной информации: Имя, Тип, Уровень, Интеллект, Ранг, Скорость.
    """
    u_key = unit.name

    # === 1. ИМЯ (NAME) ===
    if is_edit_mode:
        new_name = st.text_input("Имя", value=unit.name, key=f"name_inp_{u_key}")
        if new_name != unit.name:
            unit.name = new_name
            UnitLibrary.save_unit(unit)
    else:
        st.markdown(f"### {unit.name}")

    # === 2. ТИП / ФРАКЦИЯ ===
    labels_map = UnitType.ui_labels()
    type_options = list(labels_map.keys())

    try:
        curr_idx = type_options.index(unit.unit_type)
    except ValueError:
        curr_idx = 0

    if is_edit_mode:
        new_type = st.selectbox(
            "Тип / Фракция",
            type_options,
            index=curr_idx,
            format_func=lambda x: labels_map.get(x, x),
            key=f"type_select_{u_key}"
        )
        if new_type != unit.unit_type:
            unit.unit_type = new_type
            UnitLibrary.save_unit(unit)
            st.rerun()
    else:
        t_label = labels_map.get(unit.unit_type, unit.unit_type)
        st.caption(f"Фракция: {t_label}")

    # === 3. УРОВЕНЬ И ИНТЕЛЛЕКТ ===
    c_lvl, c_int = st.columns(2)

    with c_lvl:
        if is_edit_mode:
            new_lvl = st.number_input("Уровень", 1, 999, unit.level, key=f"lvl_{u_key}")
            if new_lvl != unit.level:
                unit.level = new_lvl
                unit.recalculate_stats()
                UnitLibrary.save_unit(unit)
                st.rerun()
        else:
            st.markdown(f"**Уровень**: {unit.level}")

    # Интеллект
    base_int = getattr(unit, 'base_intellect', 3)

    with c_int:
        if is_edit_mode:
            new_int = st.number_input("Баз. Инт.", 1, 99, base_int, key=f"base_int_{u_key}")
            if new_int != base_int:
                unit.base_intellect = new_int
                unit.recalculate_stats()
                UnitLibrary.save_unit(unit)
                st.rerun()
        else:
            pass

    total_int_data = unit.modifiers.get("total_intellect", {})
    if isinstance(total_int_data, dict):
        total_int = total_int_data.get("flat", base_int)
    else:
        total_int = total_int_data if total_int_data else base_int

    diff_int = total_int - base_int
    sign = "+" if diff_int > 0 else ""
    diff_str = f"({sign}{diff_int})" if diff_int != 0 else ""

    if is_edit_mode or diff_int != 0:
        st.info(f"🧠 Интеллект: **{total_int}** {diff_str}")
    elif not is_edit_mode:
        st.markdown(f"**Интеллект**: {total_int}")

    st.divider()

    # === 4. РАНГ (RANK / GRADE) ===
    st.markdown("**Ранг Фиксера**")
    r_c1, r_c2 = st.columns(2)

    # Используем unit.rank как Grade (9 = низкий, 1 = высокий)
    cur_rank = getattr(unit, 'rank', 9)

    with r_c1:
        if is_edit_mode:
            # Input: от 9 (слабый) до 0 (Color)
            new_rank = st.number_input("Ранг (Grade)", 0, 9, cur_rank, help="9 - Canard, 1 - Grade 1",
                                       key=f"rank_cur_{u_key}")
            if new_rank != cur_rank:
                unit.rank = new_rank
                UnitLibrary.save_unit(unit)
                st.rerun()

        r_name, r_color = _get_rank_info(unit.rank)
        st.markdown(f":{r_color}[**{r_name}**]")

    with r_c2:
        status_rank = unit.memory.get("status_rank", "Fixer")
        if is_edit_mode:
            new_status = st.text_input("Статус (Текст)", status_rank, key=f"rank_stat_{u_key}")
            if new_status != status_rank:
                unit.memory["status_rank"] = new_status
                UnitLibrary.save_unit(unit)
        else:
            st.markdown(f"_{status_rank}_")

    st.divider()

    # === 5. СКОРОСТЬ ===
    st.markdown(f"**🧊 Скорость:**")
    speed_dice = getattr(unit, 'computed_speed_dice', [])
    if not speed_dice:
        s_min = getattr(unit, 'base_speed_min', 2)
        s_max = getattr(unit, 'base_speed_max', 6)
        st.markdown(f"- {s_min}~{s_max}")
    else:
        for i, d in enumerate(speed_dice):
            st.markdown(f"{i + 1}. **{d[0]}~{d[1]}**")