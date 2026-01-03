import streamlit as st
from core.unit.unit_library import UnitLibrary
from logic.augmentations import AUGMENTATION_REGISTRY
from logic.weapon_definitions import WEAPON_REGISTRY

def render_equipment(unit, u_key):
    # EQUIPMENT, RESISTS AND WEAPON
    # --- NEW AUGMENTATION SECTION ---
    st.markdown("**🧬 Аугментации**")

    # Helper for names
    def fmt_aug(aid):
        return AUGMENTATION_REGISTRY[aid].name if aid in AUGMENTATION_REGISTRY else aid

    # Filter valid augmentations
    valid_augs = [a for a in unit.augmentations if a in AUGMENTATION_REGISTRY]

    selected_augs = st.multiselect(
        "Установленные модули:",
        options=list(AUGMENTATION_REGISTRY.keys()),
        default=valid_augs,
        format_func=fmt_aug,
        key=f"aug_sel_{u_key}"
    )

    if selected_augs != unit.augmentations:
        unit.augmentations = selected_augs
        unit.recalculate_stats()
        st.rerun()

    # Display descriptions
    if unit.augmentations:
        for aid in unit.augmentations:
            if aid in AUGMENTATION_REGISTRY:
                aug = AUGMENTATION_REGISTRY[aid]
                st.caption(f"• **{aug.name}**: {aug.description}")

    st.divider()
    # ... (Rest of existing code: Weapon, Armor, Resists) ...
    c_eq1, c_eq2 = st.columns(2)

    # WEAPON SELECTION
    wep_options = list(WEAPON_REGISTRY.keys())
    curr_idx = 0
    if unit.weapon_id in wep_options:
        curr_idx = wep_options.index(unit.weapon_id)

    new_wep_id = c_eq1.selectbox(
        "⚔️ Оружие",
        wep_options,
        index=curr_idx,
        format_func=lambda x: WEAPON_REGISTRY[x].name,
        key=f"wep_sel_{unit.name}"
    )
    if unit.weapon_id != new_wep_id:
        unit.weapon_id = new_wep_id
        unit.recalculate_stats()
        st.rerun()

    sel_wep_obj = WEAPON_REGISTRY[new_wep_id]
    c_eq1.caption(f"{sel_wep_obj.description}")

    unit.armor_name = c_eq2.text_input("🛡️ Броня", unit.armor_name, key=f"arm_{unit.name}")

    st.markdown("**Сопротивления (HP)**")
    r1, r2, r3 = st.columns(3)

    unit.hp_resists.slash = r1.number_input("🗡️ Slash", 0.1, 3.0, unit.hp_resists.slash, 0.1, format="%.1f",
                                            key=f"res_slash_{unit.name}")
    unit.hp_resists.pierce = r2.number_input("🏹 Pierce", 0.1, 3.0, unit.hp_resists.pierce, 0.1, format="%.1f",
                                             key=f"res_pierce_{unit.name}")
    unit.hp_resists.blunt = r3.number_input("🔨 Blunt", 0.1, 3.0, unit.hp_resists.blunt, 0.1, format="%.1f",
                                            key=f"res_blunt_{unit.name}")

    total_money = unit.get_total_money()
    money_color = "green" if total_money >= 0 else "red"

    with st.expander(f"💰 Финансы: :{money_color}[{total_money} Ан]", expanded=False):
        # Add form
        c_mon1, c_mon2, c_mon3 = st.columns([1, 2, 1])
        with c_mon1:
            # Allow negative numbers for spending
            amount = st.number_input("Сумма", value=0, step=100, key=f"money_amt_{u_key}")
        with c_mon2:
            reason = st.text_input("Описание", placeholder="Награда за заказ...", key=f"money_reason_{u_key}")
        with c_mon3:
            st.write("")  # Indent
            if st.button("Добавить", key=f"money_add_{u_key}", use_container_width=True):
                if amount != 0:
                    unit.money_log.append({"amount": amount, "reason": reason})
                    UnitLibrary.save_unit(unit)
                    st.rerun()

        st.divider()

        # Transaction log (newest on top)
        if unit.money_log:
            # Limit output, e.g., to last 50 entries, to prevent lag
            history = unit.money_log[::-1]

            for item in history:
                amt = item['amount']
                desc = item.get('reason', '...')

                # Pretty display: Amount on left, description below in gray
                icon = "💸" if amt < 0 else "💰"
                color = "red" if amt < 0 else "green"
                sign = "+" if amt > 0 else ""

                st.markdown(f"""
                        <div style="border-left: 3px solid {'#ff4b4b' if amt < 0 else '#09ab3b'}; padding-left: 10px; margin-bottom: 5px;">
                            <div style="font-weight: bold; font-size: 1.1em;">{icon} :{color}[{sign}{amt} Ан]</div>
                            <div style="color: gray; font-size: 0.9em;">{desc}</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.caption("История транзакций пуста.")