from core.dice import Dice
from core.enums import DiceType
from core.logging import logger, LogLevel
from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# 1. Возрождение из Стаггера
# ==========================================
class PassiveFanatStaggerRecovery(BasePassive):
    id = "fanat_stagger_recovery"
    name = "Неудержимый Фанат"
    description = "Если вы начинаете ход в состоянии оглушения (Stagger): полностью восстанавливает Выдержку и лечит 200 HP."

    def on_round_start(self, unit, log_func, **kwargs):
        # Если выдержка на нуле (или юнит считается в стаггере в начале раунда)
        if unit.current_stagger <= 0:
            # 1. Восстанавливаем HP
            heal = 0
            unit.heal_hp(heal)

            # 2. Восстанавливаем Stagger до максимума
            stagger_heal = unit.max_stagger
            unit.current_stagger = stagger_heal

            if log_func:
                log_func(f"🔥 **{self.name}**: Выход из оглушения! +{heal} HP, Stagger восстановлен.")

            logger.log(f"🔥 Fanat Recovery: Healed {heal} HP and restored Stagger for {unit.name}", LogLevel.NORMAL,
                       "Passive")


# ==========================================
# 2. Убийца Защиты
# ==========================================
class PassiveFanatAntiDefense(BasePassive):
    id = "fanat_anti_defense"
    name = "Пробивание защиты"
    description = "Против кубиков: +5 к силе броска."

    def on_roll(self, ctx, **kwargs):
        # Проверяем наличие цели и её текущего кубика
        ctx.modify_power(5, "Anti-Defense")
        logger.log(f"👊 Anti-Defense triggered", LogLevel.VERBOSE, "Passive")


# ==========================================
# 3. Охота на меченых
# ==========================================
class PassiveFanatMarkHunter(BasePassive):
    id = "fanat_mark_hunter"
    name = "Охота на меченых"
    description = "Против целей с Меткой Фаната: +15 к силе броска."

    def on_roll(self, ctx, **kwargs):
        target = ctx.target
        if target:
            # Проверяем наличие статуса метки
            if target.get_status("fanat_mark") > 0:
                ctx.modify_power(15, "Marked Target")
                logger.log(f"🎯 Mark Hunter triggered vs {target.name}", LogLevel.VERBOSE, "Passive")


# ==========================================
# 4. Зеркальный щит (Лимит 100)
# ==========================================
class PassiveFanatReflect(BasePassive):
    id = "fanat_reflect"
    name = "Зеркальный предел"
    description = "Вы не можете получить больше 100 урона за один удар. Весь урон превышающий 100 отражается обратно в атакующего."

    def modify_incoming_damage(self, unit, amount: int, damage_type: str, stack=0) -> int:
        limit = 100
        if amount > limit:
            excess = amount - limit

            # Ищем, кто нанес урон. В текущей архитектуре modify_incoming_damage
            # не всегда имеет прямой доступ к source, но мы можем попробовать достать его из контекста,
            # либо, если это невозможно, просто срезать урон.
            # *Примечание: В текущей реализации BaseEffect.modify_incoming_damage не принимает source.
            # Поэтому мы реализуем логику отражения в on_take_damage, а здесь просто срезаем.*

            # Возвращаем срезанный урон
            return limit
        return amount

    def on_take_damage(self, unit, amount, source, **kwargs):
        # amount здесь - это уже полученный (срезанный) урон?
        # Нет, в damage.py сначала вызывается modify_incoming_damage, а потом on_take_damage с финальным числом.
        # Нам нужно "сырое" значение до среза, которое передается как raw_amount в kwargs (если поддерживается damage.py)

        raw_amount = kwargs.get("raw_amount", 0)

        limit = 100
        if raw_amount > limit:
            excess = raw_amount - limit
            if source and source != unit:
                # Наносим чистый урон врагу
                source.current_hp = max(0, source.current_hp - excess)

                log_func = kwargs.get("log_func")
                if log_func:
                    log_func(f"🪞 **{self.name}**: Отражено {excess} урона в {source.name}!")

                logger.log(f"🪞 Fanat Reflect: Dealt {excess} reflected dmg to {source.name}", LogLevel.NORMAL,
                           "Passive")


class PassiveFanatUnwavering(BasePassive):
    id = "fanat_unwavering"
    name = "Непоколебимость"
    description = "Ваши кубики нельзя уничтожить. Сила кубиков не может быть понижена ниже выпавшего значения (Иммунитет к Параличу и Слабости)."

    def prevents_dice_destruction_by_speed(self, unit) -> bool:
        """Защита от разрушения разницей в скорости."""
        return True

    def prevents_specific_die_destruction(self, unit, die) -> bool:
        """Защита от разрушения эффектами карт."""
        return True

    def on_roll(self, ctx, **kwargs):
        """
        Если итоговое значение кубика стало меньше, чем выпало на кости (base_value),
        компенсируем разницу. Это контрит Паралич и снижение силы.
        """
        if ctx.final_value < ctx.base_value:
            diff = ctx.base_value - ctx.final_value
            ctx.modify_power(diff, "Unwavering (Restore)")
            # [LOG] Логирование срабатывания (Опционально, можно verbose)
            # logger.log(f"🛡️ Unwavering: Restored {diff} power for {ctx.source.name}", LogLevel.VERBOSE, "Passive")