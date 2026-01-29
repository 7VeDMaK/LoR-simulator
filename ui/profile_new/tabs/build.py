import streamlit as st
from collections import Counter
from core.library import Library
from core.unit.unit_library import UnitLibrary


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (CSS & Render) ===

def _inject_custom_css():
    """CSS для компактности и стилизации карточек"""
    st.markdown("""
        <style>
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
            gap: 0.2rem;
        }
        .card-cost {
            display: inline-block;
            width: 24px;
            height: 24px;
            background-color: #ffd700;
            color: black;
            border-radius: 50%;
            text-align: center;
            font-weight: bold;
            line-height: 24px;
            margin-right: 8px;
            font-size: 14px;
        }
        .card-name {
            font-weight: bold;
            font-size: 14px;
            vertical-align: middle;
        }
        .dice-row {
            font-size: 13px;
            margin-top: 4px;
            margin-bottom: 4px;
            background: #2b2b2b;
            padding: 4px;
            border-radius: 4px;
        }
        .dice-slash { color: #ff6b6b; }
        .dice-pierce { color: #4ecdc4; }
        .dice-blunt { color: #45b7d1; }
        .dice-block { color: #5f27cd; }
        .dice-evade { color: #feca57; }

        .card-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 5px;
            border-top: 1px solid #444;
            padding-top: 5px;
        }
        </style>
    """, unsafe_allow_html=True)


def _get_dice_icon(dtype_name):
    dtype_name = dtype_name.lower()
    if "slash" in dtype_name: return "🗡️", "dice-slash"
    if "pierce" in dtype_name: return "🏹", "dice-pierce"
    if "blunt" in dtype_name: return "🔨", "dice-blunt"
    if "block" in dtype_name: return "🛡️", "dice-block"
    if "evade" in dtype_name: return "💨", "dice-evade"
    return "🎲", "dice-normal"


def _render_dice_visual(dice_list):
    html_parts = []
    if not dice_list:
        return "<span style='color:gray; font-size:12px;'>Нет кубиков</span>"

    for die in dice_list:
        d_min = die.min_val
        d_max = die.max_val

        d_type_name = "Attack"
        if hasattr(die, "dtype"):
            if hasattr(die.dtype, "name"):
                d_type_name = die.dtype.name
            else:
                d_type_name = str(die.dtype).split('.')[-1]

        icon, css_class = _get_dice_icon(d_type_name)
        html_parts.append(f"<span class='{css_class}'>{icon} {d_min}-{d_max}</span>")

    return " &nbsp;|&nbsp; ".join(html_parts)


# === ОСНОВНАЯ ФУНКЦИЯ ===

def render_build_tab(unit, is_edit_mode: bool):
    """
    Вкладка управления колодой (Компактная версия).
    """
    _inject_custom_css()

    deck_ids = unit.deck
    total_cards = len(deck_ids)
    counts = Counter(deck_ids)

    # 1. ПОЛУЧАЕМ ВСЕ КАРТЫ И ПРЕВРАЩАЕМ В СЛОВАРЬ (FIX)
    # Library.get_all_cards() возвращает список, нам нужен словарь для удобного поиска по ID
    raw_cards_list = Library.get_all_cards()
    all_cards = {c.id: c for c in raw_cards_list}

    # --- ВЕРХНЯЯ ПАНЕЛЬ: ФИЛЬТРЫ И ДОБАВЛЕНИЕ ---
    c_filter, c_add = st.columns([2, 1])

    with c_filter:
        filter_opts = ["All", "0", "1", "2", "3", "4", "5+", "Item"]
        selected_filter = st.radio("Фильтр по стоимости:", filter_opts, horizontal=True, label_visibility="collapsed")

    with c_add:
        if is_edit_mode:
            with st.popover("➕ Добавить карту", use_container_width=True):
                # Теперь all_cards - это словарь, и .keys() сработает
                card_options = sorted(list(all_cards.keys()), key=lambda x: (all_cards[x].tier, all_cards[x].name))

                sel_card = st.selectbox(
                    "Поиск карты",
                    options=[""] + card_options,
                    format_func=lambda x: f"[{all_cards[x].tier}] {all_cards[x].name}" if x in all_cards else "...",
                )
                if sel_card and sel_card in all_cards:
                    if st.button(f"Добавить {all_cards[sel_card].name}", type="primary"):
                        unit.deck.append(sel_card)
                        UnitLibrary.save_unit(unit)
                        st.rerun()

    st.markdown(f"**Всего карт: {total_cards}** / 9")
    st.divider()

    # --- ПОДГОТОВКА СПИСКА ---
    if not counts:
        st.info("Колода пуста.")
        return

    display_cards = []
    for cid in counts.keys():
        card = Library.get_card(cid)
        if card:
            display_cards.append(card)

    filtered_cards = []
    for card in display_cards:
        tier = card.tier
        ctype = card.card_type.lower() if hasattr(card, 'card_type') else ""

        if selected_filter == "All":
            filtered_cards.append(card)
        elif selected_filter == "Item":
            if "item" in ctype or "consumable" in ctype or "ego" in ctype:
                filtered_cards.append(card)
        elif selected_filter == "5+":
            if tier >= 5 and "item" not in ctype:
                filtered_cards.append(card)
        else:
            if str(tier) == selected_filter and "item" not in ctype:
                filtered_cards.append(card)

    if not filtered_cards:
        st.caption("Нет карт, соответствующих фильтру.")
        return

    filtered_cards.sort(key=lambda x: (x.tier, x.name))

    # --- ОТРИСОВКА (GRID 3 COLUMNS) ---
    cols = st.columns(3)

    for i, card in enumerate(filtered_cards):
        col = cols[i % 3]
        count = counts[card.id]

        with col:
            with st.container(border=True):
                # HEADER
                st.markdown(
                    f"""
                    <div>
                        <span class='card-cost'>{card.tier}</span>
                        <span class='card-name'>{card.name}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # DICE
                dice_html = _render_dice_visual(card.dice_list)
                st.markdown(f"<div class='dice-row'>{dice_html}</div>", unsafe_allow_html=True)

                # DESCRIPTION
                desc = card.description if card.description else "Нет описания"
                if len(desc) > 60:
                    st.caption(desc[:60] + "...", help=desc)
                else:
                    st.caption(desc)

                # CONTROLS
                if is_edit_mode:
                    c1, c2, c3 = st.columns([1, 2, 1])
                    if c1.button("➖", key=f"dec_{card.id}_{i}", help="Убрать копию"):
                        unit.deck.remove(card.id)
                        UnitLibrary.save_unit(unit)
                        st.rerun()

                    c2.markdown(f"<div style='text-align:center; font-weight:bold; margin-top:5px;'>x{count}</div>",
                                unsafe_allow_html=True)

                    if c3.button("➕", key=f"inc_{card.id}_{i}", help="Добавить копию"):
                        unit.deck.append(card.id)
                        UnitLibrary.save_unit(unit)
                        st.rerun()
                else:
                    st.markdown(
                        f"<div style='text-align:right; font-weight:bold; color:#aaa;'>Количество: {count}</div>",
                        unsafe_allow_html=True)