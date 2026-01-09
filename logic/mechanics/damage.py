from logic.character_changing.augmentations.augmentations import AUGMENTATION_REGISTRY
from logic.character_changing.passives import PASSIVE_REGISTRY
from logic.character_changing.talents import TALENT_REGISTRY
from logic.statuses.status_manager import STATUS_REGISTRY
# Импорт для чтения модов
from logic.calculations.formulas import get_modded_value
from logic.weapon_definitions import WEAPON_REGISTRY


def deal_direct_damage(source_ctx, target, amount: int, dmg_type: str, trigger_event_func):
    """Наносит урон (HP или Stagger), учитывая резисты и барьеры."""
    if amount <= 0: return

    if hasattr(target, "talents"):
        # Импорт реестра нужен, если таланты хранятся как ID строк
        from logic.character_changing.talents import TALENT_REGISTRY

        for talent_id in target.talents:
            talent = TALENT_REGISTRY.get(talent_id)
            if talent and hasattr(talent, "modify_incoming_damage"):
                # Передаем dmg_type (например "bleed" или DiceType.SLASH)
                amount = talent.modify_incoming_damage(target, amount, dmg_type)

    final_dmg = 0

    # Определяем тип атаки (Slash/Pierce/Blunt)
    dtype_name = "slash"
    dice_obj = None
    if source_ctx and source_ctx.dice:
        dice_obj = source_ctx.dice
        dtype_name = dice_obj.dtype.value.lower()

    if dmg_type == "hp":
        # 1. Порог игнорирования
        threshold = get_modded_value(0, "damage_threshold", target.modifiers)

        # Базовый резист
        res = getattr(target.hp_resists, dtype_name, 1.0)

        # === [NEW] МЕХАНИКА STAGGER RESIST (3.5 / 3.10) ===
        is_stag_hit = False
        if target.is_staggered():
            # Базовый множитель по умолчанию
            stagger_mult = 2.0

            # Если есть талант 3.5 "Не взирая на невзгоды"
            if "despiteAdversities" in target.talents:
                # Если есть улучшение 3.10
                if "surgeOfStrength" in target.talents:
                    stagger_mult = 1.25
                else:
                    stagger_mult = 1.5
            res *= stagger_mult
            is_stag_hit = True
        # ===================================================

        # === [NEW] МЕХАНИКА АДАПТАЦИИ (3.6) ===
        # Проверяем активную адаптацию из памяти юнита
        active_adapt_type = target.memory.get("adaptation_active_type")
        if active_adapt_type and dice_obj and dice_obj.dtype == active_adapt_type:
            # Снижаем урон на 25%
            res *= 0.75
            source_ctx.log.append(f"🧬 **Adaptation**: -25% Dmg vs {active_adapt_type.name}")
        # ======================================

        final_dmg = int(amount * res)

        # Проверка порога
        if final_dmg < threshold:
            source_ctx.log.append(f"🛡️ Ignored (<{threshold})")
            return

        # Барьер
        barrier = target.get_status("barrier")
        if barrier > 0:
            absorbed = min(barrier, final_dmg)
            target.remove_status("barrier", absorbed)
            final_dmg -= absorbed
            source_ctx.log.append(f"🛡️ Barrier -{absorbed}")

        # Нанесение
        target.current_hp = max(0, target.current_hp - final_dmg)  # Безопасное вычитание

        hit_msg = f"💥 **{target.name}**: Hit {final_dmg} HP"
        if is_stag_hit: hit_msg += " (Stagger Hit!)"
        source_ctx.log.append(hit_msg)

    elif dmg_type == "stagger":
        res = getattr(target.stagger_resists, dtype_name, 1.0)

        stg_take_pct = target.modifiers["stagger_take"]["pct"]
        mod_mult = 1.0 + (stg_take_pct / 100.0)

        if target.get_status("stagger_resist") > 0:
            mod_mult *= 0.67  # -33% урона

        final_dmg = int(amount * res * mod_mult)
        target.current_stagger = max(0, target.current_stagger - final_dmg)
        source_ctx.log.append(f"😵 **{target.name}**: Stagger -{final_dmg}")

    # Триггер получения урона (Сбор статистики для Адаптации и Скалы)
    if final_dmg > 0 or amount > 0:  # Триггерим даже при 0, если нужно для "Скалы" (но лучше внутри Скалы проверять amount)

        # Передаем сырой урон (amount) и финальный (final_dmg) для талантов типа "Скала"
        extra_args = {"raw_amount": amount}
        if dice_obj: extra_args["damage_type"] = dice_obj.dtype

        log_wrapper = lambda msg: source_ctx.log.append(msg)
        trigger_event_func("on_take_damage", target, final_dmg, source=source_ctx, dmg_type=dmg_type, log_func=log_wrapper, **extra_args)


