def get_action_priority(card):
    """
    Возвращает базовый приоритет действия на основе типа карты.
    Чем выше число, тем раньше сработает карта.
    """
    if not card: return 0

    ctype = str(card.card_type).lower()

    # 1. Мгновенные эффекты
    if ctype == "on_play" or ctype == "on play": return 5000

    # 2. Массовые атаки (срабатывают до обычных столкновений)
    if "mass" in ctype: return 4000

    # 3. Стрелковые (бьют первыми в фазе боя)
    if ctype == "ranged": return 3000

    # 4. Наступательные (бьют перед обычными, но могут быть перехвачены)
    if ctype == "offensive": return 2000

    # 5. Обычные (Рукопашные)
    if ctype == "melee": return 1000

    return 0