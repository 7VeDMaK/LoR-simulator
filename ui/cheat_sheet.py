# ui/cheat_sheet.py
import streamlit as st
import pandas as pd

from core.game_templates import CHARACTER_TEMPLATES


def render_cheat_sheet_page():
    st.title("📚 Справочник характеристик")
    st.caption("Референсные значения и экономика Города.")

    tab_speed, tab_hp, tab_power, tab_eco, tab_mech, tab_balance = st.tabs([
        "💨 Скорость", "❤️ Здоровье", "⚔️ Сила", "💰 Экономика", "💀 Механики", "⚖️ Конструктор"
    ])
    base_rolls_data = []

    # Base roll logic (copied from core/ranks.py logic for display)
    def get_roll(lvl):
        if lvl >= 90: return 30, 40
        if lvl >= 80: return 25, 32
        if lvl >= 65: return 21, 27
        if lvl >= 50: return 17, 22
        if lvl >= 43: return 14, 19
        if lvl >= 36: return 11, 16
        if lvl >= 30: return 9, 13
        if lvl >= 24: return 7, 10
        if lvl >= 18: return 5, 7
        if lvl >= 12: return 4, 6
        if lvl >= 6:  return 3, 5
        return 1, 3

    for tmpl in CHARACTER_TEMPLATES:
        rmin, rmax = get_roll(tmpl['level'])
        base_rolls_data.append((tmpl['level'], tmpl['rank_name'], rmin, rmax))

    base_rolls_data.sort(key=lambda x: x[0])
    # === ТАБ 1: СКОРОСТЬ ===
    with tab_speed:
        st.header("Скорость и Кубики Скорости")
        st.markdown("*(При условии прокачки Ловкости и Скорости)*")

        data_speed = [
            {"Lvl": "90+", "Rank": "Несовершенство (Impurity)", "Dice Slots": "6x [30-40]", "Agility": "40 (+35)",
             "Speed": "40 (+30)"},
            {"Lvl": "80", "Rank": "Цвет (Звезда Усложнен)", "Dice Slots": "6x [24-27]", "Agility": "30 (+25)",
             "Speed": "30 (+20)"},
            {"Lvl": "65", "Rank": "Rank 1 (Звезда)", "Dice Slots": "5x [21-24], 1x [19-22]", "Agility": "25 (+20)",
             "Speed": "30 (+16)"},
            {"Lvl": "50", "Rank": "Rank 2 (Кошмар Усложнен)", "Dice Slots": "4x [19-22], 1x [14-17]",
             "Agility": "20 (+20)", "Speed": "25 (+16)"},
            {"Lvl": "43", "Rank": "Rank 3 (Кошмар)", "Dice Slots": "3x [16-19], 1x [13-16]", "Agility": "17 (+15)",
             "Speed": "22 (+12)"},
            {"Lvl": "36", "Rank": "Rank 4 (Чума Усложнен)", "Dice Slots": "3x [15-18], 1x [10-13]", "Agility": "14 (+15)",
             "Speed": "19 (+12)"},
            {"Lvl": "30", "Rank": "Rank 5 (Чума)", "Dice Slots": "2x [13-16], 1x [10-13]", "Agility": "12 (+10)",
             "Speed": "16 (+8)"},
            {"Lvl": "24", "Rank": "Rank 6 (Легенда Усложнен)", "Dice Slots": "2x [12-15], 1x [7-10]",
             "Agility": "10 (+10)", "Speed": "13 (+8)"},
            {"Lvl": "18", "Rank": "Rank 7 (Легенда)", "Dice Slots": "1x [10-13], 1x [7-10]", "Agility": "8 (+5)",
             "Speed": "10 (+4)"},
            {"Lvl": "12", "Rank": "Rank 8 (Миф)", "Dice Slots": "1x [9-12], 1x [4-7]", "Agility": "6 (+5)",
             "Speed": "7 (+4)"},
            {"Lvl": "6", "Rank": "Rank 9 (Слухи Усложнен)", "Dice Slots": "1x [4-7]", "Agility": "4 (+0)",
             "Speed": "4 (+0)"},
            {"Lvl": "0", "Rank": "Крысы (Слухи)", "Dice Slots": "1x [1-3]", "Agility": "1 (+0)", "Speed": "1 (+0)"},
        ]
        df_speed = pd.DataFrame(data_speed)
        st.table(df_speed)

    # === ТАБ 2: ЗДОРОВЬЕ ===
    with tab_hp:
        st.header("Расчет Здоровья (HP)")
        st.markdown("*(При условии прокачки Стойкости)*")

        hp_rows = []
        for tmpl in reversed(CHARACTER_TEMPLATES):
            hp_rows.append({
                "Lvl": str(tmpl['level']),  # FIX: Explicit string
                "Rank": tmpl['rank_name'],
                "Endurance": tmpl['endurance'],
                "Total HP (Approx)": tmpl['hp_approx']
            })

        st.dataframe(pd.DataFrame(hp_rows), width='stretch', hide_index=True)
    # === ТАБ 3: РОЛЛЫ ===
    with tab_power:
        st.header("Чистые средние роллы карты")
        st.caption("Детальная разбивка источников силы.")

        # Расширенная таблица с колонками для каждого бонуса
        data_power = [
            {
                "Lvl": 80, "Rank": "Color", "Base Roll": "25-32",
                "Str": "+5", "W.Type": "+5", "Talents": "+2", "W.Rank": "+5", "Imp": "+10",
                "Total Avg": "56 (29+27)"
            },
            {
                "Lvl": 65, "Rank": "Rank 1", "Base Roll": "21-27",
                "Str": "+5", "W.Type": "+5", "Talents": "+2", "W.Rank": "+5", "Imp": "+9",
                "Total Avg": "50 (24+26)"
            },
            {
                "Lvl": 50, "Rank": "Rank 2", "Base Roll": "17-22",
                "Str": "+4", "W.Type": "+5", "Talents": "+2", "W.Rank": "+4", "Imp": "+8",
                "Total Avg": "42 (19+23)"
            },
            {
                "Lvl": 43, "Rank": "Rank 3", "Base Roll": "14-19",
                "Str": "+4", "W.Type": "+4", "Talents": "+2", "W.Rank": "+4", "Imp": "+7",
                "Total Avg": "38 (17+21)"
            },
            {
                "Lvl": 36, "Rank": "Rank 4", "Base Roll": "11-16",
                "Str": "+3", "W.Type": "+4", "Talents": "+2", "W.Rank": "+3", "Imp": "+6",
                "Total Avg": "31 (13+18)"
            },
            {
                "Lvl": 30, "Rank": "Rank 5", "Base Roll": "9-13",
                "Str": "+2", "W.Type": "+3", "Talents": "+2", "W.Rank": "+3", "Imp": "+5",
                "Total Avg": "26 (11+15)"
            },
            {
                "Lvl": 24, "Rank": "Rank 6", "Base Roll": "7-10",
                "Str": "+2", "W.Type": "+3", "Talents": "0", "W.Rank": "+3", "Imp": "+4",
                "Total Avg": "20 (8+12)"
            },
            {
                "Lvl": 18, "Rank": "Rank 7", "Base Roll": "5-7",
                "Str": "+2", "W.Type": "+2", "Talents": "0", "W.Rank": "+2", "Imp": "+3",
                "Total Avg": "15 (6+9)"
            },
            {
                "Lvl": 12, "Rank": "Rank 8", "Base Roll": "4-6",
                "Str": "+1", "W.Type": "+1", "Talents": "0", "W.Rank": "+1", "Imp": "+2",
                "Total Avg": "10 (5+5)"
            },
            {
                "Lvl": 6, "Rank": "Rank 9", "Base Roll": "3-5",
                "Str": "1/0", "W.Type": "1/0", "Talents": "0", "W.Rank": "0/1", "Imp": "+1",
                "Total Avg": "9 / 4"
            },
        ]

        df_power = pd.DataFrame(data_power)
        # Настройка отображения колонок
        st.table(df_power)

        st.info(
            "**Легенда:** Str = Сила | W.Type = Тип оружия | Talents = Бонус веток | W.Rank = Ранг оружия | Imp = Импланты")

    # === ТАБ 4: ЭКОНОМИКА ===
    with tab_eco:
        st.header("💰 Экономика Города")

        with st.container(border=True):
            st.subheader("Доходы")
            st.metric("Средняя ЗП Перьев (в месяц)", "40,000,000 Ан", help="Чуть выше средней зарплаты в Гнезде")

        st.divider()

        st.subheader("📋 Прайс-лист на Ликвидацию (Ориентировочно)")
        st.caption("Цены для легальных контрактов. Нелегальные заказы стоят дороже. Цены зависят от сложности и целей.")

        eco_data = [
            {"Цель": "10 Крыс", "Стоимость (Ан)": "10,000"},
            {"Цель": "Жилец Подворотен / Преступник (< 9 ранга)", "Стоимость (Ан)": "10,000 - 100,000"},
            {"Цель": "Корректировщик 9 ранга", "Стоимость (Ан)": "100,000 - 500,000"},
            {"Цель": "Корректировщик 7-8 ранга", "Стоимость (Ан)": "500,000 - 3,000,000"},
            {"Цель": "Корректировщик 5-6 ранга", "Стоимость (Ан)": "3,000,000 - 10,000,000"},
            {"Цель": "Высокие ранги (Звезда / Цвет)", "Стоимость (Ан)": "100,000,000 - 1,000,000,000+"},
        ]

        df_eco = pd.DataFrame(eco_data)
        st.table(df_eco)

        st.info(
            "💡 Примечание: Для рангов выше 5-го (Городская Чума) цена растет экспоненциально (примерно х10 за ранг), но больше зависит от конкретных условий и целей, чем от фиксированного прайса.")
    # === ТАБ 5: МЕХАНИКИ ===
    with tab_mech:
        st.header("💀 Особые Состояния")
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.subheader("💔 Бессознательное состояние (HP < 0)")
                st.markdown("...")  # (Текст механики, который мы добавляли ранее)
        with c2:
            with st.container(border=True):
                st.subheader("🤯 Паника / Искажение (SP < 0)")
                st.markdown("...")  # (Текст механики)
        # === ТАБ 6: БАЛАНС (КОНСТРУКТОР) ===
    with tab_balance:
        st.header("⚖️ Конструктор Баланса Карт")
        st.caption("Калькулятор значений на основе ваших базовых роллов.")

        # --- 1. Таблица базовых бюджетов ---
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

        # --- 2. Калькулятор ---
        # === ТАБ 4: БАЛАНС (КАЛЬКУЛЯТОР) ===
        # === ТАБ 4: БАЛАНС (КАЛЬКУЛЯТОР) ===
        # === ТАБ 4: БАЛАНС (КАЛЬКУЛЯТОР) ===
        with tab_balance:
            st.header("⚖️ Конструктор Баланса Карт")
            st.caption("Калькулятор значений на основе уровня персонажа.")

            with st.expander("ℹ️ Справка: Как работает баланс?"):
                st.markdown("""
                    ### 🎲 Как создать "Хороший Куб"?
                    Система баланса построена на **Бюджете**. Ваш персонаж имеет базовую силу (зависит от уровня), которая умножается на ранг карты.

                    **Чтобы получить сильные значения:**
                    1. **Тип карты**: Карты Mass Attack и Ranged стоят дороже в плане бюджета, но их значения могут быть выше за счет этого.
                    2. **Разброс (Variance)**: Старайтесь держать разброс в "Безопасной зоне" (30-70% от среднего). 
                       - Слишком стабильные кубики (например, 5-5) получают штраф за надежность.
                       - Слишком рандомные (1-20) получают штраф за нестабильность.
                    3. **Условия**: Добавляйте сложные условия (On Hit, High Roll), чтобы получить бонус к силе (+15%). Легкие условия (On Use) снижают силу (-7.5%).
                    4. **Концентрация**: Если вы используете меньше кубиков, чем положено рангу карты (например, 1 куб на карте 3 ранга), вы получаете бонус +20% за каждый сэкономленный слот.

                    ### 📉 Откуда берутся штрафы?
                    * **Эффекты (-10%)**: Наложение статусов (Bleed, Burn, Buffs) снижает прямой урон карты.
                    * **Легкие условия (-7.5%)**: Гарантированные эффекты стоят части силы.
                    * **Разброс**: Отклонение от оптимального диапазона штрафуется на 2% за каждую единицу.
                    """)

            c_set, c_res = st.columns([1, 1])

            # --- Variables init ---
            base_avg = 2.0
            char_level_display = 0
            standard_dice_capacity = 1

            with c_set:
                st.subheader("🛠️ Настройка")

                # 1. Выбор персонажа
                if 'roster' in st.session_state and st.session_state['roster']:
                    roster_names = list(st.session_state['roster'].keys())
                    sel_char = st.selectbox("Персонаж", roster_names, key="bal_char_sel")

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

                # 2. Ранг
                card_rank = st.selectbox("Ранг карты (Tier)", [1, 2, 3, 4, 5], index=0, key="bal_card_rank")
                standard_dice_capacity = card_rank

                # 3. Тип
                type_opts = {
                    "Melee (100%)": 1.0,
                    "Offensive (115%)": 1.15,
                    "Ranged (125%)": 1.25,
                    "Mass Attack (140%)": 1.40,
                    "On Play (50%)": 0.5,
                    "Item (40%)": 0.4
                }
                ctype_label = st.selectbox("Тип карты", list(type_opts.keys()), index=0, key="bal_type")
                type_mult = type_opts[ctype_label]

                dice_count = st.slider("Количество дайсов", 1, 7, 2, key="bal_count")

                st.markdown("**Модификаторы:**")
                effects_count = st.number_input("Кол-во эффектов (-10%)", 0, 100, 0)
                cond_hard = st.number_input("Сложные условия (+15%)", 0, 100, 0)
                cond_easy = st.number_input("Легкие условия (-7.5%)", 0, 100, 0)

                # --- DYNAMIC VARIANCE SLIDER ---
                # Pre-calc budget to determine max variance
                # Using MIN between rank and dice count for budget multiplier!
                rank_budget_mult_est = min(standard_dice_capacity, dice_count)
                est_total_budget = base_avg * rank_budget_mult_est * type_mult

                est_power_mod = 1.0 - (effects_count * 0.10) + ((cond_hard * 0.15) - (cond_easy * 0.075))
                est_budget = est_total_budget * est_power_mod

                est_avg_die = est_budget / max(dice_count, 1)
                if dice_count < standard_dice_capacity:
                    bonus_mult = 1.3 ** abs(standard_dice_capacity - dice_count)
                    est_avg_die *= bonus_mult

                max_var_dynamic = max(0, int((est_avg_die - 1) * 2))
                def_var = min(4, max_var_dynamic)

                variance = st.slider("Разброс (Variance)", 0, max_var_dynamic, def_var,
                                     help=f"Лимит зависит от силы (Avg {est_avg_die:.1f}). Безопасно: 30-70%.")

                # --- BUTTON: FIND BEST VARIANCE ---
                if st.button("🔍 Найти лучший разброс"):
                    best_v = 0
                    best_score = -1.0

                    for v_check in range(max_var_dynamic + 1):
                        var_safe_min_c = est_avg_die * 0.30
                        var_safe_max_c = est_avg_die * 0.70

                        pen = 0.0
                        if v_check < var_safe_min_c:
                            pen = (var_safe_min_c - v_check) * 0.02
                        elif v_check > var_safe_max_c:
                            pen = (v_check - var_safe_max_c) * 0.02

                        factor = max(0.1, 1.0 - pen)
                        score = est_avg_die * factor

                        if score > best_score:
                            best_score = score
                            best_v = v_check

                    st.toast(f"Оптимальный разброс: {best_v}", icon="✨")
                    st.info(f"Рекомендуемый разброс для макс. силы: **{best_v}**")

            with c_res:
                st.subheader("🎯 Результат")

                # 1. Total Budget
                # FIXED: Budget multiplier is min(Rank, Count)
                rank_budget_mult = min(standard_dice_capacity, dice_count)
                total_budget = base_avg * rank_budget_mult * type_mult

                # 2. Power Mods
                eff_pen = effects_count * 0.10
                cond_mod = (cond_hard * 0.15) - (cond_easy * 0.075)
                power_mod = 1.0 - eff_pen + cond_mod

                effective_budget = total_budget * power_mod

                # 3. Split with Concentration Bonus
                avg_per_die = effective_budget / dice_count

                split_bonus_val = 1.0
                split_bonus_applied = False

                if dice_count < standard_dice_capacity:
                    split_bonus_val = 1.3 ** abs(standard_dice_capacity - dice_count)
                    avg_per_die *= split_bonus_val
                    split_bonus_applied = True

                # 4. Variance Adjustment
                var_safe_min = avg_per_die * 0.30
                var_safe_max = avg_per_die * 0.70

                var_penalty = 0.0

                if variance < var_safe_min:
                    diff = var_safe_min - variance
                    var_penalty = diff * 0.02
                elif variance > var_safe_max:
                    diff = variance - var_safe_max
                    var_penalty = diff * 0.02

                var_factor = max(0.1, 1.0 - var_penalty)
                final_avg_die = avg_per_die * var_factor

                # --- HELPER: RANGE CALCULATION ---
                def calculate_min_max_from_avg(avg, var):
                    t_sum = int(round(avg * 2))
                    eff_v = var
                    # Parity check
                    if (t_sum % 2) != (eff_v % 2):
                        if eff_v > 0:
                            eff_v -= 1
                        else:
                            eff_v += 1

                    mn = (t_sum - eff_v) // 2
                    mx = (t_sum + eff_v) // 2

                    if mn < 1:
                        sh = 1 - mn
                        mn += sh
                        mx += sh
                    return mn, mx

                # Main Result
                d_min, d_max = calculate_min_max_from_avg(final_avg_die, variance)

                with st.container(border=True):
                    st.metric("Среднее (1 кубик)", f"{final_avg_die:.3f}")
                    st.markdown(f"### 🎲 {d_min} ~ {d_max}")

                    st.caption(f"Rank Cap: {standard_dice_capacity} dice | Split: {dice_count}")

                st.info(f"""
                        **Логика:**
                        * **Base**: {base_avg} (Lvl {char_level_display})
                        * **Rank Budget**: x{rank_budget_mult} (min(Tier, Count))
                        * **Mods**: {int(power_mod * 100)}%
                        * **Split Mod**: x{split_bonus_val:.2f} {'(+Bonus)' if split_bonus_applied else ''}
                        * **Safe Var**: {var_safe_min:.1f} - {var_safe_max:.1f}
                        * **Var Penalty**: -{int(var_penalty * 100)}%
                    """)

                # --- 5. DIFFERENT DICE DISTRIBUTOR (NEW) ---
                if dice_count > 1:
                    st.divider()
                    with st.expander("🎛️ Настроить разные кубики (Распределение)"):
                        total_power_budget = final_avg_die * dice_count
                        st.caption(f"Общий бюджет (Avg): **{total_power_budget:.1f}**")

                        remaining = total_power_budget

                        # Manual Dice (All except last)
                        for i in range(dice_count - 1):
                            c1, c2, c3 = st.columns([1, 1, 2])
                            with c1:
                                # Default values to meaningful starting points
                                def_min = int(final_avg_die - 2) if (final_avg_die - 2) > 1 else 1
                                val_min = st.number_input(f"D{i + 1} Min", 1, 200, def_min, key=f"md_min_{i}")
                            with c2:
                                def_max = int(final_avg_die + 2)
                                val_max = st.number_input(f"D{i + 1} Max", 1, 200, def_max, key=f"md_max_{i}")
                            with c3:
                                val_avg = (val_min + val_max) / 2
                                st.metric(f"D{i + 1} Avg", f"{val_avg:.1f}")
                                remaining -= val_avg

                        # Last Die (Auto)
                        st.divider()
                        c_last_1, c_last_2 = st.columns([1, 2])
                        with c_last_1:
                            st.markdown(f"**Кубик {dice_count} (Auto)**")
                            st.metric("Остаток (Avg)", f"{remaining:.1f}")

                        with c_last_2:
                            if remaining < 1.0:
                                st.error("Бюджет исчерпан!")
                            else:
                                # Calculate ranges based on global variance
                                l_min, l_max = calculate_min_max_from_avg(remaining, variance)
                                st.markdown(f"### 🎲 {l_min} ~ {l_max}")
                                st.caption(f"Based on Var {variance}")