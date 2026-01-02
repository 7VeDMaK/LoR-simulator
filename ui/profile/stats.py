import streamlit as st
import random
from core.unit.unit_library import UnitLibrary

ATTR_LABELS = {
    "strength": "Сила", "endurance": "Стойкость", "agility": "Ловкость",
    "wisdom": "Мудрость", "psych": "Психика"
}

# Luck is removed from the general list as it's in a separate block
SKILL_LABELS = {
    "strike_power": "Сила удара", "medicine": "Медицина", "willpower": "Сила воли",
    "acrobatics": "Акробатика", "shields": "Щиты",
    "tough_skin": "Крепкая кожа", "speed": "Скорость",
    "light_weapon": "Лёгкое оружие", "medium_weapon": "Среднее оружие",
    "heavy_weapon": "Тяжёлое оружие", "firearms": "Огнестрел",
    "eloquence": "Красноречие", "forging": "Ковка",
    "engineering": "Инженерия", "programming": "Программирование"
}


def get_mod_value(unit, key, default=0):
    """
    Безопасно извлекает значение из modifiers.
    Если значение - словарь (новая система), возвращает 'flat' компонент.
    Если значение - число (старая система или совместимость), возвращает его.
    """
    val = unit.modifiers.get(key, default)
    if isinstance(val, dict):
        return val.get("flat", default)
    return val


