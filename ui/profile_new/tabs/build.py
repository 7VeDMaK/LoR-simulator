import streamlit as st


def render_build_tab(unit, is_edit_mode: bool):
    st.markdown("### 🎴 Боевая колода")

    if not unit.deck:
        st.info("Колода пуста.")
        if is_edit_mode:
            st.button("➕ Добавить карту")
        return

    # Сетка карт
    cols = st.columns(4)
    for i, card in enumerate(unit.deck):
        c = cols[i % 4]
        with c:
            # Карточка карты
            card_name = card.name if hasattr(card, 'name') else card.get('name', 'Card')
            card_cost = card.cost if hasattr(card, 'cost') else card.get('cost', 0)

            if is_edit_mode:
                st.button(f"{card_name} ({card_cost}) ✏️", key=f"deck_edit_{i}", use_container_width=True)
            else:
                st.button(f"{card_name}\n({card_cost})", key=f"deck_view_{i}", use_container_width=True)