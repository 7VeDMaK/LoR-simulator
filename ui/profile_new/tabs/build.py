import streamlit as st
from collections import Counter
from core.library import Library
from core.unit.unit_library import UnitLibrary

# Импортируем наши новые модули
from ui.profile_new.tabs.build_parts.styles import inject_build_tab_css
from ui.profile_new.tabs.build_parts.formatting import generate_card_html


def get_max_deck_size(unit) -> int:
    """
    Вычисляет максимальный размер колоды на основе уровня персонажа.
    
    Правила:
    - По умолчанию: 9 карт
    - 30+ уровень: 12 карт
    - 40+ уровень: 16 карт
    """
    level = getattr(unit, 'level', 1)
    
    if level >= 40:
        return 16
    elif level >= 30:
        return 12
    else:
        return 9


def render_build_tab(unit, is_edit_mode: bool):
    """
    Вкладка Колоды.
    """
    # 1. Подключаем CSS
    inject_build_tab_css()

    deck_ids = unit.deck
    counts = Counter(deck_ids)

    raw_cards_list = Library.get_all_cards()
    all_cards = {c.id: c for c in raw_cards_list}

    # --- CONTROLS ---
    c_filter, c_add = st.columns([2, 1])
    with c_filter:
        filter_opts = ["All", "0", "1", "2", "3", "4", "5+", "Item"]
        selected_filter = st.radio("Фильтр:", filter_opts, horizontal=True, label_visibility="collapsed")

    with c_add:
        if is_edit_mode:
            with st.popover("➕ Добавить карту", use_container_width=True):
                card_options = sorted(list(all_cards.keys()), key=lambda x: (getattr(all_cards[x], 'tier', 0),
                                                                             getattr(all_cards[x], 'name', '')))
                sel_card = st.selectbox(
                    "Поиск карты",
                    options=[""] + card_options,
                    format_func=lambda
                        x: f"[{getattr(all_cards[x], 'tier', '?')}] {getattr(all_cards[x], 'name', '?')}" if x in all_cards else "...",
                )
                if sel_card and sel_card in all_cards:
                    if st.button(f"Добавить", type="primary"):
                        unit.deck.append(sel_card)
                        UnitLibrary.save_unit(unit)
                        st.rerun()

    max_deck = get_max_deck_size(unit)
    count_color = "green" if len(deck_ids) == max_deck else "red"
    level_info = f" (Уровень {unit.level})" if hasattr(unit, 'level') else ""
    st.markdown(f"**Всего карт: :{count_color}[{len(deck_ids)}]** / {max_deck}{level_info}")
    st.divider()

    if not counts:
        st.info("Колода пуста.")
        return

    # --- FILTERING ---
    display_cards = [Library.get_card(cid) for cid in counts.keys() if Library.get_card(cid)]
    filtered_cards = []

    for card in display_cards:
        tier = getattr(card, 'tier', 0)
        ctype = getattr(card, 'type', getattr(card, 'card_type', '')).lower()

        if selected_filter == "All":
            filtered_cards.append(card)
        elif selected_filter == "Item":
            if any(x in ctype for x in ["item", "consumable", "ego"]): filtered_cards.append(card)
        elif selected_filter == "5+":
            if tier >= 5 and "item" not in ctype: filtered_cards.append(card)
        else:
            if str(tier) == selected_filter and "item" not in ctype: filtered_cards.append(card)

    filtered_cards.sort(key=lambda x: (getattr(x, 'tier', 0), getattr(x, 'name', '')))

    # --- RENDER GRID (2 COLUMNS) ---
    cols = st.columns(2)

    for i, card in enumerate(filtered_cards):
        col = cols[i % 2]
        count = counts[card.id]

        # Определяем стили рамки
        c_type = getattr(card, 'type', getattr(card, 'card_type', 'melee'))
        type_str = str(c_type).lower()

        border_cls = "border-melee"
        type_badge_cls = "type-melee"

        if "range" in type_str:
            border_cls = "border-ranged"
            type_badge_cls = "type-ranged"
        elif any(x in type_str for x in ["item", "consumable", "ego"]):
            border_cls = "border-item"
            type_badge_cls = "border-item"
        elif "defense" in type_str or "block" in type_str or "dodge" in type_str:
            border_cls = "border-defense"
            type_badge_cls = "border-defense"

        with col:
            # Генерация HTML через внешний модуль
            full_card_html = generate_card_html(card, border_cls, type_badge_cls)
            st.markdown(full_card_html, unsafe_allow_html=True)

            # CONTROLS
            if is_edit_mode:
                b1, b2, b3 = st.columns([1, 2, 1])
                if b1.button("➖", key=f"dec_{card.id}_{i}"):
                    unit.deck.remove(card.id)
                    UnitLibrary.save_unit(unit)
                    st.rerun()
                b2.markdown(f"<div style='text-align:center; font-weight:bold; margin-top:5px;'>x{count}</div>",
                            unsafe_allow_html=True)
                if b3.button("➕", key=f"inc_{card.id}_{i}"):
                    unit.deck.append(card.id)
                    UnitLibrary.save_unit(unit)
                    st.rerun()
            else:
                st.markdown(
                    f"<div style='text-align:right; font-size:12px; color:#666; margin-top:-5px; margin-bottom:10px;'>Количество: {count}</div>",
                    unsafe_allow_html=True)