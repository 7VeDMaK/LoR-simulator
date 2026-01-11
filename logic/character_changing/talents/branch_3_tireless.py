from core.dice import Dice
from core.enums import DiceType
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
        "3.2 Каждый раунд вы получаете кость активного Блока (5-7) в слот контр-атак.\n"
        "3.5: +1 Кость. Победа блоком -> +1 Защита.\n"
        "3.8: +1 Кость. Проигрыш блоком -> +1 Сила.\n"
        "3.10: +1 Кость (Всего 4)."
    )
    is_active_ability = False

    def on_speed_rolled(self, unit, log_func, **kwargs):
        """
        Используем on_round_start, как в 'Махнуть хвостиком',
        чтобы гарантированно добавить кубики.
        """
        # 1. Считаем количество кубиков
        count = 1  # База (3.2)

        if "despiteAdversities" in unit.talents: count += 1
        if "survivor" in unit.talents: count += 1
        if "surgeOfStrength" in unit.talents: count += 1

        # 2. Проверяем, существует ли список контр-кубиков (как в Wag Tail)
        if not hasattr(unit, 'counter_dice'):
            unit.counter_dice = []

        # 3. Создаем и добавляем кубики
        for _ in range(count):
            # Создаем кубик Блок 5-7
            # (Используем ваш конструктор, предполагая что порядок: Type, Min, Max)
            die = Dice(5, 7, DiceType.BLOCK, is_counter=True)

            # Настраиваем параметры
            die.is_counter = True

            # === Инициализируем flags вручную ===
            die.flags = ["talent_defense_die"]

            # Добавляем напрямую в юните
            unit.counter_dice.append(die)

        if log_func:
            log_func(f"🛡️ **{self.name}**: Добавлено {count} контр-кубиков Блока (5-7).")

    def on_clash_win(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        # Используем безопасную проверку флагов (getattr)
        if ctx.dice:
            flags = getattr(ctx.dice, "flags", [])

            if "talent_defense_die" in flags:
                # 3.5: Победа -> +1 Защита
                if "despiteAdversities" in ctx.source.talents:
                    ctx.source.add_status("protection", 1, duration=3)
                    ctx.log.append(f"🛡️ **{self.name}**: Победа -> +1 Защита")

    def on_clash_lose(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        # Используем безопасную проверку флагов (getattr)
        if ctx.dice:
            flags = getattr(ctx.dice, "flags", [])

            if "talent_defense_die" in flags:
                # 3.8: Проигрыш -> +1 Сила
                if "survivor" in ctx.source.talents:
                    ctx.source.add_status("strength", 1, duration=3)
                    ctx.log.append(f"💪 **{self.name}**: Проигрыш -> +1 Сила")


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
        unit.add_status("protection", amt, duration=2)
        if log_func: log_func(f"🛡️ **{self.name}**: +{amt} protection")

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        pct = 0.20
        if "tough_as_steel" in unit.talents:  # 3.7
            pct = 0.30

        heal = int(unit.max_hp * pct)
        actual = unit.heal_hp(heal)
        unit.cooldowns[self.id] = self.cooldown

        if log_func: log_func(f"💤 **Отдых**: Восстановлено {actual} HP ({int(pct * 100)}%)")
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
            return 1.25

        # Иначе просто эффект этого таланта
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
        unit.memory["adaptation_stats"] = {
            DiceType.SLASH: 0,
            DiceType.PIERCE: 0,
            DiceType.BLUNT: 0
        }

        # Лог для игрока, к чему мы адаптированы сейчас
        active_type = unit.memory.get("adaptation_active_type")
        if active_type and log_func:
            log_func(f"🧬 **{self.name}**: Активна защита от {active_type.name} (-25% урона).")

    def modify_incoming_damage(self, unit, amount: int, damage_type, **kwargs) -> int:
        """
        Специальный хук для изменения входящего урона ПЕРЕД его нанесением.
        """
        # Проверяем, есть ли активная адаптация с прошлого раунда
        active_type = unit.memory.get("adaptation_active_type")

        if active_type and damage_type == active_type and amount > 0:
            # Снижаем урон на 25%
            new_amount = int(amount * 0.75)
            # (Опционально можно вывести лог, если передается log_func, но в modify_ обычно тихо)
            return new_amount

        return amount

    def on_take_damage(self, unit, amount, source, **kwargs):
        """
        Считаем полученный урон для статистики (чтобы выбрать адаптацию на СЛЕДУЮЩИЙ раунд).
        """
        damage_type = None
        if amount > 0 and damage_type:
            stats = unit.memory.get("adaptation_stats")
            # Если по какой-то причине stats нет (первый удар в бою до старта раунда), создаем
            if not stats:
                stats = {DiceType.SLASH: 0, DiceType.PIERCE: 0, DiceType.BLUNT: 0}
                unit.memory["adaptation_stats"] = stats

            # Записываем урон в соответствующую категорию
            if damage_type in stats:
                stats[damage_type] += amount

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

        # Сохраняем результат для следующего раунда
        if best_type:
            unit.memory["adaptation_active_type"] = best_type
            if log_func:
                log_func(f"🧬 **{self.name}**: Организм перестроился! Адаптация к {best_type.name}.")


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

    def modify_incoming_damage(self, unit, amount: int, damage_type, **kwargs) -> int:
        """
        Сохраняем снижение урона от Кровотечения.
        """
        dtype_str = str(damage_type).lower()
        if dtype_str == "bleed":
            return int(amount * 0.67)  # -33%
        return amount

    def on_skill_check(self, unit, skill_name: str, ctx):
        """
        Хук для системы проверок навыков.
        ctx - это контекст проверки (CheckContext), где должен быть флаг advantage.
        """
        # Проверяем, что навык - Стойкость
        if skill_name.lower() in ["endurance", "стойкость"]:
            ctx.has_advantage = True
            # Можно добавить лог, если ctx поддерживает это
            if hasattr(ctx, "log"):
                ctx.log.append(f"🎲 **{self.name}**: Применено Преимущество к проверке Стойкости!")


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