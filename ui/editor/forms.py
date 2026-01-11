import streamlit as st
from ui.editor.config import SCRIPT_SCHEMAS, STATUS_LIST
# [NEW] Импортируем утилиты для иконок
from ui.icons import get_icon_html, FALLBACK_EMOJIS


def render_dynamic_form(prefix: str, schema_name: str) -> dict:
    """
    Рисует инпуты на основе выбранной схемы и возвращает готовый словарь params.
    """
    if schema_name not in SCRIPT_SCHEMAS:
        return {}

    schema = SCRIPT_SCHEMAS[schema_name]
    params_def = schema["params"]
    result_params = {}

    if not params_def:
        st.caption("Нет настроек.")
        return {}

    cols = st.columns(3)

    for i, p_def in enumerate(params_def):
        col = cols[i % 3]

        key = p_def["key"]
        label = p_def["label"]
        p_type = p_def["type"]
        default = p_def["default"]
        help_text = p_def.get("help", None)

        widget_key = f"{prefix}_{schema_name}_{key}"

        with col:
            if p_type == "int":
                val = st.number_input(label, value=default, step=1, key=widget_key, help=help_text)
                result_params[key] = int(val)
            elif p_type == "float":
                val = st.number_input(label, value=float(default), step=0.1, format="%.2f", key=widget_key,
                                      help=help_text)
                result_params[key] = float(val)
            elif p_type == "text":
                val = st.text_input(label, value=str(default), key=widget_key, help=help_text)
                result_params[key] = val
            elif p_type == "bool":
                val = st.checkbox(label, value=bool(default), key=widget_key, help=help_text)
                result_params[key] = val
            elif p_type == "select":
                opts = p_def["opts"]
                val = st.selectbox(label, opts, index=opts.index(default) if default in opts else 0, key=widget_key,
                                   help=help_text)
                result_params[key] = val

            # === [ИЗМЕНЕНИЕ] Улучшенный выбор статуса ===
            elif p_type == "status_select":
                idx = STATUS_LIST.index(default) if default in STATUS_LIST else 0

                # Функция для красивого отображения в списке (Эмодзи + Название)
                def format_status_option(s_key):
                    # Берем эмодзи из fallback, если есть, или знак вопроса
                    emoji = FALLBACK_EMOJIS.get(s_key, "🔹")
                    return f"{emoji} {s_key.capitalize()}"

                val = st.selectbox(label, STATUS_LIST, index=idx, format_func=format_status_option, key=widget_key,
                                   help=help_text)

                # Показываем реальную картинку (WebP/PNG) под селектором для наглядности
                icon_html = get_icon_html(val, width=24)
                st.caption(f"Превью: {icon_html}", unsafe_allow_html=True)

                result_params[key] = val

    return result_params