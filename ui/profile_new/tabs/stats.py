import streamlit as st
from core.unit.unit_library import UnitLibrary

# === КОНСТАНТЫ ===
ATTR_LABELS = {
    "strength": "Сила", "endurance": "Стойкость", "agility": "Ловкость",
    "wisdom": "Мудрость", "psych": "Психика"
}

SKILL_LABELS = {
    "strike_power": "Сила удара", "medicine": "Медицина", "willpower": "Сила воли",
    "acrobatics": "Акробатика", "shields": "Щиты",
    "tough_skin": "Крепкая кожа", "speed": "Скорость",
    "light_weapon": "Лёгкое оружие", "medium_weapon": "Среднее оружие",
    "heavy_weapon": "Тяжёлое оружие", "firearms": "Огнестрел",
    "eloquence": "Красноречие", "forging": "Ковка",
    "engineering": "Инженерия", "programming": "Программирование"
}


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def _get_mod_value(unit, key, default=0):
    """Получает итоговое значение модификатора."""
    val = unit.modifiers.get(key, default)
    if isinstance(val, dict):
        return val.get("flat", default)
    return val


def _render_value_diff(base, total, label=""):
    """Рисует значение с цветовой индикацией (зеленый/красный) если оно отличается от базы."""
    diff = total - base
    color = "white"
    arrow = ""

    if diff > 0:
        color = "#4ade80"  # green
        arrow = "▲"
    elif diff < 0:
        color = "#f87171"  # red
        arrow = "▼"

    st.markdown(
        f"""
        <div style="text-align: center;">
            <div style="color: #888; font-size: 12px;">{label}</div>
            <div style="font-size: 24px; font-weight: bold; color: {color};">
                {total} <span style="font-size: 14px;">{arrow}</span>
            </div>
            {f'<div style="font-size: 12px; color: #555;">(Base {base})</div>' if diff != 0 else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


# === ГЛАВНАЯ ФУНКЦИЯ ===
def render_stats_tab(unit, is_edit_mode: bool):
    """
    Вкладка Параметры (Attributes & Skills).
    """

    # --- 1. АТРИБУТЫ (5 колонок) ---
    st.markdown("### 🧬 Характеристики")
    cols = st.columns(5)

    for i, (key, label) in enumerate(ATTR_LABELS.items()):
        base_val = unit.attributes.get(key, 0)
        total_val = _get_mod_value(unit, key, base_val)

        with cols[i]:
            if is_edit_mode:
                st.caption(label)
                # Max value increased to 999
                new_val = st.number_input(f"Base {label}", 0, 999, base_val, key=f"attr_inp_{key}",
                                          label_visibility="collapsed")

                # Показываем превью итога
                if total_val != new_val:
                    st.caption(f"Итог: {total_val}")

                if new_val != base_val:
                    unit.attributes[key] = new_val
                    unit.recalculate_stats()  # Пересчет сразу для отображения
                    UnitLibrary.save_unit(unit)
                    st.rerun()
            else:
                _render_value_diff(base_val, total_val, label)

    st.divider()

    # --- 2. УДАЧА ---
    st.markdown("### 🍀 Удача")
    c_luck1, c_luck2, _ = st.columns([1, 1, 2])

    # Luck Skill
    base_luck = unit.skills.get("luck", 0)
    total_luck = _get_mod_value(unit, "luck", base_luck)

    with c_luck1:
        if is_edit_mode:
            st.caption("Навык Удачи")
            # Max value increased to 999
            new_luck = st.number_input("Luck Skill", 0, 999, base_luck, key="luck_skill_inp")
            if new_luck != base_luck:
                unit.skills["luck"] = new_luck
                unit.recalculate_stats()
                UnitLibrary.save_unit(unit)
                st.rerun()
        else:
            _render_value_diff(base_luck, total_luck, "Навык Удачи")

    # Luck Resource (Current Points)
    cur_luck = unit.resources.get("luck", 0)
    with c_luck2:
        if is_edit_mode:
            st.caption("Очки Удачи (Текущие)")
            # Max value increased to 999
            new_cur = st.number_input("Cur Luck", -10, 999, cur_luck, key="luck_res_inp")
            if new_cur != cur_luck:
                unit.resources["luck"] = new_cur
                UnitLibrary.save_unit(unit)  # Тут рекальк не нужен
                st.rerun()
        else:
            st.metric("Очки Удачи", cur_luck, help="Расходуемый ресурс")

    st.divider()

    # --- 3. НАВЫКИ (SKILLS) ---
    st.markdown("### 📚 Навыки")

    # Разбиваем на 3 колонки
    scols = st.columns(3)
    skill_keys = list(SKILL_LABELS.keys())

    for i, key in enumerate(skill_keys):
        label = SKILL_LABELS[key]
        col = scols[i % 3]

        base_val = unit.skills.get(key, 0)
        total_val = _get_mod_value(unit, key, base_val)

        with col:
            if is_edit_mode:
                # Режим редактирования: инпут + подпись
                c1, c2 = st.columns([2, 1])
                c1.markdown(f"**{label}**")
                # Max value increased to 999
                new_s = c2.number_input(label, 0, 999, base_val, key=f"skill_{key}", label_visibility="collapsed")

                if new_s != base_val:
                    unit.skills[key] = new_s
                    unit.recalculate_stats()
                    UnitLibrary.save_unit(unit)
                    st.rerun()
            else:
                # Режим просмотра
                val_color = "white"
                if total_val > base_val:
                    val_color = "#4ade80"
                elif total_val < base_val:
                    val_color = "#f87171"

                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding: 4px 0;">
                        <span>{label}</span>
                        <span style="color: {val_color}; font-weight: bold;">{total_val}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # --- 4. РУЧНЫЕ МОДИФИКАТОРЫ (Аугментации) ---
    if is_edit_mode:
        st.divider()
        with st.expander("💉 Ручные модификаторы (Аугментации)", expanded=False):
            st.info("Здесь можно вручную накинуть статов (например, от имплантов).")
            c_aug1, c_aug2, c_aug3 = st.columns(3)

            # HP
            with c_aug1:
                st.caption("HP Modifiers")
                nhf = st.number_input("HP Flat", -999, 999, value=unit.implants_hp_flat, key="imp_hp_f")
                nhp = st.number_input("HP %", -100, 999, value=unit.implants_hp_pct, key="imp_hp_p")
                if nhf != unit.implants_hp_flat or nhp != unit.implants_hp_pct:
                    unit.implants_hp_flat = nhf
                    unit.implants_hp_pct = nhp
                    unit.recalculate_stats()
                    UnitLibrary.save_unit(unit)
                    st.rerun()

            # SP
            with c_aug2:
                st.caption("SP Modifiers")
                nsf = st.number_input("SP Flat", -999, 999, value=unit.implants_sp_flat, key="imp_sp_f")
                nsp = st.number_input("SP %", -100, 999, value=unit.implants_sp_pct, key="imp_sp_p")
                if nsf != unit.implants_sp_flat or nsp != unit.implants_sp_pct:
                    unit.implants_sp_flat = nsf
                    unit.implants_sp_pct = nsp
                    unit.recalculate_stats()
                    UnitLibrary.save_unit(unit)
                    st.rerun()

            # Stagger
            with c_aug3:
                st.caption("Stagger Modifiers")
                nstf = st.number_input("Stg Flat", -999, 999, value=unit.implants_stagger_flat, key="imp_stg_f")
                nstp = st.number_input("Stg %", -100, 999, value=unit.implants_stagger_pct, key="imp_stg_p")
                if nstf != unit.implants_stagger_flat or nstp != unit.implants_stagger_pct:
                    unit.implants_stagger_flat = nstf
                    unit.implants_stagger_pct = nstp
                    unit.recalculate_stats()
                    UnitLibrary.save_unit(unit)
                    st.rerun()