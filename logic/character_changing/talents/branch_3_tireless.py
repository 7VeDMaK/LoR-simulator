from core.dice import Dice
from core.enums import DiceType
from core.logging import logger, LogLevel  # [NEW] Import
from core.ranks import get_base_roll_by_level
from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# 3.1 Здоровяк
# ==========================================
class TalentBigGuy(BasePassive):
    id = "big_guy"
    name = "Здоровяк"
    description = "3.1 Увеличивает максимальное здоровье на 15%."
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {"max_hp_pct": 15}


# ==========================================
# 3.2 Оборона
# ==========================================
class TalentDefense(BasePassive):
    id = "defense"
    name = "Оборона"
    description = (
        "3.2 Каждый раунд вы получаете кость активного Блока (значение зависит от Уровня) в слот контр-атак.\n"
        "3.5: +1 Кость. Победа блоком -> +1 Защита.\n"
        "3.8: +1 Кость. Проигрыш блоком -> +1 Сила.\n"
        "3.10: +1 Кость (Всего 4)."
    )
    is_active_ability = False

    def on_speed_rolled(self, unit, log_func, **kwargs):
        """
        Используем on_speed_rolled, чтобы добавить кубики.
        """
        # 1. Считаем количество кубиков (апгрейды ветки)
        count = 1  # База (3.2)

        if "despiteAdversities" in unit.talents: count += 1
        if "survivor" in unit.talents: count += 1
        if "surgeOfStrength" in unit.talents: count += 1

        # 2. Определяем силу кубика на основе уровня
        base_min, base_max = get_base_roll_by_level(unit.level)

        # 3. Проверяем список (инициализация)
        if not hasattr(unit, 'counter_dice'):
            unit.counter_dice = []

        # 4. Создаем и добавляем кубики
        for _ in range(count):
            # Создаем кубик с динамическими значениями
            die = Dice(base_min, base_max, DiceType.BLOCK, is_counter=True)

            # Флаг для работы других талантов (3.5, 3.8)
            die.flags = ["talent_defense_die"]

            unit.counter_dice.append(die)

        if log_func:
            log_func(f"🛡️ **{self.name}**: Добавлено {count} контр-кубиков Блока ({base_min}-{base_max}).")

        logger.log(f"🛡️ Defense: Added {count} counter blocks ({base_min}-{base_max}) to {unit.name}", LogLevel.VERBOSE,
                   "Talent")

    def on_clash_win(self, ctx, **kwargs):
        # ... (код без изменений) ...
        stack = kwargs.get("stack", 0)
        if ctx.dice:
            flags = getattr(ctx.dice, "flags", [])

            if "talent_defense_die" in flags:
                # 3.5: Победа -> +1 Защита
                if "despiteAdversities" in ctx.source.talents:
                    ctx.source.add_status("protection", 1, duration=3)
                    ctx.log.append(f"🛡️ **{self.name}**: Победа -> +1 Защита")
                    logger.log(f"🛡️ Defense (Despite Adversities): +1 Protection on win for {ctx.source.name}",
                               LogLevel.VERBOSE, "Talent")

    def on_clash_lose(self, ctx, **kwargs):
        # ... (код без изменений) ...
        stack = kwargs.get("stack", 0)
        if ctx.dice:
            flags = getattr(ctx.dice, "flags", [])

            if "talent_defense_die" in flags:
                # 3.8: Проигрыш -> +1 Сила
                if "survivor" in ctx.source.talents:
                    ctx.source.add_status("strength", 1, duration=3)
                    ctx.log.append(f"💪 **{self.name}**: Проигрыш -> +1 Сила")
                    logger.log(f"💪 Defense (Survivor): +1 Strength on lose for {ctx.source.name}", LogLevel.VERBOSE,
                               "Talent")


