from core.enums import DiceType
from logic.battle_flow.speed import calculate_speed_advantage


def process_onesided(engine, source, target, round_label, spd_atk, spd_def, intent_atk=True, is_redirected=False):
    report = []
    card = source.current_card
    def_card = target.current_card

    # Расчет скорости
    _, adv_def, _, destroy_def = calculate_speed_advantage(spd_atk, spd_def, intent_atk, True)

    on_use_logs = []
    engine._process_card_self_scripts("on_use", source, target, custom_log_list=on_use_logs)

    for j, die in enumerate(card.dice_list):
        if source.is_dead() or target.is_dead() or source.is_staggered(): break

        # A. COUNTER DIE
        # Если слот занят (redirected), контр-кубик не может активироваться против третьей стороны
        counter_die = None
        if not is_redirected:
            _, counter_die = engine._find_counter_die(target)
            # (Тут можно добавить логику обработки контр-кубика, если она будет реализована)

        # B. ПАССИВНАЯ ЗАЩИТА (из карты в слоте)
        def_die = None

        # === ВАЖНОЕ ИСПРАВЛЕНИЕ ===
        # Защищаться можно только если слот НЕ ЗАНЯТ (не redirected)
        if not is_redirected:
            if def_card and j < len(def_card.dice_list) and not target.is_staggered():
                candidate = def_card.dice_list[j]
                if candidate.dtype in [DiceType.BLOCK, DiceType.EVADE]:
                    def_die = candidate

        # Разрушение защиты скоростью (применяем, только если защита вообще была возможна)
        if destroy_def and def_die:
            def_die = None

        # Бросок атаки
        ctx_atk = engine._create_roll_context(source, target, die)

        detail_logs = []
        if j == 0 and on_use_logs: detail_logs.extend(on_use_logs)

        # Сценарий 1: Встретили защиту (Слот был свободен и там был защитный кубик)
        if def_die:
            ctx_def = engine._create_roll_context(target, source, def_die, is_disadvantage=adv_def)
            val_atk = ctx_atk.final_value
            val_def = ctx_def.final_value

            outcome = ""
            if val_atk > val_def:
                outcome = f"🗡️ Atk Break ({source.name})"
                engine._handle_clash_win(ctx_atk)
                engine._handle_clash_lose(ctx_def)
                engine._resolve_clash_interaction(ctx_atk, ctx_def, val_atk - val_def)
            elif val_def > val_atk:
                outcome = f"🛡️ Defended ({target.name})"
                engine._handle_clash_win(ctx_def)
                engine._handle_clash_lose(ctx_atk)
                engine._resolve_clash_interaction(ctx_def, ctx_atk, val_def - val_atk)
            else:
                outcome = "🤝 Draw"

            if ctx_atk: detail_logs.extend(ctx_atk.log)
            if ctx_def: detail_logs.extend(ctx_def.log)

            # UI Report (как Clash)
            report.append({
                "type": "clash",
                "round": f"{round_label} (Def)",
                "left": {"unit": source.name, "card": card.name, "dice": die.dtype.name, "val": val_atk,
                         "range": f"{die.min_val}-{die.max_val}"},
                "right": {"unit": target.name, "card": def_card.name, "dice": def_die.dtype.name, "val": val_def,
                          "range": f"{def_die.min_val}-{def_die.max_val}"},
                "outcome": outcome, "details": detail_logs
            })

        # Сценарий 2: Чистая атака (Unopposed)
        else:
            outcome = "Unopposed"

            # Если причина отсутствия защиты — редирект, пометим это
            if is_redirected:
                outcome += " (Redirected)"

            ATK_TYPES = [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]
            if die.dtype in ATK_TYPES:
                engine._apply_damage(ctx_atk, None, "hp")
            else:
                outcome = "Defensive (Skipped)"

            detail_logs.extend(ctx_atk.log)

            # Определяем, что писать в логе про кубик врага
            r_dice = "None"
            if is_redirected:
                r_dice = "Busy"  # Слот занят боем
            elif destroy_def:
                r_dice = "🚫 Broken"  # Слот был, но сломан скоростью

            report.append({
                "type": "onesided",
                "round": f"{round_label} (D{j + 1})",
                "left": {"unit": source.name, "card": card.name, "dice": die.dtype.name, "val": ctx_atk.final_value,
                         "range": f"{die.min_val}-{die.max_val}"},
                "right": {"unit": target.name, "card": "---", "dice": r_dice, "val": 0,
                          "range": "-"},
                "outcome": outcome, "details": detail_logs
            })

    return report