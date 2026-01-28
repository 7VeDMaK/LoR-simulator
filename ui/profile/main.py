import streamlit as st
import io
import os
from fpdf import FPDF

from core.logging import logger
from core.unit.unit import Unit
from core.unit.unit_library import UnitLibrary
from ui.profile.abilities import render_abilities
from ui.profile.equipment import render_equipment
from ui.profile.header import render_header, render_basic_info
from ui.profile.stats import render_stats


def render_profile_page():
    if 'roster' not in st.session_state or not st.session_state['roster']:
        st.session_state['roster'] = UnitLibrary.load_all() or {"New Unit": Unit("New Unit")}

    roster = st.session_state['roster']

    unit, u_key = render_header(roster)
    if unit is None:
        return

    logger.clear()
    unit.recalculate_stats()
    calculation_logs = logger.get_logs()

    col_l, col_r = st.columns([1, 2.5], gap="medium")

    with col_l:
        render_basic_info(unit, u_key)

    with col_r:
        render_equipment(unit, u_key)
        render_stats(unit, u_key)

    st.markdown("---")
    render_abilities(unit, u_key)

    with st.expander("📜 Лог расчета характеристик", expanded=False):
        if calculation_logs:
            for l in calculation_logs:
                if "Stats" in str(l) or "Talent" in str(l):
                    st.caption(f"• {l}")
                elif "ERROR" in str(l):
                    st.error(f"• {l}")
                else:
                    st.text(f"• {l}")
        else:
            st.info("Нет записей. Проверьте уровень логирования или наличие пассивок.")

    st.divider()
    st.markdown("## Скачать профиль в PDF")

    def create_character_pdf(unit: Unit) -> io.BytesIO:
        pdf = FPDF()
        pdf.add_page()

        font_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "fonts", "DejaVuSans", "DejaVuSans.ttf")
        )
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=10)

        pdf.image(unit.avatar, 100, 10, 100, 100)
        
        y = pdf.get_y()
        
        pdf.set_xy(10, y)
        
        pdf.multi_cell(
            100,
            5,
            f"ПЕРСОНАЖ\n"
            f"Имя: {unit.name}\n"
            f"Уровень: {unit.level}\n"
            f"Ранг: {unit.rank}\n"
            f"Статус: {unit.memory.get('status_rank', '-')}\n"
            f"Интеллект: {unit.base_intellect}\n"
            f"Накопленный опыт: {unit.total_xp}\n"
            f"\n"
            f"СОСТОЯНИЕ\n"
            f"HP: {unit.current_hp}/{unit.max_hp}\n"
            f"SP: {unit.current_sp}/{unit.max_hp}\n"
            f"Stagger: {unit.current_stagger}\n"
            f"Текущая удача: {unit.resources.get('luck', 0)}\n"
        )

        pdf.ln(40)

        pdf.multi_cell(
            100,
            5,
            f"АТРИБУТЫ\n"
            f"Сила: {unit.attributes.get('strength', 0)}\n"
            f"Стойкость: {unit.attributes.get('endurance', 0)}\n"
            f"Ловкость: {unit.attributes.get('agility', 0)}\n"
            f"Мудрость: {unit.attributes.get('wisdom', 0)}\n"
            f"Психический порог: {unit.attributes.get('psych', 0)}\n"
            "\n"
        )

        pdf.multi_cell(
            100,
            5,
            f"НАВЫКИ\n"
            f"Сила удара: {unit.skills.get('strike_power', 0)}\n"
            f"Медицина: {unit.skills.get('medicine', 0)}\n"
            f"Сила воли: {unit.skills.get('willpower', 0)}\n"
            f"Удача: {unit.skills.get('luck', 0)}\n"
            f"Акробатика: {unit.skills.get('acrobatics', 0)}\n"
            f"Щиты: {unit.skills.get('shields', 0)}\n"
            f"Прочная кожа: {unit.skills.get('tough_skin', 0)}\n"
            f"Скорость: {unit.skills.get('speed', 0)}\n"
            f"Лёгкое оружие: {unit.skills.get('light_weapon', 0)}\n"
            f"Среднее оружие: {unit.skills.get('medium_weapon', 0)}\n"
            f"Тяжёлое оружие: {unit.skills.get('heavy_weapon', 0)}\n"
            f"Огнестрел: {unit.skills.get('firearms', 0)}\n"
            f"Красноречие: {unit.skills.get('eloquence', 0)}\n"
            f"Кузнечное дело: {unit.skills.get('forging', 0)}\n"
            f"Инженерия: {unit.skills.get('engineering', 0)}\n"
            f"Программирование: {unit.skills.get('programming', 0)}\n"
        )

        pdf.set_xy(100, 120)

        pdf.multi_cell(
            100,
            5,
            f"Броня: {unit.armor_name}\n"
            f"Тип брони: {unit.armor_type}\n"
        )

        pdf.add_page()
        pdf.set_xy(10, y)
        
        pdf.multi_cell(200, 5, "БИОГРАФИЯ")
        pdf.multi_cell(100, 5, unit.biography) #я хз чезабаг
        
        pdf_bytes = pdf.output(dest="S")
        return io.BytesIO(pdf_bytes)

    if st.button("Сгенерировать"):
        pdf_buffer = create_character_pdf(unit)
        st.download_button(
            label="Скачать",
            data=pdf_buffer,
            file_name=f"{unit.name}_charsheet.pdf",
            mime="application/pdf"
        )
