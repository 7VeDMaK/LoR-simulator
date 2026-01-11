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

    # Разница рангов (только если враг выше рангом, иначе 0?)
    # В вашем примере штраф вычитается из уровня врага.
    # Если враг слабее (тир меньше), штраф будет 0.
    n = e_tier - p_tier

    # Формула: n(n+1)/2
    return (n * (n + 1)) // 2