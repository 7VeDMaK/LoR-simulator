import streamlit as st
from core.library import Library
from ui.editor.editor_loader import load_card_to_state, reset_editor_state


def render_editor_loader():
    st.info("📂 Управление Паками и Загрузка", icon="📂")

    # [FIX] Проверяем, загружены ли карты в память, а не просто наличие файлов
    if not Library.get_cards_dict():
        Library.load_all()

    # --- 1. Создание нового пака ---
    with st.expander("Создать новый Пак Карт"):
        c1, c2 = st.columns([3, 1])
        new_pack_name = c1.text_input("Название пака", key="new_pack_input")
        if c2.button("➕ Создать"):
            if new_pack_name:
                if Library.create_new_pack(new_pack_name):
                    st.success(f"Пак {new_pack_name}.json создан!")
                    # Сразу выбираем его
                    fname = f"{new_pack_name}.json" if not new_pack_name.endswith(".json") else new_pack_name
                    st.session_state["loader_selected_file"] = fname
                    st.rerun()
                else:
                    st.error("Ошибка создания (возможно, файл существует).")
            else:
                st.warning("Введите имя.")

    st.divider()

    # --- 2. Выбор файла ---
    all_files = Library.get_all_source_files()

    if not all_files:
        st.warning("Нет доступных паков карт.")
        return

    # Определяем индекс для селекта
    current_idx = 0
    saved_file = st.session_state.get("loader_selected_file")
    if saved_file in all_files:
        current_idx = all_files.index(saved_file)

    # Селект файла (обновляет стейт автоматически при изменении)
    selected_file = st.selectbox(
        "Выберите Пак Карт:",
        all_files,
        index=current_idx,
        key="loader_file_select"
    )

    # Синхронизируем стейт
    if selected_file != st.session_state.get("loader_selected_file"):
        st.session_state["loader_selected_file"] = selected_file
        # При смене пака сбрасываем выбор карты, чтобы не пытаться загрузить карту из старого пака
        st.session_state["loader_selected_card_str"] = "(Создать новую карту)"
        st.rerun()

    # --- 3. Выбор карты в этом файле ---
    filtered_cards = Library.load_cards_from_file(selected_file)

    # Формируем список опций
    # Format: "Имя Карты (ID)"
    card_map = {f"{c.tier}. {c.name} ({c.id})": c for c in filtered_cards}
    options = ["(Создать новую карту)"] + list(card_map.keys())

    # Пытаемся восстановить выбор карты
    sel_card_idx = 0
    if st.session_state.get("loader_selected_card_str") in options:
        sel_card_idx = options.index(st.session_state["loader_selected_card_str"])

    selected_card_str = st.selectbox(
        "Выберите карту для редактирования:",
        options,
        index=sel_card_idx,
        key="loader_card_select"
    )
    st.session_state["loader_selected_card_str"] = selected_card_str

    # --- Кнопки действий ---
    col_load, col_dup = st.columns(2)

    if col_load.button("📥 Загрузить / Сбросить", use_container_width=True):
        if selected_card_str == "(Создать новую карту)":
            reset_editor_state(default_file=selected_file)
            st.toast("Редактор сброшен для новой карты", icon="✨")
        else:
            card_obj = card_map.get(selected_card_str)
            if card_obj:
                load_card_to_state(card_obj)
                st.toast(f"Карта {card_obj.name} загружена!", icon="✅")
            else:
                st.error("Ошибка: карта не найдена в памяти.")
        st.rerun()

    # Кнопка дублирования доступна только если выбрана существующая карта
    if selected_card_str != "(Создать новую карту)":
        if col_dup.button("📑 Дублировать", use_container_width=True):
            card_obj = card_map.get(selected_card_str)
            if card_obj:
                load_card_to_state(card_obj)

                # Удаляем ID, помечаем как копию
                if "ed_loaded_id" in st.session_state:
                    del st.session_state["ed_loaded_id"]
                st.session_state["ed_name"] = f"{st.session_state['ed_name']} (Copy)"

                st.toast("Карта скопирована! Нажмите 'Сохранить', чтобы записать её.", icon="📋")
                st.rerun()