def render_stats(unit, u_key):
    # === АУГМЕНТАЦИИ (РУЧНЫЕ БОНУСЫ) ===
    with st.expander("💉 Аугментации и Модификаторы (Ручные)", expanded=False):
        c_aug1, c_aug2, c_aug3 = st.columns(3)

        with c_aug1:
            st.caption("HP Modifiers")
            # Flat
            new_hp_flat = st.number_input("HP Flat (+)", -999, 999, unit.implants_hp_flat, key=f"imp_hp_f_{u_key}")
            if new_hp_flat != unit.implants_hp_flat:
                unit.implants_hp_flat = new_hp_flat
                unit.recalculate_stats()
                st.rerun()

            # Percent
            new_hp_pct = st.number_input("HP Pct (%)", -100, 500, unit.implants_hp_pct, key=f"imp_hp_p_{u_key}")
            if new_hp_pct != unit.implants_hp_pct:
                unit.implants_hp_pct = new_hp_pct
                unit.recalculate_stats()
                st.rerun()

        with c_aug2:
            st.caption("SP Modifiers")
            # Flat
            new_sp_flat = st.number_input("SP Flat (+)", -999, 999, unit.implants_sp_flat, key=f"imp_sp_f_{u_key}")
            if new_sp_flat != unit.implants_sp_flat:
                unit.implants_sp_flat = new_sp_flat
                unit.recalculate_stats()
                st.rerun()

            # Percent
            new_sp_pct = st.number_input("SP Pct (%)", -100, 500, unit.implants_sp_pct, key=f"imp_sp_p_{u_key}")
            if new_sp_pct != unit.implants_sp_pct:
                unit.implants_sp_pct = new_sp_pct
                unit.recalculate_stats()
                st.rerun()

        with c_aug3:
            st.caption("Stagger Modifiers")
            # Flat
            new_stg_flat = st.number_input("Stg Flat (+)", -999, 999, unit.implants_stagger_flat,
                                           key=f"imp_stg_f_{u_key}")
            if new_stg_flat != unit.implants_stagger_flat:
                unit.implants_stagger_flat = new_stg_flat
                unit.recalculate_stats()
                st.rerun()

            # Percent
            new_stg_pct = st.number_input("Stg Pct (%)", -100, 500, unit.implants_stagger_pct, key=f"imp_stg_p_{u_key}")
            if new_stg_pct != unit.implants_stagger_pct:
                unit.implants_stagger_pct = new_stg_pct
                unit.recalculate_stats()
                st.rerun()
    # 2. HP/SP Bars
    with st.container(border=True):
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("HP (Здоровье)", f"{unit.current_hp} / {unit.max_hp}")
        sc2.metric("SP (Рассудок)", f"{unit.current_sp} / {unit.max_sp}")
        sc3.metric("Stagger (Выдержка)", f"{unit.current_stagger} / {unit.max_stagger}")

        # Inputs for manual edit
        c_edit1, c_edit2, c_edit3 = st.columns(3)
        unit.current_hp = c_edit1.number_input("Set HP", -999999, 999999, unit.current_hp, label_visibility="collapsed",
                                               key=f"set_hp_{u_key}")
        unit.current_sp = c_edit2.number_input("Set SP", -999999, 999999, unit.current_sp, label_visibility="collapsed",
                                               key=f"set_sp_{u_key}")
        unit.current_stagger = c_edit3.number_input("Set Stg", -999999, 999999, unit.current_stagger,
                                                    label_visibility="collapsed", key=f"set_stg_{u_key}")

    # === 3. POINTS AND LEVEL ROLLS ===
    with st.container(border=True):
        lvl_growth = max(0, unit.level - 1)

        # Base points
        base_attr = 25 + lvl_growth
        base_skill = 38 + (lvl_growth * 2)

        if "witness_gro_goroth" in unit.passives:
            # Passive changes formula: 1 skill point instead of 2
            base_skill = 38 + (lvl_growth * 1)
            st.caption("👁️ Гро-Горот: Штраф к очкам навыков (1 за уровень)")
        # Extra points from Lima's passive
        bonus_attr = 0
        bonus_skill = 0

        if "accelerated_learning" in unit.passives:
            # Every 3 levels: +1 stat, +2 skill
            cycles = unit.level // 3
            bonus_attr = cycles * 1
            bonus_skill = cycles * 2

        total_attr = base_attr + bonus_attr
        total_skill = base_skill + bonus_skill
        bonus_talents = int(unit.modifiers["talent_slots"]["flat"])
        total_tal = (unit.level // 3) + bonus_talents

        spent_a = sum(unit.attributes.values())
        spent_s = sum(unit.skills.values())
        spent_t = len(unit.talents)

        st.caption("Свободные очки (Доступно - Потрачено)")
        c_pts1, c_pts2, c_pts3 = st.columns(3)

        val_a = total_attr - spent_a
        val_s = total_skill - spent_s
        val_t = total_tal - spent_t

        # If there is a bonus, show it in tooltip
        help_a = f"Всего очков: {total_attr}"
        if bonus_attr > 0: help_a += f" (Бонус пассивки: +{bonus_attr})"

        c_pts1.metric("Характеристики", f"{val_a}", help=help_a)
        c_pts2.metric("Навыки", f"{val_s}", help=f"Всего очков: {total_skill} (+{bonus_skill})")
        c_pts3.metric("Таланты (Slots)", f"{val_t}", help=f"Всего слотов: {total_tal}")

        with st.expander("🎲 История Бросков HP/SP"):
            missing = [i for i in range(3, unit.level + 1, 3) if str(i) not in unit.level_rolls]
            if missing:
                if st.button("Бросить кубики", key=f"roll_btn_{u_key}"):
                    for l in missing:
                        unit.level_rolls[str(l)] = {"hp": random.randint(1, 5), "sp": random.randint(1, 5)}
                    UnitLibrary.save_unit(unit)
                    st.rerun()

            if unit.level_rolls:
                # === [NEW] TOTAL CALCULATION ===
                total_hp_roll = sum(v.get("hp", 0) for v in unit.level_rolls.values())
                total_sp_roll = sum(v.get("sp", 0) for v in unit.level_rolls.values())

                # Pretty output of total
                st.info(f"📊 **Итого за уровни:** +{total_hp_roll} HP / +{total_sp_roll} SP")

                st.divider()

                # Output list (as before)
                for lvl in sorted(map(int, unit.level_rolls.keys())):
                    r = unit.level_rolls[str(lvl)]
                    # Base 5 is already accounted for in engine formula, here showing clean roll + level constant
                    # Typically engine calculates: (5 + roll).
                    st.caption(f"**Lvl {lvl}**: +{5 + r['hp']} HP, +{5 + r['sp']} SP (Roll: {r['hp']}/{r['sp']})")
            else:
                st.caption("Нет записей о бросках.")

    # 4. Attributes (5 columns)
    st.subheader("Характеристики")
    acols = st.columns(5)
    attr_keys = ["strength", "endurance", "agility", "wisdom", "psych"]

    for i, k in enumerate(attr_keys):
        base_val = unit.attributes.get(k, 0)  # Using get just in case

        # FIX: Убрана приставка total_, т.к. в formulas.py ключи записываются как "strength", "agility" и т.д.
        total_val = get_mod_value(unit, k, base_val)

        with acols[i]:
            st.caption(ATTR_LABELS[k])
            c_in, c_val = st.columns([1.5, 1])
            with c_in:
                # IMPORTANT: key includes character name to avoid collisions
                new_base = st.number_input("Base", 0, 999, base_val, key=f"attr_{k}_{u_key}",
                                           label_visibility="collapsed")

                # === FIX: Instant Attributes Update ===
                if new_base != base_val:
                    unit.attributes[k] = new_base
                    unit.recalculate_stats()
                    st.rerun()

            with c_val:
                st.write("")
                if total_val > new_base:
                    st.markdown(f":green[**{total_val}**]")
                elif total_val < new_base:
                    st.markdown(f":red[**{total_val}**]")
                else:
                    st.markdown(f"**{total_val}**")

    # 5. LUCK
    st.divider()
    st.subheader("🍀 Удача")
    l_col1, l_col2, _ = st.columns([1, 1, 2])

    with l_col1:
        st.caption("Стат (Навык)")
        base_luck = unit.skills.get("luck", 0)

        # FIX: Убрана приставка total_, ключ теперь просто "luck"
        total_luck = get_mod_value(unit, "luck", base_luck)

        lc_in, lc_val = st.columns([1.5, 1])
        with lc_in:
            new_luck_skill = st.number_input("Luck Skill", 0, 999, base_luck, label_visibility="collapsed",
                                             key=f"luck_sk_{u_key}")

            # === FIX: Instant Luck (Skill) Update ===
            if new_luck_skill != base_luck:
                unit.skills["luck"] = new_luck_skill
                unit.recalculate_stats()
                st.rerun()

        with lc_val:
            st.write("")
            if total_luck > new_luck_skill:
                st.markdown(f":green[**{total_luck}**]")
            elif total_luck < new_luck_skill:
                st.markdown(f":red[**{total_luck}**]")
            else:
                st.markdown(f"**{total_luck}**")

    with l_col2:
        st.caption("Текущая (Points)")
        cur_luck = unit.resources.get("luck", 0)
        new_cur_luck = st.number_input("Current Luck", -999, 999, cur_luck, label_visibility="collapsed",
                                       key=f"luck_res_{u_key}")
        # === FIX: Instant Luck (Resource) Update ===
        if new_cur_luck != cur_luck:
            unit.resources["luck"] = new_cur_luck
            st.rerun()

    # 6. Other Skills
    st.markdown("")
    with st.expander("📚 Остальные навыки", expanded=True):
        scols = st.columns(3)
        skill_list = list(SKILL_LABELS.keys())

        for i, k in enumerate(skill_list):
            col_idx = i % 3
            with scols[col_idx]:
                base_val = unit.skills.get(k, 0)

                # FIX: Убрана приставка total_, теперь правильно ищет "strike_power", "eloquence" и т.д.
                total_val = get_mod_value(unit, k, base_val)

                st.caption(SKILL_LABELS[k])
                c_in, c_val = st.columns([1.5, 1])
                with c_in:
                    # IMPORTANT: Unique key for each skill of each character
                    new_base = st.number_input("S", 0, 999, base_val, key=f"sk_{k}_{u_key}",
                                               label_visibility="collapsed")

                    # === FIX: Instant Skills Update ===
                    if new_base != base_val:
                        unit.skills[k] = new_base
                        unit.recalculate_stats()
                        st.rerun()

                with c_val:
                    st.write("")
                    if total_val > new_base:
                        st.markdown(f":green[**{total_val}**]")
                    elif total_val < new_base:
                        st.markdown(f":red[**{total_val}**]")
                    else:
                        st.markdown(f"**{total_val}**")