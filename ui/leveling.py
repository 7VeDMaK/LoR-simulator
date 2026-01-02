import streamlit as st
import math
from core.unit.unit_library import UnitLibrary
from core.ranks import get_rank_info


def calculate_rank_penalty_values(player_lvl: int, target_lvl: int):
    """
    Возвращает (n, rank_penalty, extra_penalty).
    n - разница тиров.
    rank_penalty - n(n+1)/2.
    extra_penalty - n, если n <= 3, иначе 0.
    """
    p_tier, _ = get_rank_info(player_lvl)
    e_tier, _ = get_rank_info(target_lvl)

    n = max(0, e_tier - p_tier)

    # 1. Формула ранга: n(n+1)/2
    r_pen = (n * (n + 1)) // 2

    # 2. Доп. правило: "Влияет при первых трёх пропущенных звеньях"
    # Интерпретация из примера: при n=2 штраф был 2. При n=9 штраф был 0.
    # Значит, если n <= 3, добавляем n.
    e_pen = n if 0 < n <= 3 else 0

    return n, r_pen, e_pen


def get_target_xp_value(player_lvl: int, target_lvl: int) -> int:
    """
    Считает XP, которое дает цель определенного уровня для игрока.
    Формула: 2^(Effective_Level)
    Effective_Level = Target - RankPen - ExtraPen
    """
    _, r_pen, e_pen = calculate_rank_penalty_values(player_lvl, target_lvl)

    # Эффективный уровень награды
    # Мы не вычитаем уровень игрока здесь, так как считаем "Стоимость" цели в абсолютных единицах XP.
    # В примере: (60 + 1 - 45 - Pen) -> Это прирост.
    # Прирост + Текущий = Новый.
    # XP(Target) = 2^(Target - Pen).

    eff_lvl = max(0, target_lvl - r_pen - e_pen) - 1
    return 2 ** eff_lvl


