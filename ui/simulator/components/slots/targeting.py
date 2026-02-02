import streamlit as st

from ui.icons import get_icon_html
from ui.simulator.components.slots.utils import save_cb


def _build_target_options_cached(opposing_team, my_team, unit, selected_card, show_allies, show_enemies):
    """
    Кэшированное построение списка целей для минимизации пересчетов.
    Возвращает список опций для selectbox.
    """
    # Создаем уникальный ключ для кэша на основе состояния команд
    cache_key = f"targets_{id(opposing_team)}_{id(my_team)}_{unit.name}_{show_allies}_{show_enemies}"
    
    # Проверяем, есть ли кэш для текущего раунда
    current_round = st.session_state.get('round_number', 1)
    cache_round_key = f"{cache_key}_round"
    
    if cache_round_key in st.session_state and st.session_state[cache_round_key] == current_round:
        if cache_key in st.session_state:
            return st.session_state[cache_key]
    
    # Строим список целей
    target_options = ["None"]
    
    if show_enemies:
        alive_enemies = [u for u in opposing_team if not u.is_dead()]
        has_taunt = any(u.get_status("taunt") > 0 for u in alive_enemies)
        am_i_invisible = unit.get_status("invisibility") > 0

        for t_idx, target_unit in enumerate(opposing_team):
            if target_unit.is_dead(): continue
            is_target_invisible = target_unit.get_status("invisibility") > 0
            if is_target_invisible and not am_i_invisible: continue
            if has_taunt and target_unit.get_status("taunt") <= 0: continue

            for s_i, slot_obj in enumerate(target_unit.active_slots):
                t_spd = slot_obj['speed']
                extra = "😵" if slot_obj.get('stunned') else f"Spd {t_spd}"
                target_options.append(f"E|{t_idx}:{s_i} | ⚔️ {target_unit.name} S{s_i + 1} ({extra})")

    if show_allies:
        for t_idx, target_unit in enumerate(my_team):
            if target_unit.is_dead(): continue
            for s_i, slot_obj in enumerate(target_unit.active_slots):
                t_spd = slot_obj['speed']
                extra = "😵" if slot_obj.get('stunned') else f"Spd {t_spd}"
                target_options.append(f"A|{t_idx}:{s_i} | 🛡️ {target_unit.name} S{s_i + 1} ({extra})")
    
    # Сохраняем в кэш
    st.session_state[cache_key] = target_options
    st.session_state[cache_round_key] = current_round
    
    return target_options


