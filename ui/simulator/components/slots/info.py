import streamlit as st

from core.enums import DiceType
from logic.weapon_definitions import WEAPON_REGISTRY
from ui.components import _format_script_text
from ui.icons import get_icon_html
from ui.styles import TYPE_COLORS


def render_card_info(unit, slot):
    selected_card = slot.get('card')
    if not selected_card: return

    rank_icon = get_icon_html(f"tier_{selected_card.tier}", width=24)
    c_type_key = str(selected_card.card_type).lower()
    type_icon = get_icon_html(c_type_key, width=24)

    st.markdown(f"{rank_icon} **{selected_card.tier}** | {type_icon} **{c_type_key.capitalize()}**",
                unsafe_allow_html=True)

    if selected_card.dice_list:
        dice_display = []
        for d in selected_card.dice_list:
            color = TYPE_COLORS.get(d.dtype, "black")
            dtype_key = d.dtype.name.lower()
            if getattr(d, 'is_counter', False): dtype_key = f"counter_{dtype_key}"
            icon_html = get_icon_html(dtype_key, width=20)

            # === РАСЧЕТ БОНУСА (Визуализация) ===
            bonus = 0
            mods = unit.modifiers

            # [NEW] ПРОВЕРКА ПАССИВКИ "Доступ к истокам" (Source Access)
            override_active = False
            if "source_access" in unit.passives or "source_access" in unit.talents:
                override_active = True
                luck_val = unit.skills.get("luck", 0)
                bonus += luck_val // 5

            # 1. Глобальный бонус (Power All)
            bonus += int(mods.get("power_all", {}).get("flat", 0))

            # 2. Бонусы в зависимости от типа кубика
            if d.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
                # Если нет оверрайда, добавляем силу
                if not override_active:
                    bonus += int(mods.get("power_attack", {}).get("flat", 0))

                t_key = f"power_{d.dtype.name.lower()}"
                bonus += int(mods.get(t_key, {}).get("flat", 0))

                bonus += unit.get_status("attack_power_up")
                bonus += unit.get_status("power_up")
                bonus -= unit.get_status("weakness")

                wid = unit.weapon_id
                if wid and wid in WEAPON_REGISTRY:
                    wtype = WEAPON_REGISTRY[wid].weapon_type
                    if wtype:
                        w_key = f"power_{wtype}"
                        bonus += int(mods.get(w_key, {}).get("flat", 0))

            elif d.dtype == DiceType.BLOCK:
                if not override_active:
                    bonus += int(mods.get("power_block", {}).get("flat", 0))
                bonus += unit.get_status("endurance")
                bonus += unit.get_status("power_up")

            elif d.dtype == DiceType.EVADE:
                if not override_active:
                    bonus += int(mods.get("power_evade", {}).get("flat", 0))
                bonus += unit.get_status("endurance")
                bonus += unit.get_status("power_up")

            bonus_str = ""
            if bonus > 0:
                bonus_str = f" :green[(+{bonus})]"
            elif bonus < 0:
                bonus_str = f" :red[({bonus})]"

            dice_display.append(f"{icon_html} :{color}[**{d.min_val}-{d.max_val}**]{bonus_str}")

        st.markdown(" ".join(dice_display), unsafe_allow_html=True)

    # Scripts info
    desc_text = []
    if "on_use" in selected_card.scripts:
        for s in selected_card.scripts["on_use"]:
            text = _format_script_text(s['script_id'], s.get('params', {}))
            desc_text.append(f"On Use: {text}")

    for d in selected_card.dice_list:
        if d.scripts:
            for trig, effs in d.scripts.items():
                for e in effs:
                    t_name = trig.replace("_", " ").title()
                    text = _format_script_text(e['script_id'], e.get('params', {}))
                    desc_text.append(f"{t_name}: {text}")

    if selected_card.description: st.caption(f"📝 {selected_card.description}")
    if desc_text:
        for line in desc_text: st.caption(f"• {line}", unsafe_allow_html=True)