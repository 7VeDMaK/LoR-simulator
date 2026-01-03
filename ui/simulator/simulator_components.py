import streamlit as st
from core.library import Library
from logic.passives.__init__ import PASSIVE_REGISTRY
from logic.talents import TALENT_REGISTRY
from logic.weapon_definitions import WEAPON_REGISTRY
from ui.components import _format_script_text
from ui.styles import TYPE_ICONS, TYPE_COLORS


def render_slot_strip(unit, opposing_team, my_team, slot_idx, key_prefix):
    """
    Рендерит полоску одного слота действий.
    unit: Текущий юнит (Source)
    opposing_team: Список юнитов противника (List[Unit])
    """
    slot = unit.active_slots[slot_idx]

    # --- 1. ПРОВЕРКА ОГЛУШЕНИЯ (STAGGER) ---
    if slot.get('stunned'):
        st.error(f"😵 **STAGGERED** (Speed 0)")
        return

    # --- 2. ЗАГОЛОВОК (HEADER) ---
    speed = slot['speed']
    ui_stat = slot.get('ui_status', {"text": "...", "icon": "", "color": "gray"})

    # Текущая карта
    selected_card = slot.get('card')
    card_name = f"🃏 {selected_card.name}" if selected_card else "⛔ Пусто"

    # Скорость и эффекты
    spd_label = f"🎲{speed}"
    if slot.get("source_effect"):
        spd_label += f" ({slot.get('source_effect')})"

    lock_icon = "🔒 " if slot.get('locked') else ""

    # === ФОРМИРОВАНИЕ СПИСКА КАРТ ===
    available_cards = []
    if not slot.get('locked'):
        deck_ids = getattr(unit, 'deck', [])
        # Если есть колода - берем из нее, иначе все карты
        raw_cards = [Library.get_card(cid) for cid in deck_ids] if deck_ids else Library.get_all_cards()

        # Фильтрация по кулдауну (CD)
        for c in raw_cards:
            cd_left = unit.card_cooldowns.get(c.id, 0)
            if cd_left > 0:
                # Можно добавлять с пометкой, но пока просто пропускаем для чистоты UI
                pass
            else:
                available_cards.append(c)

    # Лейбл для экспандера
    label = f"{lock_icon}S{slot_idx + 1} ({spd_label}) | {ui_stat['icon']} {ui_stat['text']} | {card_name}"

    # --- 3. ИНТЕРФЕЙС ВЫБОРА (EXPANDER) ---
    with st.expander(label, expanded=False):
        c_tgt, c_sel = st.columns([1, 1])

        # === ЛОГИКА ВЫБОРА ЦЕЛИ ===
        target_options = ["None"]

        # Проверяем флаг карты на дружественность
        is_friendly = False
        if selected_card and "friendly" in selected_card.flags:
            is_friendly = True
            # Сохраняем флаг в слоте, чтобы движок знал, где искать цель
            slot['is_ally_target'] = True
        else:
            slot['is_ally_target'] = False

        # Формируем список целей в зависимости от флага
        team_to_show = my_team if is_friendly else opposing_team

        has_taunt = False
        if not is_friendly:
            has_taunt = any(u.get_status("taunt") > 0 for u in team_to_show if not u.is_dead())

        for t_idx, target_unit in enumerate(team_to_show):
            if target_unit.is_dead(): continue

            if target_unit.get_status("invisibility") > 0:
                continue

            # === ФИЛЬТР ПРОВОКАЦИИ ===
            # Если есть провокатор, а текущий юнит БЕЗ провокации — пропускаем его
            if has_taunt and target_unit.get_status("taunt") <= 0:
                continue

            # Теперь показываем слоты и для союзников, и для врагов
            for s_i, slot_obj in enumerate(target_unit.active_slots):
                t_spd = slot_obj['speed']
                extra = "😵" if slot_obj.get('stunned') else f"Spd {t_spd}"

                # Метка (Ally) для ясности
                tag = "(Ally)" if is_friendly else ""

                # Формат: "idx:slot | Name Tag S# (Spd)"
                opt_str = f"{t_idx}:{s_i} | {target_unit.name} {tag} S{s_i + 1} ({extra})"
                target_options.append(opt_str)

        # Определяем текущий выбор
        cur_t_unit = slot.get('target_unit_idx', -1)
        cur_t_slot = slot.get('target_slot_idx', -1)

        current_val_str = "None"
        if cur_t_unit != -1 and cur_t_slot != -1:
            prefix = f"{cur_t_unit}:{cur_t_slot}"
            # Ищем совпадение в опциях
            for opt in target_options:
                if opt.startswith(prefix):
                    current_val_str = opt
                    break

        # Виджет Selectbox
        selected_tgt_str = c_tgt.selectbox(
            "Target", target_options,
            index=target_options.index(current_val_str) if current_val_str in target_options else 0,
            key=f"{key_prefix}_{unit.name}_tgt_{slot_idx}",  # Уникальный ключ
            label_visibility="collapsed"
        )

        # Сохранение выбора в слот
        if selected_tgt_str == "None":
            slot['target_unit_idx'] = -1
            slot['target_slot_idx'] = -1
        else:
            # Парсим строку "0:1 | Name..."
            parts = selected_tgt_str.split('|')[0].strip().split(':')
            slot['target_unit_idx'] = int(parts[0])
            slot['target_slot_idx'] = int(parts[1])

        # === B. ВЫБОР КАРТЫ (PAGE) ===
        if slot.get('locked'):
            c_sel.text_input(
                "Page",
                value=selected_card.name if selected_card else "Locked",
                disabled=True,
                label_visibility="collapsed"
            )
        else:
            display_cards = [None] + available_cards
            # Находим индекс текущей карты
            c_idx = 0
            if selected_card:
                for idx, c in enumerate(display_cards):
                    if c and (c.id == selected_card.id or c.name == selected_card.name):
                        c_idx = idx
                        break

            new_card = c_sel.selectbox(
                "Page", display_cards,
                format_func=lambda x: x.name if x else "⛔ Пусто",
                index=c_idx,
                key=f"{key_prefix}_{unit.name}_card_{slot_idx}",
                label_visibility="collapsed"
            )
            slot['card'] = new_card

        # === СТРОКА 2: Опции (Чекбоксы) ===

        # Попытка определить скорость врага для валидации Aggro
        can_redirect = True
        enemy_spd_val = 0
        has_athletic = ("athletic" in unit.talents) or ("athletic" in unit.passives)

        if selected_tgt_str != "None":
            # Парсим строку вида "0:1 | Name S2 (Spd 5)"
            try:
                # Ищем "Spd " и берем число после него
                import re
                match = re.search(r"Spd (\d+)", selected_tgt_str)
                if match:
                    enemy_spd_val = int(match.group(1))

                    if has_athletic:
                        # С талантом: Можно если >=
                        if speed < enemy_spd_val:
                            can_redirect = False
                    else:
                        # Без таланта: Нужно строго >
                        if speed <= enemy_spd_val:
                            can_redirect = False
            except:
                pass

        _, c_opt1, c_opt2 = st.columns([2.5, 1, 1])

        # ЧЕКБОКС AGGRO
        aggro_val = slot.get('is_aggro', False)

        if can_redirect:
            # Если можем перехватить - показываем рабочий чекбокс
            c_opt1.checkbox("✋", value=aggro_val,
                            key=f"{key_prefix}_{unit.name}_aggro_{slot_idx}",
                            help=f"Aggro (Моя Spd {speed} > Врага {enemy_spd_val})")
        else:
            # Если не можем - показываем выключенный или просто текст
            # Чтобы не ломать структуру ключей, рисуем disabled чекбокс, но значение force False
            c_opt1.checkbox("✋", value=False, disabled=True,
                            key=f"{key_prefix}_{unit.name}_aggro_{slot_idx}",
                            help=f"Слишком медленный для перехвата! ({speed} <= {enemy_spd_val})")
            # Сбрасываем значение в слоте, чтобы логика не сработала
            if aggro_val:
                slot['is_aggro'] = False

        slot_destroy = slot.get('destroy_on_speed', True)
        new_destroy = c_opt2.checkbox("💥", value=slot_destroy,
                                      key=f"{key_prefix}_{unit.name}_destroy_{slot_idx}",
                                      help="Разрушать карту врага при разнице скорости 8+? (Если выключено -> Враг получит Помеху)")
        slot['destroy_on_speed'] = new_destroy

        st.divider()

        # --- 4. ИНФОРМАЦИЯ О КАРТЕ ---
        if selected_card:
            # Кубики
            if selected_card.dice_list:
                dice_display = []
                for d in selected_card.dice_list:
                    icon = TYPE_ICONS.get(d.dtype, "?")
                    color = TYPE_COLORS.get(d.dtype, "black")
                    dice_display.append(f":{color}[{icon} {d.min_val}-{d.max_val}]")
                st.markdown(" ".join(dice_display))

            # Скрипты (Описание эффектов)
            desc_text = []
            if "on_use" in selected_card.scripts:
                for s in selected_card.scripts["on_use"]:
                    desc_text.append(f"On Use: {_format_script_text(s['script_id'], s.get('params', {}))}")

            for d in selected_card.dice_list:
                if d.scripts:
                    for trig, effs in d.scripts.items():
                        for e in effs:
                            t_name = trig.replace("_", " ").title()
                            desc_text.append(f"{t_name}: {_format_script_text(e['script_id'], e.get('params', {}))}")

            if selected_card.description:
                st.caption(f"📝 {selected_card.description}")

            if desc_text:
                for line in desc_text:
                    st.caption(f"• {line}")

