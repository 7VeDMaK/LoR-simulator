from core.enums import DiceType
from core.logging import logger, LogLevel
from logic.battle_flow.onesided.onesided_resolution import resolve_counter_clash, resolve_passive_defense, \
    resolve_unopposed_hit
# Новые модули
from logic.battle_flow.onesided.onesided_setup import setup_onesided_parameters
from logic.battle_flow.onesided.onesided_utils import fetch_next_counter, store_unused_counter


def process_onesided(engine, source, target, round_label, spd_atk, spd_d, intent_atk=True, is_redirected=False):
    report = []
    card = source.current_card
    def_card = target.current_card

    logger.log(f"One-Sided: {source.name} vs {target.name} (Spd: {spd_atk} vs {spd_d}, Redir={is_redirected})",
               LogLevel.VERBOSE, "OneSided")

    # 1. SETUP
    params = setup_onesided_parameters(engine, source, target, spd_atk, spd_d, intent_atk)

    adv_atk = params["adv_atk"]
    adv_def = params["adv_def"]
    destroy_def = params["destroy_def"]
    defender_breaks_attacker = params["defender_breaks_attacker"]
    on_use_logs = params["on_use_logs"]

    attacker_queue = list(card.dice_list)
    att_idx = 0
    active_counter_die = None

    max_iter = 20
    cur_iter = 0

    # === ОСНОВНОЙ ЦИКЛ ===
    while att_idx < len(attacker_queue) and cur_iter < max_iter:
        cur_iter += 1
        die = attacker_queue[att_idx]

        # Прерывание боя
        if source.is_dead() or target.is_dead() or source.is_staggered():
            logger.log("One-Sided flow interrupted (Death/Stagger)", LogLevel.VERBOSE, "OneSided")
            break

        source.current_die = die
        detail_logs = []
        if att_idx == 0 and on_use_logs: detail_logs.extend(on_use_logs)

        # A. СИТУАЦИЯ: Attacker Broken (Speed > 8)
        if defender_breaks_attacker:
            logger.log(f"Attacker Die {att_idx + 1} Broken by Speed", LogLevel.NORMAL, "OneSided")
            report.append({
                "type": "onesided",
                "round": f"{round_label} (Break)",
                "left": {"unit": source.name, "card": card.name, "dice": "🚫 Broken", "val": 0, "range": "-"},
                "right": {"unit": target.name, "card": "-", "dice": "⚡ Break", "val": 0, "range": "-"},
                "outcome": "🚫 Broken (Speed)", "details": detail_logs + ["Def Speed > 8: Die Destroyed"]
            })
            att_idx += 1
            continue

        # B. ПОИСК ЗАЩИТЫ
        if not active_counter_die:
            active_counter_die = fetch_next_counter(target)

        # C. ВЕТВЛЕНИЕ ЛОГИКИ

        # 1. Counter Clash (Есть активный контр-кубик)
        if active_counter_die:
            res = resolve_counter_clash(engine, source, target, die, active_counter_die, adv_atk)

            # Обновление состояния контр-кубика
            if res["counter_spent"]:
                active_counter_die = None

            l_lbl = die.dtype.name
            r_lbl = f"{active_counter_die.dtype.name if active_counter_die else 'Broken'} (Cnt)"  # Для UI

            report.append({
                "type": "clash",
                "round": f"{round_label} (Counter)",
                "left": {"unit": source.name, "card": card.name, "dice": l_lbl, "val": res["val_atk"], "range": "-"},
                "right": {"unit": target.name, "card": "Stored", "dice": r_lbl, "val": res["val_cnt"], "range": "-"},
                "outcome": res["outcome"], "details": detail_logs + res["details"]
            })

        # 2. Passive Defense (Защитный кубик в слоте защиты)
        else:
            # Проверяем, есть ли подходящий кубик защиты в слоте
            def_die = None
            if not is_redirected and def_card and att_idx < len(def_card.dice_list) and not target.is_staggered():
                candidate = def_card.dice_list[att_idx]
                if candidate.dtype in [DiceType.BLOCK, DiceType.EVADE]:
                    def_die = candidate
                    target.current_die = def_die

            if destroy_def: def_die = None  # Если сломан скоростью

            if def_die:
                res = resolve_passive_defense(engine, source, target, die, def_die, adv_atk, adv_def)
                report.append({
                    "type": "clash",
                    "round": f"{round_label} (Passive)",
                    "left": {"unit": source.name, "card": card.name, "dice": die.dtype.name, "val": res["val_atk"],
                             "range": "-"},
                    "right": {"unit": target.name, "card": def_card.name, "dice": def_die.dtype.name,
                              "val": res["val_def"], "range": "-"},
                    "outcome": res["outcome"], "details": detail_logs + res["details"]
                })

            # 3. Unopposed (Чистый удар)
            else:
                flags = {"is_redirected": is_redirected, "destroy_def": destroy_def}
                res = resolve_unopposed_hit(engine, source, target, die, adv_atk, flags)

                r_dice_show = "🚫 Broken" if destroy_def else ("Busy" if is_redirected else "None")

                report.append({
                    "type": "onesided",
                    "round": f"{round_label} (Hit)",
                    "left": {"unit": source.name, "card": card.name, "dice": die.dtype.name, "val": res["val_atk"],
                             "range": "-"},
                    "right": {"unit": target.name, "card": "-", "dice": r_dice_show, "val": 0, "range": "-"},
                    "outcome": res["outcome"], "details": detail_logs + res["details"]
                })

        att_idx += 1

    # === CLEANUP ===
    # store_unused_counter(target, active_counter_die)

    return report