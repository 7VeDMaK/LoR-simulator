import uuid
import streamlit as st
from core.card import Card
from core.library import Library
from ui.editor.sections.dice_editor import render_dice_editor
from ui.editor.sections.general import render_general_info
from ui.editor.sections.global_effects import render_global_effects
from ui.editor.sections.loader import render_editor_loader
from ui.editor.editor_loader import reset_editor_state  # Импорт reset


def render_editor_page():
    st.markdown("### 🛠️ Мастерская Карт")

    # Инициализация (если зашли первый раз)
    if "ed_script_list" not in st.session_state:
        reset_editor_state("custom_cards.json")

    # 1. Загрузчик (выбор файла и карты)
    render_editor_loader()

    st.markdown("---")
    st.caption("Редактирование параметров")

    # 2. Основная инфа
    name, tier, ctype, desc = render_general_info()

    # 3. Эффекты
    render_global_effects()

    # 4. Кубики
    dice_objects = render_dice_editor(ctype)

    # 5. Секция Сохранения (Footer)
    st.markdown("---")
    st.subheader("💾 Сохранение")

    col_file, col_save, col_del = st.columns([2, 1, 1])

    all_files = Library.get_all_source_files()

    # Определяем текущий файл для селекта
    # Приоритет: 1. Выбранный в loader 2. Текущий файл карты 3. custom_cards 4. Первый попавшийся
    default_target = st.session_state.get("loader_selected_file")
    if not default_target:
        default_target = st.session_state.get("ed_source_file", "custom_cards.json")

    if default_target not in all_files and all_files:
        default_target = all_files[0]

    with col_file:
        target_file = st.selectbox(
            "Сохранить в файл:",
            all_files,
            index=all_files.index(default_target) if default_target in all_files else 0,
            key="save_target_selector"
        )

    with col_save:
        st.write("")
        st.write("")
        if st.button("💾 Сохранить", type="primary", use_container_width=True):
            if not name:
                st.error("Имя карты обязательно!")
            else:
                cid = st.session_state.get("ed_loaded_id")
                if not cid:
                    cid = name.lower().replace(" ", "_") + "_" + str(uuid.uuid4())[:4]

                # Сборка скриптов
                final_global_scripts = {}
                for gs in st.session_state["ed_script_list"]:
                    trig = gs["trigger"]
                    if trig not in final_global_scripts: final_global_scripts[trig] = []
                    final_global_scripts[trig].append(gs["data"])

                new_card = Card(
                    id=cid,
                    name=name,
                    tier=tier,
                    card_type=ctype,
                    description=desc,
                    dice_list=dice_objects,
                    scripts=final_global_scripts,
                    flags=st.session_state.get("ed_flags", [])
                )

                # Сохраняем в выбранный файл
                Library.save_card(new_card, filename=target_file)

                # Обновляем состояние редактора
                st.session_state["ed_source_file"] = target_file
                st.session_state["ed_loaded_id"] = cid

                # Также обновляем выбор в loader'е, чтобы мы остались в этом же файле
                st.session_state["loader_selected_file"] = target_file
                st.session_state["loader_selected_card_str"] = f"{name} ({cid})"

                st.toast(f"Сохранено в {target_file}!", icon="💾")
                st.rerun()

    with col_del:
        st.write("")
        st.write("")
        # Кнопка удаления активна только если карта уже существует
        if st.session_state.get("ed_loaded_id"):
            if st.button("🗑️ Удалить", type="secondary", use_container_width=True):
                Library.delete_card(st.session_state["ed_loaded_id"])
                st.toast("Карта удалена!", icon="🗑️")
                reset_editor_state(default_file=target_file)
                st.rerun()