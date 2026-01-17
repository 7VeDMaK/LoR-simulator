import streamlit as st
from collections import Counter
from core.library import Library
from logic.character_changing.passives import PASSIVE_REGISTRY
from logic.character_changing.talents import TALENT_REGISTRY
from logic.weapon_definitions import WEAPON_REGISTRY
from ui.components import _format_script_text
from ui.icons import get_icon_html
from ui.styles import TYPE_ICONS, TYPE_COLORS

# Эмодзи для заголовков (так как там HTML не поддерживается)
CARD_TYPE_ICONS = {
    "melee": "⚔️", "ranged": "🏹", "on play": "⚡", "on_play": "⚡",
    "mass summation": "💥", "mass individual": "💥",
    "defensive": "🛡️", "offensive": "🗡️", "item": "💊"
}


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

    # Defensive: sometimes session state or external logic can set slot['card'] to
    # a raw id (str/int). Try to resolve it to a Card object via Library.get_card.
    if selected_card and not hasattr(selected_card, 'dice_list'):
        try:
            resolved = Library.get_card(selected_card)
            # Library.get_card returns a Card-like object; ensure it has dice_list
            if hasattr(resolved, 'dice_list'):
                slot['card'] = resolved
                selected_card = resolved
            else:
                slot['card'] = None
                selected_card = None
        except Exception:
            slot['card'] = None
            selected_card = None

    # Формируем заголовок для экспандера (только текст/эмодзи)
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

    # === [UPD] ПОДСЧЕТ ДОСТУПНЫХ КАРТ ===
    deck_ids = getattr(unit, 'deck', [])
    deck_counts = Counter(deck_ids)

    available_cards = []

    if not slot.get('locked'):
        if deck_ids:
            # 1. Считаем, какие карты заняты в ДРУГИХ слотах (которые мы выбираем прямо сейчас)
            used_in_others = Counter()
            for i, s in enumerate(unit.active_slots):
                if i == slot_idx: continue  # Пропускаем текущий слот
                if s.get('card'):
                    used_in_others[s['card'].id] += 1

            # 2. Формируем список доступных
            unique_ids = sorted(list(set(deck_ids)))

            for cid in unique_ids:
                # --- [FIX START] ---
                # Получаем количество копий в КД
                cooldowns_list = unit.card_cooldowns.get(cid, [])
                # Поддержка старого формата (на всякий случай)
                if isinstance(cooldowns_list, int): cooldowns_list = [cooldowns_list]

                # Количество копий на перезарядке
                copies_on_cooldown = len(cooldowns_list)

                # Общее количество этой карты в колоде
                total_owned = deck_counts[cid]

                # Сколько копий уже выбрано в других слотах в этом раунде
                currently_used_elsewhere = used_in_others[cid]

                # Формула доступности:
                # (Всего) - (На перезарядке) - (Занято в соседнем слоте) > 0
                if total_owned - copies_on_cooldown - currently_used_elsewhere > 0:
                    c_obj = Library.get_card(cid)
                    if c_obj and str(c_obj.card_type).lower() != "item":
                        available_cards.append(c_obj)
                # --- [FIX END] ---

        else:
            # Режим отладки (нет колоды): показываем всю библиотеку без ограничений
            raw_cards = Library.get_all_cards()
            for c in raw_cards:
                if str(c.card_type).lower() != "item":
                    if unit.card_cooldowns.get(c.id, 0) <= 0:
                        available_cards.append(c)

    available_cards.sort(key=lambda x: (x.tier, x.name))
    # --- 3. ИНТЕРФЕЙС ВЫБОРА (EXPANDER) ---
    with st.expander(label, expanded=False):
        c_tgt, c_sel = st.columns([1, 1])

        # =========================================================
        # === [NEW] ЛОГИКА ВЫБОРА ЦЕЛИ (ВРАГИ / СОЮЗНИКИ) ===
        # =========================================================
        target_options = ["None"]

        # 1. Определяем, кого показывать в списке
        show_allies = False
        show_enemies = True  # По умолчанию (обычная атака)

        if selected_card:
            # Безопасное получение флагов
            flags = selected_card.flags if hasattr(selected_card, 'flags') and selected_card.flags else []

            has_friendly = "friendly" in flags
            has_offensive = "offensive" in flags

            if has_friendly and has_offensive:
                # ОБА ФЛАГА: Показываем и врагов, и союзников
                show_allies = True
                show_enemies = True
            elif has_friendly:
                # Только поддержка
                show_allies = True
                show_enemies = False
            else:
                # Только атака
                show_allies = False
                show_enemies = True

        # 2. Формируем список опций

        # --- ВРАГИ ---
        if show_enemies:
            # Проверка провокации (Taunt) - если есть таунт, бить можно только его
            alive_enemies = [u for u in opposing_team if not u.is_dead()]
            has_taunt = any(u.get_status("taunt") > 0 for u in alive_enemies)

            for t_idx, target_unit in enumerate(opposing_team):
                if target_unit.is_dead(): continue
                if target_unit.get_status("invisibility") > 0: continue
                # Фильтр таунта
                if has_taunt and target_unit.get_status("taunt") <= 0: continue

                for s_i, slot_obj in enumerate(target_unit.active_slots):
                    t_spd = slot_obj['speed']
                    extra = "😵" if slot_obj.get('stunned') else f"Spd {t_spd}"
                    display_s = s_i + 1
                    # Маркер E| (Enemy) + Иконка меча
                    target_options.append(f"E|{t_idx}:{s_i} | ⚔️ {target_unit.name} S{display_s} ({extra})")

        # --- СОЮЗНИКИ ---
        if show_allies:
            for t_idx, target_unit in enumerate(my_team):
                if target_unit.is_dead(): continue

                for s_i, slot_obj in enumerate(target_unit.active_slots):
                    t_spd = slot_obj['speed']
                    extra = "😵" if slot_obj.get('stunned') else f"Spd {t_spd}"
                    display_s = s_i + 1
                    # Маркер A| (Ally) + Иконка щита
                    target_options.append(f"A|{t_idx}:{s_i} | 🛡️ {target_unit.name} S{display_s} ({extra})")

        # 3. Восстановление текущего выбора из session state
        cur_t_unit = slot.get('target_unit_idx', -1)
        cur_t_slot = slot.get('target_slot_idx', -1)
        cur_is_ally = slot.get('is_ally_target', False)

        current_val_str = "None"

        if cur_t_unit != -1 and cur_t_slot != -1:
            # Ищем опцию, которая совпадает по ID и Типу (A или E)
            prefix_type = "A" if cur_is_ally else "E"
            search_prefix = f"{prefix_type}|{cur_t_unit}:{cur_t_slot}"

            for opt in target_options:
                if opt.startswith(search_prefix):
                    current_val_str = opt
                    break

        idx_sel = target_options.index(current_val_str) if current_val_str in target_options else 0

        selected_tgt_str = c_tgt.selectbox(
            "Target",
            target_options,
            index=idx_sel,
            key=f"{key_prefix}_{unit.name}_tgt_{slot_idx}",
            label_visibility="collapsed"
        )

        # 4. Сохранение выбора в слот
        if selected_tgt_str == "None":
            slot['target_unit_idx'] = -1
            slot['target_slot_idx'] = -1
            slot['is_ally_target'] = False  # Сброс
        else:
            try:
                # Разбираем строку вида "E|0:0 | ⚔️ Enemy..."
                meta_part, label_part = selected_tgt_str.split('|', 1)
                team_type = meta_part.strip()  # "A" или "E"
                coords = label_part.split('|')[0].strip().split(':')

                slot['target_unit_idx'] = int(coords[0])
                slot['target_slot_idx'] = int(coords[1])

                # Устанавливаем флаг: если тип "A", значит это союзник
                slot['is_ally_target'] = (team_type == "A")

            except:
                # Если что-то пошло не так при парсинге
                slot['target_unit_idx'] = -1
                slot['target_slot_idx'] = -1

        # === ВЫБОР КАРТЫ ===
        if slot.get('locked'):
            c_sel.text_input("Page", value=selected_card.name if selected_card else "Locked", disabled=True,
                             label_visibility="collapsed")
        else:
            display_cards = [None] + available_cards
            c_idx = 0

            # Если текущая карта все еще в списке доступных (или была выбрана ранее), ставим её как default
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

                # Показываем (xN), если есть колода
                if deck_ids:
                    count = deck_counts.get(x.id, 0)
                    return f"{emoji} [{x.tier}] {x.name} (x{count})"

                return f"{emoji} [{x.tier}] {x.name}"

            # Виджет выбора
            new_card = c_sel.selectbox("Page", display_cards, format_func=format_card_option, index=c_idx,
                                       key=f"{key_prefix}_{unit.name}_card_{slot_idx}", label_visibility="collapsed")

            # Применяем выбор
            slot['card'] = new_card

            # === СТРОКА 2: Опции (Чекбоксы с Картинками) ===
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

                # === [NEW] ЛОГИКА ЧЕКБОКСА AGGRO ===
                if slot.get('is_ally_target'):
                    # 1. Если цель - союзник, перехват невозможен
                    c_opt1.checkbox("Aggro", value=False, disabled=True,
                                    key=f"{key_prefix}_{unit.name}_aggro_{slot_idx}",
                                    help="Нельзя перехватить союзника", label_visibility="collapsed")
                    # Сбрасываем флаг, если он был случайно включен
                    if aggro_val: slot['is_aggro'] = False

                elif can_redirect:
                    # 2. Если цель - враг и скорости достаточно -> Можно
                    c_opt1.checkbox("Aggro", value=aggro_val, key=f"{key_prefix}_{unit.name}_aggro_{slot_idx}",
                                    help=f"Перехватить (Моя Spd {speed} > Врага {enemy_spd_val})",
                                    label_visibility="collapsed")
                else:
                    # 3. Если цель - враг, но скорости мало -> Нельзя
                    c_opt1.checkbox("Aggro", value=False, disabled=True,
                                    key=f"{key_prefix}_{unit.name}_aggro_{slot_idx}",
                                    help=f"Слишком медленный для перехвата! ({speed} <= {enemy_spd_val})",
                                    label_visibility="collapsed")
                    if aggro_val: slot['is_aggro'] = False

            slot_destroy = slot.get('destroy_on_speed', True)
            with c_opt2:
                icon_broken = get_icon_html("dice_broken", width=30)
                st.markdown(f"<div style='text-align:center; height:30px;'>{icon_broken}</div>", unsafe_allow_html=True)
                new_destroy = st.checkbox("Break", value=slot_destroy,
                                          key=f"{key_prefix}_{unit.name}_destroy_{slot_idx}",
                                          help="Разрушать карту врага при разнице скорости 8+?",
                                          label_visibility="collapsed")
                slot['destroy_on_speed'] = new_destroy

        # === 4. ИНФОРМАЦИЯ О КАРТЕ (С ИКОНКАМИ) ===
        if selected_card:
            # Ранг (картинка)
            rank_icon = get_icon_html(f"tier_{selected_card.tier}", width=24)
            # Тип (картинка)
            c_type_key = str(selected_card.card_type).lower()
            type_icon = get_icon_html(c_type_key, width=24)

            # Выводим: [ИконкаРанга] Ранг | [ИконкаТипа] Тип
            st.markdown(
                f"{rank_icon} **{selected_card.tier}** | {type_icon} **{c_type_key.capitalize()}**",
                unsafe_allow_html=True
            )

            # Кубики
            if selected_card.dice_list:
                dice_display = []
                for d in selected_card.dice_list:
                    color = TYPE_COLORS.get(d.dtype, "black")
                    dtype_key = d.dtype.name.lower()
                    if getattr(d, 'is_counter', False): dtype_key = f"counter_{dtype_key}"
                    icon_html = get_icon_html(dtype_key, width=20)
                    dice_display.append(f"{icon_html} :{color}[**{d.min_val}-{d.max_val}**]")
                st.markdown(" ".join(dice_display), unsafe_allow_html=True)

            # Эффекты
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

            if selected_card.description:
                st.caption(f"📝 {selected_card.description}")

            if desc_text:
                for line in desc_text:
                    st.caption(f"• {line}", unsafe_allow_html=True)


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
                    selected_opt = st.selectbox("Effect", options.keys(), key=f"sel_{unit_key}_{pid}",
                                                label_visibility="collapsed")

                btn_label = "Activate";
                disabled = False
                if active_dur > 0:
                    btn_label = f"Active ({active_dur})";
                    disabled = True
                elif cd > 0:
                    btn_label = f"Cooldown ({cd})";
                    disabled = True

                if st.button(f"✨ {btn_label}", key=f"act_{unit_key}_{pid}", disabled=disabled,
                             use_container_width=True):
                    def log_f(msg):
                        st.session_state.get('battle_logs', []).append(
                            {"round": "Skill", "rolls": "Activate", "details": msg})

                    if options:
                        if obj.activate(unit, log_f, choice_key=selected_opt): st.rerun()
                    else:
                        if obj.activate(unit, log_f): st.rerun()
    if has_actives: st.caption("Active Abilities")