def render_target_selector(c_tgt, c_mass, unit, slot, slot_idx, opposing_team, my_team, key_prefix):
    """
    Отрисовывает выбор цели (обычный или массовый) и опции Aggro/Break.
    """
    selected_card = slot.get('card')
    speed = slot['speed']

    # Проверка на Mass Attack
    is_mass_attack = False
    if selected_card:
        ctype = str(selected_card.card_type).lower()
        if "mass" in ctype: is_mass_attack = True

    if is_mass_attack:
        # --- MASS ATTACK LOGIC ---
        with c_mass:
            st.caption("🎯 **Выбор целей Масс. Атаки**")
            if 'mass_defenses' not in slot: slot['mass_defenses'] = {}

            for e_idx, enemy in enumerate(opposing_team):
                if enemy.is_dead(): continue
                slot_opts = ["Auto"]
                for s_i, _ in enumerate(enemy.active_slots): slot_opts.append(f"S{s_i + 1}")

                md_key = f"{key_prefix}_mass_{slot_idx}_{e_idx}"
                curr_val = slot['mass_defenses'].get(str(e_idx), "Auto")
                if curr_val not in slot_opts: curr_val = "Auto"

                cols_m = st.columns([1.5, 1])
                cols_m[0].markdown(f"**{enemy.name}**")
                new_val = cols_m[1].selectbox("Def Slot", slot_opts, index=slot_opts.index(curr_val), key=md_key,
                                              label_visibility="collapsed", on_change=save_cb)
                slot['mass_defenses'][str(e_idx)] = new_val
    else:
        # --- NORMAL ATTACK LOGIC ---
        show_allies = False
        show_enemies = True

        if selected_card:
            flags = selected_card.flags if hasattr(selected_card, 'flags') and selected_card.flags else []
            has_friendly = "friendly" in flags
            has_offensive = "offensive" in flags

            if has_friendly and has_offensive:
                show_allies = True; show_enemies = True
            elif has_friendly:
                show_allies = True; show_enemies = False
            else:
                show_allies = False; show_enemies = True

        # Используем кэшированное построение списка целей
        target_options = _build_target_options_cached(opposing_team, my_team, unit, selected_card, show_allies, show_enemies)

        # Восстановление текущего выбора
        cur_t_unit = slot.get('target_unit_idx', -1)
        cur_t_slot = slot.get('target_slot_idx', -1)
        cur_is_ally = slot.get('is_ally_target', False)
        current_val_str = "None"

        if cur_t_unit != -1 and cur_t_slot != -1:
            prefix_type = "A" if cur_is_ally else "E"
            search_prefix = f"{prefix_type}|{cur_t_unit}:{cur_t_slot}"
            for opt in target_options:
                if opt.startswith(search_prefix):
                    current_val_str = opt
                    break

        idx_sel = target_options.index(current_val_str) if current_val_str in target_options else 0
        selected_tgt_str = c_tgt.selectbox(
            "Target", target_options, index=idx_sel,
            key=f"{key_prefix}_{unit.name}_tgt_{slot_idx}", label_visibility="collapsed",
            on_change=st.session_state.get('save_callback')
        )

        if selected_tgt_str == "None":
            slot['target_unit_idx'] = -1;
            slot['target_slot_idx'] = -1;
            slot['is_ally_target'] = False
        else:
            try:
                meta_part, label_part = selected_tgt_str.split('|', 1)
                team_type = meta_part.strip()
                coords = label_part.split('|')[0].strip().split(':')
                slot['target_unit_idx'] = int(coords[0])
                slot['target_slot_idx'] = int(coords[1])
                slot['is_ally_target'] = (team_type == "A")
            except:
                slot['target_unit_idx'] = -1;
                slot['target_slot_idx'] = -1

        # --- AGGRO / BREAK OPTIONS ---
        if selected_card:
            _render_combat_options(unit, slot, slot_idx, selected_tgt_str, speed, key_prefix)

    return is_mass_attack  # Возвращаем флаг, чтобы знать как рисовать селектор карт


def _render_combat_options(unit, slot, slot_idx, selected_tgt_str, speed, key_prefix):
    can_redirect = True
    enemy_spd_val = 0
    has_athletic = ("athletic" in unit.talents) or ("athletic" in unit.passives)

    if selected_tgt_str != "None":
        try:
            import re
            match = re.search(r"Spd (\d+)", selected_tgt_str)
            if match:
                enemy_spd_val = int(match.group(1))
                if has_athletic:
                    if speed < enemy_spd_val: can_redirect = False
                else:
                    if speed <= enemy_spd_val: can_redirect = False
        except:
            pass

    _, c_opt1, c_opt2 = st.columns([2.5, 1, 1])
    aggro_val = slot.get('is_aggro', False)

    with c_opt1:
        icon_aggro = get_icon_html("dice_slot", width=30)
        st.markdown(f"<div style='text-align:center; height:30px;'>{icon_aggro}</div>", unsafe_allow_html=True)

        if slot.get('is_ally_target'):
            c_opt1.checkbox("Aggro", value=False, disabled=True, key=f"{key_prefix}_{unit.name}_aggro_{slot_idx}",
                            label_visibility="collapsed", on_change=save_cb)
            if aggro_val: slot['is_aggro'] = False
        elif can_redirect:
            c_opt1.checkbox("Aggro", value=aggro_val, key=f"{key_prefix}_{unit.name}_aggro_{slot_idx}",
                            label_visibility="collapsed", on_change=save_cb)
        else:
            c_opt1.checkbox("Aggro", value=False, disabled=True, key=f"{key_prefix}_{unit.name}_aggro_{slot_idx}",
                            label_visibility="collapsed", on_change=save_cb)
            if aggro_val: slot['is_aggro'] = False

    slot_destroy = slot.get('destroy_on_speed', True)
    with c_opt2:
        icon_broken = get_icon_html("dice_broken", width=30)
        st.markdown(f"<div style='text-align:center; height:30px;'>{icon_broken}</div>", unsafe_allow_html=True)
        new_destroy = st.checkbox("Break", value=slot_destroy, key=f"{key_prefix}_{unit.name}_destroy_{slot_idx}",
                                  label_visibility="collapsed", on_change=save_cb)
        slot['destroy_on_speed'] = new_destroy