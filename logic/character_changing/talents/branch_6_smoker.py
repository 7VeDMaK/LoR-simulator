from core.dice import Dice
from core.enums import DiceType
from core.logging import logger, LogLevel  # [NEW] Import
from core.ranks import get_base_roll_by_level
from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# 6.1 Скрываюсь в дыму
# ==========================================
class TalentHidingInSmoke(BasePassive):
    id = "hiding_in_smoke"
    name = "Скрываюсь в дыму"
    description = (
        "«Для дилетанта дым — это помеха, заставляющая слезиться глаза. Для профессионала — это вторая кожа, надежнее кевлара.»\n\n"
        "Пассивно: Изменяет свойства статуса 'Дым' на вас.\n"
        "Эффект: Дым больше не увеличивает получаемый урон. Вместо этого он дает сопротивление урону (до 30% при 10 стаках).\n"
        "Ограничение: Выбор этой ветки обязывает взять следующие 5 талантов в специализации Дыма."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        # Ставим флаг: Дым теперь дает защиту, а не уязвимость
        # Этот флаг должен обрабатываться в системе расчета урона (modify_incoming_damage)
        unit.memory["smoke_is_defensive"] = True

        if log_func:
            log_func(f"🚬 **{self.name}**: Легкие адаптировались. Дым стал щитом.")

        logger.log(f"🚬 Hiding in Smoke: {unit.name} smoke is now defensive", LogLevel.VERBOSE, "Talent")


# ==========================================
# 6.2 Универсальность дыма
# ==========================================
class TalentSmokeUniversality(BasePassive):
    id = "smoke_universality"
    name = "Универсальность дыма"
    description = (
        "«Вдохни глубже. Чувствуешь этот горький привкус? Это вкус возможностей. В правильных руках этот яд превращается в чистое топливо для тела.»\n\n"
        "Активно: Конвертация накопленного Дыма в усиления (Баффы на 3 раунда).\n"
        "Варианты обмена:\n"
        "• 4 Дыма -> +1 Сила\n"
        "• 3 Дыма -> +1 Скорость (Haste)\n"
        "• 4 Дыма -> +1 Стойкость\n"
        "• 3 Дыма -> +5 Самообладания (постоянно)\n"
        "• 3 Дыма -> +1 Защита"
    )
    is_active_ability = True

    conversion_options = {
        "str": {"label": "4 Smoke -> 1 Strength", "cost": 4, "stat": "strength", "amt": 1, "dur": 3},
        "hst": {"label": "3 Smoke -> 1 Haste", "cost": 3, "stat": "haste", "amt": 1, "dur": 3},
        "end": {"label": "4 Smoke -> 1 Endurance", "cost": 4, "stat": "endurance", "amt": 1, "dur": 3},
        "self": {"label": "3 Smoke -> 5 Self-Control", "cost": 3, "stat": "self_control", "amt": 5, "dur": 99},
        "prot": {"label": "3 Smoke -> 1 Protection", "cost": 3, "stat": "protection", "amt": 1, "dur": 3},
    }

    def activate(self, unit, log_func, choice_key=None, **kwargs):
        """
        choice_key: Ключ из conversion_options (str, hst, end, self, prot)
        """
        if not choice_key or choice_key not in self.conversion_options:
            if log_func: log_func("⚠️ Выберите тип конвертации.")
            return False

        opt = self.conversion_options[choice_key]
        cost = opt["cost"]
        target_stat = opt["stat"]
        amount = opt["amt"]
        duration = opt["dur"]

        current_smoke = unit.get_status("smoke")

        if current_smoke < cost:
            if log_func: log_func(f"❌ Недостаточно Дыма! (Нужно {cost}, есть {current_smoke})")
            return False

        # Списание и начисление
        unit.remove_status("smoke", cost)
        unit.add_status(target_stat, amount, duration=duration)

        stat_name = target_stat.replace("_", " ").title()

        if log_func:
            log_func(
                f"🌫️➡️✨ **{self.name}**: Дым переработан (-{cost}) -> +{amount} {stat_name}!"
            )

        logger.log(f"🌫️ Smoke Universality: {unit.name} converted {cost} smoke to {amount} {target_stat}",
                   LogLevel.NORMAL, "Talent")

        return True


# ==========================================
# 6.3 Воздушная стопа
# ==========================================
class TalentAerialFoot(BasePassive):
    id = "aerial_foot"
    name = "Воздушная стопа"
    description = (
        "«Стань невесомым, как пепел на ветру. Чем гуще завеса, тем сложнее уловить твои очертания. Ты не уклоняешься — тебя просто нет там, куда они бьют.»\n\n"
        "Пассивно: Вы получаете Контр-кубик Уклонения (Evade) каждый раунд.\n"
        "Бонус от Дыма: За каждые 5 стаков Дыма вы получаете +1 дополнительный кубик Уклонения (Макс +2)."
    )
    is_active_ability = False

    def on_speed_rolled(self, unit, log_func, **kwargs):
        # 1. Базовая сила от уровня
        base_min, base_max = get_base_roll_by_level(unit.level)

        # 2. Расчет количества бонусов от дыма
        smoke = unit.get_status("smoke")
        bonus_dice = min(2, smoke // 5)
        total_count = 1 + bonus_dice

        # 3. Инициализация
        if not hasattr(unit, 'counter_dice'):
            unit.counter_dice = []

        # 4. Добавление костей
        for _ in range(total_count):
            die = Dice(base_min, base_max, DiceType.EVADE, is_counter=True)
            unit.counter_dice.append(die)

        if log_func:
            log_func(
                f"🦶 **{self.name}**: Силуэт размыт. Добавлено {total_count} уклонений (Дым: {smoke}).")

        logger.log(f"🦶 Aerial Foot: Added {total_count} evade counters to {unit.name} (Lvl {unit.level})",
                   LogLevel.VERBOSE, "Talent")


# ==========================================
# 6.3 (Опционально) Дымовая завеса
# ==========================================
class TalentSmokeScreen(BasePassive):
    id = "smoke_screen"
    name = "Дымовая завеса WIP"
    description = (
        "6.3 Опц: Активно (Кость действия): Наложить 3 Дыма на всех врагов (с 6.5 -> 5).\n"
        "Вне боя: +5 к Скрытности (с 6.5 -> +7).\n"
        "с 6.7: +1 Заряд навыка."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        # Заглушка массового наложения
        if log_func: log_func("💨 **Дымовая завеса**: Все враги получают Дым (3/5).")
        logger.log(f"💨 Smoke Screen activated by {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 6.4 Переработка
# ==========================================
class TalentRecycling(BasePassive):
    id = "recycling"
    name = "Переработка WIP"
    description = "6.4 Чтобы открыть этот перк купите DLC Dascat Director's Cut."
    is_active_ability = False


# ==========================================
# 6.5 Самосохранение
# ==========================================
class TalentSelfPreservation(BasePassive):
    id = "self_preservation"
    name = "Самосохранение WIP"
    description = (
        "6.5 Снятие дебаффов за Дым:\n"
        "1 Дым -> Снять 4 Горения или 3 Кровотечения.\n"
        "3 Дыма -> Снять 1 понижение Силы/Скорости/Стойкости.\n"
        "Побег: +1 к броску за каждые 2 дыма."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        if log_func: log_func("🚑 Очистка от дебаффов активирована.")
        logger.log(f"🚑 Self Preservation activated by {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 6.5 (Опционально) Очищение
# ==========================================
class TalentCleansing(BasePassive):
    id = "cleansing"
    name = "Очищение WIP"
    description = (
        "6.5 Опц: За каждый потраченный 1 заряд Дыма -> восстановить 2 HP.\n"
        "(Не работает, если превышен максимум дыма)."
    )
    is_active_ability = False
    # Логика будет встроена в момент траты дыма


# ==========================================
# 6.6 Опытный курильщик
# ==========================================
class TalentExperiencedSmoker(BasePassive):
    id = "experienced_smoker"
    name = "Опытный курильщик WIP"
    description = (
        "6.6 Вне боя: входящий урон -20%.\n"
        "Начало боя: +5 Дыма.\n"
        "С 6.10: Урон -25%, Старт +8 Дыма."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        amt = 8 if "smoke_and_mirrors" in unit.talents else 5
        unit.add_status("smoke", amt, duration=99)
        if log_func: log_func(f"🚬 **{self.name}**: Старт с {amt} Дыма.")
        logger.log(f"🚬 Experienced Smoker: {unit.name} starts with {amt} smoke", LogLevel.VERBOSE, "Talent")


# ==========================================
# 6.7 Обрабатывания лёгких
# ==========================================
class TalentLungProcessing(BasePassive):
    id = "lung_processing"
    name = "Обрабатывания лёгких WIP"
    description = (
        "6.7 (Только Лёгкая броня) Максимум дыма: 20.\n"
        "При 15+ зарядах: Дым дает 50% понижения урона."
    )
    is_active_ability = False


# ==========================================
# 6.7 (Опционально) В Нарнию и обратно
# ==========================================
class TalentToNarnia(BasePassive):
    id = "to_narnia"
    name = "В Нарнию и обратно WIP"
    description = (
        "6.7 Опц: Первое наложение дыма на врага за бой -> Накладывает 5 понижения Силы, Стойкости и Скорости на 1 раунд."
    )
    is_active_ability = False


# ==========================================
# 6.8 Дымовое преимущество
# ==========================================
class TalentSmokeAdvantage(BasePassive):
    id = "smoke_advantage"
    name = "Дымовое преимущество WIP"
    description = (
        "6.8 В столкновении против врага с Дымом:\n"
        "+1 к силе костей за каждые 5 Дыма на враге."
    )
    is_active_ability = False

    def on_clash_start(self, ctx):
        # Проверяем дым на цели
        if ctx.target:
            smoke = ctx.target.get_status("smoke")
            bonus = smoke // 5
            if bonus > 0:
                ctx.modify_power(bonus, "Smoke Adv")
                logger.log(f"🚬 Smoke Advantage: +{bonus} Power for {ctx.source.name} vs {ctx.target.name}",
                           LogLevel.VERBOSE, "Talent")


# ==========================================
# 6.9 Уязвимость
# ==========================================
class TalentVulnerabilitySmoke(BasePassive):
    id = "vulnerability_smoke"
    name = "Уязвимость (Дым) WIP"
    description = (
        "6.9 При наложении макс. дыма на врага -> Накладывает Уязвимость.\n"
        "Его сопротивления (Slash/Pierce/Blunt) повышаются на 0.25 (получает больше урона)."
    )
    is_active_ability = False


# ==========================================
# 6.9 (Опционально) Плотный дым
# ==========================================
class TalentThickSmoke(BasePassive):
    id = "thick_smoke"
    name = "Плотный дым WIP"
    description = (
        "6.9 Опц: Атака 'Плотный дым'.\n"
        "+1 к силе за каждые 2 дыма на себе.\n"
        "Победа: Уничтожает все кости врага.\n"
        "Попадание: Макс. дым на враге 20, Макс. уязвимость от дыма 50%."
    )
    is_active_ability = False  # Это скорее карта или модификатор атаки


# ==========================================
# 6.10 Дым и зеркала
# ==========================================
class TalentSmokeAndMirrors(BasePassive):
    id = "smoke_and_mirrors"
    name = "Дым и зеркала WIP"
    description = (
        "6.10 Активно: Потратить 10 Дыма -> Создать Копию (3 раунда, макс 3).\n"
        "Враг при атаке кидает кубик (1 из X), чтобы попасть в оригинал.\n"
        "Копия умирает с 1 удара."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        # Проверка ресурса
        current_smoke = unit.get_status("smoke")
        if current_smoke < 10:
            return False

        unit.remove_status("smoke", 10)
        if log_func: log_func("🪞 **Дым и зеркала**: Копия создана! (Логика уворота заглушена)")
        logger.log(f"🪞 Smoke and Mirrors: Copy created for {unit.name}", LogLevel.NORMAL, "Talent")
        return True