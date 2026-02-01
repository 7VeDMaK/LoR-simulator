import streamlit as st
from core.unit.unit_library import UnitLibrary
from core.logging import logger
from ui.format_utils import format_large_number


def render_visuals_tab(unit, is_edit_mode: bool):
    """
    Вкладка Инфо: Биография, Финансы, Логи.
    """

    # === 1. БИОГРАФИЯ ===
    st.markdown("### 📝 Биография и Заметки")

    if is_edit_mode:
        new_bio = st.text_area(
            "История персонажа, инвентарь или заметки",
            value=unit.biography,
            height=300,
            key=f"bio_editor_{unit.name}",
            help="Здесь можно писать квенту или заметки."
        )
        if new_bio != unit.biography:
            unit.biography = new_bio
            UnitLibrary.save_unit(unit)  # Сохраняем при изменении (или можно добавить кнопку)
    else:
        if unit.biography:
            st.markdown(unit.biography)
        else:
            st.caption("Биография не заполнена.")

    st.divider()

    # === 2. ФИНАНСЫ ===
    total_money = unit.get_total_money() if hasattr(unit, 'get_total_money') else 0
    money_color = "green" if total_money >= 0 else "red"
    formatted_total = format_large_number(total_money)

    st.markdown(f"### 💰 Финансы: :{money_color}[{formatted_total} Ан]")

    if is_edit_mode:
        with st.container(border=True):
            c_mon1, c_mon2, c_mon3 = st.columns([1, 2, 1])
            with c_mon1:
                amount = st.number_input("Сумма", value=0, step=100, key=f"money_amt_{unit.name}")
            with c_mon2:
                reason = st.text_input("Описание", placeholder="Награда за заказ...", key=f"money_reason_{unit.name}")
            with c_mon3:
                st.write("")
                if st.button("Добавить", key=f"money_add_{unit.name}", width='stretch', type="primary"):
                    if amount != 0:
                        if not hasattr(unit, 'money_log'): unit.money_log = []
                        unit.money_log.append({"amount": amount, "reason": reason})
                        UnitLibrary.save_unit(unit)
                        st.toast(f"Транзакция на {amount} сохранена!")
                        st.rerun()

    # История транзакций
    with st.expander("📜 История операций", expanded=False):
        if hasattr(unit, 'money_log') and unit.money_log:
            history = unit.money_log[::-1]  # Новые сверху
            for item in history[:50]:  # Показываем последние 50
                amt = item.get('amount', 0)
                desc = item.get('reason', '...')

                icon = "💸" if amt < 0 else "💰"
                sign = "+" if amt > 0 else ""

                # Определяем HEX-цвет для CSS (такой же, как у вас в рамке)
                css_color = "#ff4b4b" if amt < 0 else "#09ab3b"

                fmt_amt = format_large_number(abs(amt))

                st.markdown(f"""
                    <div style="
                        border-left: 3px solid {css_color}; 
                        padding-left: 10px; 
                        margin-bottom: 8px; 
                        background-color: #262730; 
                        padding: 5px; 
                        border-radius: 4px;">
                        <div style="font-weight: bold; font-size: 1.0em;">
                            {icon} <span style="color: {css_color};">{sign}{fmt_amt} Ан</span>
                        </div>
                        <div style="color: #aaa; font-size: 0.9em;">{desc}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.caption("История пуста.")

    st.divider()

    # === 3. ЛОГИ РАСЧЕТА ===
    st.markdown("### ⚙️ Системный лог")
    with st.expander("📜 Лог пересчета характеристик", expanded=False):
        # БЕРЕМ ЛОГИ ИЗ ЮНИТА (snapshot), чтобы не смешивать с другими
        calculation_logs = getattr(unit, '_ui_logs', [])

        # Если вдруг пусто (например, первый запуск), пробуем глобальный
        if not calculation_logs:
            calculation_logs = logger.get_logs()

        if calculation_logs:
            for l in calculation_logs:
                log_str = str(l)
                # Красивая подсветка
                if "Stats" in log_str or "Talent" in log_str:
                    st.caption(f"• {log_str}")
                elif "ERROR" in log_str:
                    st.error(f"• {log_str}")
                elif "Passive" in log_str:
                    st.markdown(f":blue[• {log_str}]")
                elif "Recalculating" in log_str:
                    st.markdown(f"**{log_str}**")
                else:
                    st.text(f"• {log_str}")
        else:
            st.info("Нет записей. (Лог очищен)")