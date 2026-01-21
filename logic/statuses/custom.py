import random

from core.enums import DiceType
from core.logging import logger, LogLevel
from logic.context import RollContext
from logic.statuses.common import StatusEffect


class SelfControlStatus(StatusEffect):
    id = "self_control"

    def on_hit(self, ctx: RollContext, stack: int):
        chance = min(100, stack * 5)
        roll = random.randint(1, 100)
        if roll <= chance:
            ctx.damage_multiplier *= 2.0
            ctx.is_critical = True
            ctx.log.append(f"💨 CRIT! ({chance}%) x2 DMG")
            logger.log(f"💨 SelfControl Crit: {ctx.source.name} (Chance {chance}%) -> x2 Dmg", LogLevel.VERBOSE,
                       "Status")
            ctx.source.remove_status("self_control", 20)

    def on_round_end(self, unit, log_func, **kwargs):
        unit.remove_status("self_control", 20)
        return [f"💨 Self-Control decayed"]


class SmokeStatus(StatusEffect):
    id = "smoke"

    def _get_limit(self, unit):
        bonus = unit.memory.get("smoke_limit_bonus", 0)
        return 10 + bonus

    def on_roll(self, ctx: RollContext, stack: int):
        if stack >= 9:
            ctx.modify_power(1, "Smoke (Base)")

    def get_damage_modifier(self, unit, stack) -> float:
        eff_stack = min(10, stack)
        if unit.memory.get("smoke_is_defensive"):
            return -(eff_stack * 0.03)
        else:
            return eff_stack * 0.05

    def on_round_end(self, unit, log_func, **kwargs):
        msgs = []
        unit.remove_status("smoke", 1)
        msgs.append("💨 Smoke decayed (-1)")
        current = unit.get_status("smoke")
        limit = self._get_limit(unit)
        if current > limit:
            loss = current - limit
            unit.remove_status("smoke", loss)
            msgs.append(f"💨 Smoke cap ({limit}) exceeded. Removed {loss}.")
            logger.log(f"💨 Smoke cap exceeded for {unit.name}: -{loss}", LogLevel.VERBOSE, "Status")
        return msgs


class RedLycorisStatus(StatusEffect):
    id = "red_lycoris"
    name = "Красный Ликорис" # Добавил имя для красивого лога
    prevents_stagger = True
    prevents_death = True

    def modify_active_slot(self, unit, slot):
        slot['prevent_redirection'] = True
        if not slot.get('source_effect'):
            slot['source_effect'] = "Lycoris 🩸"

    def on_calculate_stats(self, unit) -> dict:
        return {"initiative": 999, "damage_take": 9999}

    def on_round_end(self, unit, log_func, **kwargs):
        return []

    # [NEW] Реализация иммунитета
    def prevents_damage(self, unit, attacker_ctx) -> bool:
        return True


class SinisterAuraStatus(StatusEffect):
    id = "sinister_aura"

    def on_roll(self, ctx: RollContext, stack: int):
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            target = ctx.target
            if target:
                dmg_val = max(0, target.current_sp) // 10
                if dmg_val > 0:
                    ctx.source.take_sanity_damage(dmg_val)
                    ctx.log.append(f"🌑 Аура: -{dmg_val} SP (от величия {target.name})")
                    # [CHANGE] VERBOSE -> MINIMAL
                    logger.log(f"🌑 Sinister Aura: {ctx.source.name} took {dmg_val} SP dmg", LogLevel.MINIMAL, "Status")


class AdaptationStatus(StatusEffect):
    id = "adaptation"
    name = "Адаптация"
    description = ("Адаптация - накапливаемое до четырёх уровней состояние...")

    def on_round_start(self, unit, log_func, **kwargs):
        current = unit.get_status("adaptation")
        if current < 4:
            unit.add_status("adaptation", 1, duration=99)
            if log_func:
                log_func(f"🧬 Адаптация: Рост -> Уровень {current + 1}")
            logger.log(f"🧬 Adaptation: {unit.name} stack increased to {current + 1}", LogLevel.VERBOSE, "Passive")
        else:
            unit.add_status("adaptation", 0, duration=99)

    # [NEW] Реализация логики защиты (пункт 4.3 из старого кода)
    def modify_resistance(self, unit, res: float, damage_type: str, dice=None, stack=0, log_list=None) -> float:
        # Проверяем, к какому типу мы адаптировались
        active_type = unit.memory.get("adaptation_active_type")

        # Если тип кубика совпадает с адаптацией -> Снижаем получаемый урон (резист * 0.75)
        if active_type and dice and dice.dtype == active_type:
            new_res = res * 0.75
            if log_list is not None:
                log_list.append(f"🧬 **Adaptation**: -25% Dmg vs {active_type.name}")
            return new_res

        return res


class BulletTimeStatus(StatusEffect):
    id = "bullet_time"

    def on_roll(self, ctx: RollContext, stack: int):
        if ctx.dice.dtype == DiceType.EVADE:
            ctx.final_value = ctx.dice.max_val
            ctx.log.append(f"🕰️ **BULLET TIME**: Идеальное уклонение ({ctx.dice.max_val})")
            logger.log(f"🕰️ Bullet Time: {ctx.source.name} Evade Max ({ctx.dice.max_val})", LogLevel.VERBOSE, "Status")
        elif ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.final_value = 0
            ctx.damage_multiplier = 0.0
            ctx.log.append("🕰️ **BULLET TIME**: Атака отменена (0)")
            logger.log(f"🕰️ Bullet Time: {ctx.source.name} Attack Nullified", LogLevel.VERBOSE, "Status")


