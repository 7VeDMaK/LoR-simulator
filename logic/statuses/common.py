from core.enums import DiceType
from core.logging import logger, LogLevel
from logic.character_changing.talents import TALENT_REGISTRY
from logic.context import RollContext
from logic.statuses.base_status import StatusEffect


# ==========================================
# 1. МОДИФИКАТОРЫ СИЛЫ КУБИКОВ
# ==========================================

class StrengthStatus(StatusEffect):
    id = "strength"
    def on_roll(self, ctx: RollContext, **kwargs):
        stack = kwargs.get('stack', 0)
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.modify_power(stack, "Strength")

class EnduranceStatus(StatusEffect):
    id = "endurance"
    def on_roll(self, ctx: RollContext, **kwargs):
        stack = kwargs.get('stack', 0)
        if ctx.dice.dtype == DiceType.BLOCK or ctx.dice.dtype == DiceType.EVADE:
            ctx.modify_power(stack, "Endurance")

class AttackPowerDownStatus(StatusEffect):
    id = "attack_power_down"
    name = "Ослабление атаки"
    
    def on_roll(self, ctx: RollContext, **kwargs):
        stack = kwargs.get('stack', 0)
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.modify_power(-stack, "Attack Power Down")
            logger.log(
                f"⬇️ Attack Power Down: {ctx.source.name} attack power reduced by {stack}",
                LogLevel.VERBOSE, "Status"
            )

class ParalysisStatus(StatusEffect):
    id = "paralysis"
    def on_roll(self, ctx: RollContext, **kwargs):
        if ctx.dice:
            diff = ctx.dice.min_val - ctx.base_value
            if diff < 0:
                ctx.modify_power(diff, "Paralysis (Min)")
                logger.log(f"⚡ Paralysis: {ctx.source.name} roll reduced by {abs(diff)}", LogLevel.VERBOSE, "Status")
            ctx.source.remove_status("paralysis", 1)


# ==========================================
# 2. МОДИФИКАТОРЫ СКОРОСТИ
# ==========================================

class HasteStatus(StatusEffect):
    id = "haste"
    name = "Спешка"

    def get_speed_dice_value_modifier(self, unit, stack=0) -> int:
        if stack == 0: stack = unit.get_status(self.id)
        return stack

class BindStatus(StatusEffect):
    id = "bind"
    name = "Замедление"

    def get_speed_dice_value_modifier(self, unit, stack=0) -> int:
        if stack == 0: stack = unit.get_status(self.id)
        return -stack


# ==========================================
# 3. МОДИФИКАТОРЫ ИСХОДЯЩЕГО УРОНА
# ==========================================

class DmgUpStatus(StatusEffect):
    id = "dmg_up"
    name = "Усиление урона"

    def modify_outgoing_damage(self, unit, amount, damage_type, stack=0, log_list=None):
        if stack == 0: stack = unit.get_status(self.id)
        if stack > 0:
            return amount + stack
        return amount

class DmgDownStatus(StatusEffect):
    id = "dmg_down"
    name = "Ослабление урона"

    def modify_outgoing_damage(self, unit, amount, damage_type, stack=0, log_list=None):
        if stack == 0: stack = unit.get_status(self.id)
        if stack > 0:
            return amount - stack
        return amount


# ==========================================
# 4. МОДИФИКАТОРЫ ВХОДЯЩЕГО УРОНА
# ==========================================

class ProtectionStatus(StatusEffect):
    id = "protection"

    def modify_incoming_damage(self, unit, amount, damage_type, stack=0, **kwargs):
        if damage_type == "hp":
            if stack == 0: stack = unit.get_status(self.id)
            return amount - stack
        return amount

# Базовый класс для статусов, увеличивающих входящий урон (Fragile, Weakness)
class _IncomingDamageIncreaseStatus(StatusEffect):
    def modify_incoming_damage(self, unit, amount, damage_type, stack=0, **kwargs):
        if damage_type == "hp":
            if stack == 0: stack = unit.get_status(self.id)
            return amount + stack
        return amount

class FragileStatus(_IncomingDamageIncreaseStatus):
    id = "fragile"