def render_leveling_page():
    st.title("📈 Калькулятор Уровня")

    if 'roster' not in st.session_state or not st.session_state['roster']:
        st.warning("Ростер пуст.")
        return

    # --- 1. ВЫБОР ПЕРСОНАЖА ---
    roster_names = list(st.session_state['roster'].keys())
    def_idx = 0
    if 'last_lvl_unit' in st.session_state and st.session_state['last_lvl_unit'] in roster_names:
        def_idx = roster_names.index(st.session_state['last_lvl_unit'])

    selected_name = st.selectbox("Персонаж", roster_names, index=def_idx, key="lvl_char_sel")
    st.session_state['last_lvl_unit'] = selected_name
    unit = st.session_state['roster'][selected_name]

    cur_tier, cur_rank_name = get_rank_info(unit.level)

    # === ИНИЦИАЛИЗАЦИЯ XP ДЛЯ СТАРЫХ ПЕРСОНАЖЕЙ ===
    # Если total_xp = 0, но уровень > 0, значит это старый сейв.
    # Восстанавливаем XP по минимуму текущего уровня.
    if unit.total_xp == 0 and unit.level > 0:
        unit.total_xp = 2 ** (unit.level - 1) if unit.level > 1 else 1  # Lvl 1 = 1 XP (2^0)

    current_xp = unit.total_xp

    # Визуализация текущего статуса
    with st.container(border=True):
        c_info1, c_info2, c_info3 = st.columns(3)
        c_info1.metric("Уровень", unit.level)
        c_info2.metric("Ранг", cur_rank_name)
        c_info3.metric("Всего XP", f"{current_xp:,}")

    st.divider()

    # === 2. НАСТРОЙКА ЗАДАНИЯ И ВРАГОВ ===

    # Инициализация переменных сессии для сохранения значений
    if "lvl_mission_base" not in st.session_state: st.session_state["lvl_mission_base"] = unit.level
    if "lvl_mission_bonus" not in st.session_state: st.session_state["lvl_mission_bonus"] = 0
    if "lvl_enemies" not in st.session_state:
        st.session_state["lvl_enemies"] = [{"count": 0, "level": unit.level}]  # По умолчанию 0, чтобы не мешало

    col_mission, col_grind = st.columns([1, 1], gap="medium")

    # --- СЕКЦИЯ: ЗАДАНИЕ ---
    with col_mission:
        st.subheader("📜 Задание / Миссия")
        st.caption("Опыт за выполнение условий задания.")

        m_base = st.number_input("Уровень Опасности", 0, 120, key="lvl_mission_base")
        m_bonus = st.number_input("Бонус (Условия)", 0, 20, key="lvl_mission_bonus",
                                  help="Прибавляется к уровню задания")

        # Расчет штрафов для миссии
        m_total_lvl = m_base + m_bonus
        if m_total_lvl > 0:
            mn, mr_pen, me_pen = calculate_rank_penalty_values(unit.level, m_total_lvl)
            m_eff = max(0, m_total_lvl - mr_pen - me_pen)

            st.markdown(f"""
            **Расчет:**
            * Уровень: {m_total_lvl}
            * Разрыв рангов (n): **{mn}**
            * Штраф ранга: **-{mr_pen}**
            * Доп. штраф: **-{me_pen}**
            * **Эфф. Уровень:** {m_eff}
            """)
        else:
            st.caption("Задание не учитывается (0)")

    # --- СЕКЦИЯ: ВРАГИ ---
    with col_grind:
        st.subheader("💀 Устраненные Враги")
        st.caption("Список побежденных в бою.")

        edited_enemies = st.data_editor(
            st.session_state["lvl_enemies"],
            num_rows="dynamic",
            column_config={
                "count": st.column_config.NumberColumn("Кол-во", min_value=0, step=1),
                "level": st.column_config.NumberColumn("Уровень", min_value=0, max_value=120)
            },
            width='stretch',
            key="lvl_editor"
        )

    st.divider()

    # === 3. ИТОГОВЫЙ РАСЧЕТ ===

    # 1. XP от Миссии
    mission_xp = 0
    if m_base > 0:
        mission_xp = get_target_xp_value(unit.level, m_total_lvl)

    # 2. XP от Врагов
    enemies_xp = 0
    enemy_details = []

    for row in edited_enemies:
        cnt = row.get("count", 0)
        lvl = row.get("level", 0)

        if cnt > 0:
            val = get_target_xp_value(unit.level, lvl)
            total_row = val * cnt
            enemies_xp += total_row

            # Для лога
            _, rp, ep = calculate_rank_penalty_values(unit.level, lvl)
            eff = max(0, lvl - rp - ep)
            enemy_details.append(f"{cnt}x Lvl {lvl} (Eff {eff}) = {total_row:,} XP")

    # 3. Сумма
    total_gained_xp = mission_xp + enemies_xp
    final_xp_pool = current_xp + total_gained_xp

    # 4. Конвертация обратно в уровень
    # Level = log2(XP) + 1
    if final_xp_pool >= 1:
        new_level = int(math.log2(final_xp_pool)) + 1
    else:
        new_level = 0

    # Нельзя понизить уровень
    new_level = max(unit.level, new_level)
    diff = new_level - unit.level

    # === ВИЗУАЛИЗАЦИЯ ИТОГА ===
    c_res_l, c_res_r = st.columns([2, 1])

    total_gained = mission_xp + enemies_xp
    final_pool = current_xp + total_gained

    with c_res_l:
        st.write("### Итог:")
        if diff > 0:
            st.markdown(f"## :green[{unit.level} ➜ {new_level} (+{diff})]")
        else:
            st.markdown(f"## :grey[{unit.level} (Нет изменений)]")

        # --- ПОЛОСКА ОПЫТА (НОВОЕ) ---
        if new_level > 0:
            # 1. Порог начала текущего (нового) уровня: 2^(Level-1)
            xp_cur_start = 2 ** (new_level - 1)

            # 2. Порог следующего уровня: 2^(Level)
            xp_next_start = 2 ** new_level

            # 3. Прогресс внутри уровня
            xp_in_level = final_pool - xp_cur_start
            xp_span = xp_next_start - xp_cur_start

            ratio = 0.0
            if xp_span > 0:
                ratio = xp_in_level / xp_span

            # Clamp 0..1
            ratio = max(0.0, min(1.0, ratio))

            st.progress(ratio,
                        text=f"До уровня {new_level + 1}: {int(ratio * 100)}% ({int(final_pool):,} / {int(xp_next_start):,} XP)")

        with st.expander("Подробности расчета"):
            st.write(f"Start XP: {current_xp:,}")
            if mission_xp > 0:
                st.write(f"+ Mission: {mission_xp:,}")
            if enemy_details:
                st.write("+ Enemies:")
                for d in enemy_details:
                    st.caption(d)
            st.write(f"= Final Pool: {final_xp_pool:,}")

    with c_res_r:
        st.write("")
        st.write("")
        if st.button("🚀 ПРИМЕНИТЬ УРОВЕНЬ", type="primary", width='stretch'):
            unit.level = new_level
            unit.total_xp = int(final_pool)  # Сохраняем точный опыт!
            unit.recalculate_stats()
            UnitLibrary.save_unit(unit)
            st.balloons()
            st.rerun()