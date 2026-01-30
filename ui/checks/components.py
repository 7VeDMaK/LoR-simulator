import streamlit as st
import random
from core.unit.unit_library import UnitLibrary
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


def _has_talent(unit, talent_id):
    """Надежная проверка наличия таланта или пассивки по ID."""
    for t in getattr(unit, 'talents', []):
        t_id = t if isinstance(t, str) else getattr(t, 'id', '')
        if t_id == talent_id: return True
    for p in getattr(unit, 'passives', []):
        p_id = p if isinstance(p, str) else getattr(p, 'id', '')
        if p_id == talent_id: return True
    return False


def _get_max_golden_dice(unit):
    """Расчет максимума золотых костей (7.5 + улучшения)."""
    base = 2
    if _has_talent(unit, "lucky_coin"): base += 1  # Старый ID, оставил для совместимости
    if _has_talent(unit, "azino_777"): base += 1
    if _has_talent(unit, "ace_sleeve") or _has_talent(unit, "joker_talent"): base += 1
    return base


def get_roll_formula(unit, key, f_type):
    """Хелпер для получения формулы броска."""
    val = unit.attributes.get(key, 0)
    if f_type == "attr":
        return 6, val // 3
    elif f_type == "skill":
        return 6, val
    elif f_type == "d20":
        return 20, val
    elif f_type == "int":
        return 6, 4 + val
    return 6, 0


def draw_luck_interface(unit):
    """Специальный интерфейс для Удачи."""
    st.divider()

    current_luck = unit.resources.get("luck", 0)
    c_cur, c_roll = st.columns([1, 1])
    c_cur.metric("Текущая Удача", current_luck)

    roll_key = f"luck_roll_val_{unit.name}"

    # === 1. КНОПКА БРОСКА ПОТЕНЦИАЛА ===
    # [FIX] Добавлен уникальный key на основе имени юнита
    if c_roll.button("🎲 Ролл Потенциала (1d12 + Luck)", type="primary", key=f"btn_luck_pot_{unit.name}"):
        roll = random.randint(1, 12)
        total_roll = roll + current_luck
        st.session_state[roll_key] = total_roll
        # Сброс выбора
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
        new_luck = current_luck - cost_val if choice > 0 else current_luck + cost_val if choice < 0 else current_luck

        msg = f"📉 Трата: -{cost_val}" if choice > 0 else f"📈 Восстановление: +{cost_val}" if choice < 0 else "Нет изменений"
        st.markdown(f"**{msg}** (Новое: {new_luck})")

        if choice != 0:
            # [FIX] Добавлен уникальный key
            if st.button("✅ Применить и сохранить", type="secondary", key=f"btn_luck_apply_{unit.name}"):
                if hasattr(unit, "trigger_hooks"):
                    unit.trigger_hooks("on_luck_check", result=choice)
                unit.resources["luck"] = new_luck
                UnitLibrary.save_unit(unit)
                del st.session_state[roll_key]
                st.success("Удача обновлена!")
                st.rerun()


