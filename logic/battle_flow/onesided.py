from core.enums import DiceType
from logic.battle_flow.speed import calculate_speed_advantage


def process_onesided(engine, source, target, round_label, spd_atk, spd_def, intent_atk=True, is_redirected=False):
    report = []
    card = source.current_card
    def_card = target.current_card

    # Расчет преимущества скорости (для пассивной защиты карты)
    # Контр-кубики обычно игнорируют speed difference в односторонних атаках (они реактивны)
    adv_atk, adv_def, _, destroy_def = calculate_speed_advantage(spd_atk, spd_def, intent_atk, True)

    # [PASSIVE] Гедонизм
    prevent_dest = False
    if hasattr(source, "iter_mechanics"):
        for mech in source.iter_mechanics():
            if mech.prevents_dice_destruction_by_speed(source):
                prevent_dest = True;
                break

    if destroy_def and prevent_dest:
        destroy_def = False
        adv_atk = True

    on_use_logs = []
    engine._process_card_self_scripts("on_use", source, target, custom_log_list=on_use_logs)

    # === ЛОГИКА КОНТР-КУБИКОВ ===
    active_counter_die = None

    def get_counter_die(unit):
        if unit.counter_dice:
            if unit.is_staggered():
                # Talent check
                can_use_staggered = False
                if hasattr(unit, "iter_mechanics"):
                    for mech in unit.iter_mechanics():
                        if mech.can_use_counter_die_while_staggered(unit):
                            can_use_staggered = True;
                            break

                if can_use_staggered:
                    # Доп. проверка на флаг самого кубика (так задумано талантом)
                    if unit.counter_dice[0].flags and "talent_defense_die" in unit.counter_dice[0].flags:
                        return unit.counter_dice.pop(0)
                # ====================================================
                return None
            return unit.counter_dice.pop(0)
            return None

    # Покубичный перебор атаки
    for j, die in enumerate(card.dice_list):
        if source.is_dead() or target.is_dead() or source.is_staggered(): break

        source.current_die = die

        # 1. Пытаемся получить активный контр-кубик
        if not active_counter_die:
            active_counter_die = get_counter_die(target)

        # 2. Создаем контекст атаки
        ctx_atk = engine._create_roll_context(source, target, die, is_disadvantage=adv_atk)

        detail_logs = []
        if j == 0 and on_use_logs: detail_logs.extend(on_use_logs)

        # --- A. ЕСЛИ ЕСТЬ КОНТР-КУБИК -> CLASH ---
        if active_counter_die:
            target.current_die = active_counter_die

            # Контр-кубик не получает штрафов скорости в One-Sided (обычно)
            ctx_cnt = engine._create_roll_context(target, source, active_counter_die)

            # Связываем
            ctx_atk.opponent_ctx = ctx_cnt
            ctx_cnt.opponent_ctx = ctx_atk

            val_atk = ctx_atk.final_value
            val_cnt = ctx_cnt.final_value

            outcome = ""

            if val_cnt >= val_atk:
                # Контр-кубик победил (Защита)
                outcome = "⚡ Counter Win"
                engine._handle_clash_win(ctx_cnt)
                engine._handle_clash_lose(ctx_atk)
                engine._resolve_clash_interaction(ctx_cnt, ctx_atk, val_cnt - val_atk)
                # active_counter_die сохраняется
            else:
                # Атака победила (Пробитие)
                outcome = "⚡ Counter Break"
                engine._handle_clash_win(ctx_atk)
                engine._handle_clash_lose(ctx_cnt)

                # Наносим урон (resolve_interaction сам определит тип урона и количество)
                engine._resolve_clash_interaction(ctx_atk, ctx_cnt, val_atk - val_cnt)

                # Контр-кубик уничтожен
                active_counter_die = None

            # Лог
            l_lbl = die.dtype.name
            r_lbl = f"{active_counter_die.dtype.name if active_counter_die else 'Broken'} (Cnt)"

            report.append({
                "type": "clash",
                "round": f"{round_label} (Counter)",
                "left": {"unit": source.name, "card": card.name, "dice": l_lbl, "val": val_atk, "range": "-"},
                "right": {"unit": target.name, "card": "Counter", "dice": r_lbl, "val": val_cnt, "range": "-"},
                "outcome": outcome, "details": detail_logs + ctx_atk.log + ctx_cnt.log
            })

            # Переходим к следующему кубику атаки
            continue

        # --- B. НЕТ КОНТР-КУБИКА -> ПАССИВНАЯ ЗАЩИТА ИЛИ ЧИСТЫЙ УРОН ---

        def_die = None
        # Проверяем карту в слоте (если атака не перенаправлена в занятый слот)
        if not is_redirected and def_card and j < len(def_card.dice_list) and not target.is_staggered():
            candidate = def_card.dice_list[j]
            # Пассивно защищаться можно только Защитными кубиками (Block/Evade)
            if candidate.dtype in [DiceType.BLOCK, DiceType.EVADE]:
                def_die = candidate
                target.current_die = def_die

        # Если кубик защиты сломан скоростью
        if destroy_def and def_die:
            def_die = None

        if def_die:
            # CLASH (Атака vs Пассивная Защита)
            ctx_def = engine._create_roll_context(target, source, def_die, is_disadvantage=adv_def)

            ctx_atk.opponent_ctx = ctx_def
            ctx_def.opponent_ctx = ctx_atk

            val_atk = ctx_atk.final_value
            val_def = ctx_def.final_value

            outcome = ""
            if val_atk > val_def:
                outcome = f"🗡️ Atk Break"
                engine._handle_clash_win(ctx_atk)
                engine._handle_clash_lose(ctx_def)
                engine._resolve_clash_interaction(ctx_atk, ctx_def, val_atk - val_def)
            elif val_def > val_atk:
                outcome = f"🛡️ Defended"
                engine._handle_clash_win(ctx_def)
                engine._handle_clash_lose(ctx_atk)
                engine._resolve_clash_interaction(ctx_def, ctx_atk, val_def - val_atk)
            else:
                outcome = "🤝 Draw"

            report.append({
                "type": "clash",
                "round": f"{round_label} (Passive Def)",
                "left": {"unit": source.name, "card": card.name, "dice": die.dtype.name, "val": val_atk, "range": "-"},
                "right": {"unit": target.name, "card": def_card.name, "dice": def_die.dtype.name, "val": val_def,
                          "range": "-"},
                "outcome": outcome, "details": detail_logs + ctx_atk.log + ctx_def.log
            })

        else:
            # UNOPPOSED (Чистый урон)
            outcome = "Unopposed"
            if is_redirected:
                outcome += " (Redirected)"
            elif destroy_def:
                outcome += " (Speed Break)"

            # Наносим урон (только если это атакующий кубик)
            ATK_TYPES = [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]
            if die.dtype in ATK_TYPES:
                engine._apply_damage(ctx_atk, None, "hp")
            else:
                outcome += " (Skipped)"

            detail_logs.extend(ctx_atk.log)

            r_dice_show = "None"
            if destroy_def:
                r_dice_show = "🚫 Broken"
            elif is_redirected:
                r_dice_show = "Busy"

            report.append({
                "type": "onesided",
                "round": f"{round_label} (Hit)",
                "left": {"unit": source.name, "card": card.name, "dice": die.dtype.name, "val": ctx_atk.final_value,
                         "range": "-"},
                "right": {"unit": target.name, "card": "-", "dice": r_dice_show, "val": 0, "range": "-"},
                "outcome": outcome, "details": detail_logs
            })

    return report