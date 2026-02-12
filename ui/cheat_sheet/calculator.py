import pandas as pd
import streamlit as st

from ui.cheat_sheet.utils import get_base_rolls_data


def render_calculator_tab():
    st.header("⚖️ Конструктор Баланса Карт")
    st.caption("Калькулятор значений на основе базовых роллов.")

    base_rolls_data = get_base_rolls_data()

    # 1. Таблица бюджетов
    with st.expander("📊 Таблица Бюджетов (Power Budget)", expanded=True):
        budget_rows = []
        for _, rank_name, b_min, b_max in base_rolls_data:
            avg = (b_min + b_max) / 2
            budget_rows.append({
                "Rank": rank_name,
                "Base Roll": f"{b_min}-{b_max}",
                "Avg (1 Die)": f"{avg:.1f}",
                "Budget 2d": f"{avg * 2:.1f}",
                "Budget 3d": f"{avg * 3:.1f}",
                "Budget 4d": f"{avg * 4:.1f}",
                "Budget 5d": f"{avg * 5:.1f}",
            })
        st.table(pd.DataFrame(budget_rows))
        st.caption("*Budget = (Base Avg) × (Dice Count).*")

    st.divider()

    # 2. Калькулятор
    c_set, c_res = st.columns([1, 1])

    base_avg = 2.0
    char_level_display = 0
    standard_dice_capacity = 1

    with c_set:
        st.subheader("🛠️ Настройка")

        if 'roster' in st.session_state and st.session_state['roster']:
            roster_names = sorted(list(st.session_state['roster'].keys()))
            current_key = st.session_state.get("bal_char_sel")
            default_index = 0
            if current_key in roster_names:
                default_index = roster_names.index(current_key)

            sel_char = st.selectbox("Персонаж", roster_names, index=default_index, key="bal_char_sel")
            unit = st.session_state['roster'][sel_char]
            char_level_display = unit.level

            found_stat = base_rolls_data[0]
            for row in base_rolls_data:
                if char_level_display >= row[0]:
                    found_stat = row
                else:
                    break

            b_min, b_max = found_stat[2], found_stat[3]
            base_avg = (b_min + b_max) / 2
            st.caption(f"Lvl {char_level_display} ({found_stat[1]}) -> Base: {b_min}-{b_max} (Avg {base_avg})")
        else:
            st.warning("Создайте персонажа для расчета!")

        card_rank = st.selectbox("Ранг карты (Tier)", [1, 2, 3, 4, 5], index=0, key="bal_card_rank")
        standard_dice_capacity = card_rank

        type_opts = {
            "Melee (100%)": 1.0, "Offensive (115%)": 1.15, "Ranged (125%)": 1.25,
            "Mass Attack (140%)": 1.40, "On Play (50%)": 0.5, "Item (40%)": 0.4
        }
        ctype_label = st.selectbox("Тип карты", list(type_opts.keys()), index=0, key="bal_type")
        type_mult = type_opts[ctype_label]

        dice_count = st.slider("Количество дайсов", 1, 7, 2, key="bal_count")

        st.markdown("**Модификаторы:**")
        effects_count = st.number_input("Кол-во эффектов (-10%)", 0, 100, 0)
        cond_hard = st.number_input("Сложные условия (+15%)", 0, 100, 0)
        cond_easy = st.number_input("Легкие условия (-7.5%)", 0, 100, 0)

        # Variance Logic
        rank_budget_mult_est = min(standard_dice_capacity, dice_count)
        est_total_budget = base_avg * rank_budget_mult_est * type_mult
        est_power_mod = 1.0 - (effects_count * 0.10) + ((cond_hard * 0.15) - (cond_easy * 0.075))
        est_budget = est_total_budget * est_power_mod

        est_avg_die = est_budget / max(dice_count, 1)
        if dice_count < standard_dice_capacity:
            bonus_mult = 1.3 ** abs(standard_dice_capacity - dice_count)
            est_avg_die *= bonus_mult

        max_var_dynamic = max(1, int((est_avg_die - 1) * 2))  # Минимум 1 для slider
        def_var = min(4, max_var_dynamic)
        variance = st.slider("Разброс (Variance)", 0, max_var_dynamic, def_var, help=f"Лимит: {max_var_dynamic}")

        if st.button("🔍 Найти лучший разброс"):
            _find_best_variance(max_var_dynamic, est_avg_die)

    with c_res:
        st.subheader("🎯 Результат")

        rank_budget_mult = min(standard_dice_capacity, dice_count)
        total_budget = base_avg * rank_budget_mult * type_mult

        eff_pen = effects_count * 0.10
        cond_mod = (cond_hard * 0.15) - (cond_easy * 0.075)
        power_mod = 1.0 - eff_pen + cond_mod
        effective_budget = total_budget * power_mod

        avg_per_die = effective_budget / dice_count

        split_bonus_val = 1.0
        split_bonus_applied = False
        if dice_count < standard_dice_capacity:
            split_bonus_val = 1.3 ** abs(standard_dice_capacity - dice_count)
            avg_per_die *= split_bonus_val
            split_bonus_applied = True

        # Variance Calc
        var_safe_min = avg_per_die * 0.30
        var_safe_max = avg_per_die * 0.70
        var_penalty = 0.0
        if variance < var_safe_min:
            var_penalty = (var_safe_min - variance) * 0.02
        elif variance > var_safe_max:
            var_penalty = (variance - var_safe_max) * 0.02

        var_factor = max(0.1, 1.0 - var_penalty)
        final_avg_die = avg_per_die * var_factor

        d_min, d_max = _calculate_min_max(final_avg_die, variance)

        with st.container(border=True):
            st.metric("Среднее (1 кубик)", f"{final_avg_die:.3f}")
            st.markdown(f"### 🎲 {d_min} ~ {d_max}")
            st.caption(f"Rank Cap: {standard_dice_capacity} dice | Split: {dice_count}")

        st.info(f"""
            **Base**: {base_avg} | **Budget**: x{rank_budget_mult} | **Mods**: {int(power_mod * 100)}%
            **Split**: x{split_bonus_val:.2f} | **Var Penalty**: -{int(var_penalty * 100)}%
        """)

        # Distribution
        if dice_count > 1:
            _render_distributor(dice_count, final_avg_die, variance)


