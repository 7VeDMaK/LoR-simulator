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
    description = (
        "«Чтобы выжить в Переулках, нужно быть либо быстрым, либо нерушимым. Ты выбрал быть горой, которую не сдвинет ни один шторм.»\n\n"
        "Пассивно: Ваше тело становится крепче стали.\n"
        "Эффект: Максимальное здоровье (HP) увеличено на 15%."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"max_hp_pct": 15}


# ==========================================
# 3.2 Оборона
# ==========================================
class TalentDefense(BasePassive):
    id = "defense"
    name = "Оборона"
    description = (
        "«Лучшая атака — это защита, которая ломает волю нападающего. Пусть они бьют, пока их руки не сотрутся в кровь; ты останешься стоять.»\n\n"
        "Пассивно: В начале каждого раунда вы получаете Контр-кубики Блока (значение растет с уровнем).\n"
        "База: 1 Кубик.\n"
        "Апгрейды (другие таланты ветки):\n"
        "• 'Вопреки всему' (3.5): +1 Кубик. Победа в блоке даёт Защиту.\n"
        "• 'Выживший' (3.8): +1 Кубик. Проигрыш в блоке даёт Силу.\n"
        "• 'Прилив сил' (3.10): +1 Кубик (Итого макс. 4)."
    )
    is_active_ability = False

    def on_speed_rolled(self, unit, *args, **kwargs):
        log_func = kwargs.get("log_func")
        """
        Генерируем защитные кубики после броска скорости.
        """
        # 1. Считаем количество кубиков (проверяем наличие апгрейдов по ID)
        count = 1  # База (3.2)

        # Проверяем ID талантов (предполагаем snake_case для consistency)
        if "despite_adversities" in unit.talents: count += 1  # 3.5
        if "survivor" in unit.talents: count += 1  # 3.8
        if "surge_of_strength" in unit.talents: count += 1  # 3.10

        # 2. Определяем силу кубика на основе уровня
        base_min, base_max = get_base_roll_by_level(unit.level)

        # 3. Инициализация списка контр-кубиков
        if not hasattr(unit, 'counter_dice'):
            unit.counter_dice = []

        # 4. Создаем и добавляем кубики
        for _ in range(count):
            # Создаем кубик Блока
            die = Dice(base_min, base_max, DiceType.BLOCK, is_counter=True)

            # Помечаем флагом для триггеров победы/поражения
            die.flags = ["talent_defense_die"]

            unit.counter_dice.append(die)

        if log_func:
            log_func(f"🛡️ **{self.name}**: Сформировано {count} линий обороны ({base_min}-{base_max}).")

        logger.log(f"🛡️ Defense: Added {count} counter blocks ({base_min}-{base_max}) to {unit.name}", LogLevel.VERBOSE,
                   "Talent")

    def on_clash_win(self, ctx, **kwargs):
        """Победа в столкновении (если есть талант 3.5)."""
        if not ctx.dice: return

        flags = getattr(ctx.dice, "flags", [])
        if "talent_defense_die" in flags:
            # 3.5: Победа -> +1 Защита
            if "despite_adversities" in ctx.source.talents:
                ctx.source.add_status("protection", 1, duration=1)
                if hasattr(ctx, 'log'):
                    ctx.log.append(f"🛡️ **Оборона**: Блок успешен! (+1 Protection)")

                logger.log(f"🛡️ Defense (Win): +1 Protection for {ctx.source.name}", LogLevel.VERBOSE, "Talent")

    def on_clash_lose(self, ctx, **kwargs):
        """Проигрыш в столкновении (если есть талант 3.8)."""
        if not ctx.dice: return

        flags = getattr(ctx.dice, "flags", [])
        if "talent_defense_die" in flags:
            # 3.8: Проигрыш -> +1 Сила (Ярость от удара)
            if "survivor" in ctx.source.talents:
                ctx.source.add_status("attack_power_up", 1, duration=1)
                if hasattr(ctx, 'log'):
                    ctx.log.append(f"💪 **Оборона**: Блок пробит! Ярость нарастает! (+1 Strength)")

                logger.log(f"💪 Defense (Lose): +1 Strength for {ctx.source.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 3.3 Похвальное телосложение
# ==========================================
class TalentCommendableConstitution(BasePassive):
    id = "commendable_constitution"
    name = "Похвальное телосложение"
    description = (
        "«Твое тело — это крепость. Даже когда стены трещат, фундамент держится. Сделай вдох, перевяжи рану и сражайся дальше.»\n\n"
        "Пассивно: +3 к Стойкости (Attribute).\n"
        "Бонус в бою: В начале раунда вы получаете +1 Защиту (Protection). (Если есть 'Выживший', то +2).\n"
        "Активно (1 раз за бой): Короткий отдых. Восстанавливает 20% HP (30% при улучшении)."
    )
    is_active_ability = True
    cooldown = 99  # Фактически 1 раз за бой

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"endurance": 3}

    def on_round_start(self, unit, *args, **kwargs):
        log_func = kwargs.get("log_func")
        amt = 1
        # Синергия с 3.8 Survivor
        if "survivor" in unit.talents:
            amt += 1

        unit.add_status("protection", amt, duration=1)

        if log_func:
            log_func(f"🛡️ **{self.name}**: Кожа твердеет (+{amt} Protection).")

        logger.log(f"🛡️ Commendable Constitution: +{amt} Protection for {unit.name}", LogLevel.VERBOSE, "Talent")

    def activate(self, unit, *args, **kwargs):
        log_func = kwargs.get("log_func")
        if unit.cooldowns.get(self.id, 0) > 0:
            if log_func: log_func("❌ Вы уже отдыхали в этом бою.")
            return False

        # Синергия с 3.7 Tough as Steel
        pct = 0.20
        msg_extra = ""
        if "tough_as_steel" in unit.talents:
            pct = 0.30
            msg_extra = "(Усилено: Крепкий как сталь)"

        heal_amount = int(unit.max_hp * pct)
        actual_healed = unit.heal_hp(heal_amount)

        unit.cooldowns[self.id] = self.cooldown

        if log_func:
            log_func(f"💤 **Отдых**: Раны затягиваются... +{actual_healed} HP {msg_extra}")

        logger.log(f"💤 Short Rest: Healed {actual_healed} HP for {unit.name}", LogLevel.NORMAL, "Talent")
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

