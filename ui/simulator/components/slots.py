import streamlit as st
from collections import Counter
from core.library import Library
from core.enums import DiceType, CardType
from logic.state_manager import StateManager
from logic.weapon_definitions import WEAPON_REGISTRY
from ui.components import _format_script_text
from ui.icons import get_icon_html
from ui.styles import TYPE_COLORS
from ui.simulator.components.common import CARD_TYPE_ICONS


def save_cb():
    StateManager.save_state(st.session_state)


def render_slot_strip(unit, opposing_team, my_team, slot_idx, key_prefix):
    """
    Рендерит полоску одного слота действий.
    """
    slot = unit.active_slots[slot_idx]

    # --- 1. ПРОВЕРКА ОГЛУШЕНИЯ (STAGGER) ---
    if slot.get('stunned'):
        st.error(f"😵 **STAGGERED** (Speed 0)")
        return

    # --- 2. ЗАГОЛОВОК (HEADER) ---
    speed = slot['speed']
    ui_stat = slot.get('ui_status', {"text": "...", "icon": "", "color": "gray"})
    selected_card = slot.get('card')

    # Defensive check
    if selected_card and not hasattr(selected_card, 'dice_list'):
        try:
            resolved = Library.get_card(selected_card)
            if hasattr(resolved, 'dice_list'):
                slot['card'] = resolved
                selected_card = resolved
            else:
                slot['card'] = None
                selected_card = None
        except Exception:
            slot['card'] = None
            selected_card = None

    # Формирование заголовка
    if selected_card:
        c_type_lower = str(selected_card.card_type).lower()
        type_emoji = "📄"
        for k, v in CARD_TYPE_ICONS.items():
            if k in c_type_lower:
                type_emoji = v
                break
        card_name_header = f"[{selected_card.tier}] {type_emoji} {selected_card.name}"
    else:
        card_name_header = "⛔ Пусто"

    spd_label = f"🎲{speed}"
    if slot.get("source_effect"):
        spd_label += f" ({slot.get('source_effect')})"

    lock_icon = "🔒 " if slot.get('locked') else ""
    label = f"{lock_icon}S{slot_idx + 1} ({spd_label}) | {ui_stat['icon']} {ui_stat['text']} | {card_name_header}"

    # === ПОДСЧЕТ ДОСТУПНЫХ КАРТ ===
    deck_ids = getattr(unit, 'deck', [])
    deck_counts = Counter(deck_ids)
    available_cards = []

    if not slot.get('locked'):
        if deck_ids:
            used_in_others = Counter()
            for i, s in enumerate(unit.active_slots):
                if i == slot_idx: continue
                if s.get('card'):
                    used_in_others[s['card'].id] += 1

            unique_ids = sorted(list(set(deck_ids)))
            for cid in unique_ids:
                cooldowns_list = unit.card_cooldowns.get(cid, [])
                if isinstance(cooldowns_list, int): cooldowns_list = [cooldowns_list]

                copies_on_cooldown = len(cooldowns_list)
                total_owned = deck_counts[cid]
                currently_used_elsewhere = used_in_others[cid]

                if total_owned - copies_on_cooldown - currently_used_elsewhere > 0:
                    c_obj = Library.get_card(cid)
                    if c_obj and str(c_obj.card_type).lower() != "item":
                        available_cards.append(c_obj)
        else:
            raw_cards = Library.get_all_cards()
            for c in raw_cards:
                if str(c.card_type).lower() != "item":
                    if unit.card_cooldowns.get(c.id, 0) <= 0:
                        available_cards.append(c)

    available_cards.sort(key=lambda x: (x.tier, x.name))

    # --- 3. ИНТЕРФЕЙС ВЫБОРА ---
    with st.expander(label, expanded=False):
        # Если выбрана МАССОВАЯ АТАКА -> Специальный интерфейс
        is_mass_attack = False
        if selected_card:
            ctype = str(selected_card.card_type).lower()
            if "mass" in ctype:
                is_mass_attack = True

        if is_mass_attack:
            c_sel, c_mass = st.columns([1, 2])
        else:
            c_tgt, c_sel = st.columns([1, 1])

        # === ВЫБОР КАРТЫ (Общий для всех) ===
        # Рисуем его первым, если это Mass Attack (чтобы был слева), или вторым если обычная

        display_cards = [None] + available_cards
        c_idx = 0
        if selected_card:
            for idx, c in enumerate(display_cards):
                if c and c.id == selected_card.id:
                    c_idx = idx
                    break

        def format_card_option(x):
            if not x: return "⛔ Пусто"
            emoji = "📄"
            ctype = str(x.card_type).lower()
            for k, v in CARD_TYPE_ICONS.items():
                if k in ctype: emoji = v; break
            if deck_ids:
                count = deck_counts.get(x.id, 0)
                return f"{emoji} [{x.tier}] {x.name} (x{count})"
            return f"{emoji} [{x.tier}] {x.name}"

        # Контейнер для селектора карты
        card_container = c_sel if not is_mass_attack else c_sel

        if slot.get('locked'):
            card_container.text_input("Page", value=selected_card.name if selected_card else "Locked", disabled=True,
                                      label_visibility="collapsed")
        else:
            new_card = card_container.selectbox("Page", display_cards, format_func=format_card_option, index=c_idx,
                                                key=f"{key_prefix}_{unit.name}_card_{slot_idx}",
                                                label_visibility="collapsed",
                                                on_change=st.session_state.get('save_callback'))
            slot['card'] = new_card

        # === ВЫБОР ЦЕЛИ (ДВА РЕЖИМА) ===

        if is_mass_attack:
            # --- РЕЖИМ МАССОВОЙ АТАКИ ---
            # Показываем список врагов и выбор слота защиты для каждого
            with c_mass:
                st.caption("🎯 **Выбор целей Масс. Атаки** (Кто чем защищается)")

                # Инициализация словаря выбора
                if 'mass_defenses' not in slot:
                    slot['mass_defenses'] = {}

                # Перебираем врагов
                for e_idx, enemy in enumerate(opposing_team):
                    if enemy.is_dead(): continue

                    # Опции слотов: Auto (Рандом), S1, S2...
                    slot_opts = ["Auto"]
                    for s_i, _ in enumerate(enemy.active_slots):
                        slot_opts.append(f"S{s_i + 1}")

                    # Ключ для виджета
                    md_key = f"{key_prefix}_mass_{slot_idx}_{e_idx}"

                    # Текущее значение
                    curr_val = slot['mass_defenses'].get(str(e_idx), "Auto")
                    if curr_val not in slot_opts: curr_val = "Auto"

                    cols_m = st.columns([1.5, 1])
                    cols_m[0].markdown(f"**{enemy.name}**")
                    new_val = cols_m[1].selectbox("Def Slot", slot_opts,
                                                  index=slot_opts.index(curr_val),
                                                  key=md_key,
                                                  label_visibility="collapsed",
                                                  on_change=save_cb)

                    slot['mass_defenses'][str(e_idx)] = new_val

            # Опции Aggro/Break для масс атак обычно скрыты или фиксированы, но можно оставить
            # Если нужно, добавим их ниже. Для масс атак Break обычно встроен в механику.

        else:
            # --- ОБЫЧНЫЙ РЕЖИМ ---
            target_options = ["None"]
            show_allies = False
            show_enemies = True

            if selected_card:
                flags = selected_card.flags if hasattr(selected_card, 'flags') and selected_card.flags else []
                has_friendly = "friendly" in flags
                has_offensive = "offensive" in flags

                if has_friendly and has_offensive:
                    show_allies = True;
                    show_enemies = True
                elif has_friendly:
                    show_allies = True;
                    show_enemies = False
                else:
                    show_allies = False;
                    show_enemies = True

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
                        display_s = s_i + 1
                        target_options.append(f"E|{t_idx}:{s_i} | ⚔️ {target_unit.name} S{display_s} ({extra})")

            if show_allies:
                for t_idx, target_unit in enumerate(my_team):
                    if target_unit.is_dead(): continue
                    for s_i, slot_obj in enumerate(target_unit.active_slots):
                        t_spd = slot_obj['speed']
                        extra = "😵" if slot_obj.get('stunned') else f"Spd {t_spd}"
                        display_s = s_i + 1
                        target_options.append(f"A|{t_idx}:{s_i} | 🛡️ {target_unit.name} S{display_s} ({extra})")

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

            # --- ОПЦИИ (Aggro/Break) ---
            if selected_card:  # Показываем опции только если карта выбрана
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
                    st.markdown(f"<div style='text-align:center; height:30px;'>{icon_aggro}</div>",
                                unsafe_allow_html=True)

                    if slot.get('is_ally_target'):
                        c_opt1.checkbox("Aggro", value=False, disabled=True,
                                        key=f"{key_prefix}_{unit.name}_aggro_{slot_idx}", label_visibility="collapsed",
                                        on_change=save_cb)
                        if aggro_val: slot['is_aggro'] = False
                    elif can_redirect:
                        c_opt1.checkbox("Aggro", value=aggro_val, key=f"{key_prefix}_{unit.name}_aggro_{slot_idx}",
                                        label_visibility="collapsed",
                                        on_change=save_cb)
                    else:
                        c_opt1.checkbox("Aggro", value=False, disabled=True,
                                        key=f"{key_prefix}_{unit.name}_aggro_{slot_idx}", label_visibility="collapsed",
                                        on_change=save_cb)
                        if aggro_val: slot['is_aggro'] = False

                slot_destroy = slot.get('destroy_on_speed', True)
                with c_opt2:
                    icon_broken = get_icon_html("dice_broken", width=30)
                    st.markdown(f"<div style='text-align:center; height:30px;'>{icon_broken}</div>",
                                unsafe_allow_html=True)
                    new_destroy = st.checkbox("Break", value=slot_destroy,
                                              key=f"{key_prefix}_{unit.name}_destroy_{slot_idx}",
                                              label_visibility="collapsed",
                                              on_change=save_cb)
                    slot['destroy_on_speed'] = new_destroy

        # --- ИНФОРМАЦИЯ О КАРТЕ ---
        if selected_card:
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
                    # Если она есть, мы не добавляем стандартные бонусы статов, а используем Удачу.
                    override_active = False
                    if "source_access" in unit.passives or "source_access" in unit.talents:
                        override_active = True
                        # Добавляем бонус от Удачи (Luck / 5)
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

                        # Статусы и прочее работают поверх
                        bonus += unit.get_status("strength")
                        bonus += unit.get_status("power_up")
                        bonus -= unit.get_status("weakness")

                        # Бонус оружия
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