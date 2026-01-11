import streamlit as st
from core.card import Card
from core.dice import Dice
from core.enums import DiceType
from core.library import Library
from core.unit.unit import Unit
from ui.styles import TYPE_ICONS, TYPE_COLORS
from ui.icons import get_icon_html  # Импорт загрузчика иконок


# --- ПЕРЕВОДЧИК СКРИПТОВ ---
def _format_script_text(script_id: str, params: dict) -> str:
    """
    Форматирует технические ID скриптов в читаемый текст с иконками.
    """

    # Вспомогательная функция для получения значения (Base или Amount)
    def get_val(p):
        return p.get("base", p.get("amount", p.get("stack", 0)))

    # Вспомогательная функция для текста скалирования
    def get_scale_text(p):
        stat = p.get("stat")
        if stat and stat != "None":
            factor = p.get("factor", 1.0)
            diff = p.get("diff", False)
            sign = "+" if factor >= 0 else ""
            diff_txt = " (Diff)" if diff else ""
            return f" [{sign}{factor}x {stat}{diff_txt}]"
        return ""

    # Вспомогательная функция для Длительности и Задержки
    def get_time_text(p):
        dur = int(p.get("duration", 0))
        dly = int(p.get("delay", 0))
        parts = []
        # Показываем длительность, если она > 1 или если это важно
        if dur > 1: parts.append(f"⏳{dur}")
        # Показываем задержку, если есть
        if dly > 0: parts.append(f"⏰{dly}")

        if parts:
            return f" ({', '.join(parts)})"
        return ""

    # === ЛЕЧЕНИЕ / РЕСУРСЫ ===
    if script_id in ["restore_hp", "restore_resource"]:
        res_type = params.get("type", "hp").lower()
        if script_id == "restore_hp": res_type = "hp"

        # Генерируем иконку
        icon = get_icon_html(res_type)

        val = get_val(params)
        scale = get_scale_text(params)
        return f"{icon} {res_type.upper()}: {val}{scale}"

    elif script_id in ["restore_sp", "restore_sp_percent"]:
        val = get_val(params)
        icon = get_icon_html("sp")
        return f"{icon} SP: {val}"

    # === СТАТУСЫ ===
    elif script_id == "apply_status":
        status_key = params.get("status", "???").lower()
        status_label = status_key.capitalize()

        # Иконка статуса
        icon = get_icon_html(status_key)

        val = get_val(params)
        scale = get_scale_text(params)
        time_info = get_time_text(params)

        target = params.get("target", "target")
        tgt_map = {"self": "себя", "target": "цель", "all": "всех", "all_allies": "союзников"}
        tgt_str = f" ({tgt_map.get(target, target)})"

        return f"{icon} {status_label}: {val}{scale}{time_info}{tgt_str}"

    # === УРОН / МОЩЬ ===
    elif script_id == "modify_roll_power":
        val = get_val(params)
        scale = get_scale_text(params)
        return f"🎲 Power: {val}{scale}"

    elif script_id == "deal_effect_damage":
        dtype = params.get("type", "hp").lower()
        icon = get_icon_html(dtype)
        val = get_val(params)
        scale = get_scale_text(params)
        return f"💔 Dmg ({icon}): {val}{scale}"

    elif script_id == "steal_status":
        status = params.get("status", "???")
        return f"✋ Украсть {status}"

    return f"🔧 {script_id} {params}"


