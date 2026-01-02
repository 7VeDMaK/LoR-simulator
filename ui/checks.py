import streamlit as st
import random

from core.unit.unit import Unit

# === 1. ОПРЕДЕЛЕНИЕ ГРУПП И НАЗВАНИЙ (Оставляем как было) ===

TYPE_10_ATTRS = {
    "strength": "Сила", "agility": "Ловкость", "endurance": "Стойкость",
    "speed": "Скорость", "psych": "Психический порог", "medicine": "Медицина", "willpower": "Сила воли"
}

TYPE_15_SKILLS = {
    "strike_power": "Сила удара", "acrobatics": "Акробатика", "shields": "Щиты",
    "light_weapon": "Легкое оружие", "medium_weapon": "Среднее оружие", "heavy_weapon": "Тяжелое оружие",
    "firearms": "Огнестрельное оружие", "tough_skin": "Крепкая кожа", "eloquence": "Красноречие",
    "forging": "Ковка", "programming": "Программирование", "engineering": "Инженерия"
}

TYPE_WISDOM = {"wisdom": "Мудрость"}
TYPE_LUCK = {"luck": "Удача"}
TYPE_INTELLECT = {"intellect": "Интеллект"}

ALL_LABELS = {**TYPE_10_ATTRS, **TYPE_15_SKILLS, **TYPE_WISDOM, **TYPE_LUCK, **TYPE_INTELLECT}


# === 2. ЛОГИКА РАСЧЕТОВ (Оставляем как было) ===
def get_difficulty_description(value, stat_key=""):
    """Возвращает текстовое описание сложности/уровня."""
    stat_key = stat_key.lower()

    # === УДАЧА (ПОЛНЫЙ ТЕКСТ) ===
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


def get_check_params(key):
    if key in TYPE_10_ATTRS:
        return "type10", "d6", "Характеристика (1/3)"
    elif key in TYPE_15_SKILLS:
        return "type15", "d6", "Навык (1 к 1)"
    elif key in TYPE_WISDOM:
        return "typeW", "d20", "Мудрость"
    elif key in TYPE_LUCK:
        return "typeL", "d12", "Удача"
    elif key in TYPE_INTELLECT:
        return "typeI", "d6", "Интеллект"
    return "unknown", "d6", "???"


def get_stat_value(unit: Unit, key: str) -> int:
    """
    Безопасно получает значение стата из unit.modifiers или базовых атрибутов.
    Обрабатывает новую структуру modifiers ({'flat': val, 'pct': val}).
    """
    # 1. Проверяем Luck отдельно (ресурс)
    if key == "luck":
        return unit.resources.get("luck", 0)

    # 2. Пытаемся найти в modifiers
    # Сначала ищем по прямому ключу (новая система: "strength"), потом по "total_" (старая/совместимость)
    val_data = None
    if key in unit.modifiers:
        val_data = unit.modifiers[key]
    elif f"total_{key}" in unit.modifiers:
        val_data = unit.modifiers[f"total_{key}"]

    # Спец. кейс для интеллекта
    if key == "intellect" and "total_intellect" in unit.modifiers:
        val_data = unit.modifiers["total_intellect"]

    # Если нашли в модах - извлекаем число
    if val_data is not None:
        if isinstance(val_data, dict):
            return int(val_data.get("flat", 0))
        return int(val_data)

    # 3. Если нет в модах, ищем в базовых хранилищах
    if key in unit.attributes: return unit.attributes[key]
    if key in unit.skills: return unit.skills[key]
    if key == "intellect": return unit.base_intellect

    return 0


def calculate_pre_roll_stats(stat_key, stat_value, difficulty, bonus):
    check_type, _, _ = get_check_params(stat_key)
    die_min, die_max = 1, 6
    stat_bonus = 0
    final_dc = difficulty

    if check_type == "type10":
        die_max = 6;
        stat_bonus = stat_value // 3
    elif check_type == "type15":
        die_max = 6;
        stat_bonus = stat_value
        if stat_key == "engineering" and difficulty > 0: final_dc = int(difficulty * 1.3)
    elif check_type == "typeW":
        die_max = 20;
        stat_bonus = stat_value
    elif check_type == "typeL":
        die_max = 12;
        stat_bonus = stat_value
    elif check_type == "typeI":
        # Была фиксированная прогрессия, теперь:
        die_max = 6
        stat_bonus = 4 + int(stat_value)

    target_roll = final_dc - stat_bonus - bonus
    success_count = 0
    for r in range(die_min, die_max + 1):
        if check_type in ["typeW", "typeL"]:
            if r == 1: continue
            if r == die_max: success_count += 1; continue
        if r >= target_roll: success_count += 1

    chance = (success_count / die_max) * 100.0
    ev = (die_min + die_max) / 2 + stat_bonus + bonus
    return chance, ev, final_dc


