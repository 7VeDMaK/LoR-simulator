import streamlit as st

def render_styled_description(text: str):
    """
    Рендерит описание:
    1. Если есть двойной перенос (\n\n) -> Первая часть как цитата, вторая как текст.
    2. Иначе -> Просто текст.
    """
    if not text:
        return

    parts = text.split("\n\n", 1)

    if len(parts) == 2:
        quote = parts[0]
        mechanics = parts[1]

        # === ФИОЛЕТОВЫЙ ДИЗАЙН ЦИТАТЫ ===
        st.markdown(
            f"""
            <div style="
                border-left: 2px solid #9370DB; /* Фиолетовая линия */
                padding-left: 14px;
                margin-bottom: 12px;
                margin-top: 4px;
            ">
                <span style="
                    font-style: italic;
                    font-size: 15px;
                    color: #b0b0b0; /* Светло-серый текст для контраста */
                    line-height: 1.5;
                    font-family: sans-serif;
                ">
                    {quote}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # === МЕХАНИКА ===
        st.markdown(mechanics)

    else:
        st.markdown(text)