def render_unit_stats(unit: Unit):
    """Отображает основные показатели юнита (HP, Stagger, SP) и активные статусы."""
    icon = '🟦' if 'Roland' in unit.name else '🟥'
    st.markdown(f"### {icon} {unit.name} (Lvl {unit.level})")

    # HP (Здоровье)
    max_hp = unit.max_hp if unit.max_hp > 0 else 1
    hp_pct = max(0.0, min(1.0, unit.current_hp / max_hp))
    st.progress(hp_pct, text=f"HP: {unit.current_hp}/{unit.max_hp}")

    # Stagger (Ошеломление)
    max_stg = unit.max_stagger if unit.max_stagger > 0 else 1
    stg_pct = max(0.0, min(1.0, unit.current_stagger / max_stg))
    st.progress(stg_pct, text=f"Stagger: {unit.current_stagger}/{unit.max_stagger}")

    # Sanity (SP / Рассудок)
    sp_limit = unit.max_sp
    total_range = sp_limit * 2 if sp_limit > 0 else 1
    current_shifted = unit.current_sp + sp_limit
    sp_pct = max(0.0, min(1.0, current_shifted / total_range))

    mood = "😐"
    if unit.current_sp >= 20:
        mood = "🙂"
    elif unit.current_sp >= 40:
        mood = "😄"
    elif unit.current_sp <= -20:
        mood = "😨"
    elif unit.current_sp <= -40:
        mood = "😱"

    st.progress(sp_pct, text=f"Sanity: {unit.current_sp}/{unit.max_sp} {mood}")

    # === ОТОБРАЖЕНИЕ СТАТУС-ЭФФЕКТОВ ===
    # Собираем данные из _status_effects (активные) и delayed_queue (отложенные)

    status_display_list = []

    # 1. Активные статусы
    if hasattr(unit, "_status_effects"):
        for name, instances in unit._status_effects.items():
            # Группируем по длительности
            grouped = {}
            for i in instances:
                d = i.get('duration', 1)
                grouped[d] = grouped.get(d, 0) + i['amount']

            for d, amt in grouped.items():
                status_display_list.append({
                    "name": name,
                    "amount": amt,
                    "duration": d,
                    "delay": 0,
                    "is_active": True
                })

    # 2. Отложенные статусы
    if hasattr(unit, "delayed_queue"):
        for item in unit.delayed_queue:
            status_display_list.append({
                "name": item['name'],
                "amount": item['amount'],
                "duration": item['duration'],
                "delay": item['delay'],
                "is_active": False
            })

    if status_display_list:
        st.markdown("---")
        html_tags = ""

        for s in status_display_list:
            name = s["name"]
            amt = s["amount"]
            dur = s["duration"]
            dly = s["delay"]

            # Получаем HTML иконки
            icon_html = get_icon_html(name, width=18)

            label_name = name.replace('_', ' ').capitalize()

            # Цвета рамок
            bg_color = "#2b2d42"
            border_color = "#8d99ae"

            # Если отложенный (Delay > 0)
            if dly > 0:
                bg_color = "#1a1a2e"
                border_color = "#6c757d"

            # Цветовая кодировка типов (упрощенная)
            if name in ["bleed", "burn", "paralysis", "fragile", "vulnerability", "weakness", "bind", "slow", "tremor",
                        "satiety"]:
                border_color = "#ef233c"  # Красный (Дебафф)
            elif name in ["strength", "endurance", "haste", "protection", "barrier", "regen_hp", "mental_protection",
                          "clarity"]:
                border_color = "#2ec4b6"  # Бирюзовый (Бафф)

            # Формирование текста значений
            value_text = f"<b>{amt}</b>"

            # Длительность
            if dur < 50:
                value_text += f" <span style='opacity:0.7'>| {dur}</span>"
            else:
                value_text += f" <span style='opacity:0.7'>| ∞</span>"

            # Задержка
            if dly > 0:
                value_text += f" <span style='color:#f4d35e'>| ⏳{dly}</span>"

            html_tags += f"""
                <div style="
                    display: inline-block;
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 5px;
                    padding: 2px 6px;
                    margin: 2px;
                    font-size: 0.85em;
                    color: white;
                    white-space: nowrap;
                    vertical-align: middle;">
                    {icon_html} {value_text} <span style='font-size:0.8em; margin-left:3px;'>{label_name}</span>
                </div>
                """

        st.markdown(html_tags, unsafe_allow_html=True)


