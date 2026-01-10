from core.enums import DiceType
from logic.battle_flow.speed import calculate_speed_advantage


def process_clash(engine, attacker, defender, round_label, is_left, spd_a, spd_d, intent_a=True, intent_d=True):
    report = []
    ac = attacker.current_card
    dc = defender.current_card

    # Определяем типы страниц
    # (В `core/card.py` поле card_type это строка, приводим к нижнему регистру для проверки или используем Enum)
    type_a = ac.card_type.lower()
    type_d = dc.card_type.lower()

    is_ranged_a = (type_a == "ranged")
    is_ranged_d = (type_d == "ranged")
    is_melee_a = (type_a == "melee")
    is_melee_d = (type_d == "melee")

    # Скрипты On Use
    on_use_logs = []
    engine._process_card_self_scripts("on_use", attacker, defender, custom_log_list=on_use_logs)
    engine._process_card_self_scripts("on_use", defender, attacker, custom_log_list=on_use_logs)

    adv_a, adv_d, destroy_a, destroy_d = calculate_speed_advantage(spd_a, spd_d, intent_a, intent_d)

    if destroy_d and "hedonism" in attacker.passives:
        destroy_d = False
        adv_a = True
        # (Опционально можно добавить лог, но пока молча меняем правила)

        # Аналогично, если Защитник (defender) перегнал Атакующего и должен сломать его кубик (destroy_a):
    if destroy_a and "hedonism" in defender.passives:
        destroy_a = False
        adv_d = True

    # Подготовка очередей кубиков (копируем, т.к. будем менять для Melee Recycle)
    queue_a = list(ac.dice_list)
    queue_d = list(dc.dice_list)

    active_counter_a = None
    active_counter_d = None

    def resolve_slot_die(unit, queue, idx, is_broken, active_counter):
        # 1. Если есть активный выживший контр-кубик, он имеет приоритет
        if active_counter:
            return active_counter, True  # Die object, Is_Counter

        # 2. Берем кубик из карты, если он есть
        card_die = queue[idx] if idx < len(queue) else None

        # 3. Если кубик сломан скоростью — уничтожаем его
        if is_broken and card_die:
            # Исключение: Cat Reflexes спасает Evade
            if card_die.dtype == DiceType.EVADE and "cat_reflexes" in unit.talents:
                pass  # Спасен
            else:
                card_die = None  # Уничтожен

        # 4. Если кубика нет (сломан или кончились в карте), ищем новый контр-кубик в пуле
        if not card_die:
            if unit.counter_dice:
                # Проверка на Stagger
                if unit.is_staggered():
                    # Талант Despite Adversities позволяет использовать спец. блоки
                    if "despiteAdversities" in unit.talents:
                        if unit.counter_dice[0].flags and "talent_defense_die" in unit.counter_dice[0].flags:
                            return unit.counter_dice.pop(0), True
                    return None, False

                # Берем контр-кубик
                return unit.counter_dice.pop(0), True

            return None, False  # Совсем ничего нет

        return card_die, False  # Обычный кубик карты

    # Индексы для отслеживания (бесконечный цикл с выходом, т.к. очереди могут расти)
    idx_a = 0
    idx_d = 0

    # Защита от бесконечного цикла (макс 10 итераций)
    max_iterations = 15
    iteration = 0

    while (idx_a < len(queue_a) or idx_d < len(queue_d)) and iteration < max_iterations:
        iteration += 1

        if attacker.is_dead() or defender.is_dead(): break
        # (Stagger проверяется внутри resolve_slot_die для контр-кубиков)

        # 1. Определяем, чем дерутся стороны
        # Передаем флаг destroy, только если мы еще в пределах длины очереди карты
        is_break_a = destroy_a if idx_a < len(queue_a) else False
        is_break_d = destroy_d if idx_d < len(queue_d) else False

        final_die_a, is_cnt_a = resolve_slot_die(attacker, queue_a, idx_a, is_break_a, active_counter_a)
        final_die_d, is_cnt_d = resolve_slot_die(defender, queue_d, idx_d, is_break_d, active_counter_d)

        # Обновляем текущие кубики для пассивок
        attacker.current_die = final_die_a
        defender.current_die = final_die_d

        # Если у обоих пусто (все сломано и контр-кубиков нет), пропускаем слот карты
        if not final_die_a and not final_die_d:
            idx_a += 1
            idx_d += 1
            continue

        # 2. Формируем контексты
        ctx_a = engine._create_roll_context(attacker, defender, final_die_a,
                                            is_disadvantage=adv_a) if final_die_a else None
        ctx_d = engine._create_roll_context(defender, attacker, final_die_d,
                                            is_disadvantage=adv_d) if final_die_d else None

        val_a = ctx_a.final_value if ctx_a else 0
        val_d = ctx_d.final_value if ctx_d else 0

        # Связываем
        if ctx_a and ctx_d:
            ctx_a.opponent_ctx = ctx_d
            ctx_d.opponent_ctx = ctx_a

        outcome = ""
        detail_logs = []
        if iteration == 1 and on_use_logs: detail_logs.extend(on_use_logs)

        # 3. Резолв
        # --- CLASH ---
        if ctx_a and ctx_d:
            if val_a > val_d:
                outcome = f"🏆 {attacker.name} Win"
                if is_cnt_a: outcome += " (Cnt)"

                engine._handle_clash_win(ctx_a)
                engine._handle_clash_lose(ctx_d)
                engine._resolve_clash_interaction(ctx_a, ctx_d, val_a - val_d)

                # Логика контр-кубиков
                if is_cnt_d:
                    active_counter_d = None  # Защитник проиграл контрой -> она ломается
                    detail_logs.append("⚡ Def Counter Broken")
                if is_cnt_a:
                    active_counter_a = final_die_a  # Атакующий выиграл контрой -> она остается

                # Melee Recycle (только для карт)
                if not is_cnt_a and not is_cnt_d and is_melee_a and is_ranged_d:
                    if final_die_a.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
                        queue_a.append(final_die_a)
                        detail_logs.append("♻️ Melee Recycled")

            elif val_d > val_a:
                outcome = f"🏆 {defender.name} Win"
                if is_cnt_d: outcome += " (Cnt)"

                engine._handle_clash_win(ctx_d)
                engine._handle_clash_lose(ctx_a)
                engine._resolve_clash_interaction(ctx_d, ctx_a, val_d - val_a)

                if is_cnt_a:
                    active_counter_a = None  # Атакующий проиграл контрой -> ломается
                    detail_logs.append("⚡ Atk Counter Broken")
                if is_cnt_d:
                    active_counter_d = final_die_d  # Защитник выиграл контрой -> остается

                if not is_cnt_d and not is_cnt_a and is_melee_d and is_ranged_a:
                    if final_die_d.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
                        queue_d.append(final_die_d)
                        detail_logs.append("♻️ Melee Recycled")
            else:
                outcome = "🤝 Draw"
                engine._handle_clash_draw(ctx_a)
                engine._handle_clash_draw(ctx_d)
                # При ничьей контр-кубики обычно выживают

        # --- ONE SIDED (ATTACKER) ---
        elif ctx_a:
            outcome = f"🏹 {attacker.name} Hit"
            engine._apply_damage(ctx_a, None, "hp")
            # Если ударили контр-кубиком без сопротивления -> он тратится (Discard)
            if is_cnt_a:
                active_counter_a = None

        # --- ONE SIDED (DEFENDER) ---
        elif ctx_d:
            outcome = f"🏹 {defender.name} Hit"
            engine._apply_damage(ctx_d, None, "hp")
            if is_cnt_d:
                active_counter_d = None

        # Сбор логов
        if ctx_a: detail_logs.extend(ctx_a.log)
        if ctx_d: detail_logs.extend(ctx_d.log)

        # Красивое отображение
        l_lbl = final_die_a.dtype.name if final_die_a else "Broken"
        r_lbl = final_die_d.dtype.name if final_die_d else "Broken"
        if is_cnt_a: l_lbl += " (C)"
        if is_cnt_d: r_lbl += " (C)"

        l_rng = f"{final_die_a.min_val}-{final_die_a.max_val}" if final_die_a else "-"
        r_rng = f"{final_die_d.min_val}-{final_die_d.max_val}" if final_die_d else "-"

        report.append({
            "type": "clash",
            "round": f"{round_label} ({iteration})",
            "left": {"unit": attacker.name if is_left else defender.name,
                     "card": ac.name if is_left else dc.name,
                     "dice": l_lbl if is_left else r_lbl, "val": val_a if is_left else val_d,
                     "range": l_rng if is_left else r_rng},
            "right": {"unit": defender.name if is_left else attacker.name,
                      "card": dc.name if is_left else ac.name,
                      "dice": r_lbl if is_left else l_lbl, "val": val_d if is_left else val_a,
                      "range": r_rng if is_left else l_rng},
            "outcome": outcome, "details": detail_logs
        })

        if idx_a < len(queue_a): idx_a += 1
        if idx_d < len(queue_d): idx_d += 1

    return report