def apply_damage(attacker_ctx, defender_ctx, dmg_type="hp",
                 trigger_event_func=None, script_runner_func=None):
    """
    Рассчитывает полный урон от атаки.
    """
    attacker = attacker_ctx.source
    defender = attacker_ctx.target

    if not defender:
        return

    if defender.get_status("red_lycoris") > 0:
        attacker_ctx.log.append(f"🚫 {defender.name} Immune (Lycoris)")
        return

    # === ON HIT TRIGGER ===
    for status_id, stack in list(attacker.statuses.items()):
        if status_id in STATUS_REGISTRY: STATUS_REGISTRY[status_id].on_hit(attacker_ctx, stack)
    for pid in attacker.passives:
        if pid in PASSIVE_REGISTRY: PASSIVE_REGISTRY[pid].on_hit(attacker_ctx)
    for pid in attacker.talents:
        if pid in TALENT_REGISTRY: TALENT_REGISTRY[pid].on_hit(attacker_ctx)
    for aid in attacker.augmentations:
        if aid in AUGMENTATION_REGISTRY:
            AUGMENTATION_REGISTRY[aid].on_hit(attacker_ctx)

    # === 4. ПАССИВКА ОРУЖИЯ ===
    if attacker.weapon_id in WEAPON_REGISTRY:
        wep = WEAPON_REGISTRY[attacker.weapon_id]
        if wep.passive_id and wep.passive_id in PASSIVE_REGISTRY:
            PASSIVE_REGISTRY[wep.passive_id].on_hit(attacker_ctx)

    if script_runner_func:
        script_runner_func("on_hit", attacker_ctx)

    # === РАСЧЕТ ===
    raw_damage = attacker_ctx.final_value

    # Бонусы атакующего
    dmg_up = attacker.get_status("dmg_up") - attacker.get_status("dmg_down")
    dmg_mods = get_modded_value(0, "damage_deal", attacker.modifiers)

    # Бонусы защитника
    inc_mod = defender.get_status("fragile") + \
              defender.get_status("vulnerability") + \
              defender.get_status("weakness") - \
              defender.get_status("protection")
    inc_mods_stat = get_modded_value(0, "damage_take", defender.modifiers)

    convert_to_sp = getattr(attacker_ctx, 'convert_hp_to_sp', False)
    inc_total = inc_mod - inc_mods_stat
    total_base = max(0, raw_damage + dmg_up + dmg_mods + inc_total)

    # Криты
    final_amt = total_base
    if attacker_ctx.damage_multiplier != 1.0:
        final_amt = int(final_amt * attacker_ctx.damage_multiplier)

    # Формула для лога
    formula_parts = [str(raw_damage)]
    if dmg_up + dmg_mods != 0: formula_parts.append(f"{dmg_up + dmg_mods:+} (Atk)")
    if inc_total != 0: formula_parts.append(f"{inc_total:+} (Def)")

    formula_str = "".join(formula_parts)
    if attacker_ctx.damage_multiplier != 1.0:
        formula_str = f"({formula_str}) x{attacker_ctx.damage_multiplier} (Crit)"

    # Для лога проверяем резисты (но они применятся внутри deal_direct_damage)
    dtype = "slash"
    if attacker_ctx.dice:
        dtype = attacker_ctx.dice.dtype.value.lower()
    res = getattr(defender.hp_resists, dtype, 1.0)
    if res != 1.0: formula_str += f" x{res} (Res)"

    if dmg_type == "hp":
        if convert_to_sp:
            ment_prot = defender.get_status("mental_protection")
            if ment_prot > 0:
                pct_red = min(0.50, ment_prot * 0.25)
                reduction = int(final_amt * pct_red)
                final_amt -= reduction
                attacker_ctx.log.append(f"🧀 **Edam**: Blocked {reduction} SP dmg")

            defender.take_sanity_damage(final_amt)
            attacker_ctx.log.append(f"🧠 **White Dmg**: {final_amt} SP (Converted) [{formula_str}]")
        else:
            deal_direct_damage(attacker_ctx, defender, final_amt, "hp", trigger_event_func)
            if attacker_ctx.log:
                attacker_ctx.log[-1] += f" [{formula_str}]"

    elif dmg_type == "stagger":
        deal_direct_damage(attacker_ctx, defender, final_amt, "stagger", trigger_event_func)

    # Побочный урон выдержке
    if dmg_type == "hp" and not defender.is_staggered():
        if defender.get_status("red_lycoris") <= 0:
            res_stg = getattr(defender.stagger_resists, dtype, 1.0)
            stg_dmg = int(final_amt * res_stg)

            # Также применяем механику адаптации к побочному урону
            if defender.memory.get(
                    "adaptation_active_type") and attacker_ctx.dice and attacker_ctx.dice.dtype == defender.memory.get(
                    "adaptation_active_type"):
                stg_dmg = int(stg_dmg * 0.75)

            defender.current_stagger = max(0, defender.current_stagger - stg_dmg)