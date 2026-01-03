import streamlit as st
from core.library import Library
from logic.passives import PASSIVE_REGISTRY
from logic.talents import TALENT_REGISTRY

def render_abilities(unit, u_key):
    # === DECK ===
    st.subheader("🃏 Боевая колода")
    all_library_cards = Library.get_all_cards()
    card_map = {c.id: c for c in all_library_cards}
    all_card_ids = [c.id for c in all_library_cards]

    valid_deck = [cid for cid in unit.deck if cid in card_map]

    sel_deck = st.multiselect(
        "Состав колоды:",
        options=all_card_ids,
        default=valid_deck,
        format_func=lambda x: f"{card_map[x].name} [{card_map[x].tier}]" if x in card_map else x,
        key=f"deck_sel_{u_key}"
    )
    if sel_deck != unit.deck:
        unit.deck = sel_deck

    st.caption(f"Всего карт: {len(unit.deck)}")

    st.markdown("---")

    # === ABILITIES ===
    st.subheader("🧬 Таланты и Пассивки")

    c_tal, c_desc = st.columns([2, 1])

    def fmt_name(aid):
        if aid in TALENT_REGISTRY: return f"★ {TALENT_REGISTRY[aid].name}"
        if aid in PASSIVE_REGISTRY: return f"🛡️ {PASSIVE_REGISTRY[aid].name}"
        return aid

    with c_tal:
        # Talents
        bonus_slots = int(unit.modifiers["talent_slots"]["flat"])
        max_talents = (unit.level // 3) + bonus_slots
        current_talents = [t for t in unit.talents if t in TALENT_REGISTRY]

        safe_limit = max(max_talents, len(current_talents))

        st.markdown(f"**Таланты ({len(unit.talents)} / {max_talents})**")

        # === FIX: Rerun on talent change to update stats ===
        new_talents = st.multiselect(
            "Список талантов",
            options=sorted(list(TALENT_REGISTRY.keys())),
            default=[t for t in unit.talents if t in TALENT_REGISTRY],
            format_func=fmt_name,
            max_selections=safe_limit,
            label_visibility="collapsed",
            key=f"mt_{u_key}"
        )
        if new_talents != [t for t in unit.talents if t in TALENT_REGISTRY]:
            # Preserve logic by keeping unknown talents (if any)
            old_unknowns = [t for t in unit.talents if t not in TALENT_REGISTRY]
            unit.talents = new_talents + old_unknowns
            unit.recalculate_stats()
            st.rerun()

        # Passives
        st.markdown("**Пассивки**")
        new_passives = st.multiselect(
            "Список пассивок",
            options=sorted(list(PASSIVE_REGISTRY.keys())),
            default=[p for p in unit.passives if p in PASSIVE_REGISTRY],
            format_func=fmt_name,
            label_visibility="collapsed",
            key=f"mp_{u_key}"
        )
        if new_passives != [p for p in unit.passives if p in PASSIVE_REGISTRY]:
            old_unknowns = [p for p in unit.passives if p not in PASSIVE_REGISTRY]
            unit.passives = new_passives + old_unknowns
            unit.recalculate_stats()
            st.rerun()

    with c_desc:
        st.info("ℹ️ **Эффекты:**")
        all_ids = unit.talents + unit.passives
        if not all_ids:
            st.caption("Пусто")
        for aid in all_ids:
            obj = TALENT_REGISTRY.get(aid) or PASSIVE_REGISTRY.get(aid)
            if obj:
                with st.expander(obj.name):
                    st.write(obj.description)