class VulnerableStatus(StatusEffect):
    id = "vulnerable"
    name = "Рассредоточенность"
    description = "Снижает силу защитных кубов (Block/Evade)"
    
    def on_roll(self, ctx: RollContext, **kwargs):
        stack = kwargs.get('stack', 0)
        if ctx.dice.dtype == DiceType.BLOCK or ctx.dice.dtype == DiceType.EVADE:
            ctx.modify_power(-stack, "Vulnerable")
            logger.log(
                f"⬇️ Vulnerable: {ctx.source.name} defense power reduced by {stack}",
                LogLevel.VERBOSE, "Status"
            )

class WeaknessStatus(_IncomingDamageIncreaseStatus):
    id = "weakness"

class WeakStatus(StatusEffect):
    id = "weak"
    name = "Слабость"
    description = "Получает на 25% больше урона"

    def modify_incoming_damage(self, unit, amount, damage_type, stack=0, **kwargs):
        if damage_type == "hp":
            if stack == 0: stack = unit.get_status(self.id)
            if stack > 0:
                return int(amount * 1.25)
        return amount

class StaggerResistStatus(StatusEffect):
    id = "stagger_resist"
    name = "Stagger Resist"

    def modify_incoming_damage(self, unit, amount, damage_type, stack=0, **kwargs):
        if damage_type == "stagger":
            return int(amount * 0.67)
        return amount


# ==========================================
# 5. СТАТУСЫ С ПЕРИОДИЧЕСКИМ УРОНОМ И ЭФФЕКТАМИ
# ==========================================

class BleedStatus(StatusEffect):
    id = "bleed"

    def on_hit(self, ctx: RollContext, **kwargs):
        stack = kwargs.get('stack', 0)
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            dmg = stack

            if ctx.source.get_status("bleed_resist") > 0:
                dmg = int(dmg * 0.67)

            if hasattr(ctx.source, "talents"):
                for talent_id in ctx.source.talents:
                    talent = TALENT_REGISTRY.get(talent_id)
                    if talent and hasattr(talent, "modify_incoming_damage"):
                        dmg = talent.modify_incoming_damage(ctx.source, dmg, "bleed")

            ctx.source.current_hp = max(0, ctx.source.current_hp - dmg)

            remove_amt = stack // 2
            ctx.source.remove_status("bleed", remove_amt)

            ctx.log.append(f"🩸 Bleed: {ctx.source.name} takes {dmg} dmg")
            logger.log(f"🩸 Bleed: {ctx.source.name} took {dmg} damage (Stack: {stack}->{stack - remove_amt})",
                       LogLevel.MINIMAL, "Status")

class BurnStatus(StatusEffect):
    id = "burn"

    def on_round_end(self, unit, *args, **kwargs):
        stack = kwargs.get('stack', 0)
        log_func = kwargs.get('log_func')
        if stack <= 0:
            return []

        msgs = []
        dmg = stack

        if hasattr(unit, "apply_mechanics_filter"):
            dmg = unit.apply_mechanics_filter("modify_incoming_damage", dmg, "burn", stack=stack)

        unit.current_hp = max(0, unit.current_hp - dmg)

        if log_func:
            log_func(f"🔥 Burn: {unit.name} takes {dmg} dmg")

        logger.log(f"🔥 Burn: {unit.name} took {dmg} damage", LogLevel.MINIMAL, "Status")

        msgs.append(f"🔥 Burn: -{dmg} HP")

        try:
            if hasattr(unit, "trigger_mechanics"):
                unit.trigger_mechanics("on_take_damage", unit, dmg, None, log_func=log_func)
        except Exception:
            pass

        new_stack = stack // 2
        remove_amt = stack - new_stack
        if remove_amt > 0:
            unit.remove_status("burn", remove_amt)
            msgs.append(f"🔥 Burn reduced: {stack} -> {new_stack}")

        return msgs