def _calculate_min_max(avg, var):
    t_sum = int(round(avg * 2))
    eff_v = var
    if (t_sum % 2) != (eff_v % 2):
        if eff_v > 0:
            eff_v -= 1
        else:
            eff_v += 1
    mn = (t_sum - eff_v) // 2
    mx = (t_sum + eff_v) // 2
    if mn < 1:
        sh = 1 - mn;
        mn += sh;
        mx += sh
    return mn, mx


def _find_best_variance(max_var, est_avg):
    best_v = 0
    best_score = -1.0
    for v_check in range(max_var + 1):
        min_c, max_c = est_avg * 0.30, est_avg * 0.70
        pen = 0.0
        if v_check < min_c:
            pen = (min_c - v_check) * 0.02
        elif v_check > max_c:
            pen = (v_check - max_c) * 0.02
        score = est_avg * max(0.1, 1.0 - pen)
        if score > best_score: best_score = score; best_v = v_check
    st.toast(f"Оптимальный разброс: {best_v}", icon="✨")


def _render_distributor(dice_count, final_avg, variance):
    st.divider()
    with st.expander("🎛️ Настроить разные кубики (Распределение)"):
        total_budget = final_avg * dice_count
        st.caption(f"Общий бюджет (Avg): **{total_budget:.1f}**")
        remaining = total_budget

        for i in range(dice_count - 1):
            c1, c2, c3 = st.columns([1, 1, 2])
            def_min = int(final_avg - 2) if (final_avg - 2) > 1 else 1
            val_min = c1.number_input(f"D{i + 1} Min", 1, 200, def_min, key=f"md_min_{i}")
            val_max = c2.number_input(f"D{i + 1} Max", 1, 200, int(final_avg + 2), key=f"md_max_{i}")
            val_avg = (val_min + val_max) / 2
            c3.metric(f"D{i + 1} Avg", f"{val_avg:.1f}")
            remaining -= val_avg

        st.divider()
        c_l1, c_l2 = st.columns([1, 2])
        c_l1.markdown(f"**Кубик {dice_count} (Auto)**")
        c_l1.metric("Остаток (Avg)", f"{remaining:.1f}")

        if remaining < 1.0:
            c_l2.error("Бюджет исчерпан!")
        else:
            l_min, l_max = _calculate_min_max(remaining, variance)
            c_l2.markdown(f"### 🎲 {l_min} ~ {l_max}")