def perform_check_logic(stat_key, stat_value, difficulty, bonus):
    stat_key = stat_key.lower()
    check_type, die_type, _ = get_check_params(stat_key)

    result = {
        "roll": 0, "die": die_type, "stat_bonus": 0, "total": 0,
        "final_difficulty": difficulty, "is_success": False,
        "is_crit": False, "is_fumble": False, "msg": "", "formula_text": ""
    }

    if check_type == "type10":
        result["roll"] = random.randint(1, 6)
        result["stat_bonus"] = stat_value // 3
        result["formula_text"] = f"`{result['stat_bonus']} (Стат // 3)`"

    elif check_type == "type15":
        result["roll"] = random.randint(1, 6)
        result["stat_bonus"] = stat_value
        result["formula_text"] = f"`{result['stat_bonus']} (Навык)`"
        if stat_key == "engineering" and difficulty > 0:
            result["final_difficulty"] = int(difficulty * 1.3)

    elif check_type == "typeW":
        result["roll"] = random.randint(1, 20)
        result["stat_bonus"] = stat_value
        result["formula_text"] = f"`{result['stat_bonus']} (Мудр)`"
        if result["roll"] == 20: result["is_crit"] = True
        if result["roll"] == 1: result["is_fumble"] = True

    elif check_type == "typeL":
        result["roll"] = random.randint(1, 12)
        result["stat_bonus"] = stat_value
        result["formula_text"] = f"`{result['stat_bonus']} (Удача)`"
        if result["roll"] == 12: result["is_crit"] = True
        if result["roll"] == 1: result["is_fumble"] = True

    elif check_type == "typeI":
        result["die"] = "d6"
        result["roll"] = random.randint(1, 6)
        result["stat_bonus"] = 4 + int(stat_value)
        result["formula_text"] = f"`{result['stat_bonus']} (4 + Инт)`"

    result["total"] = result["roll"] + result["stat_bonus"] + bonus

    if difficulty > 0:
        if result["is_crit"]:
            result["is_success"] = True; result["msg"] = "КРИТИЧЕСКИЙ УСПЕХ!"
        elif result["is_fumble"]:
            result["is_success"] = False; result["msg"] = "КРИТИЧЕСКИЙ ПРОВАЛ!"
        else:
            result["is_success"] = result["total"] >= result["final_difficulty"]
            result["msg"] = "УСПЕХ" if result["is_success"] else "ПРОВАЛ"
    else:
        result["msg"] = "РЕЗУЛЬТАТ";
        result["is_success"] = True

    return result


def calculate_luck_cost(chosen_value, current_luck):
    """
    Рассчитывает стоимость (или восстановление) удачи.
    Формула: N - P(x).
    Если x > 0: Тратим P(x).
    Если x < 0: Восстанавливаем P(x).
    """
    abs_val = abs(chosen_value)
    cost = 0

    # Таблица штрафов P(x)
    if abs_val < 6:
        cost = 1
    elif abs_val < 12:
        cost = 3
    elif abs_val < 20:
        cost = 5
    elif abs_val < 30:
        cost = 10
    elif abs_val < 45:
        cost = 20
    elif abs_val < 60:
        cost = 40
    elif abs_val < 80:
        # "Вся в зависимости от выбора". Считаем как "Все что есть"
        cost = current_luck if current_luck > 0 else 0
        if chosen_value < 0: cost = 60  # При восстановлении даем фиксированно много? Пусть будет 60.
    else:
        # 80+ "Вся вне зависимости от выбора".
        cost = current_luck if current_luck > 0 else 0
        if chosen_value < 0: cost = 100  # Восстановление

    return cost


