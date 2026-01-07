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

    # === [NEW] ЛОГИКА КОНТР-ДАЙСОВ ИЗ СПИСКА ===
    # Если слот цели занят (is_redirected) или там нет карты,
    # цель может попытаться использовать пассивные контр-кубики (Frenzy и т.д.)
    # По правилам: берем первый из списка. Он живет пока не сломается для ЭТОЙ карты.
    # На следующую карту он не переносится (это значит, что мы удаляем его из unit.counter_dice при взятии).

    active_counter_die = None

    # Пытаемся взять контр-кубик из пула цели, если это возможно
    # (обычно контр-кубики работают, когда тебя бьют one-sided)
    if target.counter_dice:
        # Берем первый доступный и удаляем из общего пула (он тратится на эту карту)
        active_counter_die = target.counter_dice.pop(0)

    for j, die in enumerate(card.dice_list):
        if source.is_dead() or target.is_dead() or source.is_staggered(): break

        # A. ОБРАБОТКА КОНТР-КУБИКА (ИЗ СПИСКА)
        # Логика: Если есть активный контр-кубик, мы сталкиваемся с ним.
        # Если он побеждает -> Атака отбита (урон атакующему?), кубик живет на след. удар этой карты.
        # Если он проигрывает -> Кубик ломается. Берем СЛЕДУЮЩИЙ из списка, если есть.

        counter_clash_ctx = None

        # Цикл проверки контр-кубиков для ОДНОГО атакующего удара
        # (Пока атака не будет отбита или пока не кончатся контр-кубики)
        while active_counter_die:
            # Создаем контексты
            ctx_atk_c = engine._create_roll_context(source, target, die)
            ctx_cnt = engine._create_roll_context(target, source, active_counter_die)

            val_atk = ctx_atk_c.final_value
            val_cnt = ctx_cnt.final_value

            detail_logs_c = []

            if val_cnt >= val_atk:
                # Контр-кубик ПОБЕДИЛ (или ничья в пользу защиты)
                outcome = f"⚡ Counter Win ({active_counter_die.min_val}-{active_counter_die.max_val})"

                engine._handle_clash_win(ctx_cnt)
                engine._handle_clash_lose(ctx_atk_c)
                engine._resolve_clash_interaction(ctx_cnt, ctx_atk_c, val_cnt - val_atk)

                # Кубик выжил! Он остается active_counter_die для следующего j

                # Логируем столкновение
                report.append({
                    "type": "clash",
                    "round": f"{round_label} (Counter)",
                    "left": {"unit": source.name, "card": card.name, "dice": die.dtype.name, "val": val_atk,
                             "range": "-"},
                    "right": {"unit": target.name, "card": "Passive Counter", "dice": active_counter_die.dtype.name,
                              "val": val_cnt, "range": f"{active_counter_die.min_val}-{active_counter_die.max_val}"},
                    "outcome": outcome, "details": ctx_cnt.log + ctx_atk_c.log
                })

                # Атака остановлена, переходим к следующему кубику карты (break из while)
                # Флаг, чтобы не наносить урон ниже
                counter_clash_ctx = "WIN"
                break

            else:
                # Контр-кубик ПРОИГРАЛ
                outcome = f"⚡ Counter Break"

                # Кубик сломан.
                active_counter_die = None

                # Логируем провал
                report.append({
                    "type": "clash",
                    "round": f"{round_label} (Counter Break)",
                    "left": {"unit": source.name, "card": card.name, "dice": die.dtype.name, "val": val_atk,
                             "range": "-"},
                    "right": {"unit": target.name, "card": "Passive Counter", "dice": "Broken", "val": val_cnt,
                              "range": "-"},
                    "outcome": outcome, "details": ["Counter die destroyed!"]
                })

                # Пробуем взять СЛЕДУЮЩИЙ кубик из запаса на ЭТУ ЖЕ атаку
                if target.counter_dice:
                    active_counter_die = target.counter_dice.pop(0)
                    # Цикл while продолжится с новым кубиком против того же die
                else:
                    # Кубики кончились, атака проходит дальше
                    break

        if counter_clash_ctx == "WIN":
            continue  # Атака отбита, переходим к следующему дайсу карты

        # ---------------------------------------------------------
        # B. ПАССИВНАЯ ЗАЩИТА (из карты в слоте, если контр-кубиков нет)
        def_die = None

        if not is_redirected:
            if def_card and j < len(def_card.dice_list) and not target.is_staggered():
                candidate = def_card.dice_list[j]
                if candidate.dtype in [DiceType.BLOCK, DiceType.EVADE]:
                    def_die = candidate

        if destroy_def and def_die:
            def_die = None

        # Бросок атаки
        ctx_atk = engine._create_roll_context(source, target, die)

        detail_logs = []
        if j == 0 and on_use_logs: detail_logs.extend(on_use_logs)

        # Сценарий 1: Встретили защиту карты
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
            if is_redirected: outcome += " (Redirected)"

            ATK_TYPES = [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]
            if die.dtype in ATK_TYPES:
                engine._apply_damage(ctx_atk, None, "hp")
            else:
                outcome = "Defensive (Skipped)"

            detail_logs.extend(ctx_atk.log)

            r_dice = "None"
            if is_redirected:
                r_dice = "Busy"
            elif destroy_def:
                r_dice = "🚫 Broken"

            report.append({
                "type": "onesided",
                "round": f"{round_label} (D{j + 1})",
                "left": {"unit": source.name, "card": card.name, "dice": die.dtype.name, "val": ctx_atk.final_value,
                         "range": f"{die.min_val}-{die.max_val}"},
                "right": {"unit": target.name, "card": "---", "dice": r_dice, "val": 0, "range": "-"},
                "outcome": outcome, "details": detail_logs
            })

    return report