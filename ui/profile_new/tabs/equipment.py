import streamlit as st
from core.unit.unit_library import UnitLibrary
# Импорт реестров данных
from logic.weapon_definitions import WEAPON_REGISTRY
from logic.character_changing.augmentations.augmentations import AUGMENTATION_REGISTRY


def render_equipment_tab(unit, is_edit_mode: bool):
    """
    Вкладка Снаряжения: Оружие, Броня, Аугментации.
    """

    # === 1. ОРУЖИЕ (WEAPON) ===
    st.markdown("### ⚔️ Оружие")

    current_wep_id = unit.weapon_id
    # Проверка на валидность ID
    if current_wep_id not in WEAPON_REGISTRY:
        current_wep_id = "none"  # Fallback

    wep_obj = WEAPON_REGISTRY[current_wep_id]

    # Layout: Карточка слева, Детали/Селектор справа
    c_wep_l, c_wep_r = st.columns([1, 2])

    with c_wep_l:
        # Визуальная карточка
        with st.container(border=True):
            st.markdown(f"**{wep_obj.name}**")
            st.caption(f"Rank: {wep_obj.rank} | Type: {wep_obj.weapon_type.capitalize()}")

            # Отображение статов оружия
            if wep_obj.stats:
                stats_str = ", ".join([f"{k}: +{v}" for k, v in wep_obj.stats.items()])
                st.markdown(f"*{stats_str}*")
            else:
                st.caption("No stats modifiers")

    with c_wep_r:
        if is_edit_mode:
            # Селектор оружия
            wep_options = list(WEAPON_REGISTRY.keys())

            # Находим индекс текущего
            try:
                idx = wep_options.index(current_wep_id)
            except ValueError:
                idx = 0

            new_wep_id = st.selectbox(
                "Выбрать оружие",
                wep_options,
                index=idx,
                format_func=lambda x: f"{WEAPON_REGISTRY[x].name} (Rank {WEAPON_REGISTRY[x].rank})",
                label_visibility="collapsed"
            )

            if new_wep_id != current_wep_id:
                unit.weapon_id = new_wep_id
                unit.recalculate_stats()
                UnitLibrary.save_unit(unit)
                st.rerun()

            # Показываем описание выбранного (для справки при выборе)
            sel_obj = WEAPON_REGISTRY[new_wep_id]
            st.info(sel_obj.description)

        else:
            # Режим просмотра - просто описание
            st.markdown(wep_obj.description)
            if wep_obj.passive_id:
                st.caption(f"Grant Passive: {wep_obj.passive_id}")

    st.divider()

    # === 2. БРОНЯ (ARMOR) ===
    st.markdown("### 🛡️ Броня")
    # Пока реестра брони нет, используем текстовое поле и резисты

    c_arm_l, c_arm_r = st.columns([1, 2])

    with c_arm_l:
        if is_edit_mode:
            new_armor = st.text_input("Название брони", value=unit.armor_name)
            if new_armor != unit.armor_name:
                unit.armor_name = new_armor
                UnitLibrary.save_unit(unit)  # Save string only
        else:
            st.markdown(f"**{unit.armor_name if unit.armor_name else 'Без брони'}**")

    with c_arm_r:
        st.caption("Сопротивления (HP Resistances)")
        # Резисты (Slash / Pierce / Blunt)
        r1, r2, r3 = st.columns(3)

        # Получаем объект резистов (предполагаем, что это объект с полями slash, pierce, blunt)
        # В UnitData это обычно unit.hp_resists
        resists = unit.hp_resists if hasattr(unit, 'hp_resists') else None

        if resists:
            # Helper to render/edit resist
            def _res_field(col, label, val_attr):
                val = getattr(resists, val_attr, 1.0)
                if is_edit_mode:
                    new_val = col.number_input(label, 0.1, 3.0, val, 0.1, key=f"res_{val_attr}")
                    if new_val != val:
                        setattr(resists, val_attr, new_val)
                        UnitLibrary.save_unit(unit)  # Нужно сохранять структуру
                else:
                    color = "white"
                    if val < 1.0:
                        color = "#4ade80"  # Resist
                    elif val > 1.0:
                        color = "#f87171"  # Fatal/Weak
                    col.markdown(f"{label}: <span style='color:{color}'><b>{val}</b></span>", unsafe_allow_html=True)

            _res_field(r1, "🗡️ Slash", "slash")
            _res_field(r2, "🏹 Pierce", "pierce")
            _res_field(r3, "🔨 Blunt", "blunt")
        else:
            st.error("Resistances data missing on unit.")

    st.divider()

    # === 3. АУГМЕНТАЦИИ (AUGMENTATIONS) ===
    st.markdown("### 🧬 Аугментации")

    # 1. Получаем список аугментаций (ID)
    current_augs = unit.augmentations if hasattr(unit, 'augmentations') else []

    # 2. Фильтруем валидные (которые есть в реестре)
    valid_augs = [aid for aid in current_augs if aid in AUGMENTATION_REGISTRY]

    if is_edit_mode:
        # Мультиселект для удобного добавления/удаления
        # Форматируем имена
        def fmt_aug(aid):
            return AUGMENTATION_REGISTRY[aid].name if aid in AUGMENTATION_REGISTRY else aid

        new_selection = st.multiselect(
            "Установленные модули:",
            options=list(AUGMENTATION_REGISTRY.keys()),
            default=valid_augs,
            format_func=fmt_aug,
            key=f"aug_multiselect_{unit.name}"
        )

        # Если изменилось
        if new_selection != current_augs:
            unit.augmentations = new_selection
            unit.recalculate_stats()
            UnitLibrary.save_unit(unit)
            st.rerun()

    # 3. Отображение списком (Детали)
    if valid_augs:
        for aid in valid_augs:
            aug = AUGMENTATION_REGISTRY[aid]
            with st.expander(f"🧬 {aug.name}", expanded=True):
                st.markdown(aug.description)
                # Если у аугментации есть метод on_calculate_stats, можно попробовать показать статы
                # Но это сложно без инстанцирования. Просто описание ок.
    else:
        st.info("Нет установленных аугментаций.")