def render_active_abilities(unit, unit_key):
    abilities = []
    for pid in unit.passives:
        if pid in PASSIVE_REGISTRY: abilities.append((pid, PASSIVE_REGISTRY[pid]))
        # === ПАССИВКА ОРУЖИЯ (НОВОЕ) ===
    if unit.weapon_id in WEAPON_REGISTRY:
        wep = WEAPON_REGISTRY[unit.weapon_id]
        if wep.passive_id and wep.passive_id in PASSIVE_REGISTRY:
            # Добавляем в список способностей
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

                btn_label = "Activate"
                disabled = False
                if active_dur > 0:
                    btn_label = f"Active ({active_dur})"; disabled = True
                elif cd > 0:
                    btn_label = f"Cooldown ({cd})"; disabled = True

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
    """
    Рендерит секцию инвентаря с предметами (CardType.ITEM).
    """
    # Фильтруем карты в колоде, оставляя только предметы
    inventory_cards = []
    if unit.deck:
        for cid in unit.deck:
            card = Library.get_card(cid)
            # Проверяем тип
            if card and str(card.card_type).lower() == "item":
                inventory_cards.append(card)

    if not inventory_cards:
        return

    with st.expander("🎒 Inventory (Consumables)", expanded=False):
        for card in inventory_cards:
            btn_key = f"use_item_{unit_key}_{card.id}"
            desc = card.description if card.description else "No description"

            # Кнопка использования
            if st.button(f"💊 {card.name}", key=btn_key, help=desc, use_container_width=True):
                from ui.simulator.simulator_logic import use_item_action
                use_item_action(unit, card)
                st.rerun()