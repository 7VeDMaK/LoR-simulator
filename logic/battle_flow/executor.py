from logic.battle_flow.mass_attack import process_mass_attack


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
    if src_id in executed_slots: return []

    # Проверка состояния бойца
    if source.is_dead() or source.is_staggered(): return []

    # Загружаем карту
    source.current_card = act['slot_data'].get('card')
    if not source.current_card: return []

    intent_src = act['slot_data'].get('destroy_on_speed', True)
    target = act['target_unit']

    # === 1. MASS ATTACK ===
    if "mass" in act['card_type']:
        executed_slots.add(src_id)
        p_label = "Mass Atk" if act['is_left'] else "Enemy Mass"

        # Кулдаун
        if source.current_card.id != "unknown":
            source.card_cooldowns[source.current_card.id] = source.current_card.tier

        return process_mass_attack(engine, act, act['opposing_team'], p_label)

    # === 2. ON PLAY / INSTANT ===
    if "on_play" in act['card_type'] or "on play" in act['card_type']:
        executed_slots.add(src_id)
        engine._process_card_self_scripts("on_use", source, target)
        tgt_name = f" on {target.name}" if target else ""

        details = [f"⚡ {source.name} used {act['slot_data']['card'].name}{tgt_name}"]
        if engine.logs:
            details.extend(engine.logs)

        # Кулдаун
        if source.current_card.id != "unknown":
            source.card_cooldowns[source.current_card.id] = source.current_card.tier

        return [{"round": "On Play", "details": details}]

    # === 3. STANDARD COMBAT (Melee, Ranged, Offensive) ===
    # target = act['target_unit'] (уже получен выше)
    t_s_idx = act['target_slot_idx']

    if not target or target.is_dead():
        return []

    # Проверяем Clash или One-Sided
    is_clash = False
    tgt_id = (target.name, t_s_idx)
    target_slot = None
    slot_data = act['slot_data']

    if t_s_idx != -1 and t_s_idx < len(target.active_slots):
        target_slot = target.active_slots[t_s_idx]

        if slot_data.get('force_onesided'):
            is_clash = False
        # Clash если: слот цели свободен, там есть карта, цель не в стане
        elif (tgt_id not in executed_slots) and \
                target_slot.get('card') and \
                not target.is_staggered():
            is_clash = True

    # Кулдаун Атакующего
    if source.current_card.id != "unknown":
        source.card_cooldowns[source.current_card.id] = max(0, source.current_card.tier)

    battle_logs = []
    spd_src = act['slot_data']['speed']

    if is_clash:
        # === CLASH ===
        executed_slots.add(src_id)
        executed_slots.add(tgt_id)

        target.current_card = target_slot.get('card')
        spd_tgt = target_slot['speed']
        intent_tgt = target_slot.get('destroy_on_speed', True)

        # Кулдаун Защитника (он тоже тратит карту)
        if target.current_card and target.current_card.id != "unknown":
            target.card_cooldowns[target.current_card.id] = target.current_card.tier

        engine.log(f"⚔️ Clash: {source.name} vs {target.name}")

        logs = engine._resolve_card_clash(
            source, target, "Clash", act['is_left'],
            spd_src, spd_tgt,
            intent_a=intent_src, intent_d=intent_tgt
        )
        battle_logs.extend(logs)

    else:
        # === ONE-SIDED ===
        executed_slots.add(src_id)
        p_label = "L" if act['is_left'] else "R"

        is_redirected = slot_data.get('force_onesided', False)

        # Слот занят, если он в списке сыгранных ИЛИ атака перенаправлена
        is_target_busy = (tgt_id in executed_slots) or is_redirected

        spd_def_val = 0
        if target_slot: spd_def_val = target_slot['speed']

        logs = engine._resolve_one_sided(
            source, target, f"{p_label} Hit",
            spd_src, spd_def_val,
            intent_atk=intent_src,
            is_redirected=is_target_busy
        )
        battle_logs.extend(logs)

    return battle_logs