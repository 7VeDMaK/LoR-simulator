import base64
import os
import mimetypes  # <--- Добавляем этот модуль
import streamlit as st

# Путь к папке с иконками
ICON_DIR = "data/icons"

# Маппинг ключей на файлы
# Теперь можно указывать любые расширения
ICON_FILES = {
    "hp": "hp.webp",  # <--- Пример с WEBP
    "sp": "sp.webp",
    "stagger": "stagger.webp",
    "slash": "slash.webp",
    "pierce": "pierce.webp",
    "blunt": "blunt.webp",
    "block": "block.webp",
    "evade": "evade.webp",
    "strength": "strength.webp",  # <--- Еще пример
}

# Эмодзи по умолчанию
FALLBACK_EMOJIS = {
    "hp": "💚",
    "sp": "🧠",
    "stagger": "😵",
    "slash": "🗡️",
    "pierce": "🏹",
    "blunt": "🔨",
    "block": "🛡️",
    "evade": "💨",
    "strength": "💪",
    "endurance": "🧱",
    "haste": "👟",
    "protection": "🛡️",
    "vulnerability": "🎯"
}


@st.cache_data
def get_icon_html(key: str, width: int = 20) -> str:
    """
    Возвращает HTML-тег <img>. Автоматически определяет MIME-тип (png/webp/jpeg).
    """
    key = key.lower()
    filename = ICON_FILES.get(key)

    if filename:
        path = os.path.join(ICON_DIR, filename)
        if os.path.exists(path):
            try:
                # 1. Определяем MIME-тип (например, 'image/webp' или 'image/png')
                mime_type, _ = mimetypes.guess_type(path)
                if not mime_type: mime_type = "image/png"  # Фолбек

                # 2. Читаем и кодируем
                with open(path, "rb") as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()

                # 3. Вставляем правильный mime_type в строку src
                return f'<img src="data:{mime_type};base64,{encoded}" width="{width}" style="vertical-align: middle; margin-bottom: 2px;">'
            except Exception:
                pass

    return FALLBACK_EMOJIS.get(key, "❓")