def render_combat_info(unit: Unit):
    """Отображает сопротивления и боевые бонусы юнита."""
    with st.expander("🛡️ Resists & Bonuses", expanded=False):
        # Резисты
        c1, c2, c3 = st.columns(3)
        c1.metric("Slash", f"x{unit.hp_resists.slash}")
        c2.metric("Pierce", f"x{unit.hp_resists.pierce}")
        c3.metric("Blunt", f"x{unit.hp_resists.blunt}")

        st.divider()

        # Бонусы
        mods = unit.modifiers
        atk_power = mods.get("power_attack", 0) + mods.get("power_medium", 0)
        def_block = mods.get("power_block", 0)
        def_evade = mods.get("power_evade", 0)
        init_bonus = mods.get("initiative", 0)

        b1, b2, b3 = st.columns(3)
        b1.metric("⚔️ Atk Power", f"+{atk_power}")
        b2.metric("🛡️ Block", f"+{def_block}")
        b3.metric("💨 Evade", f"+{def_evade}")

        st.caption(f"Init Bonus: +{init_bonus}")


def card_selector_ui(unit: Unit, key_prefix: str):
    """Интерфейс выбора карты из библиотеки или создания кастомной."""
    mode = st.radio("Src", ["📚 Library", "🛠️ Custom"], key=f"{key_prefix}_mode", horizontal=True,
                    label_visibility="collapsed")

    if mode == "📚 Library":
        all_cards_objs = Library.get_all_cards()
        if not all_cards_objs:
            st.error("Library empty!")
            return None

        selected_card = st.selectbox(
            "Preset",
            all_cards_objs,
            format_func=lambda x: x.name,
            key=f"{key_prefix}_lib"
        )
        if selected_card and selected_card.description:
            st.caption(f"📝 {selected_card.description}")

    else:
        with st.container(border=True):
            c_name = st.text_input("Name", "My Card", key=f"{key_prefix}_custom_name")
            num_dice = st.slider("Dice", 1, 4, 2, key=f"{key_prefix}_cnt")
            custom_dice = []
            for i in range(num_dice):
                c1, c2, c3 = st.columns([1.5, 1, 1])
                dtype_str = c1.selectbox("T", [t.name for t in DiceType], key=f"{key_prefix}_d_{i}_t",
                                         label_visibility="collapsed")
                dmin = c2.number_input("Min", 1, 50, 4, key=f"{key_prefix}_d_{i}_min", label_visibility="collapsed")
                dmax = c3.number_input("Max", 1, 50, 8, key=f"{key_prefix}_d_{i}_max", label_visibility="collapsed")
                custom_dice.append(Dice(dmin, dmax, DiceType[dtype_str]))

            selected_card = Card(name=c_name, dice_list=custom_dice, description="Custom Card")

    if not unit.is_staggered():
        unit.current_card = selected_card
    return unit.current_card


def render_card_visual(card: Card, is_staggered: bool = False):
    """Визуальное представление карты с её кубиками и эффектами."""
    with st.container(border=True):
        if is_staggered:
            st.error("😵 STAGGERED")
            return
        if not card:
            st.warning("No card selected")
            return

        type_icon = "🏹" if card.card_type == "ranged" else "⚔️"
        st.markdown(f"**{card.name}** {type_icon}")

        # Скрипты карты (On Use и т.д.)
        if card.scripts:
            for trig, scripts in card.scripts.items():
                trigger_name = trig.replace("_", " ").title()
                st.markdown(f"**{trigger_name}:**")
                for s in scripts:
                    friendly_text = _format_script_text(s['script_id'], s.get('params', {}))
                    # Разрешаем HTML, чтобы картинки отображались
                    st.caption(f"- {friendly_text}", unsafe_allow_html=True)

        st.divider()

        # Кубики карты
        cols = st.columns(len(card.dice_list)) if card.dice_list else [st]
        for i, dice in enumerate(card.dice_list):
            with cols[i]:
                color = TYPE_COLORS.get(dice.dtype, "black")

                # Иконка кубика (Slash/Pierce/Blunt)
                dtype_key = dice.dtype.name.lower()
                icon_html = get_icon_html(dtype_key, width=24)

                # Используем markdown с html
                st.markdown(f"{icon_html} : {color}[**{dice.min_val}-{dice.max_val}**]", unsafe_allow_html=True)

                if dice.scripts:
                    for trig, effs in dice.scripts.items():
                        for e in effs:
                            friendly_text = _format_script_text(e['script_id'], e.get('params', {}))
                            st.caption(f"*{friendly_text}*", unsafe_allow_html=True)