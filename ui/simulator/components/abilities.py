import streamlit as st

from core.enums import CardType
from core.library import Library
from core.unit.unit_library import UnitLibrary  # Для сохранения состояния
from logic.character_changing.passives import PASSIVE_REGISTRY
from logic.character_changing.talents import TALENT_REGISTRY
from logic.weapon_definitions import WEAPON_REGISTRY


def draw_azino_simulator_interface(unit, talent):
    """
    Специальный интерфейс для таланта Азино 777.
    """
    with st.container(border=True):
        st.markdown(f"**🎰 {talent.name}**")

        # 1. Текущее состояние слотов
        current_slots = unit.memory.get("azino_slots", [])
        if current_slots:
            cols_display = st.columns(3)
            for i, val in enumerate(current_slots):
                color = "#888"
                if val == 7:
                    color = "#4CAF50"  # Green
                elif val == 1:
                    color = "#F44336"  # Red
                elif val == 6:
                    color = "#FF9800"  # Orange
                elif val == 4:
                    color = "#9C27B0"  # Purple

                cols_display[i].markdown(
                    f"<div style='text-align: center; color: white; border: 2px solid {color}; "
                    f"border-radius: 8px; background-color: #222; padding: 5px; font-weight: bold; font-size: 20px;'>"
                    f"{val}</div>",
                    unsafe_allow_html=True
                )

            # Подсказка по эффектам
            effects_text = []
            counts = {x: current_slots.count(x) for x in set(current_slots)}
            for num, cnt in counts.items():
                mult = cnt ** 2
                effect_name = {
                    1: "Паралич", 2: "Сила", 3: "Скорость",
                    4: "Урон по себе", 5: "Стойкость",
                    6: "Урон врагу", 7: "Реген Удачи"
                }.get(num, "???")
                effects_text.append(f"[{num}] {effect_name} x{mult}")

            st.caption(f"Эффекты: {', '.join(effects_text)}")
            st.divider()

        # 2. Настройка спина
        k_pfx = f"sim_az_{unit.name}"
        opts = {0: "🎲 Рандом", 1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7"}

        c1, c2, c3 = st.columns(3)
        with c1:
            s1 = st.selectbox("Слот 1", list(opts.keys()), format_func=lambda x: opts[x], key=f"{k_pfx}_1")
        with c2:
            s2 = st.selectbox("Слот 2", list(opts.keys()), format_func=lambda x: opts[x], key=f"{k_pfx}_2")
        with c3:
            s3 = st.selectbox("Слот 3", list(opts.keys()), format_func=lambda x: opts[x], key=f"{k_pfx}_3")

        # 3. Расчет цены
        fixed_vals = [s1, s2, s3]
        cost = 0
        if hasattr(talent, 'calculate_cost'):
            cost = talent.calculate_cost(fixed_vals)
        else:
            cnt = sum(1 for x in fixed_vals if x > 0)
            if cnt >= 1: cost += 7
            if cnt >= 2: cost += 49
            if cnt >= 3: cost += 343

        current_luck = unit.resources.get("luck", 0)
        can_afford = current_luck >= cost

        # 4. Кнопка
        btn_text = f"🎰 SPIN (-{cost} Luck)"
        if not can_afford:
            btn_text = f"Не хватает ({cost})"

        if st.button(btn_text, disabled=not can_afford, key=f"btn_spin_{k_pfx}", use_container_width=True):
            def sim_logger(msg):
                st.toast(msg)
                st.session_state.setdefault('battle_logs', []).append(
                    {"round": "Azino", "rolls": "Spin", "details": msg}
                )

            if hasattr(talent, 'perform_spin'):
                success = talent.perform_spin(unit, fixed_vals, log_func=sim_logger)
                if success:
                    UnitLibrary.save_unit(unit)
                    st.rerun()


def render_active_abilities(unit, unit_key):
    abilities = []
    # Собираем все способности
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

            # === [NEW] ИНТЕГРАЦИЯ АЗИНО 777 ===
            if pid == "azino_777":
                draw_azino_simulator_interface(unit, obj)
                continue
            # ==================================

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

                # 2.5 Выбор карты
                selected_card_id = None
                if getattr(obj, "requires_card_selection", False):
                    if selected_target:
                        deck_ids = getattr(selected_target, "deck", [])
                        cooldowns = getattr(selected_target, "card_cooldowns", {})

                        card_options = {}
                        for cid in deck_ids:
                            is_on_cooldown = False
                            if cid in cooldowns:
                                current_cds = cooldowns[cid]
                                if current_cds and min(current_cds) > 0:
                                    is_on_cooldown = True

                            if is_on_cooldown:
                                continue

                            c_obj = Library.get_card(cid)
                            c_name = c_obj.name if c_obj else cid

                            # Фильтр типов карт
                            type_str = str(c_obj.card_type).upper() if c_obj else ""
                            if c_obj and (c_obj.card_type in [CardType.MASS_SUMMATION, CardType.MASS_INDIVIDUAL,
                                                              CardType.ITEM] or "MASS" in type_str or "ITEM" in type_str):
                                continue

                            label = f"{c_name}"
                            card_options[label] = cid

                        if card_options:
                            sorted_labels = sorted(card_options.keys())
                            choice_label = st.selectbox(
                                "Выберите доступную карту",
                                options=sorted_labels,
                                key=f"card_sel_{unit_key}_{pid}"
                            )
                            selected_card_id = card_options[choice_label]
                        else:
                            st.caption("Нет доступных карт")
                    else:
                        st.caption("Сначала выберите цель")

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

    if has_actives:
        st.caption("Active Abilities")