import streamlit as st
import random
from ui.checks.logic import get_stat_value, calculate_pre_roll_stats, perform_check_logic


def get_difficulty_description(value, stat_key=""):
    """Возвращает текстовое описание сложности/уровня."""
    stat_key = stat_key.lower()
    if stat_key == "luck":
        val_abs = abs(value)
        prefix = "ОТРИЦАТЕЛЬНАЯ: " if value < 0 else ""
        if val_abs < 6: return prefix + "1 - Полный неудачник"
        if val_abs < 12: return prefix + "6 - Обычная удача"
        if val_abs < 20: return prefix + "12 - Сегодня везёт!"
        if val_abs < 30: return prefix + "20 - Куш в казино"
        if val_abs < 45: return prefix + "30 - Нереальное везение"
        if val_abs < 60: return prefix + "45 - Корни странностей"
        if val_abs < 80: return prefix + "60 - Потустороннее вмешательство"
        if val_abs < 100: return prefix + "80 - Влияние на историю Города"
        return prefix + "100+ - Поле 'Удачи'"
    return None


def calculate_luck_cost(chosen_value, current_luck):
    abs_val = abs(chosen_value)
    if abs_val < 6:
        return 1
    elif abs_val < 12:
        return 3
    elif abs_val < 20:
        return 5
    elif abs_val < 30:
        return 10
    elif abs_val < 45:
        return 20
    elif abs_val < 60:
        return 40
    elif abs_val < 80:
        return current_luck if current_luck > 0 else 0
    else:
        return current_luck if current_luck > 0 else 0


def draw_luck_interface(unit):
    """Специальный интерфейс для Удачи."""
    st.divider()

    current_luck = unit.resources.get("luck", 0)
    c_cur, c_roll = st.columns([1, 1])
    c_cur.metric("Текущая Удача (Ресурс)", current_luck)

    roll_key = f"luck_roll_val_{unit.name}"

    # === 1. КНОПКА БРОСКА (Просто определяет потенциал) ===
    if c_roll.button("🎲 Ролл Потенциала (1d12 + Luck)", type="primary"):
        roll = random.randint(1, 12)
        total_roll = roll + current_luck

        st.session_state[roll_key] = total_roll

        # Сброс выбора
        if f"luck_choice_{unit.name}" in st.session_state:
            del st.session_state[f"luck_choice_{unit.name}"]

        # [ИЗМЕНЕНИЕ] УБРАЛИ ВЫЗОВ ТРИГГЕРА ОТСЮДА
        # Мы не хотим давать опыт за сам факт броска потенциала

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
        new_luck = current_luck - cost_val if choice > 0 else current_luck + cost_val if choice < 0 else current_luck

        msg = f"📉 Трата: -{cost_val}" if choice > 0 else f"📈 Восстановление: +{cost_val}" if choice < 0 else "Нет изменений"
        st.markdown(f"**{msg}** (Новое: {new_luck})")

        if choice != 0:
            # === 2. КНОПКА ПРИМЕНЕНИЯ (Здесь срабатывает эффект) ===
            if st.button("✅ Применить и сохранить", type="secondary"):

                # [ИЗМЕНЕНИЕ] ВЫЗЫВАЕМ ХУК ЗДЕСЬ С ВЫБРАННЫМ ЗНАЧЕНИЕМ
                if hasattr(unit, "trigger_hooks"):
                    # Передаем 'choice', так как это и есть итоговый результат проверки
                    unit.trigger_hooks("on_luck_check", result=choice)

                unit.resources["luck"] = new_luck
                del st.session_state[roll_key]
                st.success("Удача обновлена и опыт начислен!")
                st.rerun()


def draw_roll_interface(unit, selected_key, selected_label):
    st.divider()
    val = get_stat_value(unit, selected_key)

    c_val, c_dc, c_bonus = st.columns([1, 1, 1])
    c_val.metric(f"{selected_label}", val)

    difficulty = c_dc.number_input("Сложность (DC)", 0, 100, 15, key=f"dc_{selected_key}")
    bonus = c_bonus.number_input("Бонус", -20, 20, 0, key=f"bonus_{selected_key}")

    chance, ev, final_dc = calculate_pre_roll_stats(unit, selected_key, val, difficulty, bonus)
    color = "green" if chance >= 80 else "orange" if chance >= 50 else "red"
    st.markdown(f"Шанс: :{color}[**{chance:.1f}%**] | Ожидание: **{ev:.1f}** | DC: **{final_dc}**")

    if st.button("🎲 Бросить", type="primary", width='stretch', key=f"btn_{selected_key}"):
        res = perform_check_logic(unit, selected_key, val, difficulty, bonus)
        res_color = "green" if res["is_success"] else "red"

        # ВЫЗЫВАЕМ ХУК ПАССИВКИ (Для обычных навыков)
        if hasattr(unit, "trigger_hooks"):
            unit.trigger_hooks("on_skill_check", check_result=res['total'], stat_key=selected_key)

        with st.container(border=True):
            st.markdown(f"### :{res_color}[{res['msg']}]")
            st.markdown(f"**{res['total']}** vs **{res['final_difficulty']}**")
            if res['is_crit']: st.caption("🔥 CRITICAL SUCCESS")