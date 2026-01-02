import streamlit as st
import os
from core.unit.unit import Unit
from core.unit.unit_library import UnitLibrary

def save_avatar_file(uploaded, unit_name):
    os.makedirs("data/avatars", exist_ok=True)
    safe = "".join(c for c in unit_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
    path = f"data/avatars/{safe}.{uploaded.name.split('.')[-1]}"
    with open(path, "wb") as f: f.write(uploaded.getbuffer())
    return path

def render_header(roster):
    # --- HEADER / SELECTION ---
    c1, c2 = st.columns([3, 1])

    # FIRST check the button (to update state before rendering selector)
    if c2.button("➕ Новый"):
        n = f"Unit_{len(roster) + 1}"
        u = Unit(n)
        roster[n] = u
        UnitLibrary.save_unit(u)

        # Update selection to the new character
        st.session_state["profile_unit_selector"] = n

        # Reload page to apply changes
        st.rerun()

    # THEN draw the selector (it picks up value from session_state)
    sel = c1.selectbox("Персонаж", list(roster.keys()), key="profile_unit_selector")
    unit = roster[sel]
    u_key = unit.name.replace(" ", "_")

    if st.button("💾 СОХРАНИТЬ ПРОФИЛЬ", type="primary", width='stretch', key=f"save_btn_{u_key}"):
        UnitLibrary.save_unit(unit)
        st.toast("Данные персонажа сохранены!", icon="✅")

    st.divider()
    return unit, u_key

def render_basic_info(unit, u_key):
    # Avatar
    img = unit.avatar if unit.avatar and os.path.exists(
        unit.avatar) else "https://placehold.co/150x150/png?text=No+Image"
    st.image(img, width='stretch')
    upl = st.file_uploader("Загрузить арт", type=['png', 'jpg'], label_visibility="collapsed", key=f"upl_{u_key}")
    if upl:
        unit.avatar = save_avatar_file(upl, unit.name)
        UnitLibrary.save_unit(unit)
        st.rerun()

    # Basic Data
    unit.name = st.text_input("Имя", unit.name, key=f"name_{u_key}")

    c_lvl, c_int = st.columns(2)
    unit.level = c_lvl.number_input("Уровень", 1, 100, unit.level, key=f"lvl_{u_key}")

    # Интеллект
    # === FIX: Добавлена проверка на изменение ===
    new_int = c_int.number_input("Баз. Инт.", 1, 30, unit.base_intellect, key=f"base_int_{u_key}")
    if new_int != unit.base_intellect:
        unit.base_intellect = new_int
        unit.recalculate_stats()
        st.rerun()

    # === ИСПРАВЛЕНИЕ: Чтение из новой структуры modifiers ===
    # Раньше было: unit.modifiers.get("total_intellect", ...)
    # Теперь там словарь {'flat': X, 'pct': Y}.

    total_int_data = unit.modifiers.get("total_intellect", {})
    if isinstance(total_int_data, dict):
        # Если это словарь, берем flat (интеллект обычно flat)
        total_int = total_int_data.get("flat", unit.base_intellect)
    else:
        # Если вдруг там старое число (совместимость)
        total_int = total_int_data if total_int_data else unit.base_intellect

    # Сравниваем числа
    if total_int > unit.base_intellect:
        st.info(f"🧠 Интеллект: **{total_int}** (+{total_int - unit.base_intellect})")
    else:
        st.info(f"🧠 Интеллект: **{total_int}**")

    st.divider()

    # === RANK (Two slots) ===
    st.markdown("**Ранг Фиксера**")
    r_c1, r_c2 = st.columns(2)
    unit.rank = r_c1.number_input("Текущий", 1, 12, unit.rank, help="Официальный ранг", key=f"rank_cur_{u_key}")

    # Status Rank
    status_rank = unit.memory.get("status_rank", "9 (Fixer)")
    new_status = r_c2.text_input("Статус", status_rank, help="Ранг репутации", key=f"rank_stat_{u_key}")
    unit.memory["status_rank"] = new_status

    st.divider()

    # Speed
    st.markdown(f"**🧊 Скорость:**")
    if unit.computed_speed_dice:
        for d in unit.computed_speed_dice:
            st.markdown(f"- {d[0]}~{d[1]}")
    else:
        st.markdown(f"- {unit.base_speed_min}~{unit.base_speed_max}")

    st.divider()

    # === BIOGRAPHY AND NOTES ===
    with st.expander("📝 Биография и Заметки", expanded=False):
        unit.biography = st.text_area(
            "История персонажа",
            value=unit.biography,
            height=300,
            key=f"bio_{u_key}",
            help="Сюда можно писать квенту, инвентарь (мелочевку) или заметки."
        )