#TODO опц 3.3

# ==========================================
# 3.4 Скала
# ==========================================
class TalentRock(BasePassive):
    id = "rock"
    name = "Скала"
    description = (
        "«Тот, кто бьёт гору, лишь ломает собственные кости. Твоя кожа стала тверже железа, и любой бессильный удар эхом отдается в теле врага.»\n\n"
        "Пассивно: Если атака наносит вам 0 урона (из-за Сопротивлений или Защиты, но НЕ из-за кубика Блока):\n"
        "Эффект: Весь исходный урон (до снижения) отражается обратно в атакующего как Чистый урон."
    )
    is_active_ability = False

    def on_take_damage(self, unit, amount, source, **kwargs):
        """
        Срабатывает после расчета урона.
        amount - итоговый урон, который прошел в HP.
        raw_amount - урон, который был нанесен кубиком до вычета резистов (должен передаваться в kwargs).
        """
        # 1. Условие: Итоговый урон по здоровью должен быть 0 (мы танканули телом)
        if amount > 0:
            return

        # 2. Условие: Источник должен существовать и быть врагом (не отражаем селф-дамп)
        if not source or source == unit:
            return

        # 3. Условие: Это не должно быть благодаря активному Блоку (DiceType.BLOCK)
        # Проверяем текущий кубик юнита, если он есть
        current_die = getattr(unit, "current_die", None)
        if current_die and current_die.dtype == DiceType.BLOCK:
            return

        # 4. Определяем, сколько урона отразить
        # raw_amount должен передаваться из системы боя
        reflect_amt = kwargs.get("raw_amount", 0)

        # 5. Отражаем урон (Pure Damage)
        if reflect_amt > 0:
            # Наносим урон напрямую, или через take_damage с флагом 'reflected'
            if hasattr(source, 'take_damage'):
                # Вариант через метод (чтобы триггерить смерти и т.д.)
                source.take_damage(reflect_amt)
            else:
                # Прямое вычитание (как в примере)
                source.current_hp = max(0, source.current_hp - reflect_amt)

            # Логируем
            log_func = kwargs.get("log_func")
            if log_func:
                log_func(f"🪨 **{self.name}**: Броня непробиваема! Враг получает {reflect_amt} урона отдачей.")

            logger.log(f"🪨 Rock: Reflected {reflect_amt} damage to {source.name}", LogLevel.NORMAL, "Talent")


