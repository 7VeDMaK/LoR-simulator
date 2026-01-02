from logic.passives import PASSIVE_REGISTRY
from logic.talents import TALENT_REGISTRY
from logic.statuses.status_manager import STATUS_REGISTRY
# Импорт для чтения модов
from logic.calculations.formulas import get_modded_value
from logic.weapon_definitions import WEAPON_REGISTRY


def deal_direct_damage(source_ctx, target, amount: int, dmg_type: str, trigger_event_func):
    """Наносит урон (HP или Stagger), учитывая резисты и барьеры."""
    if amount <= 0: return

    final_dmg = 0

    if dmg_type == "hp":
        # 1. Порог игнорирования
        threshold = get_modded_value(0, "damage_threshold", target.modifiers)

        dtype_name = "slash"
        if source_ctx and source_ctx.dice:
            dtype_name = source_ctx.dice.dtype.value.lower()

        res = getattr(target.hp_resists, dtype_name, 1.0)

        is_stag_hit = False
        if target.is_staggered():
            res *= 2.0
            is_stag_hit = True

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
        target.current_hp -= final_dmg
        hit_msg = f"💥 Hit {final_dmg} HP"
        if is_stag_hit: hit_msg += " (Stagger x2!)"
        source_ctx.log.append(hit_msg)

    elif dmg_type == "stagger":
        dtype_name = "slash"
        if source_ctx and source_ctx.dice:
            dtype_name = source_ctx.dice.dtype.value.lower()

        res = getattr(target.stagger_resists, dtype_name, 1.0)

        # Модификатор получаемого урона по выдержке (Stagger Take Mult)
        # get_modded_value вернет (0 + Flat) * (1 + Pct/100).
        # Если pct = -50 (Адаптация), множитель будет 0.5.
        # Но нам нужен базовый 1.0. Поэтому берем get_modded_value(100, ...) / 100
        # Или просто берем Pct напрямую, если мы хотим (1 + mod).

        # Вариант: берем Pct из модификаторов
        stg_take_pct = target.modifiers["stagger_take"]["pct"]
        mod_mult = 1.0 + (stg_take_pct / 100.0)

        final_dmg = int(amount * res * mod_mult)
        target.current_stagger -= final_dmg
        source_ctx.log.append(f"😵 Stagger Dmg {final_dmg}")

    # Триггер получения урона
    if final_dmg > 0:
        log_wrapper = lambda msg: source_ctx.log.append(msg)
        trigger_event_func("on_take_damage", target, final_dmg, dmg_type, log_func=log_wrapper)


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

    # === 4. ПАССИВКА ОРУЖИЯ (НОВОЕ) ===
    if attacker.weapon_id in WEAPON_REGISTRY:
        wep = WEAPON_REGISTRY[attacker.weapon_id]
        if wep.passive_id and wep.passive_id in PASSIVE_REGISTRY:
            # Вызываем on_hit у пассивки оружия (Банганранг, Лимаган и т.д.)
            PASSIVE_REGISTRY[wep.passive_id].on_hit(attacker_ctx)

    if script_runner_func:
        script_runner_func("on_hit", attacker_ctx)

    # === РАСЧЕТ ===
    raw_damage = attacker_ctx.final_value

    # Бонусы атакующего
    dmg_up = attacker.get_status("dmg_up") - attacker.get_status("dmg_down")

    # [FIX] Читаем damage_deal через хелпер
    dmg_mods = get_modded_value(0, "damage_deal", attacker.modifiers)

    # Бонусы защитника
    inc_mod = defender.get_status("fragile") + defender.get_status("vulnerability") - defender.get_status("protection")

    # [FIX] Читаем damage_take через хелпер
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

    dtype = "slash"
    if attacker_ctx.dice:
        dtype = attacker_ctx.dice.dtype.value.lower()

    res = getattr(defender.hp_resists, dtype, 1.0)
    if res != 1.0: formula_str += f" x{res} (Res)"

    if dmg_type == "hp":

        if convert_to_sp:
            # Наносим SP урон вместо HP
            defender.take_sanity_damage(final_amt)
            attacker_ctx.log.append(f"🧠 **White Dmg**: {final_amt} SP (Converted) [{formula_str}]")
        else:
            # Обычный HP урон
            deal_direct_damage(attacker_ctx, defender, final_amt, "hp", trigger_event_func)
            attacker_ctx.log[-1] += f" [{formula_str}]"

        deal_direct_damage(attacker_ctx, defender, final_amt, "hp", trigger_event_func)
        attacker_ctx.log[-1] += f" [{formula_str}]"

    elif dmg_type == "stagger":
        deal_direct_damage(attacker_ctx, defender, final_amt, "stagger", trigger_event_func)

    # Побочный урон выдержке
    if dmg_type == "hp" and not defender.is_staggered():
        if defender.get_status("red_lycoris") <= 0:
            res_stg = getattr(defender.stagger_resists, dtype, 1.0)
            stg_dmg = int(final_amt * res_stg)
            defender.current_stagger -= stg_dmg