import streamlit as st

from core.unit.unit import Unit
from ui.icons import get_icon_html


def render_unit_stats(unit: Unit):
    """Отображает HP, Stagger, SP и статусы."""
    icon = '🟦' if 'Roland' in unit.name else '🟥'
    st.markdown(f"### {icon} {unit.name} (Lvl {unit.level})")

    # HP
    max_hp = unit.max_hp if unit.max_hp > 0 else 1
    hp_pct = max(0.0, min(1.0, unit.current_hp / max_hp))
    st.progress(hp_pct, text=f"HP: {unit.current_hp}/{unit.max_hp}")

    # Stagger
    max_stg = unit.max_stagger if unit.max_stagger > 0 else 1
    stg_pct = max(0.0, min(1.0, unit.current_stagger / max_stg))
    st.progress(stg_pct, text=f"Stagger: {unit.current_stagger}/{unit.max_stagger}")

    # SP
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

    # Statuses
    status_display_list = []

    # Active
    if hasattr(unit, "_status_effects"):
        for name, instances in unit._status_effects.items():
            grouped = {}
            for i in instances:
                d = i.get('duration', 1)
                grouped[d] = grouped.get(d, 0) + i['amount']
            for d, amt in grouped.items():
                status_display_list.append({"name": name, "amount": amt, "duration": d, "delay": 0})

    # Delayed
    if hasattr(unit, "delayed_queue"):
        for item in unit.delayed_queue:
            status_display_list.append(
                {"name": item['name'], "amount": item['amount'], "duration": item['duration'], "delay": item['delay']})

    if status_display_list:
        st.markdown("---")
        html_tags = ""
        for s in status_display_list:
            name = s["name"]
            amt = s["amount"]
            dur = s["duration"]
            dly = s["delay"]

            icon_html = get_icon_html(name, width=18)
            label_name = name.replace('_', ' ').capitalize()
            bg_color, border_color = "#2b2d42", "#8d99ae"

            if dly > 0: bg_color, border_color = "#1a1a2e", "#6c757d"

            if name in ["bleed", "burn", "paralysis", "fragile", "vulnerability", "weakness", "bind", "tremor"]:
                border_color = "#ef233c"
            elif name in ["strength", "endurance", "haste", "protection", "barrier", "regen_hp"]:
                border_color = "#2ec4b6"

            value_text = f"<b>{amt}</b>"
            value_text += f" <span style='opacity:0.7'>| {dur if dur < 50 else '∞'}</span>"
            if dly > 0: value_text += f" <span style='color:#f4d35e'>| ⏳{dly}</span>"

            html_tags += f"""
                <div style="display: inline-block; background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 5px; padding: 2px 6px; margin: 2px; font-size: 0.85em; color: white; white-space: nowrap; vertical-align: middle;">
                    {icon_html} {value_text} <span style='font-size:0.8em; margin-left:3px;'>{label_name}</span>
                </div>
            """
        st.markdown(html_tags, unsafe_allow_html=True)