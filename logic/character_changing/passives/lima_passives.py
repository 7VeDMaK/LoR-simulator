from core.enums import DiceType
from core.logging import logger, LogLevel  # [NEW] Import
from logic.character_changing.passives.base_passive import BasePassive
from logic.context import RollContext


class PassiveAcceleratedLearning(BasePassive):
    id = "accelerated_learning"
    name = "Программа ускоренного обучения"
    description = "Каждый 3-й уровень: +10 HP/SP (вместо 5+1d5)."

    def calculate_level_growth(self, unit) -> dict:
        # count = количество записей (каждая запись делается раз в 3 уровня)
        count = len(unit.level_rolls)
        return {
            "hp": count * 10,
            "sp": count * 10,
            "logs": [f"🎓 Ускоренное обучение: +10 HP/SP за каждые 3 уровня"]
        }


class TalentArtOfSelfDefense(BasePassive):
    id = "art_of_self_defense"
    name = "Искусство самообороны"
    description = (
        "Активно: Накладывает эффект 'BULLET TIME' на этот раунд.\n"
        "Эффект: Все кубики Уклонения выпадают на максимум. Атаки не производятся (0)."
    )
    is_active_ability = True
    cooldown = 3  # Перезарядка 3 хода

    def activate(self, unit, log_func, **kwargs):
        # Проверка кулдауна
        if unit.cooldowns.get(self.id, 0) > 0:
            return False

        # Накладываем статус
        unit.add_status("bullet_time", 1, duration=1)

        # Ставим кулдаун
        unit.cooldowns[self.id] = self.cooldown

        if log_func:
            log_func(f"🕰️ **{self.name}**: Активирован BULLET TIME! (Уклонение MAX, Атака 0)")

        logger.log(f"🕰️ Art of Self Defense activated by {unit.name}", LogLevel.NORMAL, "Passive")
        return True


class PassiveLuckyStreak(BasePassive):
    id = "lucky_streak"
    name = "Полоса удач"
    description = (
        "В последнее время с Лимой случались одни неудачи, но это наконец кончилось. "
        "Астрологи объявили время приключений!\n"
        "Лима получает иммунитет к внезапным атакам, появлениям зловещих киборгов-убийц, "
        "сверхсильным социопатам, фатальным травмам черепа, нанесённых ударом дверью и тому подобному.\n"
        "Она в целом более удачлива, но эта удача не перерастает в нечто явно аномальное."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"luck": 7}

    def prevents_surprise_attack(self, unit) -> bool:
        """Иммунитет к внезапным атакам (например, от талантов 9-й ветки)."""
        return True


class PassiveFourEyes(BasePassive):
    id = "four_eyes"
    name = "Четыре глаза"
    description = (
        "Если Лима без очков: Атакующие кубики (кроме Контр) получают штраф -50% от их МАКСИМУМА.\n"
        "Активно: Нажмите, чтобы Снять/Надеть очки."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        # Механика переключателя (Toggle)
        if unit.get_status("no_glasses") > 0:
            unit.remove_status("no_glasses", 999)
            if log_func: log_func(f"👓 **{self.name}**: Лима нашла свои очки! Зрение восстановлено.")
            logger.log(f"👓 Four Eyes: Glasses put ON by {unit.name}", LogLevel.NORMAL, "Passive")
        else:
            unit.add_status("no_glasses", 1, duration=99)
            if log_func: log_func(f"👓 **{self.name}**: Очки потеряны/разбиты! Лима ничего не видит.")
            logger.log(f"👓 Four Eyes: Glasses taken OFF by {unit.name}", LogLevel.NORMAL, "Passive")
        return True

    def on_roll(self, ctx: RollContext):
        # 1. Проверяем, есть ли статус "без очков"
        if ctx.source.get_status("no_glasses") <= 0:
            return

        # 2. Проверяем, что это АТАКА (Slash/Pierce/Blunt)
        if ctx.dice.dtype not in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            return

        # 3. Проверяем, что это НЕ контр-кубик
        # (В ТЗ: "но не контр-атакующие")
        if getattr(ctx.dice, 'is_counter', False):
            return

        # 4. Считаем штраф: Половина от МАКСИМУМА (математ. округление)
        # Пример: Кубик 5-7. Макс = 7. Половина = 3.5. Округление -> 4.
        max_val = ctx.dice.max_val
        penalty = int((max_val / 2) + 0.5)

        # 5. Применяем штраф (с минусом)
        ctx.modify_power(-penalty, "Blind 👓")
        logger.log(f"👓 Four Eyes Penalty: -{penalty} power for {ctx.source.name}", LogLevel.VERBOSE, "Passive")


# ==========================================
# Охотничьи веды
# ==========================================
class PassiveHuntersVedas(BasePassive):
    id = "hunters_vedas"
    name = "Охотничьи веды"
    description = "Пассивно: +15 Мудрости."

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"wisdom": 15}


# ==========================================
# Подавление разумом
# ==========================================
class PassiveMindSuppression(BasePassive):
    id = "mind_suppression"
    name = "Подавление разумом"
    description = "Пассивно: +1 к Красноречию за каждую единицу разницы в Интеллекте с целью (если ваш выше)."

    def on_combat_start(self, unit, log_func, **kwargs):
        opponent = kwargs.get("opponent")
        if not opponent:
            # Fallback if opponent passed differently or not found
            # Try getting from enemies list if provided
            enemies = kwargs.get("enemies")
            if enemies and len(enemies) > 0:
                opponent = enemies[0]
            else:
                return

        # Получаем итоговый интеллект (с учетом всех бонусов)
        # Если total_intellect еще не рассчитан, берем базу
        my_int = unit.modifiers.get("total_intellect", unit.base_intellect)
        if isinstance(my_int, dict): my_int = my_int.get('flat', unit.base_intellect)

        op_int = opponent.modifiers.get("total_intellect", opponent.base_intellect)
        if isinstance(op_int, dict): op_int = op_int.get('flat', opponent.base_intellect)

        # Считаем разницу (только если мы умнее)
        diff = max(0, my_int - op_int)

        # Сохраняем бонус в память, чтобы on_calculate_stats мог его подхватить
        unit.memory["mind_suppression_bonus"] = diff

        if log_func and diff > 0:
            log_func(f"🧠 **{self.name}**: Интеллект {my_int} vs {op_int}. Бонус +{diff} к Красноречию.")
            logger.log(f"🧠 Mind Suppression: +{diff} Eloquence for {unit.name} (Int Diff)", LogLevel.VERBOSE, "Passive")

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        # Считываем сохраненный бонус
        bonus = unit.memory.get("mind_suppression_bonus", 0)
        return {"eloquence": bonus}


# ==========================================
# Проблема корабля Тесея (Ship of Theseus Problem)
# ==========================================
class PassiveShipOfTheseus(BasePassive):
    id = "ship_of_theseus"
    name = "Проблема корабля Тесея"
    description = (
        "Лима негативно относится к любым инородным модификациям своего тела.\n"
        "Эффективность любых модификаций снижена вдвое.\n"
        "Кибернетические модификации не оказывают никакого полезного действия и вызывают желание избавиться от них."
    )
    is_active_ability = False


# ==========================================
# Wild Cityscape
# ==========================================
class PassiveWildCityscape(BasePassive):
    id = "wild_cityscape"
    name = "Wild Cityscape"
    description = (
        "Особенность 'Wild Cityscape' превращает несколько 'обычных' случайных встреч в Городе "
        "в безумные и невероятные!"
    )
    is_active_ability = False