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

    # [NEW] Получаем контекст команд для таргетинга
    team_left = st.session_state.get('team_left', [])
    team_right = st.session_state.get('team_right', [])
    is_left = unit in team_left
    allies = team_left if is_left else team_right
    enemies = team_right if is_left else team_left

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

                # 1. Выбор опций (если есть conversion_options)
                if options:
                    def format_option(key):
                        val = options.get(key, key)
                        if isinstance(val, dict): return key
                        return val

                    selected_opt = st.selectbox(
                        "Effect",
                        options.keys(),
                        format_func=format_option,
                        key=f"sel_{unit_key}_{pid}",
                        label_visibility="collapsed"
                    )

                # [NEW] 2. Выбор цели (если есть selection_type)
                selection_type = getattr(obj, "selection_type", None)
                selected_target = None

                if selection_type:
                    targets = []
                    if selection_type == "enemy":
                        targets = enemies
                    elif selection_type == "ally":
                        targets = allies
                    elif selection_type == "self":
                        targets = [unit]
                    elif selection_type == "all":
                        targets = allies + enemies

                    # Исключаем мертвых
                    targets = [t for t in targets if not t.is_dead()]

                    if targets:
                        # Формируем список: "Имя (HP)"
                        target_map = {f"{t.name} ({t.current_hp} HP)": t for t in targets}
                        tgt_choice = st.selectbox(
                            "Цель",
                            options=target_map.keys(),
                            key=f"tgt_{unit_key}_{pid}"
                        )
                        if tgt_choice:
                            selected_target = target_map[tgt_choice]
                    else:
                        st.caption("Нет доступных целей")

                # 3. Кнопка активации
                btn_label = "Activate"
                disabled = False
                if active_dur > 0:
                    btn_label = f"Active ({active_dur})"
                    disabled = True
                elif cd > 0:
                    btn_label = f"Cooldown ({cd})"
                    disabled = True
                elif selection_type and not selected_target:
                    # Если нужен таргет, но его нет
                    btn_label = "Select Target"
                    disabled = True

                if st.button(f"✨ {btn_label}", key=f"act_{unit_key}_{pid}", disabled=disabled, width='stretch'):
                    def log_f(msg):
                        st.session_state.get('battle_logs', []).append(
                            {"round": "Skill", "rolls": "Activate", "details": msg})

                    # Собираем все аргументы (опции + цель)
                    kwargs = {}
                    if selected_opt: kwargs['choice_key'] = selected_opt
                    if selected_target: kwargs['target'] = selected_target

                    if obj.activate(unit, log_f, **kwargs):
                        st.rerun()

    if has_actives: st.caption("Active Abilities")