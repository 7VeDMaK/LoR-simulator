import streamlit as st
from collections import Counter
from core.library import Library
from logic.character_changing.passives import PASSIVE_REGISTRY
from logic.character_changing.talents import TALENT_REGISTRY


def render_abilities(unit, u_key):
    # === DECK ===
    st.subheader("🃏 Боевая колода")
    all_library_cards = Library.get_all_cards()

    # === [ДОБАВЛЕНО] Сортировка: Сначала по Тиру (1->5), потом по Имени ===
    all_library_cards.sort(key=lambda x: (x.tier, x.name))
    # ======================================================================

    card_map = {c.id: c for c in all_library_cards}
    all_card_ids = [c.id for c in all_library_cards]

    # 1. Считаем текущее количество каждой карты в колоде юнита
    current_counts = Counter(unit.deck)

    # Уникальные ID, которые уже есть в колоде (для дефолтного выбора в мультиселекте)
    # Фильтруем, чтобы не упало, если карты удалили из базы
    valid_unique_ids = [cid for cid in current_counts.keys() if cid in card_map]

    # 2. Мультиселект для выбора ТИПОВ карт (без дублей)
    selected_unique_ids = st.multiselect(
        "Выберите карты для колоды:",
        options=all_card_ids,
        default=valid_unique_ids,
        format_func=lambda x: f"{card_map[x].name} [{card_map[x].tier}]" if x in card_map else x,
        key=f"deck_sel_{u_key}"
    )

    # 3. Настройка КОЛИЧЕСТВА копий (x1, x2, x3)
    new_deck_list = []

    if selected_unique_ids:
        st.caption("Настройка количества копий (Макс 3):")

        # Разбиваем на колонки для компактности
        cols = st.columns(3)

        for idx, cid in enumerate(selected_unique_ids):
            card_obj = card_map.get(cid)
            if not card_obj: continue

            col = cols[idx % 3]

            with col:
                # Получаем текущее кол-во или ставим 1 по умолчанию
                default_qty = current_counts[cid] if current_counts[cid] > 0 else 1

                qty = st.number_input(
                    f"{card_obj.name}",
                    min_value=1,
                    max_value=3,  # Ограничение как в LoR
                    value=default_qty,
                    key=f"qty_{u_key}_{cid}",
                    label_visibility="visible"
                )

                # Добавляем в итоговый список нужное количество раз
                new_deck_list.extend([cid] * qty)

    # 4. Сохранение изменений
    # Проверяем, изменился ли состав колоды
    # Сортируем списки для корректного сравнения (порядок не важен для движка, важен состав)
    if sorted(unit.deck) != sorted(new_deck_list):
        unit.deck = new_deck_list
        # Автосохранение происходит при нажатии кнопок или смене фокуса,
        # но для надежности можно вызвать пересчет
        # unit.recalculate_stats()

    # Визуализация итогового размера
    count_color = "green" if len(unit.deck) == 9 else "red"
    st.markdown(f"**Итого карт: :{count_color}[{len(unit.deck)}]** (Рекомендуется 9)")

    st.markdown("---")

    # === ABILITIES (Talents & Passives) ===
    # (Оставляем этот блок без изменений, как был у вас)
    st.subheader("🧬 Таланты и Пассивки")

    c_tal, c_desc = st.columns([2, 1])

    def fmt_name(aid):
        if aid in TALENT_REGISTRY: return f"★ {TALENT_REGISTRY[aid].name}"
        if aid in PASSIVE_REGISTRY: return f"🛡️ {PASSIVE_REGISTRY[aid].name}"
        return aid

    with c_tal:
        # --- TALENTS ---
        bonus_slots = int(unit.modifiers["talent_slots"]["flat"])
        max_talents = (unit.level // 3) + bonus_slots
        if max_talents < 0: max_talents = 0

        current_talents = [t for t in unit.talents if t in TALENT_REGISTRY]
        talents_key = f"mt_{u_key}"
        session_selection = st.session_state.get(talents_key, [])
        safe_limit = max(max_talents, len(current_talents), len(session_selection))

        st.markdown(f"**Таланты ({len(current_talents)} / {max_talents})**")

        if len(current_talents) > max_talents:
            st.warning(f"⚠️ Лимит превышен! Доступно: {max_talents}")

        new_talents = st.multiselect(
            "Список талантов",
            options=sorted(list(TALENT_REGISTRY.keys())),
            default=current_talents,
            format_func=fmt_name,
            max_selections=safe_limit,
            label_visibility="collapsed",
            key=talents_key
        )

        if new_talents != current_talents:
            old_unknowns = [t for t in unit.talents if t not in TALENT_REGISTRY]
            unit.talents = new_talents + old_unknowns
            unit.recalculate_stats()
            st.rerun()

        # --- PASSIVES ---
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