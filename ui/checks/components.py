import random

import streamlit as st

from ui.checks.logic import get_stat_value, calculate_pre_roll_stats, perform_check_logic


def get_difficulty_description(value, stat_key=""):
    """Возвращает текстовое описание сложности/уровня."""
    stat_key = stat_key.lower()

    if stat_key == "luck":
        val_abs = abs(value)
        prefix = "ОТРИЦАТЕЛЬНАЯ: " if value < 0 else ""

        if val_abs < 6: return prefix + "1 - Полный неудачник (Свиппер уже выехал)"
        if val_abs < 12: return prefix + "6 - Обычная удача (Кетчуп на месте)"
        if val_abs < 20: return prefix + "12 - Сегодня везёт! (Монетка)"
        if val_abs < 30: return prefix + "20 - Куш в казино (Осторожнее)"
        if val_abs < 45: return prefix + "30 - Нереальное везение (Друзья, Улики)"
        if val_abs < 60: return prefix + "45 - Корни странностей (Исправление ошибок)"
        if val_abs < 80: return prefix + "60 - Потустороннее вмешательство"
        if val_abs < 100: return prefix + "80 - Влияние на историю Города"
        return prefix + "100+ - Поле 'Удачи' (Звезда Города)"
    return None

def calculate_luck_cost(chosen_value, current_luck):
    """
    Рассчитывает стоимость (или восстановление) удачи.
    """
    abs_val = abs(chosen_value)
    cost = 0

    if abs_val < 6: cost = 1
    elif abs_val < 12: cost = 3
    elif abs_val < 20: cost = 5
    elif abs_val < 30: cost = 10
    elif abs_val < 45: cost = 20
    elif abs_val < 60: cost = 40
    elif abs_val < 80:
        cost = current_luck if current_luck > 0 else 0
        if chosen_value < 0: cost = 60
    else:
        cost = current_luck if current_luck > 0 else 0
        if chosen_value < 0: cost = 100

    return cost

def draw_luck_interface(unit):
    """Специальный интерфейс для Удачи."""
    st.divider()

    current_luck = unit.resources.get("luck", 0)
    c_cur, c_roll = st.columns([1, 1])
    c_cur.metric("Текущая Удача (Ресурс)", current_luck)

    roll_key = f"luck_roll_val_{unit.name}"

    if c_roll.button("🎲 Ролл Потенциала (1d12 + Luck)", type="primary"):
        roll = random.randint(1, 12)
        total_roll = roll + current_luck
        st.session_state[roll_key] = total_roll
        if f"luck_choice_{unit.name}" in st.session_state:
            del st.session_state[f"luck_choice_{unit.name}"]

    if roll_key in st.session_state:
        max_pot = abs(st.session_state[roll_key])
        st.info(f"🎰 Максимальный потенциал: **{max_pot}**")

        choice = st.slider(
            "Выберите уровень воздействия",
            min_value=-max_pot, max_value=max_pot, value=0,
            key=f"luck_choice_{unit.name}",
            help="Положительное: Тратит удачу. Отрицательное: Восстанавливает."
        )

        desc = get_difficulty_description(choice, "luck")
        st.caption(f"📜 {desc}")

        cost_val = calculate_luck_cost(choice, current_luck)
        new_luck = 0
        msg = ""

        if choice > 0:
            new_luck = current_luck - cost_val
            msg = f"📉 Трата: -{cost_val} (Новое значение: {new_luck})"
            if new_luck < 0:
                st.warning(f"⚠️ Внимание: Удача уйдет в минус ({new_luck})!")
        elif choice < 0:
            new_luck = current_luck + cost_val
            msg = f"📈 Восстановление: +{cost_val} (Новое значение: {new_luck})"
        else:
            new_luck = current_luck
            msg = "Нет изменений"

        st.markdown(f"**{msg}**")

        if choice != 0:
            if st.button("✅ Применить и сохранить", type="secondary"):
                unit.resources["luck"] = new_luck
                del st.session_state[roll_key]
                del st.session_state[f"luck_choice_{unit.name}"]
                st.success("Удача обновлена!")
                st.rerun()

def draw_roll_interface(unit, selected_key, selected_label):
    st.divider()
    val = get_stat_value(unit, selected_key)

    c_val, c_dc, c_bonus = st.columns([1, 1, 1])
    c_val.metric(f"{selected_label}", val)

    difficulty = c_dc.number_input("Сложность (DC)", 0, 100, 15, key=f"dc_{selected_key}")
    bonus = c_bonus.number_input("Бонус", -20, 20, 0, key=f"bonus_{selected_key}")

    chance, ev, final_dc = calculate_pre_roll_stats(unit, selected_key, val, difficulty, bonus)

    if chance >= 80: color = "green"
    elif chance >= 50: color = "orange"
    else: color = "red"

    st.markdown(f"Шанс: :{color}[**{chance:.1f}%**] | Ожидание: **{ev:.1f}** | DC: **{final_dc}**")

    if st.button("🎲 Бросить", type="primary", width='stretch', key=f"btn_{selected_key}"):
        res = perform_check_logic(unit, selected_key, val, difficulty, bonus)
        res_color = "green" if res["is_success"] else "red"

        with st.container(border=True):
            c_img, c_txt = st.columns([1, 4])
            with c_img:
                img = unit.avatar if unit.avatar else "https://placehold.co/100x100/png?text=Unit"
                st.image(img, width=80)

            with c_txt:
                st.markdown(f"### :{res_color}[{res['msg']}]")
                st.markdown(f"**{res['total']}** vs **{res['final_difficulty']}**")

                # Формула: бросок + модификаторы = итог
                die_text = f"`{res['roll']} ({res['die']})`" if res['die'] != "Fixed" else ""
                st.markdown(f"{die_text} + {res['formula_text']} = **{res['total']}**")

                if res['is_crit']: st.caption("🔥 CRITICAL SUCCESS")
                if res['is_fumble']: st.caption("💀 CRITICAL FAILURE")