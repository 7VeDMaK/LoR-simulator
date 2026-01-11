from logic.character_changing.augmentations.augmentations import AUGMENTATION_REGISTRY
from logic.character_changing.passives import PASSIVE_REGISTRY
from logic.character_changing.talents import TALENT_REGISTRY
from logic.statuses.status_manager import STATUS_REGISTRY
# Импорт для чтения модов
from logic.calculations.formulas import get_modded_value
from logic.weapon_definitions import WEAPON_REGISTRY


def deal_direct_damage(source_ctx, target, amount: int, dmg_type: str, trigger_event_func):
    """
    Наносит урон (HP или Stagger), учитывая резисты, барьеры и защитные модификаторы.
    amount — это "сырой" урон (или разница кубиков).
    """
    if amount <= 0: return

    if hasattr(target, "apply_mechanics_filter"):
        amount = target.apply_mechanics_filter("modify_incoming_damage", amount, damage_type=dmg_type)

    final_dmg = 0
    source_unit = source_ctx.source if source_ctx else None

    # Определяем тип атаки
    dtype_name = "slash"
    dice_obj = None
    if source_ctx and source_ctx.dice:
        dice_obj = source_ctx.dice
        dtype_name = dice_obj.dtype.value.lower()

    # Собираем части формулы для лога
    log_formula = [str(amount)]

    if dmg_type == "hp":
        # 1. ЗАЩИТНЫЕ МОДИФИКАТОРЫ

        # А. Статусы: Fragile(+), Protection(-)
        status_mod = (
                target.get_status("fragile") +
                target.get_status("vulnerability") +
                target.get_status("weakness") -
                target.get_status("protection")
        )

        stat_reduction = get_modded_value(0, "damage_take", target.modifiers)

        defense_sum = status_mod - stat_reduction
        amount_after_def = max(0, amount + defense_sum)

        # Логируем
        if defense_sum != 0:
            sign = "+" if defense_sum > 0 else ""  # Если минус, он сам добавится
            log_formula.append(f"{sign}{defense_sum} (Def)")

        # 2. ПОРОГ ИГНОРИРОВАНИЯ (Threshold)
        threshold = get_modded_value(0, "damage_threshold", target.modifiers)

        # 3. РЕЗИСТЫ (Resistance)
        res = getattr(target.hp_resists, dtype_name, 1.0)

        # Пробивание резистов (Адаптация)
        if source_ctx and source_ctx.source:
            adapt_stack = source_ctx.source.get_status("adaptation")
            if adapt_stack > 0:
                min_res = 0.25 * (adapt_stack + 1)
                if res < min_res:
                    res = min_res
                    source_ctx.log.append(f"🧬 Adaptation Pierce: Res {res:.2f}")

        is_stag_hit = False
        if target.is_staggered():
            stagger_mult = 2.0

            if hasattr(target, "apply_mechanics_filter"):
                # Передаем текущий множитель (2.0) и просим всех изменить его при желании
                stagger_mult = target.apply_mechanics_filter("modify_stagger_damage_multiplier", stagger_mult)

            res *= stagger_mult
            is_stag_hit = True
        # =====================================

        # Адаптация защитника
        active_adapt_type = target.memory.get("adaptation_active_type")
        if active_adapt_type and dice_obj and dice_obj.dtype == active_adapt_type:
            res *= 0.75
            source_ctx.log.append(f"🧬 **Adaptation**: -25% Dmg vs {active_adapt_type.name}")

        final_dmg = int(amount_after_def * res)
        log_formula.append(f"x{res:.1f} (Res)")

        # 4. ПРОВЕРКА ПОРОГА
        if final_dmg < threshold:
            source_ctx.log.append(f"🛡️ Ignored (<{threshold})")
            final_dmg = 0
        else:
            # Барьер
            barrier = target.get_status("barrier")
            if barrier > 0:
                absorbed = min(barrier, final_dmg)
                target.remove_status("barrier", absorbed)
                final_dmg -= absorbed
                source_ctx.log.append(f"🛡️ Barrier -{absorbed}")

            target.current_hp = max(0, target.current_hp - final_dmg)

            formula_str = "".join(log_formula)
            hit_msg = f"💥 **{target.name}**: Hit {final_dmg} HP [{formula_str}]"
            if is_stag_hit: hit_msg += " (Staggered)"
            source_ctx.log.append(hit_msg)

    elif dmg_type == "stagger":
        res = getattr(target.stagger_resists, dtype_name, 1.0)
        stg_take_pct = target.modifiers["stagger_take"]["pct"]
        mod_mult = 1.0 + (stg_take_pct / 100.0)

        if target.get_status("stagger_resist") > 0:
            mod_mult *= 0.67

        final_dmg = int(amount * res * mod_mult)
        target.current_stagger = max(0, target.current_stagger - final_dmg)

        source_ctx.log.append(f"😵 **{target.name}**: Stagger -{final_dmg}")

    # Триггер событий
    if amount > 0:
        extra_args = {"raw_amount": amount}
        if dice_obj: extra_args["damage_type"] = dice_obj.dtype

        log_wrapper = lambda msg: source_ctx.log.append(msg)

        trigger_event_func(
            "on_take_damage",
            target,
            final_dmg,
            source_unit,
            log_func=log_wrapper,
            dmg_type=dmg_type,
            **extra_args
        )


