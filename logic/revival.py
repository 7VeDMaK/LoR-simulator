import random
import streamlit as st
from core.logging import logger, LogLevel


def calculate_revival_chance(unit):
    """
    Рассчитывает параметры проверки Возрождения.
    """
    # 1. Сложность (DC) = Overkill / 10
    dc = unit.overkill_damage // 10

    # 2. Бонус Силы Воли = Willpower / 3
    willpower = unit.skills.get("willpower", 0)
    wp_bonus = willpower // 3

    # 3. Штраф за количество ИСПОЛЬЗОВАННЫХ ПОПЫТОК
    # 0 попыток (сейчас 1-я) = 0
    # 1 попытка (сейчас 2-я) = 3
    # 2 попытки (сейчас 3-я) = 7
    penalties = {0: 0, 1: 3, 2: 7}
    penalty = penalties.get(unit.death_count, 999)  # 999 значит лимит исчерпан

    return dc, wp_bonus, penalty


def attempt_revive_action(unit):
    """
    Выполняет механику возрождения.
    """
    # Запоминаем раунд попытки (блокировка до конца хода)
    current_round = st.session_state.get('round_number', 1)
    unit.memory["last_revive_attempt_round"] = current_round

    dc, wp_bonus, penalty = calculate_revival_chance(unit)

    # Бросок 1d6
    roll = random.randint(1, 6)

    # Итоговый результат
    total = roll + wp_bonus - penalty
    success = total >= dc

    # [CHANGE] Списываем попытку СРАЗУ, независимо от исхода
    unit.death_count += 1

    unit.memory["last_revive_log"] = {
        "roll": roll,
        "bonus": wp_bonus,
        "penalty": penalty,
        "total": total,
        "dc": dc,
        "success": success
    }

    if success:
        # УСПЕХ: Возвращаем в строй
        unit.overkill_damage = 0

        # Хил (не срезаем, если уже есть хп)
        heal_hp = int(unit.max_hp * 0.2) or 1
        unit.current_hp = max(unit.current_hp, heal_hp)

        if unit.current_sp <= 0:
            heal_sp = int(unit.max_sp * 0.2) or 1
            unit.current_sp = max(unit.current_sp, heal_sp)

        logger.log(f"👼 {unit.name} REVIVED! (Roll {total} vs DC {dc})", LogLevel.NORMAL, "Revival")
        st.toast(f"{unit.name} использует попытку и встает!", icon="👼")
    else:
        # ПРОВАЛ: Попытка сгорела, юнит лежит
        logger.log(f"💀 {unit.name} Failed Revive (Roll {total} vs DC {dc})", LogLevel.NORMAL, "Revival")
        st.toast(f"Попытка провалена... {unit.name} остается лежать.", icon="💀")


def render_death_overlay(unit, key_prefix):
    """
    Рисует интерфейс смерти вместо обычных слотов.
    """
    st.error(f"💀 **{unit.name} В БЕССОЗНАТЕЛЬНОМ СОСТОЯНИИ**")

    # [CHECK] Проверка лимита попыток (0, 1, 2 - ок; 3 - всё)
    if unit.death_count >= 3:
        st.markdown("⛔ **Все 3 попытки возрождения исчерпаны.**")
        st.caption(f"Персонаж окончательно мертв. Overkill: {unit.overkill_damage}")
        return

    # Проверка на повторную попытку в том же ходу
    last_attempt = unit.memory.get("last_revive_attempt_round", -1)
    current_round = st.session_state.get("round_number", 1)

    if last_attempt == current_round:
        st.warning(f"⏳ Попытка в этом раунде уже использована.")

        last_log = unit.memory.get("last_revive_log")
        if last_log:
            res_text = "УСПЕХ" if last_log["success"] else "ПРОВАЛ"
            st.info(f"Результат: **{res_text}** (Roll {last_log['total']} vs DC {last_log['dc']})")
        return

    # === РАСЧЕТ И ИНТЕРФЕЙС ===
    dc, wp_bonus, penalty = calculate_revival_chance(unit)
    attempt_num = unit.death_count + 1

    # Предпросмотр шансов
    target_roll = dc - wp_bonus + penalty
    winning_faces = 0
    for r in range(1, 7):
        if r >= target_roll: winning_faces += 1
    chance_pct = int((winning_faces / 6) * 100)
    chance_pct = max(0, min(100, chance_pct))

    color = "red"
    if chance_pct > 50: color = "orange"
    if chance_pct > 80: color = "green"

    cols = st.columns([2, 1])
    with cols[0]:
        st.markdown(f"**Попытка возрождения: {attempt_num} из 3**")
        st.caption(f"Overkill: {unit.overkill_damage} | Сложность (DC): **{dc}**")
        st.caption(f"Willpower: +{wp_bonus} | Штраф за смерти: -{penalty}")
        st.markdown(f"Шанс успеха: :{color}[**{chance_pct}%**]")

    with cols[1]:
        # Кнопка красная, если шанс маленький, иначе обычная
        btn_type = "primary" if chance_pct > 30 else "secondary"
        if st.button("🎲 РИСКНУТЬ", key=f"revive_btn_{key_prefix}", type=btn_type):
            attempt_revive_action(unit)
            st.rerun()

    # История последнего броска (из прошлого раунда)
    last_log = unit.memory.get("last_revive_log")
    if last_log and last_attempt != current_round:
        res_emoji = "✅" if last_log["success"] else "❌"
        st.caption(f"Прошлый бросок: {res_emoji} {last_log['total']} (vs {last_log['dc']})")