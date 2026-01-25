import streamlit as st
import os

# Импортируем библиотеку для сохранения файлов напрямую
from core.unit.unit_library import UnitLibrary
from ui.app_modules.state_controller import update_and_save_state
# Импортируем Enum для красивых названий типов
from core.enums import UnitType


def get_avatar_path(unit):
    path = getattr(unit, 'avatar', None) or getattr(unit, 'icon_path', None)
    if path and os.path.exists(path):
        return path
    return "https://placehold.co/200x300?text=No+Image"


def save_unit_data(unit):
    """Принудительно сохраняет файл юнита и обновляет стейт"""
    UnitLibrary.save_unit(unit)
    update_and_save_state()


def render_relationships_page():
    st.header("❤️ Управление отношениями")

    if "roster" not in st.session_state or not st.session_state["roster"]:
        st.warning("⚠️ Нет персонажей. Загрузите их в меню Profile или Simulator.")
        return

    roster = st.session_state["roster"]
    roster_keys = sorted(list(roster.keys()))

    # === ВЫБОР ПЕРСОНАЖА ===
    current_key = st.session_state.get("rel_selected_unit_name")
    default_index = roster_keys.index(current_key) if current_key in roster_keys else 0

    col_header_img, col_header_sel = st.columns([1, 2])

    with col_header_sel:
        selected_name = st.selectbox(
            "Выберите главного персонажа (Субъект)",
            roster_keys,
            index=default_index,
            key="rel_selected_unit_name"
        )
        subject = roster[selected_name]

        # --- СТАТЫ И ТИП ---
        char_status = subject.memory.get("status_rank", "Неизвестно")

        # Получаем красивое название типа (например, "👤 Игрок")
        u_type = getattr(subject, "unit_type", UnitType.FIXER.value)
        type_label = UnitType.ui_labels().get(u_type, u_type)

        # Выводим тип жирным шрифтом в начале
        st.markdown(f"### {type_label}")
        st.markdown(f"**Lvl:** {subject.level} | **Rank:** {subject.rank} | **Status:** {char_status}")

        st.caption(subject.biography[:100] + "..." if getattr(subject, 'biography', '') else "...")

    with col_header_img:
        st.image(get_avatar_path(subject), width='stretch')

    st.divider()

    # === ГАРАНТИЯ ДАННЫХ ===
    if not hasattr(subject, "relationships"):
        subject.relationships = {}

    # ==========================================
    # 📝 РЕДАКТОР (ДОБАВЛЕНИЕ/ИЗМЕНЕНИЕ)
    # ==========================================
    edit_target = st.session_state.get("rel_edit_focus", None)
    is_expanded = (edit_target is not None)

    target_options = [n for n in roster_keys if n != selected_name]

    with st.expander("➕ Добавить / Редактировать связь", expanded=is_expanded):
        if not target_options:
            st.info("Нужен хотя бы еще один персонаж.")
        else:
            try:
                sel_idx = target_options.index(edit_target) if edit_target in target_options else 0
            except:
                sel_idx = 0

            c1, c2 = st.columns(2)
            with c1:
                target_name_input = st.selectbox("К кому (Цель)", target_options, index=sel_idx, key="rel_target_sel")

                # Показываем тип цели в редакторе для удобства
                tgt_u = roster.get(target_name_input)
                if tgt_u:
                    t_type_val = getattr(tgt_u, "unit_type", UnitType.FIXER.value)
                    t_label = UnitType.ui_labels().get(t_type_val, t_type_val)
                    st.caption(f"Тип цели: {t_label}")

                # Данные для формы
                curr_data = subject.relationships.get(target_name_input, {})

                status_opts = ["Soulmate", "Lover", "Best Friend", "Friend", "Neutral", "Rival", "Enemy", "Nemesis"]
                try:
                    s_idx = status_opts.index(curr_data.get("status", "Neutral"))
                except:
                    s_idx = 4

                new_status = st.selectbox("Статус", status_opts, index=s_idx, key="rel_status_sel")

            with c2:
                new_val = st.number_input("Значение (-100..100)", -100, 100, int(curr_data.get("value", 0)), step=5,
                                          key="rel_val_sel")
                new_note = st.text_input("Заметка", curr_data.get("notes", ""), key="rel_note_sel")

                st.write("")
                if st.button("💾 Сохранить связь", type="primary", width='stretch'):
                    # 1. Обновляем словарь
                    subject.relationships[target_name_input] = {
                        "value": new_val,
                        "status": new_status,
                        "notes": new_note
                    }
                    # 2. ЖЕЛЕЗНО СОХРАНЯЕМ В ФАЙЛ
                    save_unit_data(subject)

                    st.session_state["rel_edit_focus"] = None
                    st.toast(f"Связь с {target_name_input} сохранена на диск!", icon="💾")
                    st.rerun()

    # ==========================================
    # 📋 СПИСОК ВЗАИМООТНОШЕНИЙ (ДВУСТОРОННИЙ)
    # ==========================================
    st.subheader(f"Круг общения: {selected_name}")

    # Собираем список всех, с кем есть связь (в любую сторону)
    related_names = set()
    # 1. Те, кого мы добавили (Outgoing)
    related_names.update(subject.relationships.keys())
    # 2. Те, у кого мы есть в списках (Incoming)
    for name, unit in roster.items():
        if name == selected_name: continue
        if hasattr(unit, "relationships") and selected_name in unit.relationships:
            related_names.add(name)

    if not related_names:
        st.info("У этого персонажа нет активных связей (ни исходящих, ни входящих).")
    else:
        # Сортируем
        for t_name in sorted(list(related_names)):
            if t_name not in roster: continue  # Защита от удаленных

            target_unit = roster[t_name]

            # Получаем тип и статус цели для отображения
            t_type_val = getattr(target_unit, "unit_type", UnitType.FIXER.value)
            t_type_label = UnitType.ui_labels().get(t_type_val, t_type_val)

            t_rank_status = target_unit.memory.get("status_rank", "")
            t_status_str = f" | {t_rank_status}" if t_rank_status else ""

            # --- Данные ИСХОДЯЩИЕ (Я -> К нему) ---
            out_data = subject.relationships.get(t_name)

            # --- Данные ВХОДЯЩИЕ (Он -> Ко мне) ---
            inc_data = getattr(target_unit, "relationships", {}).get(selected_name)

            # Отрисовка
            with st.container(border=True):
                c_img, c_info, c_act = st.columns([1, 3.5, 0.5])

                # 1. Аватар собеседника
                with c_img:
                    st.image(get_avatar_path(target_unit), width='stretch')

                # 2. Информация (Две строки)
                with c_info:
                    # Имя
                    st.subheader(f"{t_name}")
                    # Тип и статус (например: "🔧 Фиксер | Легенда")
                    st.caption(f"{t_type_label}{t_status_str}")

                    st.markdown("---")

                    # Строка 1: Мое отношение (Outgoing)
                    if out_data:
                        val = out_data.get('value', 0)
                        icon = "❤️" if val >= 50 else "🙂" if val >= 0 else "☠️"
                        color = "green" if val >= 0 else "red"

                        st.markdown(
                            f"➡️ **Вы:** {icon} :{color}[{out_data.get('status')}] ({val})"
                            f" *{out_data.get('notes', '')}*"
                        )
                    else:
                        st.markdown(f"➡️ **Вы:** :grey[Нет отношений] (0)")

                    # Строка 2: Его отношение (Incoming)
                    if inc_data:
                        inc_val = inc_data.get('value', 0)
                        inc_icon = "❤️" if inc_val >= 50 else "🙂" if inc_val >= 0 else "☠️"
                        inc_color = "green" if inc_val >= 0 else "red"

                        st.markdown(
                            f"⬅️ **В ответ:** {inc_icon} :{inc_color}[{inc_data.get('status')}] ({inc_val})"
                            f" *{inc_data.get('notes', '')}*"
                        )
                    else:
                        st.markdown(f"⬅️ **В ответ:** :grey[Не знает вас / Нейтрален]")

                # 3. Действия
                with c_act:
                    st.write("")
                    if st.button("✏️", key=f"edit_{t_name}"):
                        st.session_state["rel_edit_focus"] = t_name
                        st.rerun()

                    # Кнопка удаления (удаляет только исходящую связь)
                    if out_data:
                        if st.button("🗑️", key=f"del_{t_name}"):
                            del subject.relationships[t_name]
                            if st.session_state.get("rel_edit_focus") == t_name:
                                st.session_state["rel_edit_focus"] = None
                            save_unit_data(subject)  # Сохраняем удаление
                            st.rerun()