def render_inventory(unit, unit_key):
    inventory_cards = []
    if unit.deck:
        for cid in unit.deck:
            card = Library.get_card(cid)
            if card and str(card.card_type).lower() == "item":
                inventory_cards.append(card)

    deck_counts = Counter(unit.deck)

    if not inventory_cards: return

    with st.expander("🎒 Inventory (Consumables)", expanded=False):
        # Используем set для уникальных карт, чтобы не рисовать 3 кнопки "Аптечка"
        seen_items = set()

        for card in inventory_cards:
            if card.id in seen_items: continue
            seen_items.add(card.id)

            btn_key = f"use_item_{unit_key}_{card.id}"
            desc = card.description if card.description else "No description"

            # [FIX] Логика кулдауна предметов
            cooldowns_list = unit.card_cooldowns.get(card.id, [])
            if isinstance(cooldowns_list, int): cooldowns_list = [cooldowns_list]

            copies_on_cd = len(cooldowns_list)
            total_copies = deck_counts[card.id]
            available_copies = total_copies - copies_on_cd

            if available_copies <= 0:
                # Все копии в КД. Берем максимальный таймер для отображения
                max_cd = max(cooldowns_list) if cooldowns_list else 0
                st.button(
                    f"⏳ {card.name} ({max_cd})",
                    key=btn_key,
                    disabled=True,
                    use_container_width=True,
                    help=f"{desc}\n\n(Все копии на перезарядке)"
                )
            else:
                # Есть доступные копии
                label = f"💊 {card.name}"
                if total_copies > 1:
                    label += f" ({available_copies}/{total_copies})"

                if st.button(label, key=btn_key, help=desc, use_container_width=True):
                    from ui.simulator.simulator_logic import use_item_action
                    use_item_action(unit, card)
                    st.rerun()