class ClarityStatus(StatusEffect):
    id = "clarity"

    def on_round_end(self, unit, log_func, **kwargs):
        return []


class EnrageTrackerStatus(StatusEffect):
    id = "enrage_tracker"

    def on_take_damage(self, unit, amount, source, **kwargs):
        log_func = kwargs.get("log_func")
        if amount > 0:
            unit.add_status("strength", amount, duration=2)
            if log_func:
                log_func(f"😡 **Разозлить**: Получено {amount} урона -> +{amount} Силы!")
            logger.log(f"😡 Enrage: {unit.name} gain +{amount} Strength from damage", LogLevel.VERBOSE, "Status")

    def on_round_end(self, unit, log_func, **kwargs):
        return []


class InvisibilityStatus(StatusEffect):
    id = "invisibility"

    def on_hit(self, ctx: RollContext, **kwargs):
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.source.remove_status("invisibility", 999)
            ctx.log.append("👻 **Невидимость**: Раскрыт после удара!")
            logger.log(f"👻 Invisibility broken (Attack) for {ctx.source.name}", LogLevel.NORMAL, "Status")

    def on_clash_lose(self, ctx: RollContext, **kwargs):
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.source.remove_status("invisibility", 999)
            ctx.log.append("👻 **Невидимость**: Раскрыт (перехвачен)!")
            logger.log(f"👻 Invisibility broken (Clash Lose) for {ctx.source.name}", LogLevel.NORMAL, "Status")

    def on_round_end(self, unit, log_func, **kwargs):
        return ["👻 Невидимость рассеялась."]



class MentalProtectionStatus(StatusEffect):
    id = "mental_protection"
    pass


class SatietyStatus(StatusEffect):
    id = "satiety"

    def on_calculate_stats(self, unit, stack=0) -> dict:
        if unit.get_status("ignore_satiety") > 0: return {}
        penalties = {}
        if stack >= 15:
            penalties = {"initiative": -3}
        if hasattr(unit, "apply_mechanics_filter"):
            penalties = unit.apply_mechanics_filter("modify_satiety_penalties", penalties)
        return penalties

    def on_round_end(self, unit, log_func, **kwargs):
        stack = kwargs.get("stack")
        msgs = []
        threshold = 20
        if "food_lover" in unit.passives: threshold = 27

        if stack > threshold:
            excess = stack - threshold
            damage = excess * 10
            unit.current_hp = max(0, unit.current_hp - damage)
            msgs.append(f"**Переедание**: {excess} лишних стаков -> -{damage} HP!")
            # [CHANGE] NORMAL -> MINIMAL
            logger.log(f"🍗 Satiety Overload: {unit.name} took {damage} HP damage", LogLevel.MINIMAL, "Status")

        unit.remove_status("satiety", 1)
        msgs.append("🍗 Сытость немного спала (-1)")
        return msgs


# === СТАТУСЫ КОНФЕТ ===
class IgnoreSatietyStatus(StatusEffect):
    id = "ignore_satiety"
    pass


class BleedResistStatus(StatusEffect):
    id = "bleed_resist"
    pass


class RegenGanacheStatus(StatusEffect):
    id = "regen_ganache"

    def on_round_start(self, unit, log_func, **kwargs):
        heal = int(unit.max_hp * 0.05)
        if heal > 0:
            unit.heal_hp(heal)
            if log_func: log_func(f"🍫 **Ганаш**: Регенерация +{heal} HP")
            logger.log(f"🍫 Ganache Regen: {unit.name} +{heal} HP", LogLevel.VERBOSE, "Status")

    def on_round_end(self, unit, log_func, **kwargs):
        return []


class RevengeDmgUpStatus(StatusEffect):
    id = "revenge_dmg_up"

    def on_hit(self, ctx: RollContext, stack: int):
        ctx.damage_multiplier *= 1.5
        ctx.log.append(f"🩸 **Месть**: Урон x1.5!")
        logger.log(f"🩸 Revenge Triggered: {ctx.source.name} Damage x1.5", LogLevel.VERBOSE, "Status")
        ctx.source.remove_status("revenge_dmg_up", 999)

    def on_round_end(self, unit, log_func, **kwargs):
        return []


class TauntStatus(StatusEffect):
    id = "taunt"


class FanatMarkStatus(StatusEffect):
    id = "fanat_mark"
    name = "Метка Фаната"
    description = "Цель получает +20 входящего урона от кубиков Фаната (через пассивку)."


class MentalProtectionStatus(StatusEffect):
    id = "mental_protection"
    name = "Ментальная защита"

    def modify_incoming_damage(self, unit, amount, damage_type, stack=0, log_list=None, **kwargs):
        # Работаем только если тип урона 'sp' (конвертированный)
        if damage_type == "sp":
            if stack == 0: stack = unit.get_status(self.id)

            if stack > 0:
                # 25% за стак, макс 50%
                pct_red = min(0.50, stack * 0.25)
                reduction = int(amount * pct_red)

                if reduction > 0:
                    if log_list is not None:
                        log_list.append(f"🧀 **Edam**: Blocked {reduction} SP dmg")

                    return amount - reduction
        return amount