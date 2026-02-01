import random

from core.enums import CardType
from core.logging import logger, LogLevel


def process_mass_attack(engine, action, opposing_team, round_label, executed_slots=None):
    """
    Обрабатывает массовую атаку.
    executed_slots: множество (unit_name, slot_idx), которые уже походили.
    """
    source = action['source']
    card = source.current_card

    is_summation = (card.card_type == CardType.MASS_SUMMATION.value)

    # Настройки выбора слотов (кто чем защищается)
    mass_defenses = action['slot_data'].get('mass_defenses', {})

    report = []
    atk_type_str = "Summation" if is_summation else "Individual"
    logger.log(f"💥 {source.name} uses Mass Attack: {card.name} ({atk_type_str})", LogLevel.NORMAL, "MassAtk")

    # === [FIX] 0. ЗАПУСК СКРИПТОВ ON USE ===
    # Массовая атака должна активировать свои эффекты "При использовании" (баффы, дров и т.д.)
    # Передаем target=None, так как On Use для масс атак обычно баффает себя или накладывает глобальные эффекты
    on_use_logs = []
    engine._process_card_self_scripts("on_use", source, None, custom_log_list=on_use_logs)

    for log in on_use_logs:
        logger.log(f"MassAtk On Use: {log}", LogLevel.VERBOSE, "MassAtk")

    # Перебираем всех живых врагов
    for e_idx, target in enumerate(opposing_team):
        if target.is_dead(): continue

        target_slot = None
        target_dice_list = []
        is_undefended = False
        chosen_s_idx = -1

        # --- 1. СБОР ДОСТУПНЫХ СЛОТОВ ---
        valid_defense_slots = []
        executed_card_slots = []

        if not target.is_staggered() and target.active_slots:
            for s_i, s in enumerate(target.active_slots):
                if not s.get('card'): continue

                is_executed = False
                if executed_slots and (target.name, s_i) in executed_slots:
                    is_executed = True

                if not is_executed:
                    valid_defense_slots.append((s_i, s))
                else:
                    executed_card_slots.append((s_i, s))

        # --- 2. ВЫБОР СЛОТА (Manual vs Auto) ---
        user_choice = mass_defenses.get(str(e_idx), "Auto")

        if user_choice != "Auto" and user_choice.startswith("S"):
            try:
                s_idx = int(user_choice[1:]) - 1
                if 0 <= s_idx < len(target.active_slots):
                    slot = target.active_slots[s_idx]
                    chosen_s_idx = s_idx
                    if slot.get('card'):
                        target_slot = slot
                        if executed_slots and (target.name, s_idx) in executed_slots:
                            is_undefended = True
                            logger.log(f"Targeting {target.name} (Manual S{s_idx + 1}: Executed -> One-Sided)",
                                       LogLevel.VERBOSE, "MassAtk")
                        else:
                            logger.log(f"Targeting {target.name} (Manual S{s_idx + 1}: {slot['card'].name})",
                                       LogLevel.VERBOSE, "MassAtk")
                    else:
                        is_undefended = True
                        logger.log(f"Targeting {target.name} (Manual S{s_idx + 1}: Empty -> One-Sided)",
                                   LogLevel.VERBOSE, "MassAtk")
            except:
                pass

        if not target_slot and not is_undefended:
            if valid_defense_slots:
                s_idx, slot = random.choice(valid_defense_slots)
                target_slot = slot
                chosen_s_idx = s_idx
                logger.log(f"Targeting {target.name} (Auto: S{s_idx + 1} {slot['card'].name})", LogLevel.VERBOSE,
                           "MassAtk")
            elif executed_card_slots:
                s_idx, slot = random.choice(executed_card_slots)
                target_slot = slot
                chosen_s_idx = s_idx
                is_undefended = True
                logger.log(f"Targeting {target.name} (Auto: All executed -> One-Sided vs S{s_idx + 1})",
                           LogLevel.VERBOSE, "MassAtk")
            else:
                is_undefended = True
                logger.log(f"Targeting {target.name} (No cards/Staggered -> One-Sided)", LogLevel.VERBOSE, "MassAtk")

        # --- 3. ФИКСАЦИЯ ИСПОЛЬЗОВАНИЯ ---
        if target_slot and not is_undefended and executed_slots is not None and chosen_s_idx != -1:
            executed_slots.add((target.name, chosen_s_idx))

        if target_slot and not is_undefended:
            target_dice_list = target_slot['card'].dice_list
            # === [FIX] АКТИВАЦИЯ ON_USE ДЛЯ ЗАЩИТНИКА ===
            # Временно устанавливаем карту защитника для активации скриптов
            old_defender_card = target.current_card
            target.current_card = target_slot['card']
            
            defender_on_use_logs = []
            engine._process_card_self_scripts("on_use", target, source, custom_log_list=defender_on_use_logs)
            if defender_on_use_logs:
                logger.log(f"Defender On Use: {' | '.join(defender_on_use_logs)}", LogLevel.VERBOSE, "MassAtk")
            
            # Восстанавливаем оригинальную карту
            target.current_card = old_defender_card
        else:
            target_dice_list = []

        # === ЛОГИКА MASS-SUMMATION (Сумма на Сумму) ===
        if is_summation:
            atk_sum = 0
            atk_rolls = []
            for d in card.dice_list:
                ctx = engine._create_roll_context(source, target, d)
                atk_sum += ctx.final_value
                atk_rolls.append(str(ctx.final_value))

            def_sum = 0
            def_rolls = []
            for d in target_dice_list:
                ctx = engine._create_roll_context(target, source, d)
                def_sum += ctx.final_value
                def_rolls.append(str(ctx.final_value))

            outcome = ""
            details = []
            if on_use_logs and e_idx == 0:  # Добавляем логи On Use только к первому врагу, чтобы не спамить
                details.extend(on_use_logs)

            def_range_str = f"Rolls: {','.join(def_rolls)}" if def_rolls else "One-Sided"

            logger.log(f"∑ Clash: {source.name}({atk_sum}) vs {target.name}({def_sum})", LogLevel.VERBOSE, "MassAtk")

            if atk_sum > def_sum:
                outcome = f"🎯 Hit! ({atk_sum} > {def_sum})"
                if is_undefended:
                    details.append("💥 One-Sided Hit")
                elif target_slot:
                    target_slot['card'] = None
                    details.append(f"🚫 {target.name}'s page destroyed!")
                    logger.log(f"🚫 {target.name}'s page destroyed", LogLevel.NORMAL, "MassAtk")

                for d in card.dice_list:
                    ctx_dmg = engine._create_roll_context(source, target, d)
                    engine._apply_damage(ctx_dmg, None, "hp")
                    details.extend(ctx_dmg.log)
            else:
                outcome = f"🛡️ Blocked ({def_sum} >= {atk_sum})"
                details.append(f"{target.name} withstood the attack.")

            report.append({
                "type": "clash",
                "round": f"{round_label} (Mass)",
                "left": {"unit": source.name, "card": "MASS SUM", "dice": "Sum", "val": atk_sum,
                         "range": f"Rolls: {','.join(atk_rolls)}"},
                "right": {"unit": target.name, "card": "Defense", "dice": "Sum", "val": def_sum,
                          "range": def_range_str},
                "outcome": outcome, "details": details
            })

        # === ЛОГИКА MASS-INDIVIDUAL (Кубик на Кубик) ===
        else:
            num_checks = len(card.dice_list)
            for i in range(num_checks):
                die_atk = card.dice_list[i]
                die_def = target_dice_list[i] if i < len(target_dice_list) else None

                ctx_atk = engine._create_roll_context(source, target, die_atk)
                val_atk = ctx_atk.final_value

                val_def = 0
                ctx_def = None
                if die_def:
                    ctx_def = engine._create_roll_context(target, source, die_def)
                    val_def = ctx_def.final_value

                details = []
                if on_use_logs and e_idx == 0 and i == 0:
                    details.extend(on_use_logs)

                outcome = ""
                logger.log(f"Indiv Clash #{i + 1}: {val_atk} vs {val_def}", LogLevel.VERBOSE, "MassAtk")

                if val_atk > val_def:
                    outcome = "🎯 Hit"
                    if is_undefended:
                        details.append("💥 One-Sided Hit")
                    elif target_slot and i < len(target_slot['card'].dice_list):
                        details.append(f"🚫 {target.name}'s Die #{i + 1} broken")

                    engine._apply_damage(ctx_atk, None, "hp")
                    details.extend(ctx_atk.log)
                else:
                    outcome = "🛡️ Blocked"

                r_dice_name = die_def.dtype.name if die_def else "None"
                if is_undefended: r_dice_name = "Used/None"

                report.append({
                    "type": "clash",
                    "round": f"{round_label} (M-Indiv {i + 1})",
                    "left": {"unit": source.name, "card": "Mass", "dice": die_atk.dtype.name, "val": val_atk,
                             "range": "-"},
                    "right": {"unit": target.name, "card": "-", "dice": r_dice_name, "val": val_def, "range": "-"},
                    "outcome": outcome, "details": details
                })

    return report