def apply_damage(attacker_ctx, defender_ctx, dmg_type="hp",
                 trigger_event_func=None, script_runner_func=None):
    attacker = attacker_ctx.source
    defender = attacker_ctx.target

    if not defender: return

    if defender.get_status("red_lycoris") > 0:
        attacker_ctx.log.append(f"🚫 {defender.name} Immune (Lycoris)")
        return

    # === [ОПТИМИЗАЦИЯ] Trigger On Hit effects ===
    if hasattr(attacker, "trigger_mechanics"):
        attacker.trigger_mechanics("on_hit", attacker_ctx)
    # ============================================

    if script_runner_func: script_runner_func("on_hit", attacker_ctx)

    # Calculation
    raw_damage = attacker_ctx.final_value
    dmg_up = attacker.get_status("dmg_up") - attacker.get_status("dmg_down")
    dmg_mods = get_modded_value(0, "damage_deal", attacker.modifiers)

    total_base = max(0, raw_damage + dmg_up + dmg_mods)

    final_amt = total_base
    if attacker_ctx.damage_multiplier != 1.0:
        final_amt = int(final_amt * attacker_ctx.damage_multiplier)

    if dmg_up + dmg_mods != 0:
        attacker_ctx.log.append(f"👊 Atk Boost: {dmg_up + dmg_mods:+}")

    convert_to_sp = getattr(attacker_ctx, 'convert_hp_to_sp', False)

    if dmg_type == "hp":
        if convert_to_sp:
            ment_prot = defender.get_status("mental_protection")
            if ment_prot > 0:
                pct_red = min(0.50, ment_prot * 0.25)
                reduction = int(final_amt * pct_red)
                final_amt -= reduction
                attacker_ctx.log.append(f"🧀 **Edam**: Blocked {reduction} SP dmg")

            defender.take_sanity_damage(final_amt)
            attacker_ctx.log.append(f"🧠 **White Dmg**: {final_amt} SP")
        else:
            deal_direct_damage(attacker_ctx, defender, final_amt, "hp", trigger_event_func)

    elif dmg_type == "stagger":
        deal_direct_damage(attacker_ctx, defender, final_amt, "stagger", trigger_event_func)

    # Stagger side-damage
    if dmg_type == "hp" and not defender.is_staggered():
        if defender.get_status("red_lycoris") <= 0:
            dtype = "slash"
            if attacker_ctx.dice:
                dtype = attacker_ctx.dice.dtype.value.lower()
            res_stg = getattr(defender.stagger_resists, dtype, 1.0)

            # === [FIX START] Получаем защиту для Stagger ===
            # Считаем защиту так же, как для HP (Protection, Tough Skin и т.д.)
            # Или берем только damage_take, если Protection не должен работать на Stagger

            # Вариант 1: Полная защита (как у HP)
            status_def = defender.get_status("protection") - defender.get_status("fragile") - defender.get_status(
                "vulnerability")
            skin_def = get_modded_value(0, "damage_take", defender.modifiers)  # Крепкая кожа

            total_def = status_def + skin_def

            # Применяем защиту к базе (не может быть меньше 0)
            base_stg_dmg = max(0, final_amt - total_def)
            # === [FIX END] ===

            stg_dmg = int(base_stg_dmg * res_stg)  # Используем base_stg_dmg вместо final_amt

            stg_take_pct = defender.modifiers["stagger_take"]["pct"]
            if stg_take_pct != 0:
                mod_mult = 1.0 + (stg_take_pct / 100.0)
                stg_dmg = int(stg_dmg * mod_mult)

            defender.current_stagger = max(0, defender.current_stagger - stg_dmg)