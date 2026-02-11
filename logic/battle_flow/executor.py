from core.logging import logger, LogLevel
from logic.battle_flow.mass_attack import process_mass_attack


def _apply_card_cooldown(unit, card):
    """
    Накладывает кулдаун на карту.
    """
    if not unit or not card or card.id == "unknown":
        return

    cd_val = max(0, card.tier)

    if cd_val > 0:
        if card.id not in unit.card_cooldowns:
            unit.card_cooldowns[card.id] = []

        if isinstance(unit.card_cooldowns[card.id], int):
            unit.card_cooldowns[card.id] = [unit.card_cooldowns[card.id]]

        unit.card_cooldowns[card.id].append(cd_val)
        logger.log(f"⏳ {unit.name}: Cooldown applied to '{card.name}' ({cd_val} turns)", LogLevel.NORMAL, "Cooldown")


def _consume_one_time_card(unit, card):
    if not unit or not card:
        return
    if "one_time" not in getattr(card, "flags", []):
        return

    if card.id in unit.deck:
        unit.deck.remove(card.id)

    cds = unit.card_cooldowns.get(card.id)
    if isinstance(cds, list) and cds:
        cds.pop()
        if not cds:
            unit.card_cooldowns.pop(card.id, None)

    logger.log(f"🧨 {unit.name}: One-time card consumed ({card.name})", LogLevel.NORMAL, "Cooldown")


def execute_single_action(engine, act, executed_slots):
    """
    Фаза 2 (Микро): Выполнение конкретного действия из очереди.
    """
    engine.logs = []
    source = act['source']
    s_idx = act['source_idx']

    # ID слота источника
    src_id = (source.name, s_idx)

    # Если этот слот уже сыграл, пропускаем
    if src_id in executed_slots:
        return []

    # Проверка состояния бойца
    if source.is_dead() or source.is_staggered():
        logger.log(f"🚫 {source.name} action skipped (Dead or Staggered)", LogLevel.VERBOSE, "Executor")
        return []

    # Загружаем карту
    source.current_card = act['slot_data'].get('card')
    if not source.current_card:
        return []

    intent_src = act['slot_data'].get('destroy_on_speed', True)
    target = act['target_unit']

    # === 1. MASS ATTACK ===
    if "mass" in act['card_type']:
        logger.log(f"💥 {source.name} initiates Mass Attack: {source.current_card.name}", LogLevel.NORMAL, "Combat")

        # Помечаем слот атакующего как использованный
        executed_slots.add(src_id)

        p_label = "Mass Atk" if act['is_left'] else "Enemy Mass"

        # Кулдаун
        _apply_card_cooldown(source, source.current_card)
        _consume_one_time_card(source, source.current_card)

        # [FIX] Передаем executed_slots, чтобы функция знала, какие слоты врагов уже пусты/использованы
        return process_mass_attack(engine, act, act['opposing_team'], p_label, executed_slots)

    # === 2. ON PLAY / INSTANT ===
    if "on_play" in act['card_type'] or "on play" in act['card_type']:
        logger.log(f"⚡ {source.name} activates On Play: {source.current_card.name}", LogLevel.NORMAL, "Combat")
        executed_slots.add(src_id)
        engine._process_card_self_scripts("on_use", source, target)
        tgt_name = f" on {target.name}" if target else ""

        details = [f"⚡ {source.name} used {act['slot_data']['card'].name}{tgt_name}"]
        if engine.logs:
            details.extend(engine.logs)

        _apply_card_cooldown(source, source.current_card)
        _consume_one_time_card(source, source.current_card)
        return [{"round": "On Play", "details": details}]

    # === 3. STANDARD COMBAT ===
    t_s_idx = act['target_slot_idx']

    if not target or target.is_dead():
        logger.log(f"⚠️ {source.name}: Target missing or dead, action skipped.", LogLevel.VERBOSE, "Executor")
        return []

    is_clash = False
    tgt_id = (target.name, t_s_idx)
    target_slot = None
    slot_data = act['slot_data']

    if t_s_idx != -1 and t_s_idx < len(target.active_slots):
        target_slot = target.active_slots[t_s_idx]

        if slot_data.get('force_onesided'):
            is_clash = False
        elif (tgt_id not in executed_slots) and \
                target_slot.get('card') and \
                not target.is_staggered():
            is_clash = True

    _apply_card_cooldown(source, source.current_card)
    _consume_one_time_card(source, source.current_card)
    battle_logs = []
    spd_src = act['slot_data']['speed']

    if is_clash:
        executed_slots.add(src_id)
        executed_slots.add(tgt_id)

        target.current_card = target_slot.get('card')
        spd_tgt = target_slot['speed']
        intent_tgt = target_slot.get('destroy_on_speed', True)
        _apply_card_cooldown(target, target.current_card)

        logger.log(f"⚔️ Clash: {source.name} vs {target.name}", LogLevel.NORMAL, "Combat")

        logs = engine._resolve_card_clash(
            source, target, "Clash", act['is_left'],
            spd_src, spd_tgt,
            intent_a=intent_src, intent_d=intent_tgt
        )
        battle_logs.extend(logs)

    else:
        executed_slots.add(src_id)
        p_label = "L" if act['is_left'] else "R"

        is_redirected = slot_data.get('force_onesided', False)
        is_target_busy = (tgt_id in executed_slots) or is_redirected

        spd_def_val = 0
        if target_slot:
            spd_def_val = target_slot['speed']
            if not is_target_busy and not target.is_staggered():
                target.current_card = target_slot.get('card')
            else:
                target.current_card = None
        else:
            target.current_card = None

        logger.log(f"🏹 One-Sided: {source.name} -> {target.name} ({'Redirected' if is_redirected else 'Direct'})",
                   LogLevel.NORMAL, "Combat")

        logs = engine._resolve_one_sided(
            source, target, f"{p_label} Hit",
            spd_src, spd_def_val,
            intent_atk=intent_src,
            is_redirected=is_target_busy
        )
        battle_logs.extend(logs)

    return battle_logs