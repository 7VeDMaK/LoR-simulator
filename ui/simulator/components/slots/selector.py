from collections import Counter

import streamlit as st

from core.library import Library
from ui.simulator.components.common import CARD_TYPE_ICONS


def render_card_selector(container, unit, slot, slot_idx, key_prefix):
    """
    Отрисовывает Selectbox для выбора карты из доступной колоды.
    """
    deck_ids = getattr(unit, 'deck', [])
    deck_counts = Counter(deck_ids)
    available_cards = []
    selected_card = slot.get('card')

    # Расчет доступных карт (исключая кулдауны и уже выбранные в других слотах)
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
            # Fallback если колоды нет (берем все из библиотеки)
            raw_cards = Library.get_all_cards()
            for c in raw_cards:
                if str(c.card_type).lower() != "item":
                    # [FIX] Проверка кулдауна: если список пуст или None, карта доступна
                    cds = unit.card_cooldowns.get(c.id)
                    is_on_cooldown = False
                    if cds:
                        if isinstance(cds, list):
                            is_on_cooldown = len(cds) > 0
                        elif isinstance(cds, int):
                            is_on_cooldown = cds > 0

                    if not is_on_cooldown:
                        available_cards.append(c)

    available_cards.sort(key=lambda x: (x.tier, x.name))

    # Подготовка списка для selectbox
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

    if slot.get('locked'):
        container.text_input("Page", value=selected_card.name if selected_card else "Locked", disabled=True,
                             label_visibility="collapsed")
    else:
        new_card = container.selectbox(
            "Page", display_cards,
            format_func=format_card_option,
            index=c_idx,
            key=f"{key_prefix}_{unit.name}_card_{slot_idx}",
            label_visibility="collapsed",
            on_change=st.session_state.get('save_callback')
        )
        slot['card'] = new_card