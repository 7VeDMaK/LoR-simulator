import streamlit as st
from core.unit.unit_library import UnitLibrary
from .item_generator import ItemGenerator
from .item_effects import RARITY_NAMES, ITEM_TIERS, POWER_MODIFIER_LABELS
from .roulette_logic import RouletteRandomizer


def _format_non_zero_stats(stats: dict) -> str:
    parts = [f"{key}: {value:+d}" for key, value in stats.items() if value != 0]
    return ", ".join(parts) if parts else "Нет"


def render_roulette_page():
    """Рулетка Рейна - главная страница"""
    
    st.title("🎰 Рулетка Рейна")
    
    # Инициализируем session state
    if "roulette_selected_unit" not in st.session_state:
        st.session_state.roulette_selected_unit = None
    if "roulette_items_generated" not in st.session_state:
        st.session_state.roulette_items_generated = False
    if "roulette_items" not in st.session_state:
        st.session_state.roulette_items = None
    if "roulette_randomizer" not in st.session_state:
        st.session_state.roulette_randomizer = RouletteRandomizer()
    
    # Загружаем юнитов
    units = UnitLibrary.load_all()
    
    if not units:
        st.warning("❌ Юниты не найдены. Загрузите данные юнитов.")
        return
    
    # Выбор юнита
    st.subheader("1️⃣ Выбери персонажа")
    unit_names = sorted(list(units.keys()))
    
    selected_unit_name = st.selectbox(
        "Юнит",
        unit_names,
        key="roulette_unit_select"
    )
    
    if selected_unit_name:
        selected_unit = units[selected_unit_name]
        st.session_state.roulette_selected_unit = selected_unit
        
        # Показываем информацию о юните
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Персонаж", selected_unit.name)
        with col2:
            st.metric("Ранг", selected_unit.rank)
        
        # Кнопка для генерации возможных предметов
        st.subheader("2️⃣ Генерация возможных предметов")
        
        if st.button("📋 Возможные предметы", use_container_width=True, type="secondary"):
            generator = ItemGenerator()
            items_data = generator.generate_all_items(selected_unit.rank)
            st.session_state.roulette_items = items_data
            st.session_state.roulette_items_generated = True
        
        # Если предметы сгенерированы, показываем список
        if st.session_state.roulette_items_generated and st.session_state.roulette_items:
            st.divider()
            st.subheader("📦 Возможные предметы")
            
            items = st.session_state.roulette_items
            
            # Вкладки для оружия и брони
            tab_weapons, tab_armor = st.tabs(["⚔️ Оружие", "🛡️ Броня"])
            
            with tab_weapons:
                st.write(f"**Всего вариантов: {len(items['weapons'])}**")
                for weapon in items['weapons']:
                    tier_info = ITEM_TIERS[weapon.tier]
                    tier_label = f"{tier_info['code']} ({tier_info['name']})"
                    
                    with st.expander(f"🗡️ {weapon.name} - Тир {tier_label}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Тип:** {weapon.item_type}")
                            st.write(f"**Класс:** {weapon.item_class}")
                            st.write(f"**Ранг:** {weapon.rank}")
                            st.write(f"**Редкость:** {RARITY_NAMES[weapon.rarity]}")
                        with col2:
                            st.write(f"**Тир:** {tier_label}")
                            st.write(f"**Множитель цены:** x{tier_info['price_multiplier']}")
                            st.write(f"**Репутация:** Ранг {'+' if tier_info['reputation_req'] > 0 else ''}{tier_info['reputation_req'] if tier_info['reputation_req'] is not None else 'Любая'}")
                        
                        if weapon.power_modifiers:
                            modifiers_text = ", ".join(
                                f"{POWER_MODIFIER_LABELS.get(key, key)}: +{value}"
                                for key, value in weapon.power_modifiers.items()
                            )
                            st.write(f"**Модификаторы:** {modifiers_text}")

                        st.write(f"**Пассивно:** {weapon.passive_effect}")
                        st.write(f"**Активно:** {weapon.active_effect}")
                        st.write(f"**Attributes:** {_format_non_zero_stats(weapon.attributes)}")
                        st.write(f"**Skills:** {_format_non_zero_stats(weapon.skills)}")

                        with st.expander("📜 Полный потенциал предмета", expanded=False):
                            for line in weapon.full_potential:
                                st.write(f"• {line}")

                        st.write(f"**Описание тира:** {tier_info['description']}")
                        st.write(f"**Эффекты:**")
                        for effect in weapon.effects:
                            st.write(f"  • {effect}")
            
            with tab_armor:
                st.write(f"**Всего вариантов: {len(items['armor'])}**")
                for armor in items['armor']:
                    tier_info = ITEM_TIERS[armor.tier]
                    tier_label = f"{tier_info['code']} ({tier_info['name']})"
                    
                    with st.expander(f"🛡️ {armor.name} - Тир {tier_label}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Тип:** {armor.item_type}")
                            st.write(f"**Класс:** {armor.item_class}")
                            st.write(f"**Ранг:** {armor.rank}")
                            st.write(f"**Редкость:** {RARITY_NAMES[armor.rarity]}")
                        with col2:
                            st.write(f"**Тир:** {tier_label}")
                            st.write(f"**Множитель цены:** x{tier_info['price_multiplier']}")
                            st.write(f"**Репутация:** Ранг {'+' if tier_info['reputation_req'] > 0 else ''}{tier_info['reputation_req'] if tier_info['reputation_req'] is not None else 'Любая'}")
                        
                        if armor.power_modifiers:
                            modifiers_text = ", ".join(
                                f"{POWER_MODIFIER_LABELS.get(key, key)}: +{value}"
                                for key, value in armor.power_modifiers.items()
                            )
                            st.write(f"**Модификаторы:** {modifiers_text}")

                        st.write(f"**Пассивно:** {armor.passive_effect}")
                        st.write(f"**Активно:** {armor.active_effect}")
                        st.write(f"**Attributes:** {_format_non_zero_stats(armor.attributes)}")
                        st.write(f"**Skills:** {_format_non_zero_stats(armor.skills)}")

                        with st.expander("📜 Полный потенциал предмета", expanded=False):
                            for line in armor.full_potential:
                                st.write(f"• {line}")

                        st.write(f"**Описание тира:** {tier_info['description']}")
                        st.write(f"**Эффекты:**")
                        for effect in armor.effects:
                            st.write(f"  • {effect}")
            
            # Кнопка кручения рулетки
            st.divider()
            st.subheader("3️⃣ Крутить рулетку")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🎲 Крутить", use_container_width=True, type="primary"):
                    # Объединяем все предметы
                    all_items = items['weapons'] + items['armor']
                    roulette = st.session_state.roulette_randomizer
                    
                    # Крутим рулетку
                    result = roulette.spin(all_items)
                    tier_info = ITEM_TIERS[result.tier]
                    tier_label = f"{tier_info['code']} ({tier_info['name']})"
                    
                    st.balloons()
                    st.success(f"🎉 **Выпало:** {result.name}")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Класс:** {result.item_class}")
                        st.write(f"**Ранг:** {result.rank}")
                        st.write(f"**Редкость:** {RARITY_NAMES[result.rarity]}")
                    with col_b:
                        st.write(f"**Тир:** {tier_label}")
                        st.write(f"**Множитель цены:** x{tier_info['price_multiplier']}")
                    
                    if result.power_modifiers:
                        modifiers_text = ", ".join(
                            f"{POWER_MODIFIER_LABELS.get(key, key)}: +{value}"
                            for key, value in result.power_modifiers.items()
                        )
                        st.write(f"**Модификаторы:** {modifiers_text}")

                    st.write(f"**Пассивно:** {result.passive_effect}")
                    st.write(f"**Активно:** {result.active_effect}")
                    st.write(f"**Attributes:** {_format_non_zero_stats(result.attributes)}")
                    st.write(f"**Skills:** {_format_non_zero_stats(result.skills)}")

                    with st.expander("📜 Полный потенциал предмета", expanded=False):
                        for line in result.full_potential:
                            st.write(f"• {line}")

                    st.info(f"**Описание тира:** {tier_info['description']}")
                    st.write(f"**Эффекты:** {', '.join(result.effects)}")
