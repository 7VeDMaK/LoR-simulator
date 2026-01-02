import random
from core.enums import DiceType
from logic.context import RollContext
from logic.statuses.base_status import StatusEffect

# === STANDARD STATUSES ===

class StrengthStatus(StatusEffect):
    id = "strength"

    def on_roll(self, ctx: RollContext, stack: int):
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.modify_power(stack, "Strength")


class EnduranceStatus(StatusEffect):
    id = "endurance"

    def on_roll(self, ctx: RollContext, stack: int):
        if ctx.dice.dtype == DiceType.BLOCK:
            ctx.modify_power(stack, "Endurance")


class BleedStatus(StatusEffect):
    id = "bleed"

    def on_roll(self, ctx: RollContext, stack: int):
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            dmg = stack
            ctx.source.current_hp -= dmg
            remove_amt = stack // 2
            ctx.source.remove_status("bleed", remove_amt)
            ctx.log.append(f"🩸 Bleed: {ctx.source.name} takes {dmg} dmg")


class ParalysisStatus(StatusEffect):
    id = "paralysis"

    def on_roll(self, ctx: RollContext, stack: int):
        ctx.modify_power(-3, "Paralysis")
        ctx.source.remove_status("paralysis", 1)


class ProtectionStatus(StatusEffect):
    id = "protection"
    # Логика: Снижает получаемый урон на X (реализовано в damage.py)
    pass


class FragileStatus(StatusEffect):
    id = "fragile"
    # Логика: Увеличивает получаемый урон на X (реализовано в damage.py)
    pass


class VulnerabilityStatus(StatusEffect):
    id = "vulnerability"
    # Логика: То же самое, что и Fragile
    pass


class BarrierStatus(StatusEffect):
    id = "barrier"
    # Логика: Поглощает урон вместо HP (для карты Зиккурат)
    pass