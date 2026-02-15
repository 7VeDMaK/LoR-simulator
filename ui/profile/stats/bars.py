import random

import streamlit as st

from core.unit.unit_library import UnitLibrary


def render_status_bars(unit, u_key):
    """Отрисовка полосок HP/SP и очков прокачки."""

    # 1. HP/SP/Stagger Metrics
    with st.container(border=True):
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("HP (Здоровье)", f"{unit.current_hp} / {unit.max_hp}")
        sc2.metric("SP (Рассудок)", f"{unit.current_sp} / {unit.max_sp}")
        sc3.metric("Stagger (Выдержка)", f"{unit.current_stagger} / {unit.max_stagger}")

        # Manual Edits
        c_edit1, c_edit2, c_edit3 = st.columns(3)
        unit.current_hp = c_edit1.number_input("Set HP", -999999, 999999, unit.current_hp, label_visibility="collapsed",
                                               key=f"set_hp_{u_key}")
        unit.current_sp = c_edit2.number_input("Set SP", -999999, 999999, unit.current_sp, label_visibility="collapsed",
                                               key=f"set_sp_{u_key}")
        unit.current_stagger = c_edit3.number_input("Set Stg", -999999, 999999, unit.current_stagger,
                                                    label_visibility="collapsed", key=f"set_stg_{u_key}")

    # 2. Points & Level Rolls
    with st.container(border=True):
        lvl_growth = max(0, unit.level - 1)
        base_attr = 25 + lvl_growth
        base_skill = 38 + (lvl_growth * 2)

        if "witness_gro_goroth" in unit.passives:
            base_skill = 38 + (lvl_growth * 1)
            st.caption("👁️ Гро-Горот: Штраф к очкам навыков (1 за уровень)")

        bonus_attr = 0
        bonus_skill = 0
        if "accelerated_learning" in unit.passives:
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

        help_a = f"Всего очков: {total_attr}"
        if bonus_attr > 0: help_a += f" (Бонус пассивки: +{bonus_attr})"

        c_pts1.metric("Характеристики", f"{total_attr - spent_a}", help=help_a)
        c_pts2.metric("Навыки", f"{total_skill - spent_s}", help=f"Всего очков: {total_skill} (+{bonus_skill})")
        c_pts3.metric("Таланты (Slots)", f"{total_tal - spent_t}", help=f"Всего слотов: {total_tal}")

        # Проверяем наличие пассивки "Суровые тренировки"
        has_severe_training = "severe_training" in unit.passives
        
        # Проверка непрокинутых уровней
        missing = [i for i in range(3, unit.level + 1, 3) if str(i) not in unit.level_rolls]
        if missing:
            if has_severe_training:
                st.info(f"🏋️ Суровые тренировки: Фиксированный прирост +10 HP / +5 SP за уровень")
            st.warning(f"⚠️ Не прокинуты кубики HP/SP для уровней: {', '.join(map(str, missing))}")
            btn_label = "📊 Установить фиксированные значения" if has_severe_training else "🎲 Бросить кубики для всех уровней"
            if st.button(btn_label, key=f"roll_btn_{u_key}", type="primary"):
                for l in missing:
                    if has_severe_training:
                        # Фиксированные значения для пассивки: +5+5=10 HP, +5+0=5 SP
                        unit.level_rolls[str(l)] = {"hp": 5, "sp": 0}
                    else:
                        # Обычный случайный бросок
                        unit.level_rolls[str(l)] = {"hp": random.randint(1, 5), "sp": random.randint(1, 5)}
                UnitLibrary.save_unit(unit)
                st.rerun()

        with st.expander("🎲 История Бросков HP/SP"):
            if unit.level_rolls:
                total_hp_roll = sum(v.get("hp", 0) for v in unit.level_rolls.values())
                total_sp_roll = sum(v.get("sp", 0) for v in unit.level_rolls.values())
                st.info(f"📊 **Итого за уровни:** +{total_hp_roll} HP / +{total_sp_roll} SP")
                
                # Кнопки управления бросками
                col1, col2 = st.columns(2)
                with col1:
                    reroll_label = "📊 Сбросить на фиксированные" if has_severe_training else "🔄 Перекинуть все кубики"
                    if st.button(reroll_label, key=f"reroll_all_{u_key}"):
                        for lvl in range(3, unit.level + 1, 3):
                            if has_severe_training:
                                unit.level_rolls[str(lvl)] = {"hp": 5, "sp": 0}
                            else:
                                unit.level_rolls[str(lvl)] = {"hp": random.randint(1, 5), "sp": random.randint(1, 5)}
                        UnitLibrary.save_unit(unit)
                        st.rerun()
                with col2:
                    if st.button("🗑️ Очистить все броски", key=f"clear_all_{u_key}"):
                        unit.level_rolls = {}
                        UnitLibrary.save_unit(unit)
                        st.rerun()
                
                st.divider()
                for lvl in sorted(map(int, unit.level_rolls.keys())):
                    r = unit.level_rolls[str(lvl)]
                    st.caption(f"**Lvl {lvl}**: +{5 + r['hp']} HP, +{5 + r['sp']} SP (Roll: {r['hp']}/{r['sp']})")
            else:
                st.caption("Нет записей о бросках.")