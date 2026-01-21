from core.logging import logger, LogLevel
from logic.calculations.formulas import get_modded_value


# === HELPERS ===

def _check_death_threshold(unit, current_val, max_val, resource_name):
    """
    Checks if a resource has dropped below zero, calculates overkill, and returns the clamped value (0).
    """
    if current_val <= 0:
        overkill = abs(current_val)
        unit.overkill_damage = overkill
        return 0
    return current_val


def _get_attack_info(source_ctx):
    """Extracts dice type and object from context."""
    dtype_name = "slash"
    dice_obj = None
    if source_ctx and source_ctx.dice:
        dice_obj = source_ctx.dice
        dtype_name = dice_obj.dtype.value.lower()
    return dtype_name, dice_obj


def _calculate_resistance(target, source_ctx, dtype_name, dice_obj, log_list=None):
    """
    Calculates the final resistance multiplier.
    1. Base Resistance (HP Resists).
    2. Attacker Adaptation (Pierce).
    3. Stagger Multiplier (x2.0).
    4. Defender Mechanics hooks (Defender Adaptation).
    """
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

    return res, is_stag_hit


def _apply_resource_damage(target, amount: int, resource_type: str, source_ctx, log_prefix=""):
    """
    Applies damage to HP or SP, checks death thresholds, and handles logging.
    """
    if resource_type == "hp":
        new_val = target.current_hp - amount
        target.current_hp = _check_death_threshold(target, new_val, target.max_hp, "HP")

        hit_msg = f"💥 **{target.name}**: {log_prefix}Hit {amount} HP"
        if target.is_staggered():
            hit_msg += " (Staggered)"

        if target.current_hp == 0 and target.overkill_damage > 0:
            hit_msg += f" (DEAD! Overkill: {target.overkill_damage})"

        if source_ctx: source_ctx.log.append(hit_msg)
        logger.log(f"💥 {target.name} took {amount} HP Damage", LogLevel.MINIMAL, "Damage")

    elif resource_type == "sp":
        new_val = target.current_sp - amount
        target.current_sp = _check_death_threshold(target, new_val, target.max_sp, "SP")

        if source_ctx:
            source_ctx.log.append(f"🧠 **White Dmg**: {amount} SP")
            if target.current_sp == 0 and target.overkill_damage > 0:
                source_ctx.log.append(f"🤯 **PANIC/DEATH**: Overkill {target.overkill_damage}")

        logger.log(f"🧠 {defender_name_safe(target)} took {amount} SP Damage (White)", LogLevel.MINIMAL, "Damage")


def _calculate_outgoing_damage(attacker, attacker_ctx, dmg_type):
    """
    Calculates the final outgoing damage value considering base roll, stats, statuses, and multipliers.
    """
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


def _apply_stagger_side_damage(target, attacker_ctx, final_amt):
    """
    Calculates and applies side-damage to Stagger when an HP attack connects.
    """
    if target.is_staggered() or target.get_status("red_lycoris") > 0:
        return

    dtype, dice_obj = _get_attack_info(attacker_ctx)

    # Resistance
    res_stg, _ = _calculate_resistance(
        target, attacker_ctx, dtype, dice_obj,
        log_list=attacker_ctx.log
    )

    stg_base_amt = final_amt

    # Incoming Filters (Protection etc)
    if hasattr(target, "apply_mechanics_filter"):
        stg_base_amt = target.apply_mechanics_filter("modify_incoming_damage", stg_base_amt, damage_type="hp")

    # Stat Defense (Tough Skin)
    stat_reduction = get_modded_value(0, "damage_take", target.modifiers)
    stg_after_def = max(0, stg_base_amt - stat_reduction)

    # Apply Resistance
    stg_dmg = int(stg_after_def * res_stg)

    # Stagger Take Modifiers
    stg_take_pct = target.modifiers["stagger_take"]["pct"]
    if stg_take_pct != 0:
        mod_mult = 1.0 + (stg_take_pct / 100.0)
        stg_dmg = int(stg_dmg * mod_mult)

    # Apply
    target.current_stagger = max(0, target.current_stagger - stg_dmg)
    logger.log(f"😵 {target.name} took {stg_dmg} Stagger Side-Damage (Res: {res_stg:.2f})", LogLevel.MINIMAL, "Damage")


def defender_name_safe(unit):
    return unit.name if hasattr(unit, 'name') else "Unknown"


# === MAIN FUNCTIONS ===

