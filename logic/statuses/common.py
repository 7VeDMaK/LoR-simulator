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

class BindStatus(StatusEffect):
    id = "bind"
    pass

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

            if ctx.source.get_status("bleed_resist") > 0:
                # Снижаем на 33%
                dmg = int(dmg * 0.67)
                # Лог можно добавить при желании

            ctx.source.current_hp -= dmg
            remove_amt = stack // 2
            ctx.source.remove_status("bleed", remove_amt)
            ctx.log.append(f"🩸 Bleed: {ctx.source.name} takes {dmg} dmg")


class ParalysisStatus(StatusEffect):
    id = "paralysis"

    def on_roll(self, ctx: RollContext, stack: int):
        if ctx.dice:
            # Рассчитываем разницу между базовым броском и минимальным возможным
            # Например: выпало 7 на кубе 4-8. Мин = 4. Разница = 4 - 7 = -3.
            diff = ctx.dice.min_val - ctx.base_value

            # Применяем штраф, только если он отрицательный (не даем бонусов)
            if diff < 0:
                ctx.modify_power(diff, "Paralysis (Min)")

            # Снимаем 1 стак
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


class DeepWoundStatus(StatusEffect):
    id = "deep_wound"
    name = "Глубокая рана"
    description = (
        "При лечении: Тратится 1 заряд, лечение снижается до 75%.\n"
        "При использовании Защиты (Block/Evade): Получает урон = стакам, затем накладывается столько же Кровотечения."
    )

    def on_roll(self, ctx: RollContext, stack: int):
        # Проверяем, является ли кубик защитным
        if ctx.dice and ctx.dice.dtype in [DiceType.BLOCK, DiceType.EVADE]:
            # === FIX: Прямое изменение HP вместо take_damage ===
            dmg = stack
            ctx.source.current_hp = max(0, ctx.source.current_hp - dmg)
            # ==================================================

            # Накладываем Кровотечение
            ctx.source.add_status("bleed", stack, duration = 3)

            ctx.log.append(f"💔 **Глубокая рана**: Защита вскрыла раны! -{dmg} HP и +{stack} Bleed.")

    def apply_heal_reduction(self, unit, amount: int) -> int:
        """
        Метод вызывается при попытке лечения.
        Возвращает уменьшенное значение лечения.
        """
        # Снижаем лечение до 75%
        new_amount = int(amount * 0.75)

        # Тратим 1 заряд
        unit.remove_status("deep_wound", 1)

        return new_amount

class HasteStatus(StatusEffect):
    id = "haste"
    name = "Спешка"
    # Логика скорости обычно вшита в core/unit/mixins/combat.py,
    # поэтому здесь методов может не быть, но класс обязан существовать.
    pass

class SlowStatus(StatusEffect):
    id = "slow"
    name = "Замедление"
    pass