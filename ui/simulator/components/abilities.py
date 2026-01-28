import streamlit as st

from core.enums import CardType
from core.library import Library
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

    # Контекст команд
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

                # 1. Опции
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

                # 2. Цель
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

                    targets = [t for t in targets if not t.is_dead()]

                    if targets:
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

                # [FIXED] 2.5 Выбор карты (Только доступные в текущем ходу)
                selected_card_id = None
                if getattr(obj, "requires_card_selection", False):
                    if selected_target:
                        deck_ids = getattr(selected_target, "deck", [])
                        cooldowns = getattr(selected_target, "card_cooldowns", {})

                        card_options = {}
                        for cid in deck_ids:
                            # [СТРОГИЙ ФИЛЬТР]
                            # Если карта имеет записи в cooldowns и хотя бы одна копия в откате (>0),
                            # мы считаем её недоступной для "копирования текущего момента".
                            # (Или можно проверять min(cooldowns[cid]) == 0, если копий много и одна свободна)

                            is_on_cooldown = False
                            if cid in cooldowns:
                                # Если все копии этой карты в откате - она недоступна
                                # Если хотя бы одна доступна (0) - можно копировать
                                current_cds = cooldowns[cid]
                                if current_cds and min(current_cds) > 0:
                                    is_on_cooldown = True

                            if is_on_cooldown:
                                continue

                            c_obj = Library.get_card(cid)
                            c_name = c_obj.name if c_obj else cid

                            forbidden_types = [CardType.MASS_SUMMATION, CardType.MASS_INDIVIDUAL, CardType.ITEM]
                            if c_obj.card_type in forbidden_types:
                                continue

                            # Проверяем строку (на всякий случай)
                            type_str = str(c_obj.card_type).upper()
                            if "MASS" in type_str or "ITEM" in type_str:
                                continue

                            # Формируем Label. Используем ID как Value.
                            # Группируем дубликаты (Set Logic в UI)
                            label = f"{c_name}"
                            card_options[label] = cid

                        if card_options:
                            # Сортируем по имени
                            sorted_labels = sorted(card_options.keys())

                            choice_label = st.selectbox(
                                "Выберите доступную карту",
                                options=sorted_labels,
                                key=f"card_sel_{unit_key}_{pid}"
                            )
                            selected_card_id = card_options[choice_label]
                        else:
                            st.caption("Нет доступных карт (все в откате)")
                    else:
                        st.caption("Сначала выберите цель")

                # 3. Кнопка
                btn_label = "Activate"
                disabled = False
                if active_dur > 0:
                    btn_label = f"Active ({active_dur})"
                    disabled = True
                elif cd > 0:
                    btn_label = f"Cooldown ({cd})"
                    disabled = True
                elif selection_type and not selected_target:
                    btn_label = "Select Target"
                    disabled = True
                elif getattr(obj, "requires_card_selection", False) and not selected_card_id:
                    btn_label = "Select Card"
                    disabled = True

                if st.button(f"✨ {btn_label}", key=f"act_{unit_key}_{pid}", disabled=disabled, width='stretch'):
                    def log_f(msg):
                        st.session_state.get('battle_logs', []).append(
                            {"round": "Skill", "rolls": "Activate", "details": msg})

                    kwargs = {}
                    if selected_opt: kwargs['choice_key'] = selected_opt
                    if selected_target: kwargs['target'] = selected_target
                    if selected_card_id: kwargs['selected_card_id'] = selected_card_id

                    if obj.activate(unit, log_f, **kwargs):
                        st.rerun()

    if has_actives: st.caption("Active Abilities")