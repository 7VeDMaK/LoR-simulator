import base64
import os
import mimetypes
import streamlit as st

# Путь к папке с иконками
ICON_DIR = "data/icons"

# Маппинг ключей (в коде) на имена файлов
# Ключи должны быть в нижнем регистре
ICON_FILES = {
    # --- Основные типы ---
    "slash": "Slash.webp",
    "pierce": "Pierce.webp",
    "blunt": "Blunt.webp",
    "block": "Block.webp",
    "evade": "Evade.webp",

    "melee": "Close.webp",  # Обычно Melee это Close range
    "offensive": "Mixed.webp",
    "ranged": "Ranged.webp",
    "mass summation": "Mass.webp",  # Для Mass Attack
    "mass": "Mass.webp",  # Для Mass Attack

    # --- Контр-кубики ---
    "counter_slash": "ContrSlash.webp",
    "counter_pierce": "ContrPierce.webp",
    "counter_blunt": "ContrBlunt.webp",
    "counter_block": "ContrBlock.webp",
    "counter_evade": "ContrEvade.webp",

    # --- Статы и Ресурсы ---
    "hp": "HealthPoint.webp",
    "sp": "Sanity.webp",
    "stagger": "Stagger.webp",
    "speed": "Speed.webp",
    "ammo": "Ammo.webp",
    "luck": "LuckDice.webp",  # Luck
    "charge": "Charge.webp",  # Charge (Заряд)

    # --- Статусы (Buffs/Debuffs) ---
    "strength": "AttackPowerUp.webp",  # Сила (обычно это Power Up)
    "endurance": "Endurance.webp",
    "haste": "Haste.webp",
    "protection": "Protection.webp",  # Или Protection, если есть
    "barrier": "Barrier.webp",

    "bleed": "Bleed.webp",
    "burn": "Burn.webp",
    "smoke": "Smoke.webp",
    "paralysis": "Paralize.webp",  # Паралич часто похож на Weakness или отдельную иконку
    "fragile": "Fragile.webp",
    "vulnerability": "Vulnerable.webp",
    "weakness": "AttackPowerDown.webp",  # Weakness = снижение силы атаки

    "bind": "Bind.webp",
    "tremor": "Tremor.webp",
    "rupture": "Rapture.webp",  # Внимание на опечатку в файле: Rapture вместо Rupture
    "poise": "Poise.webp",
    "poison": "Poison.webp",
    "sinking": "Overdose.webp",  # Или Sinking, если есть. Overdose подходит для негатива.

    # --- Специальные ---
    "dmg_up": "DamageUp.webp",
    "dmg_down": "DamageDown.webp",
    "power_up": "AttackPowerUp.webp",
    "power_down": "AttackPowerDown.webp",
    "invisibility": "Undetectable.webp",
    "rhythm": "Rythm.webp",  # Rythm

    # --- Типы карт (Ранги) ---
    "tier_1": "page1.webp",
    "tier_2": "page2.webp",
    "tier_3": "page3.webp",
    "tier_4": "page4.webp",
    "tier_5": "page5.webp",

    # --- Прочее из списка ---
    "throwing": "Throwing.webp",

    "madness": "Madness.webp",
    "dice_broken": "DiceBroken.webp",
    "dice_slot": "DiceSlot.webp",
    "positive": "Positive.webp",
    "negative": "Negative.webp",
    "liquid_blood": "LiquidBlood.webp",
    "tremor_burst": "TremorBurst.webp",
    "tremor_conversion": "TremorConversion.webp",
}

# Эмодзи по умолчанию (если картинки нет или ошибка)
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

    # Пытаемся найти прямое совпадение
    filename = ICON_FILES.get(key)

    # Если не нашли, пробуем эвристику для типов атак (Counter Slash -> contrslash)
    if not filename:
        if "counter" in key:
            # Пример: "counter_slash" -> ищем "contrslash" (но у нас ключи маппинга есть)
            pass

    if filename:
        path = os.path.join(ICON_DIR, filename)
        if os.path.exists(path):
            try:
                # 1. Определяем MIME-тип
                mime_type, _ = mimetypes.guess_type(path)
                if not mime_type:
                    # Фолбек для webp, если mimetypes его не знает
                    if filename.endswith(".webp"):
                        mime_type = "image/webp"
                    else:
                        mime_type = "image/png"

                # 2. Читаем и кодируем
                with open(path, "rb") as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()

                # 3. Вставляем
                return f'<img src="data:{mime_type};base64,{encoded}" width="{width}" style="vertical-align: middle; margin-bottom: 2px;">'
            except Exception:
                pass

    return FALLBACK_EMOJIS.get(key, "❓")