def draw_luck_interface(unit):
    """Специальный интерфейс для Удачи."""
    st.divider()

    # 1. Текущее состояние
    # Важно: берем из resources, так как удача тратится
    current_luck = unit.resources.get("luck", 0)

    c_cur, c_roll = st.columns([1, 1])
    c_cur.metric("Текущая Удача (Ресурс)", current_luck)

    # Состояние броска хранится в session_state, чтобы не сбрасывалось при взаимодействии
    roll_key = f"luck_roll_val_{unit.name}"

    # 2. Кнопка Броска (Определение Максимума)
    if c_roll.button("🎲 Ролл Потенциала (1d12 + Luck)", type="primary"):
        roll = random.randint(1, 12)
        total_roll = roll + current_luck
        st.session_state[roll_key] = total_roll
        # Сброс выбора при новом броске
        if f"luck_choice_{unit.name}" in st.session_state:
            del st.session_state[f"luck_choice_{unit.name}"]

    # 3. Если бросок сделан -> Показываем выбор
    if roll_key in st.session_state:
        max_pot = abs(st.session_state[roll_key])  # Модуль, на всякий случай

        st.info(f"🎰 Максимальный потенциал: **{max_pot}**")

        # Слайдер выбора значения x
        # Диапазон: [-Max, Max]
        choice = st.slider(
            "Выберите уровень воздействия",
            min_value=-max_pot,
            max_value=max_pot,
            value=0,
            key=f"luck_choice_{unit.name}",
            help="Положительное: Тратит удачу. Отрицательное: Восстанавливает."
        )

        # Описание уровня
        desc = get_difficulty_description(choice, "luck")
        st.caption(f"📜 {desc}")

        # Расчет стоимости
        cost_val = calculate_luck_cost(choice, current_luck)

        # Предпросмотр
        new_luck = 0
        msg = ""

        if choice > 0:
            # Трата
            new_luck = current_luck - cost_val
            msg = f"📉 Трата: -{cost_val} (Новое значение: {new_luck})"
            if new_luck < 0:
                st.warning(f"⚠️ Внимание: Удача уйдет в минус ({new_luck})!")
        elif choice < 0:
            # Восстановление
            new_luck = current_luck + cost_val
            msg = f"📈 Восстановление: +{cost_val} (Новое значение: {new_luck})"
        else:
            new_luck = current_luck
            msg = "Нет изменений"

        st.markdown(f"**{msg}**")

        # 4. Применить
        if choice != 0:
            if st.button("✅ Применить и сохранить", type="secondary"):
                unit.resources["luck"] = new_luck
                # Сбрасываем бросок после применения
                del st.session_state[roll_key]
                del st.session_state[f"luck_choice_{unit.name}"]
                st.success("Удача обновлена!")
                st.rerun()

# === 3. НОВАЯ ФУНКЦИЯ ОТРИСОВКИ ИНТЕРФЕЙСА ===
# Мы выносим отрисовку "нижней части" сюда, чтобы вызывать её внутри КАЖДОГО таба отдельно.

def draw_roll_interface(unit, selected_key, selected_label):
    st.divider()

    # 1. Получаем значение
    val = get_stat_value(unit, selected_key)

    # 2. Настройки (Сложность/Бонус)
    c_val, c_dc, c_bonus = st.columns([1, 1, 1])

    c_val.metric(f"{selected_label}", val)

    # Используем уникальные ключи (key=...) чтобы Streamlit не путался между табами
    difficulty = c_dc.number_input("Сложность (DC)", 0, 100, 15, key=f"dc_{selected_key}")
    bonus = c_bonus.number_input("Бонус", -20, 20, 0, key=f"bonus_{selected_key}")

    # 3. Шансы
    chance, ev, final_dc = calculate_pre_roll_stats(selected_key, val, difficulty, bonus)

    if chance >= 80:
        color = "green"
    elif chance >= 50:
        color = "orange"
    else:
        color = "red"

    st.markdown(f"Шанс: :{color}[**{chance:.1f}%**] | Ожидание: **{ev:.1f}** | DC: **{final_dc}**")

    # 4. Кнопка
    if st.button("🎲 Бросить", type="primary", use_container_width=True, key=f"btn_{selected_key}"):
        res = perform_check_logic(selected_key, val, difficulty, bonus)

        res_color = "green" if res["is_success"] else "red"

        with st.container(border=True):
            c_img, c_txt = st.columns([1, 4])
            with c_img:
                img = unit.avatar if unit.avatar else "https://placehold.co/100x100/png?text=Unit"
                st.image(img, width=80)

            with c_txt:
                st.markdown(f"### :{res_color}[{res['msg']}]")
                st.markdown(f"**{res['total']}** vs **{res['final_difficulty']}**")

                die_text = f"`{res['roll']} ({res['die']})`" if res['die'] != "Fixed" else ""
                bonus_text = f" + `{bonus}`" if bonus != 0 else ""

                st.markdown(f"{die_text} + {res['formula_text']}{bonus_text} = **{res['total']}**")

                if res['is_crit']: st.caption("🔥 CRITICAL SUCCESS")
                if res['is_fumble']: st.caption("💀 CRITICAL FAILURE")


