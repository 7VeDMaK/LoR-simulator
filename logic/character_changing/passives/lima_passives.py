from core.enums import DiceType
from logic.context import RollContext
from logic.character_changing.passives.base_passive import BasePassive

class PassiveAcceleratedLearning(BasePassive):
    id = "accelerated_learning"
    name = "Программа ускоренного обучения"
    description = (
        "Лима схватывает всё на лету.\n"
        "Каждый 3-й уровень: +10 HP/SP (вместо 5+1d5).\n"
        "Каждый 3-й уровень: +1 очко характеристик и +2 очка навыков."
    )
    is_active_ability = False


class TalentArtOfSelfDefense(BasePassive):
    id = "art_of_self_defense"
    name = "Искусство самообороны"
    description = (
        "Активно: Накладывает эффект 'BULLET TIME' на этот раунд.\n"
        "Эффект: Все кубики Уклонения выпадают на максимум. Атаки не производятся (0)."
    )
    is_active_ability = True
    cooldown = 3  # Перезарядка 3 хода

    def activate(self, unit, log_func):
        # Проверка кулдауна
        if unit.cooldowns.get(self.id, 0) > 0:
            return False

        # Накладываем статус
        unit.add_status("bullet_time", 1, duration=1)

        # Ставим кулдаун
        unit.cooldowns[self.id] = self.cooldown

        if log_func:
            log_func(f"🕰️ **{self.name}**: Активирован BULLET TIME! (Уклонение MAX, Атака 0)")
        return True

class PassiveLuckyStreak(BasePassive):
    id = "lucky_streak"
    name = "Полоса удач"
    description = "Пассивно: +7 к Удаче."
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        # "luck" находится в unit.skills, движок (calculations.py)
        # автоматически добавит это значение к навыку.
        return {"luck": 7}

class PassiveFourEyes(BasePassive):
    id = "four_eyes"
    name = "Четыре глаза"
    description = (
        "Если Лима без очков: Атакующие кубики (кроме Контр) получают штраф -50% от их МАКСИМУМА.\n"
        "Активно: Нажмите, чтобы Снять/Надеть очки."
    )
    is_active_ability = True

    def activate(self, unit, log_func):
        # Механика переключателя (Toggle)
        if unit.get_status("no_glasses") > 0:
            unit.remove_status("no_glasses", 999)
            if log_func: log_func(f"👓 **{self.name}**: Лима нашла свои очки! Зрение восстановлено.")
        else:
            unit.add_status("no_glasses", 1, duration=99)
            if log_func: log_func(f"👓 **{self.name}**: Очки потеряны/разбиты! Лима ничего не видит.")
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

# ==========================================
# Охотничьи веды
# ==========================================
class PassiveHuntersVedas(BasePassive):
    id = "hunters_vedas"
    name = "Охотничьи веды"
    description = "Пассивно: +15 Мудрости."

    def on_calculate_stats(self, unit) -> dict:
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
            return

        # Получаем итоговый интеллект (с учетом всех бонусов)
        # Если total_intellect еще не рассчитан, берем базу
        my_int = unit.modifiers.get("total_intellect", unit.base_intellect)['flat']
        op_int = opponent.modifiers.get("total_intellect", opponent.base_intellect)['flat']

        # Считаем разницу (только если мы умнее)
        diff = max(0, my_int - op_int)

        # Сохраняем бонус в память, чтобы on_calculate_stats мог его подхватить
        unit.memory["mind_suppression_bonus"] = diff

        if log_func and diff > 0:
            log_func(f"🧠 **{self.name}**: Интеллект {my_int} vs {op_int}. Бонус +{diff} к Красноречию.")

    def on_calculate_stats(self, unit) -> dict:
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