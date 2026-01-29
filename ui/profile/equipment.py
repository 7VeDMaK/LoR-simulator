import streamlit as st
from core.library import Library
from core.unit.unit_library import UnitLibrary


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def _render_passive_details(passive_ids):
    """
    Принимает список ID пассивок (например ['mech_banganrang'])
    и выводит их описание из Библиотеки.
    """
    if not passive_ids:
        return

    st.markdown("<div style='margin-top: 6px; font-weight:bold; font-size:12px; color:#aaa;'>Эффекты оружия:</div>",
                unsafe_allow_html=True)

    for pid in passive_ids:
        # Пытаемся найти пассивку в библиотеке
        passive = Library.get_passive(pid)

        if passive:
            # Если нашли — выводим красиво
            name = passive.name
            desc = passive.description

            # Рендер блока пассивки
            st.markdown(
                f"""
                <div style="
                    background: #222; 
                    border-left: 3px solid #ffd700; 
                    padding: 4px 8px; 
                    margin-bottom: 4px; 
                    border-radius: 0 4px 4px 0;
                ">
                    <div style="font-weight: bold; font-size: 13px; color: #ffd700;">{name}</div>
                    <div style="font-size: 11px; color: #ccc; font-style: italic;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # Если не нашли (или это просто текст), выводим как есть, но аккуратно
            st.warning(f"Unknown Passive ID: {pid}")


def render_equipment_tab(unit, is_edit_mode: bool):
    """
    Вкладка Снаряжения (Оружие).
    """
    st.markdown("### ⚔️ Арсенал")

    # Получаем список всего оружия из библиотеки
    all_weapons = Library.get_all_weapons()  # Предполагаем, что такой метод есть
    # Если нет метода get_all_weapons, можно использовать заглушку или фильтр get_all_cards

    # Текущее оружие юнита
    current_weapon = unit.equipped_weapon  # Объект или ID

    # === БЛОК ТЕКУЩЕГО ОРУЖИЯ ===
    with st.container(border=True):
        c_img, c_info = st.columns([1, 3])

        with c_img:
            st.markdown("🖼️")  # Тут можно иконку оружия

        with c_info:
            if current_weapon:
                # Заголовок
                st.markdown(f"#### {current_weapon.name}")
                st.caption(f"Tier: {current_weapon.tier} | Type: {current_weapon.weapon_type}")

                # Рендер пассивок оружия (ВМЕСТО Grant Passive: ID)
                if hasattr(current_weapon, 'passives') and current_weapon.passives:
                    _render_passive_details(current_weapon.passives)

                # Описание самого оружия
                if current_weapon.description:
                    st.markdown(
                        f"<div style='font-size:12px; color:#888; margin-top:5px;'>{current_weapon.description}</div>",
                        unsafe_allow_html=True)
            else:
                st.info("Оружие не экипировано.")

    st.divider()

    # === СМЕНА ОРУЖИЯ (Только в Edit Mode) ===
    if is_edit_mode:
        st.subheader("🛠️ Сменить оружие")

        # Создаем словарь {name: object} для селектора
        w_options = {w.name: w for w in all_weapons}
        w_names = ["(Снять)"] + list(w_options.keys())

        # Текущий индекс
        cur_idx = 0
        if current_weapon and current_weapon.name in w_names:
            cur_idx = w_names.index(current_weapon.name)

        selected_name = st.selectbox("Выберите оружие", w_names, index=cur_idx)

        # Логика смены
        if selected_name == "(Снять)":
            if unit.equipped_weapon is not None:
                unit.equipped_weapon = None
                UnitLibrary.save_unit(unit)
                st.rerun()
        else:
            new_w = w_options[selected_name]
            # Проверяем, изменилось ли оружие (по ID или имени)
            if not current_weapon or new_w.id != current_weapon.id:
                unit.equipped_weapon = new_w
                UnitLibrary.save_unit(unit)
                st.rerun()

        # Превью выбранного в селекте (если отличается от надетого)
        if selected_name != "(Снять)" and (not current_weapon or selected_name != current_weapon.name):
            preview_w = w_options[selected_name]
            st.caption("Предпросмотр:")
            st.markdown(f"**{preview_w.name}**")
            if hasattr(preview_w, 'passives'):
                _render_passive_details(preview_w.passives)