from core.enums import DiceType
from core.logging import logger, LogLevel


def resolve_counter_clash(engine, source, target, die_atk, die_cnt, adv_atk):
    """
    Решает столкновение Атаки против Активного Контр-кубика.
    Возвращает: outcome_dict { outcome_str, details_list, counter_spent_bool }
    """
    target.current_die = die_cnt

    # Создаем контексты бросков
    ctx_atk = engine._create_roll_context(source, target, die_atk, is_disadvantage=adv_atk)
    ctx_cnt = engine._create_roll_context(target, source, die_cnt)

    # Связываем их для проверки эффектов "On Clash"
    ctx_atk.opponent_ctx = ctx_cnt
    ctx_cnt.opponent_ctx = ctx_atk

    val_atk = ctx_atk.final_value
    val_cnt = ctx_cnt.final_value

    outcome = ""
    counter_spent = True

    is_atk_def = die_atk.dtype in [DiceType.BLOCK, DiceType.EVADE]

    # 1. Специфичный случай: Защита об Защиту
    if is_atk_def and die_cnt.dtype in [DiceType.BLOCK, DiceType.EVADE]:
        outcome = "🛡️ Defensive Clash (Both Spent)"
        counter_spent = True

    # 2. Победа КОНТР-КУБИКА
    elif val_cnt > val_atk:
        counter_spent = False  # Не тратится

        engine._handle_clash_win(ctx_cnt)
        engine._handle_clash_lose(ctx_atk)

        if die_cnt.dtype == DiceType.EVADE:
            outcome = f"⚡ Stored Evade! (Recycle)"
            rec = target.restore_stagger(val_cnt)
            ctx_cnt.log.append(f"🛡️ +{rec} Stagger")
        else:
            # [FIX] Контр-атака победила
            dmg_val = val_cnt - val_atk
            dmg = engine._resolve_clash_interaction(ctx_cnt, ctx_atk, dmg_val)

            dmg_str = f" 💥 **-{dmg} HP**" if dmg else ""
            outcome = f"⚡ Counter Hit (Recycle){dmg_str}"

    # 3. Победа АТАКИ (Контр-кубик сломан)
    elif val_atk > val_cnt:
        counter_spent = True  # Кубик уничтожен

        engine._handle_clash_win(ctx_atk)
        engine._handle_clash_lose(ctx_cnt)

        # Если атака не была защитной, она пробивает дальше
        if not is_atk_def:
            # [FIX] Урон по цели (Break damage)
            dmg = engine._resolve_clash_interaction(ctx_atk, ctx_cnt, val_atk - val_cnt)

            dmg_str = f" 💥 **-{dmg} HP**" if dmg else ""
            outcome = f"💥 Counter Broken{dmg_str}"
        else:
            outcome = f"💥 Counter Broken"

    # 4. Ничья
    else:
        outcome = "🤝 Draw (Counter Broken)"
        counter_spent = True
        engine._handle_clash_draw(ctx_atk)
        engine._handle_clash_draw(ctx_cnt)

    # [FIX] Собираем логи ПОСЛЕ всех действий, чтобы захватить сообщения об уроне
    details = ctx_atk.log + ctx_cnt.log

    return {
        "outcome": outcome,
        "details": details,
        "counter_spent": counter_spent,
        "val_atk": val_atk,
        "val_cnt": val_cnt,
        "atk_ctx": ctx_atk
    }


def resolve_passive_defense(engine, source, target, die_atk, die_def, adv_atk, adv_def):
    """
    Решает столкновение Атаки против Защитного кубика в слоте (Passive).
    """
    target.current_die = die_def
    ctx_atk = engine._create_roll_context(source, target, die_atk, is_disadvantage=adv_atk)
    ctx_def = engine._create_roll_context(target, source, die_def, is_disadvantage=adv_def)

    ctx_atk.opponent_ctx = ctx_def
    ctx_def.opponent_ctx = ctx_atk

    val_atk = ctx_atk.final_value
    val_def = ctx_def.final_value

    outcome = ""
    is_atk_def = die_atk.dtype in [DiceType.BLOCK, DiceType.EVADE]

    if is_atk_def:
        outcome = "🛡️ Defensive Clash (Both Spent)"

    elif val_atk > val_def:
        engine._handle_clash_win(ctx_atk)
        engine._handle_clash_lose(ctx_def)

        # [FIX]
        dmg = engine._resolve_clash_interaction(ctx_atk, ctx_def, val_atk - val_def)
        dmg_str = f" 💥 **-{dmg} HP**" if dmg else ""
        outcome = f"🗡️ Atk Break{dmg_str}"

    elif val_def > val_atk:
        engine._handle_clash_win(ctx_def)
        engine._handle_clash_lose(ctx_atk)

        # [FIX] (Например, Stagger урон от блока)
        dmg = engine._resolve_clash_interaction(ctx_def, ctx_atk, val_def - val_atk)
        # Если это был блок, урон идет в Stagger, но interaction вернет число
        outcome = f"🛡️ Defended"

    else:
        outcome = "🤝 Draw"
        engine._handle_clash_draw(ctx_atk)
        engine._handle_clash_draw(ctx_def)

    # [FIX] Собираем логи в конце
    return {
        "outcome": outcome,
        "details": ctx_atk.log + ctx_def.log,
        "val_atk": val_atk,
        "val_def": val_def
    }


def resolve_unopposed_hit(engine, source, target, die_atk, adv_atk, flags):
    """
    Решает безответный удар (Unopposed).
    """
    outcome = "Unopposed"
    if flags.get("is_redirected"):
        outcome += " (Redirected)"
    elif flags.get("destroy_def"):
        outcome += " (Speed Break)"

    ctx_atk = engine._create_roll_context(source, target, die_atk, is_disadvantage=adv_atk)

    ATK_TYPES = [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]

    if die_atk.dtype in ATK_TYPES:
        logger.log(f"⚔️ Direct Hit! {ctx_atk.final_value} Dmg", LogLevel.NORMAL, "OneSided")
        # [FIX]
        dmg = engine._apply_damage(ctx_atk, None, "hp")
        dmg_str = f" 💥 **-{dmg} HP**" if dmg else ""
        outcome += dmg_str

    elif die_atk.dtype == DiceType.EVADE:
        if not hasattr(source, 'stored_dice') or not isinstance(source.stored_dice, list):
            source.stored_dice = []
        source.stored_dice.append(die_atk)
        outcome = "🏃 Evade Stored"
        logger.log("🏃 Evade die stored (Unopposed)", LogLevel.VERBOSE, "OneSided")

    elif die_atk.dtype == DiceType.BLOCK:
        outcome = "🛡️ Block (Ignored)"
        logger.log("🛡️ Offensive Block ignored", LogLevel.VERBOSE, "OneSided")
    else:
        outcome += " (Skipped)"

    return {
        "outcome": outcome,
        "details": ctx_atk.log,
        "val_atk": ctx_atk.final_value
    }