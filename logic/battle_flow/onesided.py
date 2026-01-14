from core.enums import DiceType
from logic.battle_flow.speed import calculate_speed_advantage


def process_onesided(engine, source, target, round_label, spd_atk, spd_d, intent_atk=True, is_redirected=False):
    report = []
    card = source.current_card
    def_card = target.current_card

    # Расчет преимущества скорости
    adv_atk, adv_def, _, destroy_def = calculate_speed_advantage(spd_atk, spd_d, intent_atk, True)

    # 1. Break Check (Пустой слот ломается, если скорость врага >= 8)
    defender_breaks_attacker = False
    if not def_card:
        if spd_d - spd_atk >= 8:
            if hasattr(target, "iter_mechanics"):
                for mech in target.iter_mechanics():
                    if hasattr(mech, "can_break_empty_slot") and mech.can_break_empty_slot(target):
                        defender_breaks_attacker = True
                        break

    # 2. Prevent Destruction (Passive, e.g. Hedonist)
    prevent_dest = False
    if hasattr(source, "iter_mechanics"):
        for mech in source.iter_mechanics():
            if mech.prevents_dice_destruction_by_speed(source):
                prevent_dest = True
                break

    if destroy_def and prevent_dest:
        destroy_def = False
        adv_atk = True

    on_use_logs = []
    engine._process_card_self_scripts("on_use", source, target, custom_log_list=on_use_logs)

    # --- ЦИКЛ ПО КУБИКАМ АТАКИ ---

    attacker_queue = list(card.dice_list)
    att_idx = 0

    # Активный контр-кубик, который "держит оборону" (ресайклится)
    active_counter_die = None

    # Функция для извлечения следующего контр-кубика из запасов
    def fetch_next_counter(unit):
        # 1. Stored Dice (Приоритет)
        if hasattr(unit, 'stored_dice') and unit.stored_dice:
            # Проверка на Stagger
            if unit.is_staggered():
                can_use = False
                if hasattr(unit, "iter_mechanics"):
                    for mech in unit.iter_mechanics():
                        if mech.can_use_counter_die_while_staggered(unit):
                            can_use = True;
                            break
                if not can_use: return None

            return unit.stored_dice.pop(0)

        # 2. Counter Dice (Карта)
        if unit.counter_dice:
            if unit.is_staggered():
                can_use = False
                if hasattr(unit, "iter_mechanics"):
                    for mech in unit.iter_mechanics():
                        if mech.can_use_counter_die_while_staggered(unit):
                            can_use = True;
                            break
                if not can_use: return None

            return unit.counter_dice.pop(0)

        return None

    while att_idx < len(attacker_queue):
        die = attacker_queue[att_idx]

        if source.is_dead() or target.is_dead(): break
        # Stagger check для атакующего (он не может бить в стане)
        if source.is_staggered(): break

        source.current_die = die

        detail_logs = []
        if att_idx == 0 and on_use_logs: detail_logs.extend(on_use_logs)

        # A. Проверка на слом скоростью (без карт)
        if defender_breaks_attacker:
            report.append({
                "type": "onesided",
                "round": f"{round_label} (Break)",
                "left": {"unit": source.name, "card": card.name, "dice": "🚫 Broken", "val": 0, "range": "-"},
                "right": {"unit": target.name, "card": "-", "dice": "⚡ Break", "val": 0, "range": "-"},
                "outcome": "🚫 Broken (Speed)", "details": detail_logs + ["Def Speed > 8: Die Destroyed"]
            })
            att_idx += 1
            # Активный контр-кубик не тратится, так как атаки не было
            continue

        ctx_atk = engine._create_roll_context(source, target, die, is_disadvantage=adv_atk)

        # B. ПОЛУЧЕНИЕ ЗАЩИТЫ (Активный или Новый)
        if not active_counter_die:
            active_counter_die = fetch_next_counter(target)

        # C. РЕЗОЛВ (COUNTER CLASH)
        if active_counter_die:
            target.current_die = active_counter_die
            ctx_cnt = engine._create_roll_context(target, source, active_counter_die)  # Контры без штрафа

            ctx_atk.opponent_ctx = ctx_cnt
            ctx_cnt.opponent_ctx = ctx_atk

            val_atk = ctx_atk.final_value
            val_cnt = ctx_cnt.final_value

            outcome = ""

            is_atk_type = die.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]
            is_evade_cnt = active_counter_die.dtype == DiceType.EVADE

            if val_cnt > val_atk:
                # === Counter Wins ===
                engine._handle_clash_win(ctx_cnt)
                engine._handle_clash_lose(ctx_atk)

                if is_evade_cnt:
                    outcome = f"⚡ Stored Evade! (Recycle)"
                    target.restore_stagger(val_cnt)
                    # Кубик остается в active_counter_die (Recycle)
                else:
                    outcome = f"⚡ Counter Hit"
                    engine._resolve_clash_interaction(ctx_cnt, ctx_atk, val_cnt - val_atk)
                    # Атакующий контр (если это атака) обычно тоже ресайклится при победе в LoR
                    # (Counter Die recycles on win).
                    # Оставим его активным.

            elif val_atk > val_cnt:
                # === Attack Wins (Counter Broken) ===
                outcome = f"💥 Counter Broken"
                engine._handle_clash_win(ctx_atk)
                engine._handle_clash_lose(ctx_cnt)

                if is_atk_type:
                    engine._resolve_clash_interaction(ctx_atk, ctx_cnt, val_atk - val_cnt)

                # Контр уничтожен
                active_counter_die = None

            else:
                # === Draw ===
                outcome = "🤝 Draw (Counter Broken)"
                # При ничьей атакующий сгорает, защитный (уворот) тоже ломается
                active_counter_die = None

            # Логирование
            l_lbl = die.dtype.name
            r_lbl = f"{active_counter_die.dtype.name if active_counter_die else 'Broken'} (Cnt)"

            report.append({
                "type": "clash",
                "round": f"{round_label} (Counter)",
                "left": {"unit": source.name, "card": card.name, "dice": l_lbl, "val": val_atk, "range": "-"},
                "right": {"unit": target.name, "card": "Counter", "dice": r_lbl, "val": val_cnt, "range": "-"},
                "outcome": outcome, "details": detail_logs + ctx_atk.log + ctx_cnt.log
            })

            att_idx += 1  # Атакующий куб всегда тратится (или проиграл, или выиграл)
            continue

        # D. ПАССИВНАЯ ЗАЩИТА (Если нет контра)
        def_die = None

        # Индекс слота защиты = индексу атаки (синхронно)
        slot_idx = att_idx

        if not is_redirected and def_card and slot_idx < len(def_card.dice_list) and not target.is_staggered():
            candidate = def_card.dice_list[slot_idx]
            if candidate.dtype in [DiceType.BLOCK, DiceType.EVADE]:
                def_die = candidate
                target.current_die = def_die

        if destroy_def: def_die = None

        if def_die:
            # Passive Clash
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
                engine._handle_clash_draw(ctx_atk)
                engine._handle_clash_draw(ctx_def)

            report.append({
                "type": "clash",
                "round": f"{round_label} (Passive)",
                "left": {"unit": source.name, "card": card.name, "dice": die.dtype.name, "val": val_atk, "range": "-"},
                "right": {"unit": target.name, "card": def_card.name, "dice": def_die.dtype.name, "val": val_def,
                          "range": "-"},
                "outcome": outcome, "details": detail_logs + ctx_atk.log + ctx_def.log
            })
            att_idx += 1
            continue

        # E. ЧИСТЫЙ УРОН (UNOPPOSED)
        outcome = "Unopposed"
        if is_redirected:
            outcome += " (Redirected)"
        elif destroy_def:
            outcome += " (Speed Break)"

        ATK_TYPES = [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]

        if die.dtype in ATK_TYPES:
            engine._apply_damage(ctx_atk, None, "hp")
        elif die.dtype == DiceType.EVADE:
            # Одностороннее уклонение в атаке -> Сохраняется!
            if not hasattr(source, 'stored_dice'): source.stored_dice = []
            source.stored_dice.append(die)
            outcome = "🏃 Evade Stored"
        else:
            outcome += " (Defensive)"

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
            "outcome": outcome, "details": detail_logs + ctx_atk.log
        })

        att_idx += 1

    if active_counter_die:
        if not hasattr(target, 'stored_dice') or not isinstance(target.stored_dice, list):
            target.stored_dice = []
        target.stored_dice.insert(0, active_counter_die)

    return report