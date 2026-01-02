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

    # Передаем интенты в калькулятор
    adv_a, adv_d, destroy_a, destroy_d = calculate_speed_advantage(spd_a, spd_d, intent_a, intent_d)

    # Подготовка очередей кубиков (копируем, т.к. будем менять для Melee Recycle)
    queue_a = list(ac.dice_list)
    queue_d = list(dc.dice_list)

    # Индексы для отслеживания (бесконечный цикл с выходом, т.к. очереди могут расти)
    idx_a = 0
    idx_d = 0

    # Защита от бесконечного цикла (макс 10 итераций)
    max_iterations = 15
    iteration = 0

    while idx_a < len(queue_a) and idx_d < len(queue_d) and iteration < max_iterations:
        iteration += 1

        # Проверка жизни
        if attacker.is_dead() or defender.is_dead(): break
        if attacker.is_staggered() or defender.is_staggered(): break

        die_a = queue_a[idx_a]
        die_d = queue_d[idx_d]

        # Разрушение кубиков скоростью
        if destroy_a: die_a = None
        if destroy_d: die_d = None

        if not die_a and not die_d:
            idx_a += 1;
            idx_d += 1;
            continue

        # Броски
        ctx_a = engine._create_roll_context(attacker, defender, die_a, is_disadvantage=adv_a)
        ctx_d = engine._create_roll_context(defender, attacker, die_d, is_disadvantage=adv_d)

        val_a = ctx_a.final_value if ctx_a else 0
        val_d = ctx_d.final_value if ctx_d else 0

        outcome = ""
        detail_logs = []
        if iteration == 1 and on_use_logs: detail_logs.extend(on_use_logs)

        # === ЛОГИКА ПОБЕДЫ ===
        winner = None  # 'A', 'D' or None (Draw)

        if ctx_a and ctx_d:
            if val_a > val_d:
                winner = 'A'
                outcome = f"🏆 {attacker.name} Win"
                engine._handle_clash_win(ctx_a)
                engine._handle_clash_lose(ctx_d)
                engine._resolve_clash_interaction(ctx_a, ctx_d, val_a - val_d)

                # === RANGED SPECIFIC RULES ===
                # Если Ranged проиграл (D) против Block/Counter -> Нет урона?
                # Это обрабатывается в resolve_interaction, но здесь можно добавить логику.

                # === MELEE RECYCLE ===
                # Если Melee (A) выиграл атакующим кубиком против Ranged (D)
                if is_melee_a and is_ranged_d:
                    # Проверяем, что это Атака
                    if die_a.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
                        queue_a.append(die_a)
                        detail_logs.append("♻️ Melee die recycled!")

            elif val_d > val_a:
                winner = 'D'
                outcome = f"🏆 {defender.name} Win"
                engine._handle_clash_win(ctx_d)
                engine._handle_clash_lose(ctx_a)
                engine._resolve_clash_interaction(ctx_d, ctx_a, val_d - val_a)

                # === MELEE RECYCLE (Defender) ===
                if is_melee_d and is_ranged_a:
                    if die_d.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
                        queue_d.append(die_d)
                        detail_logs.append("♻️ Melee die recycled!")

            else:
                outcome = "🤝 Draw"
                # При ничьей оба кубика сгорают

        # Если у одного нет кубика (разрушен или кончились)
        elif ctx_a:
            outcome = f"🏹 {attacker.name} Unanswered"
            engine._apply_damage(ctx_a, None, "hp")
        elif ctx_d:
            outcome = f"🏹 {defender.name} Unanswered"
            engine._apply_damage(ctx_d, None, "hp")

        if ctx_a: detail_logs.extend(ctx_a.log)
        if ctx_d: detail_logs.extend(ctx_d.log)

        # UI
        l_dice = die_a.dtype.name if die_a else "None"
        r_dice = die_d.dtype.name if die_d else "None"

        report.append({
            "type": "clash",
            "round": f"{round_label} (Roll {iteration})",
            "left": {"unit": attacker.name if is_left else defender.name, "card": ac.name if is_left else dc.name,
                     "dice": l_dice if is_left else r_dice, "val": val_a if is_left else val_d, "range": "-"},
            "right": {"unit": defender.name if is_left else attacker.name, "card": dc.name if is_left else ac.name,
                      "dice": r_dice if is_left else l_dice, "val": val_d if is_left else val_a, "range": "-"},
            "outcome": outcome, "details": detail_logs
        })

        # Переходим к следующим кубикам
        # (Победивший кубик в Clash обычно сгорает, если это не Counter, но в Ranged vs Melee рецикл добавляет копию в конец)
        idx_a += 1
        idx_d += 1

    # 1. Если у АТАКУЮЩЕГО остались кубики
    while idx_a < len(
            queue_a) and not attacker.is_dead() and not attacker.is_staggered() and not defender.is_dead():
        die_a = queue_a[idx_a]

        # Бросаем как одностороннюю атаку
        # Важно: Защитник уже без кубиков (или они сломаны), так что защиты нет
        ctx_a = engine._create_roll_context(attacker, defender, die_a)

        # Применяем урон
        engine._apply_damage(ctx_a, None, "hp")

        # Логируем
        report.append({
            "type": "onesided",  # Отображаем как одностороннюю атаку
            "round": f"{round_label} (Extra {idx_a + 1})",
            "left": {"unit": attacker.name if is_left else defender.name, "card": ac.name if is_left else dc.name,
                     "dice": die_a.dtype.name, "val": ctx_a.final_value, "range": "-"},
            "right": {"unit": defender.name if is_left else attacker.name, "card": "-",
                      "dice": "None", "val": 0, "range": "-"},
            "outcome": "Unopposed (Clash Win)",
            "details": ctx_a.log
        })

        idx_a += 1

    return report