def deal_direct_damage(source_ctx, target, amount: int, dmg_type: str, trigger_event_func):
    """
    Calculates and deals damage to HP or Stagger.
    Handles filters, defenses, resistances, thresholds, barriers, and event triggers.
    """
    if amount <= 0: return

    initial_amount = amount

    if hasattr(target, "apply_mechanics_filter"):
        amount = target.apply_mechanics_filter("modify_incoming_damage", amount, damage_type=dmg_type)

    if amount <= 0 < initial_amount:
        if source_ctx: source_ctx.log.append("🛡️ Damage mitigated to 0")
        return

    final_dmg = 0
    dtype_name, dice_obj = _get_attack_info(source_ctx)
    log_list = source_ctx.log if source_ctx else None

    if dmg_type == "hp":
        # 2. Stat Defenses (Tough Skin)
        stat_reduction = get_modded_value(0, "damage_take", target.modifiers)
        amount_after_def = max(0, amount - stat_reduction)

        # 3. Resistance Calculation
        res, is_stag_hit = _calculate_resistance(target, source_ctx, dtype_name, dice_obj, log_list)
        final_dmg = int(amount_after_def * res)

        # 4. Threshold & Barrier
        threshold = get_modded_value(0, "damage_threshold", target.modifiers)

        if final_dmg < threshold:
            if log_list is not None: log_list.append(f"🛡️ Ignored (<{threshold})")
            final_dmg = 0
        else:
            # Absorb (Barrier)
            if hasattr(target, "apply_mechanics_filter"):
                final_dmg = target.apply_mechanics_filter("absorb_damage", final_dmg, damage_type=dmg_type,
                                                          log_list=log_list)

            # Apply HP Damage
            # Construct log prefix for _apply_resource_damage
            prefix = ""
            if stat_reduction != 0: prefix += f"[-{stat_reduction} Skin] "
            prefix += f"[x{res:.1f} Res] "

            _apply_resource_damage(target, final_dmg, "hp", source_ctx, log_prefix=prefix)

    elif dmg_type == "stagger":
        # Stagger Logic
        res = getattr(target.hp_resists, dtype_name, 1.0)
        stg_take_pct = target.modifiers["stagger_take"]["pct"]
        mod_mult = 1.0 + (stg_take_pct / 100.0)

        final_dmg = int(amount * res * mod_mult)
        target.current_stagger = max(0, target.current_stagger - final_dmg)

        if source_ctx: source_ctx.log.append(f"😵 **{target.name}**: Stagger -{final_dmg}")
        logger.log(f"😵 {target.name} took {final_dmg} Stagger Damage", LogLevel.MINIMAL, "Damage")

    # 5. Trigger Events
    if initial_amount > 0:
        extra_args = {"raw_amount": initial_amount}
        if dice_obj: extra_args["damage_type"] = dice_obj.dtype

        log_wrapper = lambda msg: source_ctx.log.append(msg) if source_ctx else None

        trigger_event_func(
            "on_take_damage",
            target,
            final_dmg,
            source_ctx.source if source_ctx else None,
            log_func=log_wrapper,
            dmg_type=dmg_type,
            **extra_args
        )


def apply_damage(attacker_ctx, defender_ctx, dmg_type="hp",
                 trigger_event_func=None, script_runner_func=None):
    """
    Main entry point for dealing combat damage (Attack vs Defense).
    """
    attacker = attacker_ctx.source
    defender = attacker_ctx.target
    if defender_ctx: defender = defender_ctx.source

    if not defender: return

    # Immunity Check
    if hasattr(defender, "iter_mechanics"):
        for mech in defender.iter_mechanics():
            if mech.prevents_damage(defender, attacker_ctx):
                attacker_ctx.log.append(f"🚫 {defender.name} Immune ({mech.name if hasattr(mech, 'name') else mech.id})")
                logger.log(f"🚫 {defender.name} Immune to Damage ({mech.id})", LogLevel.MINIMAL, "Damage")
                return

    # Trigger On Hit
    if hasattr(attacker, "trigger_mechanics"):
        attacker.trigger_mechanics("on_hit", attacker_ctx)
    if script_runner_func:
        script_runner_func("on_hit", attacker_ctx)

    # 1. Calculate Outgoing Damage
    final_amt = _calculate_outgoing_damage(attacker, attacker_ctx, dmg_type)

    # 2. HP -> SP Conversion Logic
    convert_to_sp = getattr(attacker_ctx, 'convert_hp_to_sp', False)

    if dmg_type == "hp":
        if convert_to_sp:
            sp_damage = final_amt

            # Apply Incoming Filters (MentalProtection, etc)
            if hasattr(defender, "apply_mechanics_filter"):
                sp_damage = defender.apply_mechanics_filter(
                    "modify_incoming_damage",
                    sp_damage,
                    damage_type="sp",
                    log_list=attacker_ctx.log
                )

            _apply_resource_damage(defender, sp_damage, "sp", attacker_ctx)
        else:
            deal_direct_damage(attacker_ctx, defender, final_amt, "hp", trigger_event_func)

    elif dmg_type == "stagger":
        deal_direct_damage(attacker_ctx, defender, final_amt, "stagger", trigger_event_func)

    # 3. Side-Damage (Stagger from HP hit)
    if dmg_type == "hp":
        _apply_stagger_side_damage(defender, attacker_ctx, final_amt)