# ==========================================
# 3.3 Похвальное телосложение
# ==========================================
class TalentCommendableConstitution(BasePassive):
    id = "commendable_constitution"
    name = "Похвальное телосложение"
    description = (
        "3.3 Стойкость +3.\n"
        "Пассивно в бою: +1 Стойкость (Endurance). Если есть 3.8 -> +2.\n"
        "Активно (1 раз в день): Короткий отдых. Восстанавливает 20% HP (30%, если есть 3.7)."
    )
    is_active_ability = True
    cooldown = 99  # 1 раз за бой/день

    def on_calculate_stats(self, unit) -> dict:
        return {"endurance": 3}

    def on_round_start(self, unit, log_func, **kwargs):
        amt = 1
        if "survivor" in unit.talents:  # 3.8
            amt += 1
        unit.add_status("protection", amt, duration=1)
        if log_func: log_func(f"🛡️ **{self.name}**: +{amt} protection")

        logger.log(f"🛡️ Commendable Constitution: +{amt} Protection for {unit.name}", LogLevel.VERBOSE, "Talent")

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        pct = 0.20
        if "tough_as_steel" in unit.talents:  # 3.7
            pct = 0.30

        heal = int(unit.max_hp * pct)
        actual = unit.heal_hp(heal)
        unit.cooldowns[self.id] = self.cooldown

        if log_func: log_func(f"💤 **Отдых**: Восстановлено {actual} HP ({int(pct * 100)}%)")
        logger.log(f"💤 Short Rest: Healed {actual} HP for {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 3.3 (Опционально) Большое сердце
# ==========================================
class TalentBigHeart(BasePassive):
    id = "big_heart"
    name = "Большое сердце WIP"
    description = (
        "3.3 Опц: Реакцией можно защитить союзника, подставившись под удар (используя неиспользованные кости Блока).\n"
        "Если используются кости Обороны, союзник получает эффекты навыка."
    )
    is_active_ability = False


# ==========================================
# 3.4 Скала
# ==========================================
class TalentRock(BasePassive):
    id = "rock"
    name = "Скала"
    description = (
        "3.4 Если вы получаете 0 урона от атаки (благодаря резистам или статусам, но НЕ Блоку),\n"
        "весь исходный урон отражается в атакующего."
    )
    is_active_ability = False

    def on_take_damage(self, unit, amount, source, **kwargs):
        """
        Срабатывает после расчета урона, когда HP уже (не) отнялось.
        amount - это ИТОГОВЫЙ урон (который прошел через резисты).
        """
        # 1. Условие: Итоговый урон по здоровью должен быть 0 (мы танканули)
        if amount > 0:
            return

        # 2. Условие: Источник должен существовать и быть врагом
        if not source or source == unit:
            return

        # 3. Условие: Это не должно быть благодаря Блоку
        # [FIX] Безопасная проверка, чтобы не крашнулось, если current_die не задан
        current_die = getattr(unit, "current_die", None)
        if current_die and current_die.dtype == DiceType.BLOCK:
            return

        # 4. Определяем, сколько урона отразить
        # Берем "сырой" урон до резистов, который мы передали из damage.py
        reflect_amt = kwargs.get("raw_amount", 0)

        # 5. Отражаем урон (Pure Damage)
        if reflect_amt > 0:
            # [FIX] Используем прямое вычитание HP, т.к. метода take_damage нет
            source.current_hp = max(0, source.current_hp - reflect_amt)

            # Логируем
            log_func = kwargs.get("log_func")
            if log_func:
                log_func(f"🪨 **Скала**: Броня непробиваема! Отражено {reflect_amt} урона.")

            logger.log(f"🪨 Rock: Reflected {reflect_amt} damage to {source.name}", LogLevel.NORMAL, "Talent")


# ==========================================
# 3.5 Не взирая на невзгоды
# ==========================================
class TalentDespiteAdversities(BasePassive):
    id = "despiteAdversities"
    name = "Не взирая на невзгоды"
    description = (
        "3.5 В Оглушении входящий урон x1.5 (вместо x2.0).\n"
        "Кости навыка 'Оборона' остаются активными даже в Оглушении.\n"
        "Если есть 3.10 -> входящий урон x1.25."
    )
    is_active_ability = False

    # === [NEW] Реализация хука ===
    def modify_stagger_damage_multiplier(self, unit, multiplier: float) -> float:
        # Стандартный множитель x2.0. Мы меняем его.

        # Если есть улучшение 3.10 (Прилив сил)
        if "surgeOfStrength" in unit.talents:
            logger.log(f"🛡️ Despite Adversities (Surge): Stagger multiplier set to 1.25 for {unit.name}",
                       LogLevel.VERBOSE, "Talent")
            return 1.25

        # Иначе просто эффект этого таланта
        logger.log(f"🛡️ Despite Adversities: Stagger multiplier set to 1.5 for {unit.name}", LogLevel.VERBOSE, "Talent")
        return 1.5


# ==========================================
# 3.5 (Опционально) Термостойкий
# ==========================================
class TalentHeatResistant(BasePassive):
    id = "heat_resistant"
    name = "Термостойкий"
    description = "3.5 Опц: Урон от Огня и Холода снижен на 33%."
    is_active_ability = False


# ==========================================
# 3.6 Адаптация (Тип 2)
# ==========================================
class TalentAdaptationTireless(BasePassive):
    id = "adaptation_tireless"
    name = "Адаптация"
    description = (
        "3.6 В конце раунда вы адаптируетесь к типу урона, полученному больше всего.\n"
        "В следующем раунде получаемый урон этого типа снижен на 25%."
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        # ИСПОЛЬЗУЕМ СТРОКИ ВМЕСТО DiceType
        unit.memory["adaptation_stats"] = {
            "slash": 0,
            "pierce": 0,
            "blunt": 0
        }

        # Лог для игрока, к чему мы адаптированы сейчас
        active_type_str = unit.memory.get("adaptation_active_type")

        # Превращаем строку обратно в Enum для красивого вывода имени (если нужно) или просто используем строку
        if active_type_str and log_func:
            # Для красивого лога делаем первую букву заглавной
            type_name = active_type_str.capitalize()
            log_func(f"🧬 **{self.name}**: Активна защита от {type_name} (-25% урона).")
            # [LOG]
            # logger.log не обязателен тут, если вы не используете глобальный логгер внутри этого метода

    def on_take_damage(self, unit, amount, source, **kwargs):
        """
        Считаем полученный урон для статистики.
        """
        damage_type = kwargs.get("damage_type")  # Это уже приходит как строка ("slash", "pierce"...)

        if amount > 0 and damage_type:
            stats = unit.memory.get("adaptation_stats")
            # Если stats нет, создаем со строковыми ключами
            if not stats:
                stats = {"slash": 0, "pierce": 0, "blunt": 0}
                unit.memory["adaptation_stats"] = stats

            # Приводим к строке и нижнему регистру для надежности
            dtype_key = str(damage_type).lower()

            # Обработка случая, если damage_type вдруг пришел как Enum (на всякий случай)
            if hasattr(damage_type, 'name'):
                dtype_key = damage_type.name.lower()

            if dtype_key in stats:
                stats[dtype_key] += amount

    def on_round_end(self, unit, log_func, **kwargs):
        """
        Подводим итоги раунда и выбираем тип для адаптации.
        """
        stats = unit.memory.get("adaptation_stats", {})

        best_type = None
        max_dmg = 0

        # Ищем тип с максимальным уроном
        for dtype, val in stats.items():
            if val > max_dmg:
                max_dmg = val
                best_type = dtype

        # Сохраняем результат (строку)
        if best_type:
            unit.memory["adaptation_active_type"] = best_type
            if log_func:
                log_func(f"🧬 **{self.name}**: Организм перестроился! Адаптация к {best_type.capitalize()}.")


# ==========================================
# 3.7 Крепкий как сталь
# ==========================================
class TalentToughAsSteel(BasePassive):
    id = "tough_as_steel"
    name = "Крепкий как сталь"
    description = (
        "3.7 Макс. Здоровье +20%.\n"
        "Победа костью блока -> накладывает 1 Хрупкость (Fragile)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {"max_hp_pct": 20}

    def on_clash_win(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        if ctx.dice.dtype == DiceType.BLOCK:
            target = ctx.target  # Тот, с кем столкновение (атакующий)
            if target:
                target.add_status("fragile", 1, duration=3)
                ctx.log.append(f"🧱 **{self.name}**: Враг получил +1 Хрупкость")
                logger.log(f"🧱 Tough As Steel: Applied Fragile to {target.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 3.7 (Опционально) Защитник
# ==========================================
class TalentDefender(BasePassive):
    id = "defender"
    name = "Защитник WIP"
    description = (
        "3.7 Опц: Союзники получают 4 Защиты в первом раунде.\n"
        "Можно перехватывать удары за союзников без костей блока (получая +1 Силу за каждый удар)."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        # В текущей версии сложно найти "союзников", наложим на себя как ауру
        if log_func: log_func(f"🛡️ **{self.name}**: Аура защиты активирована.")


# ==========================================
# 3.8 Выживший
# ==========================================
class TalentSurvivor(BasePassive):
    id = "survivor"
    name = "Выживший"
    description = (
        "3.8 Проверки навыка Стойкости (Endurance) проходят с Преимуществом.\n"
        "Пассивно: Если здоровье падает до 30% и ниже, вы восстанавливаете 10% HP в начале раунда.\n"
        "Урон от Кровотечения снижен на 33%.\n"
    )
    is_active_ability = False  # Больше не активная способность

    def on_round_start(self, unit, log_func, **kwargs):
        """
        Пассивная регенерация при низком здоровье.
        """
        # Порог срабатывания (30%)
        low_hp_threshold = unit.max_hp * 0.30

        if unit.current_hp <= low_hp_threshold:
            # Лечение (10%)
            heal_amount = int(unit.max_hp * 0.10)
            if heal_amount > 0:
                actual = unit.heal_hp(heal_amount)
                if log_func:
                    log_func(f"❤️ **{self.name}**: Критическое состояние! Регенерация +{actual} HP.")
                logger.log(f"❤️ Survivor: Critical HP regen +{actual} HP for {unit.name}", LogLevel.NORMAL, "Talent")

    def modify_incoming_damage(self, unit, amount: int, damage_type, **kwargs) -> int:
        active_type = unit.memory.get("adaptation_active_type")  # Это теперь строка

        # Приводим входящий тип к строке
        incoming_type_str = str(damage_type).lower()
        if hasattr(damage_type, 'name'):
            incoming_type_str = damage_type.name.lower()

        if active_type and incoming_type_str == active_type and amount > 0:
            new_amount = int(amount * 0.75)
            return new_amount

        return amount

    def on_check_roll(self, unit, attribute: str, context):
        """
        Хук для системы проверок навыков (UI).
        """
        if attribute.lower() in ["endurance", "стойкость"]:
            context.is_advantage = True
            if hasattr(context, "log"):
                context.log.append(f"🎲 **{self.name}**: Преимущество на Стойкость!")
            from core.logging import logger, LogLevel
            logger.log(f"🎲 Survivor: Advantage on Endurance check for {unit.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 3.9 Перенапряжение мышц
# ==========================================
class TalentMuscleOverstrain(BasePassive):
    id = "muscle_overstrain"
    name = "Перенапряжение мышц"
    description = "3.9 Активно: Потратить 5 HP или 10 Stagger -> +1 Мощь кубиков (2 раза/раунд)."
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        # Тратим 5 HP
        unit.current_hp = max(1, unit.current_hp - 5)
        unit.add_status("strength", 1, duration=1)
        if log_func: log_func("💪 **Перенапряжение**: -5 HP -> +1 Сила")

        logger.log(f"💪 Muscle Overstrain: -5 HP for +1 Strength for {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 3.9 (Опционально) Клятва идола
# ==========================================
class TalentIdolOath(BasePassive):
    id = "idol_oath"
    name = "Клятва идола"
    description = (
        "3.9 Опц: Вы отказываетесь от лечения других WIP.\n"
        "Медицина +15.\n"
        "HP < 25% -> +2 Мощь.\n"
        "Крепкая кожа +15."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        # Базовые бонусы
        mods = {"medicine": 15, "tough_skin": 15}

        # Проверка HP < 25%
        if unit.max_hp > 0 and (unit.current_hp / unit.max_hp) < 0.25:
            # Заменяем нерабочий "power_all" на три конкретных бонуса
            mods["power_attack"] = 2  # Для Атаки (Slash/Pierce/Blunt)
            mods["power_block"] = 2  # Для Блока
            mods["power_evade"] = 2  # Для Уклонения

            # Log this effect only once per recalc cycle ideally, or rely on stats diff
            # logger.log(f"💪 Idol Oath: HP < 25% -> +2 Power activated for {unit.name}", LogLevel.VERBOSE, "Talent")

        return mods


# ==========================================
# 3.10 Прилив сил
# ==========================================
class TalentSurgeOfStrength(BasePassive):
    id = "surgeOfStrength"  # Связь с Обороной
    name = "Прилив сил"
    description = (
        "3.10 HP < 25% -> Мгновенный выход из Оглушения и переброс инициативы.\n"
        "До конца раунда: +4 Силы, Стойкости, Спешки, Защиты.\n"
        "Далее до конца боя: +2 Спешки, Откаты -1."
    )
    is_active_ability = False

    # Логика "HP < 25%" должна проверяться в on_take_damage или on_round_start