# ==========================================
# 3.5 Не взирая на невзгоды
# ==========================================
class TalentDespiteAdversities(BasePassive):
    id = "despite_adversities"
    name = "Не взирая на невзгоды"
    description = (
        "«Даже стоя на коленях, ты остаешься угрозой. Боль затуманивает разум, но инстинкты продолжают держать щит.»\n\n"
        "Пассивно: Вы получаете меньше урона, находясь в состоянии Оглушения (Stagger).\n"
        "Эффект: Множитель урона по оглушенным снижен с x2.0 до x1.5.\n"
        "Бонус (при наличии таланта 'Прилив сил'): Множитель снижен до x1.25.\n"
        "Особенность: Ваши защитные контр-кубики (от таланта 'Оборона') остаются активными даже в Оглушении."
    )
    is_active_ability = False

    def modify_stagger_damage_multiplier(self, unit, multiplier: float) -> float:
        """
        Изменяет множитель входящего урона, когда юнит находится в Stagger.
        Стандартное значение в системе обычно 2.0.
        """
        # Проверяем наличие синергии с талантом 3.10 (surge_of_strength)
        if "surge_of_strength" in unit.talents:
            logger.log(
                f"🛡️ Despite Adversities (Surge): Stagger multiplier set to 1.25 for {unit.name}",
                LogLevel.VERBOSE,
                "Talent"
            )
            return 1.25

        # Базовый эффект таланта
        logger.log(
            f"🛡️ Despite Adversities: Stagger multiplier set to 1.5 for {unit.name}",
            LogLevel.VERBOSE,
            "Talent"
        )
        return 1.5

    # def can_use_counter_die_while_staggered(self, unit):
    #     """
    #     Разрешает использование защитных (Counter) кубиков, даже если юнит в Stagger.
    #     """
    #     return True


#TODO опц 3.5

# ==========================================
# 3.5 (Опционально) Термостойкий
# ==========================================
class TalentHeatResistant(BasePassive):
    id = "heat_resistant"
    name = "Термостойкий WIP"
    description = "3.5 Опц: Урон от Огня и Холода снижен на 33%."
    is_active_ability = False


