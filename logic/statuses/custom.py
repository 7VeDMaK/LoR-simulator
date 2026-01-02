import random
from core.enums import DiceType
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
            ctx.source.remove_status("self_control", 20)

    def on_turn_end(self, unit, stack) -> list[str]:
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
        if "hiding_in_smoke" in unit.talents:
            return -(eff_stack * 0.03)
        else:
            return eff_stack * 0.05

    def on_turn_end(self, unit, stack) -> list[str]:
        msgs = []
        unit.remove_status("smoke", 1)
        msgs.append("💨 Smoke decayed (-1)")
        current = unit.get_status("smoke")
        limit = self._get_limit(unit)
        if current > limit:
            loss = current - limit
            unit.remove_status("smoke", loss)
            msgs.append(f"💨 Smoke cap ({limit}) exceeded. Removed {loss}.")
        return msgs


class RedLycorisStatus(StatusEffect):
    id = "red_lycoris"

    def on_calculate_stats(self, unit) -> dict:
        return {"initiative": 999, "damage_take": 9999}

    def on_turn_end(self, unit, stack) -> list[str]:
        return []


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


class AdaptationStatus(StatusEffect):
    id = "adaptation"

    def on_hit(self, ctx: RollContext, stack: int):
        # stack = Уровень Адаптации (1-5)
        lvl = max(1, min(stack, 5))
        thresholds = [0.5, 0.75, 1.0, 1.25, 1.5]
        target_min = thresholds[lvl - 1]

        target = ctx.target
        if not target: return

        # Определяем тип урона
        dtype = ctx.dice.dtype.value.lower()
        current_res = getattr(target.hp_resists, dtype, 1.0)

        # Эффективный резист не может быть ниже порога адаптации
        effective_res = max(current_res, target_min)

        if effective_res > current_res:
            factor = effective_res / current_res
            ctx.damage_multiplier *= factor
            ctx.log.append(f"🧬 Adapt (x{factor:.2f})")

    def on_turn_end(self, unit, stack) -> list[str]:
        return []


class BulletTimeStatus(StatusEffect):
    id = "bullet_time"

    def on_roll(self, ctx: RollContext, stack: int):
        # 1. Максимальное уклонение
        if ctx.dice.dtype == DiceType.EVADE:
            ctx.final_value = ctx.dice.max_val
            ctx.log.append(f"🕰️ **BULLET TIME**: Идеальное уклонение ({ctx.dice.max_val})")

        # 2. Отмена атак
        elif ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.final_value = 0
            ctx.damage_multiplier = 0.0
            ctx.log.append("🕰️ **BULLET TIME**: Атака отменена (0)")

class ClarityStatus(StatusEffect):
    id = "clarity"
    # Просто отображение, логика в таланте
    def on_turn_end(self, unit, stack) -> list[str]:
        return [] # Не исчезает сам по себе (duration 99)


class EnrageTrackerStatus(StatusEffect):
    id = "enrage_tracker"

    def on_take_damage(self, unit, amount, dmg_type, log_func=None):
        if amount > 0:
            # 1 урона = 1 силы
            unit.add_status("strength", amount,
                            duration=2)  # На этот и следующий ход (или duration=1 если только на следующий)
            if log_func:
                log_func(f"😡 **Разозлить**: Получено {amount} урона -> +{amount} Силы!")

    def on_turn_end(self, unit, stack) -> list[str]:
        return []  # Исчезает сам по duration


class InvisibilityStatus(StatusEffect):
    id = "invisibility"

    def on_roll(self, ctx: RollContext, stack: int):
        # Если Азгик атакует - невидимость спадает
        # Проверяем, что это не защитный кубик
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.source.remove_status("invisibility", 999)
            ctx.log.append("👻 **Невидимость**: Раскрыт после атаки!")

    def on_turn_end(self, unit, stack) -> list[str]:
        return ["👻 Невидимость рассеялась."]


class WeaknessStatus(StatusEffect):
    id = "weakness"

    # Логика увеличения урона должна быть прописана в damage.py
    # Либо этот статус просто наследует Vulnerability, если движок это позволяет,
    # но лучше прописать явно в damage.py

    def on_turn_end(self, unit, stack) -> list[str]:
        # Уменьшаем стаки на 1 в конце хода (или снимаем все, как решите)
        unit.remove_status("weakness", 1)
        return ["🔻 Слабость уменьшилась (-1)"]