def draw_roll_interface(unit, selected_key, selected_label, formula="skill"):
    st.divider()
    val = get_stat_value(unit, selected_key)

    c_val, c_dc, c_bonus = st.columns([1, 1, 1])
    c_val.metric(f"{selected_label}", val)

    # Уникальные ключи для инпутов
    difficulty = c_dc.number_input("Сложность (DC)", 0, 100, 15, key=f"dc_{unit.name}_{selected_key}")
    bonus = c_bonus.number_input("Бонус", -20, 20, 0, key=f"bonus_{unit.name}_{selected_key}")

    # === [NEW] ТАЛАНТ 7.10: Невозможное возможно ===
    if _has_talent(unit, "impossible_possible"):
        bonus += 10
        st.caption("✨ **+10** (Невозможное возможно)")

    chance, ev, final_dc = calculate_pre_roll_stats(unit, selected_key, val, difficulty, bonus)
    color = "green" if chance >= 80 else "orange" if chance >= 50 else "red"
    st.markdown(f"Шанс: :{color}[**{chance:.1f}%**] | Ожидание: **{ev:.1f}** | DC: **{final_dc}**")

    chk_key = f"last_check_{unit.name}_{selected_key}"

    # === [NEW] МЕХАНИКА 7.8: СЧАСТЛИВАЯ МОНЕТКА ===
    if _has_talent(unit, "blessed_by_fate"):
        coins = unit.memory.get("lucky_coin_count", 0)

        col_c1, col_c2 = st.columns([2, 1])
        with col_c2:
            st.caption(f"🪙 Монеты: {coins}")

        with col_c1:
            if coins > 0:
                # [FIX] Добавлен уникальный key
                if st.button(f"🪙 Подбросить монету (50/50)", help="Орел = Успех, Решка = 1.", type="primary",
                             use_container_width=True, key=f"btn_coin_{unit.name}_{selected_key}"):

                    unit.memory["lucky_coin_count"] -= 1
                    is_heads = random.choice([True, False])

                    max_die, base_bonus = get_roll_formula(unit, selected_key, formula)
                    dc_val = difficulty

                    if is_heads:
                        # ОРЕЛ
                        final_total = max(dc_val, dc_val + 2)
                        roll_val = max(1, final_total - base_bonus - bonus)
                        if roll_val > max_die: roll_val = max_die
                        msg_toast = "ОРЕЛ! Судьба на вашей стороне."
                        icon_toast = "🦅"
                    else:
                        # РЕШКА
                        roll_val = 1
                        final_total = 1 + base_bonus + bonus
                        msg_toast = "РЕШКА! Критический провал."
                        icon_toast = "💀"

                    st.session_state[chk_key] = {
                        "key": selected_key,
                        "roll": roll_val,
                        "die": f"d{max_die}",
                        "max_die": max_die,
                        "bonus": base_bonus + bonus,
                        "total": final_total,
                        "final_difficulty": dc_val,
                        "formula_text": f"Coin({roll_val}) + {base_bonus + bonus}",
                        "is_success": final_total >= dc_val,
                        "is_crit": False,
                        "golden_recovered": False
                    }

                    UnitLibrary.save_unit(unit)
                    st.toast(msg_toast, icon=icon_toast)
                    st.rerun()

    # === ОБЫЧНАЯ КНОПКА БРОСКА ===
    # [FIX] Добавлен уникальный key с именем юнита
    if st.button("🎲 Бросить", type="primary", use_container_width=True, key=f"btn_roll_{unit.name}_{selected_key}"):
        res = perform_check_logic(unit, selected_key, val, difficulty, bonus)
        res["golden_recovered"] = False
        st.session_state[chk_key] = res
        st.rerun()

    # === ОТОБРАЖЕНИЕ РЕЗУЛЬТАТА ===
    if chk_key in st.session_state:
        res = st.session_state[chk_key]

        # 1. Восстановление при крит провале (7.5)
        if res.get("roll") == 1 and _has_talent(unit, "not_luck_just_skill"):
            if not res.get("golden_recovered", False):
                max_dice = _get_max_golden_dice(unit)
                current_dice = unit.memory.get("golden_dice_current", 0)

                if current_dice < max_dice:
                    unit.memory["golden_dice_current"] = current_dice + 1
                    UnitLibrary.save_unit(unit)
                    st.toast("Критический провал (1)! Получена Золотая кость +1", icon="🎲")

                res["golden_recovered"] = True

        is_success = res["total"] >= res["final_difficulty"]
        res_color = "green" if is_success else "red"
        msg_text = "УСПЕХ" if is_success else "ПРОВАЛ"

        with st.container(border=True):
            st.markdown(f"### :{res_color}[{msg_text}]")
            st.markdown(f"**{res['total']}** vs **{res['final_difficulty']}**")

            roll_str = f"**{res['roll']}**" if res['roll'] == 1 else f"{res['roll']}"
            st.caption(f"Кубик: {roll_str} ({res['die']}) | Формула: {res['formula_text']}")
            if res.get('is_crit'): st.caption("🔥 CRITICAL SUCCESS")

            # --- ИНТЕРФЕЙС "ЗОЛОТЫХ КОСТЕЙ" (Talent 7.5) ---
            if _has_talent(unit, "not_luck_just_skill"):
                charges = unit.memory.get("golden_dice_current", 0)
                st.write(f"🔸 **Золотые кости:** {charges}")

                c_g1, c_g2 = st.columns(2)

                def spend_golden_die(amount):
                    # Эффект костей
                    bonus_val = 0
                    for _ in range(amount):
                        bonus_val += (random.randint(1, 5) + 5)

                    res["total"] += bonus_val
                    res["formula_text"] += f" + {bonus_val}(Gold)"
                    unit.memory["golden_dice_current"] -= amount

                    # СИНЕРГИЯ 7.8: Трата кости дает Монетку
                    if _has_talent(unit, "blessed_by_fate"):
                        current_coins = unit.memory.get("lucky_coin_count", 0)
                        unit.memory["lucky_coin_count"] = current_coins + 1
                        st.toast("Судьба оценила риск: Получена Монетка!", icon="🪙")

                    UnitLibrary.save_unit(unit)
                    st.rerun()

                # Кнопка: Потратить 1
                if charges >= 1:
                    # [FIX] Ключи уже были уникальны (chk_key), но для надежности оставил как есть, так как chk_key включает unit.name
                    if c_g1.button("🎲 +1 Кость (+1d5+5)", key=f"gold_1_{chk_key}"):
                        spend_golden_die(1)

                # Кнопка: Потратить 2
                if charges >= 2:
                    if c_g2.button("🎲🎲 +2 Кости (+2x)", key=f"gold_2_{chk_key}"):
                        spend_golden_die(2)

            # --- ИНТЕРФЕЙС "ПОСЛЕДОВАТЕЛЬНОЙ УДАЧИ" (Talent 7.3) ---
            # Показываем только при ПРОВАЛЕ
            if not is_success and _has_talent(unit, "sequential_luck"):
                st.divider()
                st.caption("🍀 7.3 Последовательная удача")

                missing = res['final_difficulty'] - res['total']
                cost = missing * 2  # Цена исправления
                roll_val = res.get('roll', 0)
                gain = max(0, 20 - roll_val)
                current_luck = unit.resources.get("luck", 0)

                c_fail, c_fix = st.columns(2)

                # Опция 1: Принять провал
                with c_fail:
                    if st.button(f"📉 Принять провал\n(+{gain} Удачи)", key=f"fail_{chk_key}", use_container_width=True):
                        unit.resources["luck"] = current_luck + gain
                        UnitLibrary.save_unit(unit)
                        del st.session_state[chk_key]
                        st.toast(f"Провал принят. Удача: {unit.resources['luck']} (+{gain})")
                        st.rerun()

                # Опция 2: Исправить
                with c_fix:
                    can_afford = current_luck >= cost
                    label_fix = f"🔥 Исправить (-{cost} Удачи)"
                    if not can_afford:
                        label_fix += "\n[Не хватает]"

                    if st.button(label_fix, disabled=not can_afford, key=f"fix_{chk_key}", type="primary",
                                 use_container_width=True):
                        unit.resources["luck"] = current_luck - cost
                        UnitLibrary.save_unit(unit)
                        del st.session_state[chk_key]
                        st.toast(f"Судьба изменена на Успех! Удача: {unit.resources['luck']} (-{cost})")
                        st.rerun()

            else:
                st.write("")
                if st.button("Закрыть результат", key=f"close_{chk_key}", use_container_width=True):
                    del st.session_state[chk_key]
                    st.rerun()