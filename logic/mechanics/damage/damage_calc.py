from logic.calculations.base_calc import get_modded_value


def _calculate_resistance(target, source_ctx, dtype_name, dice_obj, log_list=None):
    """Рассчитывает множитель сопротивления цели."""
    # 1. Base Resistance
    res = getattr(target.hp_resists, dtype_name, 1.0)

    # 2. Attacker Adaptation
    if source_ctx and source_ctx.source:
        adapt_stack = source_ctx.source.get_status("adaptation")
        if adapt_stack > 0:
            min_res = 0.25 * adapt_stack
            if res < min_res:
                res = min_res
                if log_list is not None:
                    log_list.append(f"🧬 Adaptation Pierce: Res {res:.2f}")

    # 3. Stagger Multiplier
    is_stag_hit = False
    if target.is_staggered():
        stagger_mult = 2.0
        if hasattr(target, "apply_mechanics_filter"):
            stagger_mult = target.apply_mechanics_filter("modify_stagger_damage_multiplier", stagger_mult)
        res = max(res, stagger_mult)
        is_stag_hit = True

    # 4. Defender Mechanics
    if hasattr(target, "apply_mechanics_filter"):
        res = target.apply_mechanics_filter(
            "modify_resistance",
            res,
            damage_type=dtype_name,
            dice=dice_obj,
            log_list=log_list
        )

    # === [NEW] 5. Attacker Mechanics (Penetration / Void Cleave) ===
    if source_ctx and source_ctx.source and hasattr(source_ctx.source, "apply_mechanics_filter"):
        res = source_ctx.source.apply_mechanics_filter(
            "on_calculate_damage_multiplier",  # Хук для таланта
            res,
            attacker=source_ctx.source,
            target=target,
            dice=dice_obj,
            damage_type=dtype_name
        )

    return res, is_stag_hit

def _calculate_outgoing_damage(attacker, attacker_ctx, dmg_type):
    """Рассчитывает исходящий урон атакующего до применения защиты цели."""
    base_dmg = attacker_ctx.final_value
    stat_bonus = get_modded_value(0, "damage_deal", attacker.modifiers)
    current_dmg = base_dmg + stat_bonus

    if hasattr(attacker, "apply_mechanics_filter"):
        dmg_before = current_dmg
        current_dmg = attacker.apply_mechanics_filter(
            "modify_outgoing_damage",
            current_dmg,
            damage_type=dmg_type,
            log_list=None
        )
        diff = current_dmg - dmg_before

        total_boost = stat_bonus + diff
        if total_boost != 0:
            attacker_ctx.log.append(f"👊 Atk Boost: {total_boost:+}")
    elif stat_bonus != 0:
        attacker_ctx.log.append(f"👊 Atk Boost: {stat_bonus:+}")

    if attacker_ctx.damage_multiplier != 1.0:
        current_dmg = int(current_dmg * attacker_ctx.damage_multiplier)

    return max(0, current_dmg)