# ==========================================
# 3.6 Адаптация
# ==========================================
class TalentAdaptationTireless(BasePassive):
    id = "adaptation_tireless"
    name = "Адаптация"
    description = (
        "«Боль — это лучший учитель. Единожды познав, как сталь режет плоть, тело само учится отвергать лезвие в следующий раз.»\n\n"
        "Пассивно: В конце каждого раунда организм анализирует полученный урон.\n"
        "Эффект: Вы получаете сопротивление (-25% урона) к тому типу физического урона (Р, К или Д), которого получили больше всего в прошлом раунде."
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
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
        "«Бить железо голыми руками — глупость. Чем яростнее их удары, тем быстрее их собственные кости превратятся в пыль.»\n\n"
        "Пассивно: +20% к Максимальному Здоровью.\n"
        "Эффект: Успешная защита разрушает врага.\n"
        "При победе кубиком Блока: Накладывает 1 Хрупкость (Fragile) на атакующего."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"max_hp_pct": 20}

    def on_clash_win(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        if ctx.dice.dtype == DiceType.BLOCK:
            target = ctx.target  # Тот, с кем столкновение (атакующий)
            if target:
                target.add_status("fragile", 1, duration=3)
                ctx.log.append(f"🧱 **{self.name}**: Враг получил +1 Хрупкость")
                logger.log(f"🧱 Tough As Steel: Applied Fragile to {target.name}", LogLevel.VERBOSE, "Talent")

#TODO Opc 3.7

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
        "«Ты как таракан. Тебя бьют, режут, ломают, но ты всё равно ползешь вперед. Смерть просто устала гоняться за тобой.»\n\n"
        "Пассивно: Проверки Стойкости (Endurance) всегда с Преимуществом.\n"
        "Регенерация: Если HP <= 30%, в начале раунда восстанавливает 10% HP.\n"
        "Свертываемость: Урон от Кровотечения снижен на 33%."
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        """
        Пассивная регенерация при низком здоровье.
        """
        low_hp_threshold = unit.max_hp * 0.30

        if unit.current_hp <= low_hp_threshold:
            heal_amount = int(unit.max_hp * 0.10)
            if heal_amount > 0:
                actual = unit.heal_hp(heal_amount)
                if log_func:
                    log_func(f"❤️ **{self.name}**: Организм борется за жизнь! (+{actual} HP).")
                logger.log(f"❤️ Survivor: Critical HP regen +{actual} HP for {unit.name}", LogLevel.NORMAL, "Talent")

    def modify_incoming_damage(self, unit, amount: int, damage_type, **kwargs) -> int:
        """
        Снижение урона от кровотечения.
        """
        # Проверяем, является ли источник урона статусом "bleed"
        status_id = kwargs.get("status_id") or kwargs.get("source_type")

        if status_id == "bleed" and amount > 0:
            # Снижаем на 33% (оставляем 67%)
            new_amount = int(amount * 0.67)
            logger.log(
                f"🩸 Survivor: Bleed damage reduced ({amount} -> {new_amount})",
                LogLevel.VERBOSE,
                "Talent"
            )
            return new_amount

        return amount

    def on_check_roll(self, unit, attribute: str, context):
        """
        Дает преимущество на проверки Стойкости.
        """
        if attribute.lower() in ["endurance", "стойкость"]:
            context.is_advantage = True
            if hasattr(context, "log"):
                context.log.append(f"🎲 **{self.name}**: Тело выдержит (Преимущество).")

            logger.log(f"🎲 Survivor: Advantage on Endurance check for {unit.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 3.9 Перенапряжение мышц
# ==========================================
class TalentMuscleOverstrain(BasePassive):
    id = "muscle_overstrain"
    name = "Перенапряжение мышц"
    description = (
        "«Мышцы рвутся с приятным хрустом. Боль — это цена за силу, которую они не смогут остановить.»\n\n"
        "Активно (Макс 2 раза за раунд): Пожертвовать здоровьем или выдержкой ради силы.\n"
        "Стоимость: 5 HP или 10 Stagger.\n"
        "Эффект: +1 Мощь (Strength) на этот раунд."
    )
    is_active_ability = True

    # Опции для UI выбора
    conversion_options = {
        "pay_hp": "Потратить 5 HP",
        "pay_sp": "Потратить 10 Stagger"
    }

    def on_round_start(self, unit, *args, **kwargs):
        """Сброс счетчика использований в начале раунда."""
        unit.memory["muscle_overstrain_uses"] = 0

    def activate(self, unit, log_func, choice_key="pay_hp", **kwargs):
        # 1. Проверка лимита (2 раза в раунд)
        uses = unit.memory.get("muscle_overstrain_uses", 0)
        if uses >= 2:
            if log_func: log_func("⚠️ Предел напряжения достигнут (макс. 2 раза за раунд).")
            return False

        # 2. Обработка выбора (HP или Stagger)
        cost_hp = 0
        cost_stagger = 0

        if choice_key == "pay_sp":  # Используем ключ SP как Stagger в контексте UI, если так удобнее, или переименовать
            cost_stagger = 10
        else:
            cost_hp = 5

        # 3. Проверка ресурсов
        if unit.current_hp <= cost_hp:
            if log_func: log_func("❌ Недостаточно здоровья!")
            return False

        # Stagger технически может уйти в 0 (Staggered state), разрешаем, но предупреждаем
        if unit.current_stagger < cost_stagger:
            if log_func: log_func("❌ Недостаточно выдержки (Stagger)!")
            return False

        # 4. Списание ресурсов
        if cost_hp > 0:
            unit.current_hp -= cost_hp

        if cost_stagger > 0:
            unit.current_stagger -= cost_stagger

        # 5. Применение эффекта
        unit.add_status("attack_power_up", 1, duration=1)
        unit.memory["muscle_overstrain_uses"] = uses + 1

        if log_func:
            res_name = "HP" if cost_hp > 0 else "Stagger"
            val = cost_hp if cost_hp > 0 else cost_stagger
            log_func(f"💪 **{self.name}**: Жертва {val} {res_name} -> +1 Сила (Использовано {uses + 1}/2).")

        logger.log(f"💪 Muscle Overstrain: Paid cost for +1 Strength", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 3.9 (Опционально) Клятва идола
# ==========================================
class TalentIdolOath(BasePassive):
    id = "idol_oath"
    name = "Клятва идола WIP"
    description = (
        "3.9 Опц: Вы отказываетесь от лечения других WIP.\n"
        "Медицина +15.\n"
        "HP < 25% -> +2 Мощь.\n"
        "Крепкая кожа +15."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
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
    name = "Прилив сил WIP"
    description = (
        "3.10 HP < 25% -> Мгновенный выход из Оглушения и переброс инициативы.\n"
        "До конца раунда: +4 Силы, Стойкости, Спешки, Защиты.\n"
        "Далее до конца боя: +2 Спешки, Откаты -1."
    )
    is_active_ability = False

    # Логика "HP < 25%" должна проверяться в on_take_damage или on_round_start

#TODO 3.9 opc 3 10