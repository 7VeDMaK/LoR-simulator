from core.logging import logger, LogLevel
from logic.battle_flow.speed import calculate_speed_advantage


def setup_onesided_parameters(engine, source, target, spd_atk, spd_d, intent_atk):
    """
    Рассчитывает параметры односторонней атаки: скорость, иммунитеты, слом пустого слота.
    """
    # 1. On Use Scripts
    on_use_logs = []
    engine._process_card_self_scripts("on_use", source, target, custom_log_list=on_use_logs)
    
    # === [FIX] АКТИВАЦИЯ ON_USE ДЛЯ ЗАЩИТНИКА (если есть защитная карта) ===
    if target.current_card:
        defender_on_use_logs = []
        engine._process_card_self_scripts("on_use", target, source, custom_log_list=defender_on_use_logs)
        if defender_on_use_logs:
            on_use_logs.extend(defender_on_use_logs)
            logger.log(f"Defender On Use: {' | '.join(defender_on_use_logs)}", LogLevel.VERBOSE, "OneSided")

    # 2. Расчет скорости
    adv_atk, adv_def, _, destroy_def = calculate_speed_advantage(spd_atk, spd_d, intent_atk, True)

    if destroy_def:
        logger.log(f"Speed Advantage: {source.name} breaks {target.name}'s defense die", LogLevel.VERBOSE, "OneSided")

    # 3. Иммунитеты
    source_immune = False
    if hasattr(source, "iter_mechanics"):
        for mech in source.iter_mechanics():
            if mech.prevents_dice_destruction_by_speed(source):
                source_immune = True;
                break

    target_immune = False
    if hasattr(target, "iter_mechanics"):
        for mech in target.iter_mechanics():
            if mech.prevents_dice_destruction_by_speed(target):
                target_immune = True;
                break

    # 4. Break Check (Empty Slot Break / Speed > 8)
    defender_breaks_attacker = False
    def_card = target.current_card

    if not def_card and (spd_d - spd_atk >= 8):
        if hasattr(target, "iter_mechanics"):
            for mech in target.iter_mechanics():
                if hasattr(mech, "can_break_empty_slot") and mech.can_break_empty_slot(target):
                    if source_immune:
                        logger.log(f"🛡️ Empty Slot Break prevented by Immunity for {source.name}", LogLevel.VERBOSE,
                                   "OneSided")
                    else:
                        defender_breaks_attacker = True
                        logger.log(f"Empty Slot Break: {target.name} breaks {source.name} (Spd Diff > 8)",
                                   LogLevel.VERBOSE, "OneSided")
                    break

    # 5. Prevent Destruction (Target Immunity)
    if destroy_def and target_immune:
        destroy_def = False
        adv_atk = True
        logger.log(f"Destruction Prevented for {target.name} (Immunity)", LogLevel.VERBOSE, "OneSided")

    return {
        "adv_atk": adv_atk,
        "adv_def": adv_def,
        "destroy_def": destroy_def,
        "defender_breaks_attacker": defender_breaks_attacker,
        "on_use_logs": on_use_logs
    }