class DeepWoundStatus(StatusEffect):
    id = "deep_wound"
    name = "Глубокая рана"
    description = (
        "При лечении: Тратится 1 заряд, лечение снижается до 75%.\n"
        "При использовании Защиты (Block/Evade): Получает урон = стакам, затем накладывается столько же Кровотечения."
    )

    def on_roll(self, ctx: RollContext, **kwargs):
        stack = kwargs.get('stack', 0)
        if ctx.dice and ctx.dice.dtype in [DiceType.BLOCK, DiceType.EVADE]:
            dmg = stack
            if hasattr(ctx.source, "apply_mechanics_filter"):
                dmg = ctx.source.apply_mechanics_filter("modify_incoming_damage", dmg, "deep_wound", stack=stack)

            ctx.source.current_hp = max(0, ctx.source.current_hp - dmg)
            ctx.source.add_status("bleed", stack, duration=3)

            ctx.log.append(f"💔 **Глубокая рана**: Защита вскрыла раны! -{dmg} HP и +{stack} Bleed.")
            logger.log(f"💔 Deep Wound triggered on {ctx.source.name}: -{dmg} HP", LogLevel.MINIMAL, "Status")

    def apply_heal_reduction(self, unit, amount: int) -> int:
        new_amount = int(amount * 0.75)
        unit.remove_status("deep_wound", 1)
        logger.log(f"💔 Deep Wound reduced healing on {unit.name}: {amount} -> {new_amount}", LogLevel.VERBOSE, "Status")
        return new_amount

class RuptureStatus(StatusEffect):
    id = "rupture"
    name = "Разрыв"
    description = (
        "Эффект Разрыва: Когда персонаж с Разрывом получает урон от любой атаки,\n"
        "он получает дополнительный урон равный количеству стаков Разрыва.\n"
        "Затем стаки Разрыва уменьшаются в 2 раза (в меньшую сторону).\n"
        "Эффект имеет бесконечную длительность, пока не будет удален."
    )

    def on_take_damage(self, unit, amount, source, **kwargs):
        """Срабатывает при получении урона персонажем с Разрывом."""
        log_func = kwargs.get("log_func")
        
        # Получаем текущие стаки Разрыва
        rupture_stack = unit.get_status("rupture")
        if rupture_stack <= 0:
            return
        
        # Если урон не от атаки (может быть урон от статуса), не срабатываем
        if amount <= 0:
            return
        
        # Дополнительный урон = стакам Разрыва
        extra_dmg = rupture_stack
        
        # Применяем фильтры талантов юнита (если есть специальная логика для снижения урона от Разрыва)
        if hasattr(unit, "talents"):
            for talent_id in unit.talents:
                talent = TALENT_REGISTRY.get(talent_id)
                if talent and hasattr(talent, "modify_incoming_damage"):
                    extra_dmg = talent.modify_incoming_damage(unit, extra_dmg, "rupture")
        
        # Наносим дополнительный чистый урон
        unit.current_hp = max(0, unit.current_hp - extra_dmg)
        
        # Снимаем половину эффекта (в меньшую сторону)
        remove_amt = max (1, rupture_stack // 2)
        unit.remove_status("rupture", remove_amt)
        
        if log_func:
            log_func(f"⚡ **Разрыв**: {unit.name} взрывается! -{extra_dmg} урона (Rupture {rupture_stack}->{rupture_stack - remove_amt})")
        
        logger.log(
            f"⚡ Rupture: {unit.name} took {extra_dmg} damage from Rupture explosion (Stack: {rupture_stack}->{rupture_stack - remove_amt})",
            LogLevel.MINIMAL, "Status"
        )

# ==========================================
# 6. БАРЬЕРЫ И ЩИТЫ
# ==========================================

class BarrierStatus(StatusEffect):
    id = "barrier"
    name = "Барьер"

    def absorb_damage(self, unit, amount, damage_type, stack=0, log_list=None):
        # [FIX] Получаем стаки, если они не переданы
        if stack == 0:
            stack = unit.get_status(self.id)

        # Если урона нет или барьера нет - ничего не делаем
        if amount <= 0 or stack <= 0:
            return amount

        absorbed = min(stack, amount)

        unit.remove_status(self.id, absorbed)

        if log_list is not None:
            log_list.append(f"🛡️ Barrier ({damage_type}) -{absorbed}")

        # Возвращаем остаток урона
        return amount - absorbed