# === 4. ГЛАВНАЯ ФУНКЦИЯ ===

def render_checks_page():
    st.title("🎲 Проверки (Skill Checks)")

    if 'roster' not in st.session_state or not st.session_state['roster']:
        st.warning("Ростер пуст.")
        return

    roster_names = list(st.session_state['roster'].keys())
    default_ix = 0
    if 'last_check_unit' in st.session_state and st.session_state['last_check_unit'] in roster_names:
        default_ix = roster_names.index(st.session_state['last_check_unit'])

    c_sel, _ = st.columns([1, 1])
    selected_name = c_sel.selectbox("Персонаж", roster_names, index=default_ix)
    st.session_state['last_check_unit'] = selected_name
    unit = st.session_state['roster'][selected_name]
    unit.recalculate_stats()

    # --- ТАБЫ ---
    tabs = st.tabs(["💪 Характеристики", "🛠️ Навыки", "🧠 Мудрость", "🍀 Удача", "💡 Интеллект"])

    # В КАЖДОМ ТАБЕ МЫ ВЫЗЫВАЕМ draw_roll_interface ОТДЕЛЬНО

    # 1. Характеристики
    with tabs[0]:
        l_dict = {v: k for k, v in TYPE_10_ATTRS.items()}
        chosen = st.radio("Параметр", list(TYPE_10_ATTRS.values()), horizontal=True, label_visibility="collapsed")
        st.caption("🎲 **1d6 + (Значение / 3)**. Макс стат: 30.")

        # Рисуем интерфейс броска
        draw_roll_interface(unit, l_dict[chosen], chosen)

        # Подсказка по сложности (Ваш текст)
        with st.expander("ℹ️ Таблица Сложности (Характеристики)", expanded=True):
            st.markdown("""
                * **1~4** — дела, что может сделать любой, кто не инвалид или умственно отсталый 
                * **5~8** — проблемы, которые может решить любой человек, немного подстёгнутый в данной сфере 
                * **9~12** — задачи, решаемые только обученными специалистами 
                * **13~16** — тяжелые задачи, решаемые только профессионалами в данной деятельности
                * **17~20** — нечеловеческий уровень проблем, достигаемый только аугментациями, либо иными улучшениями
                * **21+** — проблемы, которые не должен решать человек в принципе
                """)

    # 2. Навыки
    with tabs[1]:
        l_dict = {v: k for k, v in TYPE_15_SKILLS.items()}
        c1, c2 = st.columns(2)
        items = list(TYPE_15_SKILLS.values())
        chosen = st.selectbox("Выберите навык", items, label_visibility="collapsed")

        info_text = "🎲 **1d6 + Значение**. Макс: 15."
        if l_dict[chosen] == "engineering": info_text += " ⚠️ Сложность x1.3"
        st.caption(info_text)

        # Рисуем интерфейс
        draw_roll_interface(unit, l_dict[chosen], chosen)

        # Подсказка по сложности (Навыки)
        with st.expander("ℹ️ Таблица Сложности (Навыки)", expanded=True):
            st.markdown("""
            * **1~7** — дела, что может сделать любой, кто не инвалид или умственно отсталый 
            * **8~14** — проблемы, которые может решить любой человек, немного подстёгнутый в данной сфере 
            * **15~21** — задачи, решаемые только обученными специалистами 
            * **22~29** — нечеловеческий уровень проблем, достигаемый только аугментациями, либо иными улучшениями
            * **30+** — проблемы, которые не должен решать человек в принципе 
            """)

        # 3. Мудрость
        with tabs[2]:
            st.caption("🎲 **1d20 + Значение**. Для ролевых ситуаций.")
            draw_roll_interface(unit, "wisdom", "Мудрость")

            # Подсказка по сложности (Мудрость)
            with st.expander("ℹ️ Таблица Сложности (Мудрость)", expanded=True):
                st.markdown("""
                * **1~6** — дела, что может сделать любой, кто не инвалид или умственно отсталый 
                * **7~12** — уровень обычного человека
                * **13~19** — проблемы, которые может решить любой человек, немного подстёгнутый в данной сфере 
                * **20~27** — уровень хорошо образованного жителя города
                * **28~35** — задачи, решаемые только обученными специалистами 
                * **36~44** — нечеловеческий уровень проблем, достигаемый только аугментациями, либо иными улучшениями
                * **45+** — проблемы, которые не должен решать человек в принципе
                """)
    # 4. Удача
    with tabs[3]:
        st.caption("🎲 **1d12 + Текущая Удача**. Трата удачи приводит к штрафам.")
        # ИСПОЛЬЗУЕМ СПЕЦИАЛЬНЫЙ ИНТЕРФЕЙС
        draw_luck_interface(unit)

        with st.expander("ℹ️ Уровни Удачи (ПОЛНОЕ ОПИСАНИЕ)", expanded=True):
            st.markdown("""
            * **1** — вы полный неудачник, ожидайте своего Свиппера ночью
            * **6** — у вас обычная удача среднестатистического человека. Вы не опоздаете на работу и найдёте кетчуп до его биоразложения
            * **12** — сегодня вам везёт! Найденная монетка в 100 ан, либо завалявшийся носок под кроватью тому свидетель
            * **20** — вы нашли свой вчерашний день, а также смогли выиграть куш в казино. Осторожнее, везунчики смертны! А ещё сегодня пошли по кратчайшей дорожке и не попали под машину
            * **30** — везение на этой стадии переходит в нечто нереальное. Вы легко находите своих друзей на улице, от вас не скроются важные детали преступления, а также ваша депрессия перестаёт ощущаться ежедневной рутиной
            * **45** — дальнейший рост вашего везения уходит в корни странностей. У вас развивается ощущение, что вы можете исправлять свои ошибки чистой случайностью, находить нужные памятки в голове и не ошибаться в ударении даже в самых сложных словах (вы их не знаете). Ваша удача сравнима с харизмой руководителя офиса корректировщиков 4-6 рангов, а также с репутацией синдикатов уровня Городской Чумы. Это не нормально.
            * **60** — Вы начинаете создавать потустороннее вмешательство, паранормальные действия и вмешиваться в глобальную историю мира. Хоть вы и сравнительно слабы, но последующие действия могут спровоцировать череду "удачных" стечений обстоятельств, которые затронут только вас.
            * **80** — Ваше вмешательство не на шутку влияет течение истории Города, вплоть до того, что из-за вас могут начаться войны между целыми частями района. Случайность вашего появления уже не случайна. Детерминированные успехи в любой деятельности, практически абсолют во всём.
            * **100+** — Лишь единицы могут похвастаться тем, что они создают вокруг себя собственное поле "удачи". Вы способны тягаться с Звездами Города голыми руками

            ⚠️ *Таблица Штрафов (Трата/Восстановление):*
            * **0~6**: 1
            * **6~12**: 3
            * **12~20**: 5
            * **20~30**: 10
            * **30~45**: 20
            * **45~60**: 40
            * **60+**: Вся удача / Сброс
            """)

    # 5. Интеллект
    with tabs[4]:
        st.caption("🎲 **1d6 + 4 + Интеллект**.")
        draw_roll_interface(unit, "intellect", "Интеллект")
        with st.expander("ℹ️ Таблица Сложности (Интеллект)", expanded=True):
            st.markdown("""
            * **1~7** — дела, что может сделать любой, кто не инвалид или умственно отсталый 
            * **8~14** — проблемы, которые может решить любой человек, немного подстёгнутый в данной сфере 
            * **15~21** — задачи, решаемые только обученными специалистами 
            * **22~29** — нечеловеческий уровень проблем, достигаемый только аугментациями, либо иными улучшениями
            * **30+** — проблемы, которые не должен решать человек в принципе 
            """)