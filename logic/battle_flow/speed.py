def calculate_speed_advantage(spd_a: int, spd_d: int, intent_a: bool = True, intent_d: bool = True):
    """
    intent_X = True: Разрушить карту (Destroy) при разнице 8+
    intent_X = False: Не разрушать, наложить Disadvantage врагу при разнице 8+
    """
    diff = abs(spd_a - spd_d)

    adv_a = False  # Помеха атакующему (кидает 2, берет худший)
    adv_d = False  # Помеха защитнику
    destroy_a = False  # Кубик атакующего сломан (удален)
    destroy_d = False  # Кубик защитника сломан (удален)

    if diff >= 8:
        if spd_a > spd_d:
            # Атакующий быстрее на 8+
            if intent_a:
                destroy_d = True  # Уничтожаем кубик защитника
            else:
                adv_d = True  # Накладываем помеху защитнику
        else:
            # Защитник быстрее на 8+
            if intent_d:
                destroy_a = True
            else:
                adv_a = True

    elif diff >= 4:
        if spd_a > spd_d:
            adv_d = True  # Защитник медленнее -> помеха ему
        else:
            adv_a = True  # Атакующий медленнее -> помеха ему

    return adv_a, adv_d, destroy_a, destroy_d