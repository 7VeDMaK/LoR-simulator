from core.enums import DiceType


def resolve_interaction(engine, winner_ctx, loser_ctx, diff: int):
    """
    Определяет эффект победы в зависимости от типа кубиков.
    engine: Экземпляр ClashSystem (для доступа к методам нанесения урона).
    """
    w_type = winner_ctx.dice.dtype
    l_type = loser_ctx.dice.dtype

    # Группировка типов
    ATK_TYPES = [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]

    w_is_atk = w_type in ATK_TYPES
    l_is_atk = l_type in ATK_TYPES
    w_is_blk = w_type == DiceType.BLOCK
    l_is_blk = l_type == DiceType.BLOCK
    w_is_evd = w_type == DiceType.EVADE
    l_is_evd = l_type == DiceType.EVADE

    # 1. Победила АТАКА
    if w_is_atk:
        if l_is_atk:
            # Атака vs Атака -> Полный урон
            engine._apply_damage(winner_ctx, loser_ctx, "hp")
        elif l_is_blk:
            # Атака vs Блок -> Урон снижен на значение блока (damage = diff)
            original_val = winner_ctx.final_value
            winner_ctx.final_value = diff

            engine._apply_damage(winner_ctx, loser_ctx, "hp")

            winner_ctx.final_value = original_val  # Возвращаем как было
        elif l_is_evd:
            # Атака vs Уворот (Провал уворота) -> Полный урон
            engine._apply_damage(winner_ctx, loser_ctx, "hp")

    # 2. Победил БЛОК
    elif w_is_blk:
        if l_is_atk:
            # Блок vs Атака -> Урон выдержке атакующего (Stagger Dmg)
            damage_amt = diff
            engine._deal_direct_damage(winner_ctx, loser_ctx.source, damage_amt, "stagger")
        elif l_is_blk:
            # Блок vs Блок -> Урон выдержке проигравшего
            damage_amt = diff
            engine._deal_direct_damage(winner_ctx, loser_ctx.source, damage_amt, "stagger")
        elif l_is_evd:
            # Блок vs Уворот -> Урон выдержке уворачивающегося
            damage_amt = diff
            engine._deal_direct_damage(winner_ctx, loser_ctx.source, damage_amt, "stagger")

    # 3. Победил УВОРОТ
    elif w_is_evd:
        # Уворот просто избегает урона (и может восстановить Stagger/нанести урон при наличии пассивок)
        winner_ctx.log.append("💨 Dodged!")