# core/ranks.py

RANK_THRESHOLDS = [
    (0, "Крысы (Rats)", 0),
    (6, "Слухи (Grade 9)", 1),
    (12, "Городской Миф (Grade 8)", 2),
    (18, "Городская Легенда (Grade 7)", 3),
    (24, "Легенда+ (Grade 6)", 4),
    (30, "Городская Чума (Grade 5)", 5),
    (36, "Чума+ (Grade 4)", 6),
    (43, "Городской Кошмар (Grade 3)", 7),
    (50, "Кошмар+ (Grade 2)", 8),
    (65, "Звезда Города (Grade 1)", 9),
    (80, "Звезда+ (Color)", 10),
    (90, "Несовершенство (Impurity)", 11)
]


def get_rank_info(level: int):
    """Возвращает (Tier, Name) для заданного уровня."""
    current_tier = 0
    current_name = "Крысы"

    for thresh, name, tier in RANK_THRESHOLDS:
        if level >= thresh:
            current_tier = tier
            current_name = name
        else:
            break
    return current_tier, current_name


def calculate_rank_penalty(player_lvl: int, enemy_lvl: int) -> int:
    """Считает штраф уровня на основе разницы рангов."""
    p_tier, _ = get_rank_info(player_lvl)
    e_tier, _ = get_rank_info(enemy_lvl)
    n = e_tier - p_tier
    return (n * (n + 1)) // 2


# === [NEW] Базовые значения бросков по уровням ===
def get_base_roll_by_level(level: int):
    """
    Возвращает (min, max) базового броска карты в зависимости от уровня.
    Основано на таблице 'Чистые средние роллы'.
    """
    if level >= 90: return 35, 45 # Несовершенство (экстраполяция)
    if level >= 80: return 25, 32 # Цвет
    if level >= 65: return 21, 27 # 1 ранг
    if level >= 50: return 17, 22 # 2 ранг
    if level >= 43: return 14, 19 # 3 ранг
    if level >= 36: return 11, 16 # 4 ранг
    if level >= 30: return 9, 13  # 5 ранг
    if level >= 24: return 7, 10  # 6 ранг
    if level >= 18: return 5, 7   # 7 ранг
    if level >= 12: return 4, 6   # 8 ранг
    if level >= 6:  return 3, 5   # 9 ранг
    return 1, 3                   # Крысы