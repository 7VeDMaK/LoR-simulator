import streamlit as st
from core.unit.unit_library import UnitLibrary
# Импорт реестров данных
from logic.weapon_definitions import WEAPON_REGISTRY
from logic.armor_definitions import ARMOR_REGISTRY
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

    # Получаем текущий ID брони
    if not hasattr(unit, 'armor_id'):
        unit.armor_id = "standard_fixer_suit"  # Fallback для старых юнитов
    
    current_armor_id = unit.armor_id
    # Проверка на валидность ID
    if current_armor_id not in ARMOR_REGISTRY:
        current_armor_id = "none"  # Fallback

    armor_obj = ARMOR_REGISTRY[current_armor_id]

    # Layout: Карточка слева, Детали/Селектор справа
    c_arm_l, c_arm_r = st.columns([1, 2])

    with c_arm_l:
        # Визуальная карточка
        with st.container(border=True):
            st.markdown(f"**{armor_obj.name}**")
            st.caption(f"Rank: {armor_obj.rank}")

            # Отображение резистов брони
            st.caption("HP Resists:")
            for dtype, val in armor_obj.hp_resists.items():
                color = "#4ade80" if val < 1.0 else "#f87171" if val > 1.0 else "white"
                st.markdown(f"<span style='color:{color}'>×{val:.2f}</span> {dtype.capitalize()}", unsafe_allow_html=True)

    with c_arm_r:
        if is_edit_mode:
            # Селектор брони
            armor_options = list(ARMOR_REGISTRY.keys())

            # Находим индекс текущей
            try:
                idx = armor_options.index(current_armor_id)
            except ValueError:
                idx = 0

            new_armor_id = st.selectbox(
                "Выбрать броню",
                armor_options,
                index=idx,
                format_func=lambda x: f"{ARMOR_REGISTRY[x].name} (Rank {ARMOR_REGISTRY[x].rank})",
                label_visibility="collapsed"
            )

            if new_armor_id != current_armor_id:
                unit.armor_id = new_armor_id
                unit.armor_name = ARMOR_REGISTRY[new_armor_id].name
                
                # Применяем резисты из брони
                armor = ARMOR_REGISTRY[new_armor_id]
                unit.hp_resists.slash = armor.hp_resists["slash"]
                unit.hp_resists.pierce = armor.hp_resists["pierce"]
                unit.hp_resists.blunt = armor.hp_resists["blunt"]
                unit.stagger_resists.slash = armor.stagger_resists["slash"]
                unit.stagger_resists.pierce = armor.stagger_resists["pierce"]
                unit.stagger_resists.blunt = armor.stagger_resists["blunt"]
                
                unit.recalculate_stats()
                UnitLibrary.save_unit(unit)
                st.rerun()

            # Показываем описание выбранной (для справки при выборе)
            sel_armor = ARMOR_REGISTRY[new_armor_id]
            st.info(sel_armor.description)
            
            # Показываем дополнительные статы если есть
            if sel_armor.stats:
                stats_str = ", ".join([f"{k}: {'+' if v > 0 else ''}{v}" for k, v in sel_armor.stats.items()])
                st.caption(f"Stats: {stats_str}")

        else:
            # Режим просмотра - просто описание
            st.markdown(armor_obj.description)
            if armor_obj.passive_id:
                st.caption(f"Grant Passive: {armor_obj.passive_id}")
            
            # Показываем резисты
            st.caption("Сопротивления (HP Resistances)")
            r1, r2, r3 = st.columns(3)
            for i, (dtype, val) in enumerate(armor_obj.hp_resists.items()):
                col = [r1, r2, r3][i]
                emoji = ["🗡️", "🏹", "🔨"][i]
                color = "#4ade80" if val < 1.0 else "#f87171" if val > 1.0 else "white"
                col.markdown(f"{emoji} {dtype.capitalize()}: <span style='color:{color}'><b>×{val:.2f}</b></span>", unsafe_allow_html=True)

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