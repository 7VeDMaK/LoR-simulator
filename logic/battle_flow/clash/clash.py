from core.enums import DiceType
from core.logging import logger, LogLevel
from logic.battle_flow.clash.clash_one_sided import handle_one_sided_exchange
from logic.battle_flow.clash.clash_resolution import resolve_clash_round
from logic.battle_flow.clash.clash_setup import setup_clash_parameters
from logic.battle_flow.clash.clash_state import ClashParticipantState


def process_clash(engine, attacker, defender, round_label, is_left, spd_a, spd_d, intent_a=True, intent_d=True):
    report = []

    logger.log(f"⚔️ Clash Start: {attacker.name} vs {defender.name} (Spd: {spd_a} vs {spd_d})", LogLevel.NORMAL,
               "Clash")

    # 1. SETUP
    adv_a, adv_d, destroy_a, destroy_d, on_use_logs = setup_clash_parameters(
        engine, attacker, defender, spd_a, spd_d, intent_a, intent_d
    )

    # 2. INITIALIZE STATE
    state_a = ClashParticipantState(attacker, attacker.current_card, destroy_a)
    state_d = ClashParticipantState(defender, defender.current_card, destroy_d)

    iteration = 0
    max_iterations = 25

    # === ОСНОВНОЙ ЦИКЛ ===
    while (state_a.has_dice_left() or state_d.has_dice_left()) and iteration < max_iterations:
        iteration += 1
        if attacker.is_dead() or defender.is_dead(): break

        # Получаем кубики
        die_a = state_a.resolve_current_die()
        die_d = state_d.resolve_current_die()

        if not die_a and not die_d:
            state_a.consume()
            state_d.consume()
            continue

        # Создание контекстов
        ctx_a = engine._create_roll_context(attacker, defender, die_a, is_disadvantage=adv_a) if die_a else None
        ctx_d = engine._create_roll_context(defender, attacker, die_d, is_disadvantage=adv_d) if die_d else None

        # Связывание
        state_a.current_ctx = ctx_a
        state_d.current_ctx = ctx_d

        val_a = ctx_a.final_value if ctx_a else 0
        val_d = ctx_d.final_value if ctx_d else 0

        logger.log(f"Clash {iteration}: {attacker.name}({val_a}) vs {defender.name}({val_d})", LogLevel.VERBOSE,
                   "Clash")

        if ctx_a and ctx_d:
            ctx_a.opponent_ctx = ctx_d
            ctx_d.opponent_ctx = ctx_a

        # [FIX] Предварительные логи (нужны для One-Sided ветки, которая требует их аргументом)
        detail_logs = []
        if iteration == 1 and on_use_logs: detail_logs.extend(on_use_logs)
        if ctx_a: detail_logs.extend(ctx_a.log)
        if ctx_d: detail_logs.extend(ctx_d.log)

        outcome = ""

        # === РЕЗОЛЮЦИЯ ===

        # Случай 1: Атакующий сломан/пуст
        if not die_a and die_d:
            outcome = handle_one_sided_exchange(engine, active_side=state_d, passive_side=state_a,
                                                detail_logs=detail_logs)

        # Случай 2: Защитник сломан/пуст
        elif die_a and not die_d:
            outcome = handle_one_sided_exchange(engine, active_side=state_a, passive_side=state_d,
                                                detail_logs=detail_logs)

        # Случай 3: Оба защитные
        elif (die_a.dtype in [DiceType.EVADE, DiceType.BLOCK]) and (die_d.dtype in [DiceType.EVADE, DiceType.BLOCK]):
            outcome = "🛡️ Defensive Clash (Both Spent)"
            state_a.consume()
            state_d.consume()

        # Случай 4: Полноценная стычка
        else:
            res = resolve_clash_round(engine, ctx_a, ctx_d, die_a, die_d)
            outcome = res["outcome"]

            # [FIX] ВАЖНО: Пересобираем логи ПОСЛЕ резолва, чтобы захватить сообщения об уроне
            # (так как resolve_clash_round -> apply_damage пишет в ctx_a.log, но detail_logs имеет старую копию)
            detail_logs = []
            if iteration == 1 and on_use_logs: detail_logs.extend(on_use_logs)
            if ctx_a: detail_logs.extend(ctx_a.log)
            if ctx_d: detail_logs.extend(ctx_d.log)

            detail_logs.extend(res["details"])

            if res["recycle_a"]:
                state_a.recycle()
            else:
                state_a.consume()

            if res["recycle_d"]:
                state_d.recycle()
            else:
                state_d.consume()

        # Формирование отчета UI
        l_lbl = die_a.dtype.name if die_a else "Broken"
        r_lbl = die_d.dtype.name if die_d else "Broken"
        if state_a.current_src_is_counter: l_lbl += " (C)"
        if state_d.current_src_is_counter: r_lbl += " (C)"
        l_rng = f"{die_a.min_val}-{die_a.max_val}" if die_a else "-"
        r_rng = f"{die_d.min_val}-{die_d.max_val}" if die_d else "-"

        report.append({
            "type": "clash",
            "round": f"{round_label} ({iteration})",
            "left": {"unit": attacker.name if is_left else defender.name,
                     "card": attacker.current_card.name if is_left else defender.current_card.name,
                     "dice": l_lbl if is_left else r_lbl, "val": val_a if is_left else val_d,
                     "range": l_rng if is_left else r_rng},
            "right": {"unit": defender.name if is_left else attacker.name,
                      "card": defender.current_card.name if is_left else attacker.current_card.name,
                      "dice": r_lbl if is_left else l_lbl, "val": val_d if is_left else val_a,
                      "range": r_rng if is_left else l_rng},
            "outcome": outcome, "details": detail_logs
        })

    # 3. CLEANUP
    state_a.store_remaining(report)
    state_d.store_remaining(report)

    return report