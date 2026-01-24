import streamlit as st

from logic.character_changing.passives import PASSIVE_REGISTRY
from logic.character_changing.talents import TALENT_REGISTRY
from logic.weapon_definitions import WEAPON_REGISTRY


def render_active_abilities(unit, unit_key):
    abilities = []
    for pid in unit.passives:
        if pid in PASSIVE_REGISTRY: abilities.append((pid, PASSIVE_REGISTRY[pid]))
    if unit.weapon_id in WEAPON_REGISTRY:
        wep = WEAPON_REGISTRY[unit.weapon_id]
        if wep.passive_id and wep.passive_id in PASSIVE_REGISTRY:
            abilities.append((wep.passive_id, PASSIVE_REGISTRY[wep.passive_id]))
    for pid in unit.talents:
        if pid in TALENT_REGISTRY: abilities.append((pid, TALENT_REGISTRY[pid]))

    has_actives = False
    for pid, obj in abilities:
        if getattr(obj, "is_active_ability", False):
            has_actives = True
            with st.container(border=True):
                cd = unit.cooldowns.get(pid, 0)
                active_dur = unit.active_buffs.get(pid, 0)
                options = getattr(obj, "conversion_options", None)
                selected_opt = None

                st.markdown(f"**{obj.name}**")
                if options:
                    selected_opt = st.selectbox(
                        "Effect", 
                        options.keys(), 
                        format_func=lambda x: options.get(x, x),
                        key=f"sel_{unit_key}_{pid}",
                        label_visibility="collapsed"
                    )

                btn_label = "Activate"
                disabled = False
                if active_dur > 0:
                    btn_label = f"Active ({active_dur})"
                    disabled = True
                elif cd > 0:
                    btn_label = f"Cooldown ({cd})"
                    disabled = True

                if st.button(f"✨ {btn_label}", key=f"act_{unit_key}_{pid}", disabled=disabled,
                             width='stretch'):
                    def log_f(msg):
                        st.session_state.get('battle_logs', []).append(
                            {"round": "Skill", "rolls": "Activate", "details": msg})

                    if options:
                        if obj.activate(unit, log_f, choice_key=selected_opt): st.rerun()
                    else:
                        if obj.activate(unit, log_f): st.rerun()
    if has_actives: st.caption("Active Abilities")