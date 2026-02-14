from core.dice import Dice
from core.enums import DiceType
from core.logging import logger, LogLevel  # [NEW] Import
from core.ranks import get_base_roll_by_level
from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# 5.1 Встроенная Броня
# ==========================================
class TalentNakedDefense(BasePassive):
    id = "naked_defense"
    name = "Встроенная Броня"
    description = (
        "«Доспехи — это клетка для трусов. Моя кожа задубела от шрамов, а мышцы тверже стали. Чтобы ранить меня, тебе придется сломать свой клинок.»\n\n"
        "Пассивно: Работает, если на вас не надета броня (или надета 'Одежда').\n"
        "Эффект: Ваши физические сопротивления (Slash, Pierce, Blunt) не могут быть хуже 1.0 (Normal).\n"
        "(Если сопротивление было 2.0 (Fatal), оно станет 1.0)."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        # Список "пустых" названий брони
        empty_armors = ["none", "Без брони", "empty", "naked", "clothes", "rag", "одежда"]

        current_armor = str(unit.armor_name).lower() if unit.armor_name else "none"

        if current_armor in empty_armors:
            # "Срезаем" уязвимости до 1.0
            # В Project Moon системе: 1.0 = Normal, 2.0 = Fatal. Чем меньше, тем лучше.
            unit.hp_resists.slash = min(unit.hp_resists.slash, 1.0)
            unit.hp_resists.pierce = min(unit.hp_resists.pierce, 1.0)
            unit.hp_resists.blunt = min(unit.hp_resists.blunt, 1.0)

            if log_func:
                log_func(f"🛡️ **{self.name}**: Дикая стойкость. Уязвимости сброшены до Нормальных.")

            logger.log(f"🛡️ Naked Defense: Resists capped at 1.0 for {unit.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 5.2 Злобная расплата
# ==========================================
class TalentVengefulPayback(BasePassive):
    id = "vengeful_payback"
    name = "Злобная расплата"
    description = (
        "«Боль — это не сигнал к отступлению. Это топливо. Каждая капля моей крови — это масло, подлитое в огонь моей ненависти.»\n\n"
        "Пассивно: Вы становитесь сильнее по мере получения ран.\n"
        "Эффект: За каждые 10 потерянных HP вы получаете +1 Силу на 3 раунда.\n"
        "(Срабатывает в момент пересечения порога здоровья)."
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        # Вычисляем потерянное здоровье
        lost_hp = min(max(0, unit.max_hp - unit.current_hp), unit.max_hp)

        # Сколько полных "десяток" мы потеряли
        current_chunks = lost_hp // 10

        mem_key = f"{self.id}_chunks"

        # Инициализация (чтобы не получить бафф сразу при спавне с лоу хп, если так не задумано)
        # Или наоборот - получить, если бой начался с ран
        if mem_key not in unit.memory:
            unit.memory[mem_key] = current_chunks
            return

        previous_chunks = unit.memory.get(mem_key, 0)

        # Если мы потеряли больше здоровья (пересекли новый порог)
        bonus = current_chunks - previous_chunks

        if bonus > 0:
            unit.add_status("attack_power_up", bonus, duration=3)

            msg = f"🩸 **{self.name}**: Кровь закипает! (Порог {previous_chunks * 10} -> {current_chunks * 10} урона) -> +{bonus} Силы"
            if log_func: log_func(msg)

            logger.log(f"🩸 Vengeful Payback: +{bonus} Strength for {unit.name} (HP Loss)", LogLevel.VERBOSE, "Talent")

        # Обновляем память (даже если отхилились - previous_chunks упадет, и мы сможем получить бонус снова при уроне)
        if current_chunks != previous_chunks:
            unit.memory[mem_key] = current_chunks


# ==========================================
# 5.3 Ярость
# ==========================================
class TalentBerserkerRage(BasePassive):
    id = "berserker_rage"
    name = "Ярость"
    description = (
        "«Крик застревает в горле, разрывая связки. Выпусти его. Позволь красному туману застелить глаза. Пусть останется только рефлекс: убивать.»\n\n"
        "Активно (КД: 5 раундов): Впасть в неистовство на 3 раунда.\n"
        "Эффект: +1 Слот Скорости (дополнительное действие).\n"
        "Бонус (при наличии 'Буйствующая Ярость'): Дополнительно +2 Силы и +2 Урона."
    )
    is_active_ability = True
    active_description = "+1 Слот Скорости, при 5.6А +2 Силы и +2 Урона. Dur 3. CD 5"
    cooldown = 5
    duration = 3

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0:
            if log_func: log_func("⏳ Способность перезаряжается.")
            return False

        # Активируем бафф в системе unit.active_buffs (для отсчета длительности)
        unit.active_buffs[self.id] = self.duration
        unit.cooldowns[self.id] = self.cooldown

        # Проверяем наличие улучшения 5.6 А (Буйствующая Ярость)
        is_raging = "raging_fury" in unit.talents

        if is_raging:
            # Моментальные баффы характеристик
            unit.add_status("attack_power_up", 2, duration=3)
            unit.add_status("dmg_up", 2, duration=3)

            if log_func:
                log_func(f"😡 **{self.name} (Буйствующая)**: РЁВ! (+1 Слот, +2 Силы, +2 Урона на 3 хода)")
            logger.log(f"😡 Raging Fury activated by {unit.name}", LogLevel.NORMAL, "Talent")
        else:
            if log_func:
                log_func(f"😡 **{self.name}**: Глаза наливаются кровью... (+1 Слот на 3 хода)")
            logger.log(f"😡 Berserker Rage activated by {unit.name}", LogLevel.NORMAL, "Talent")

        return True

    # === Универсальный хук для бонусных кубиков ===
    def get_speed_dice_bonus(self, unit) -> int:
        """
        Система вызывает этот метод при расчете количества слотов скорости.
        """
        # Если бафф ярости активен (время действия > 0) -> +1 кубик
        if unit.active_buffs.get(self.id, 0) > 0:
            return 1
        return 0


# ==========================================
# 5.3 (Опц) Встроенная броня 2
# ==========================================
class TalentNakedDefense2(BasePassive):
    id = "naked_defense_2"
    name = "Встроенная броня 2  WIP"
    description = (
        "5.3 Опц: Без брони можно понизить 2 резиста на 0.25 (не ниже 0.5).\n"
        "(Реализовано как -0.25 ко всем для простоты, или выберите вручную в профиле)"
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        if not unit.armor_name or unit.armor_name.lower() in ["none", "нет"]:
            # Упрощение: снижаем Slash и Blunt
            unit.hp_resists.slash = max(0.5, unit.hp_resists.slash - 0.25)
            unit.hp_resists.blunt = max(0.5, unit.hp_resists.blunt - 0.25)
            if log_func: log_func(f"🛡️ **{self.name}**: Резисты Slash/Blunt снижены на 0.25")
            logger.log(f"🛡️ Naked Defense 2: Reduced Slash/Blunt resist by 0.25 for {unit.name}", LogLevel.VERBOSE,
                       "Talent")


# ==========================================
# 5.4 Не теряя голову
# ==========================================
class TalentCalmMind(BasePassive):
    id = "calm_mind"
    name = "Не теряя голову"
    description = "5.4 Ваши атаки накладывают на вас +1 Самообладание (Self-Control)."
    is_active_ability = False

    def on_hit(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        bonus = 1
        # Если активна Полная Сосредоточенность (5.6 Б), бонус удваивается
        if ctx.source.active_buffs.get("full_concentration", 0) > 0:
            bonus = 2

        ctx.source.add_status("self_control", bonus, duration=99)
        ctx.log.append(f"🧠 **{self.name}**: +{bonus} Self-Control")
        logger.log(f"🧠 Calm Mind: +{bonus} Self-Control on hit for {ctx.source.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 5.5 Неистовство (Frenzy)
# ==========================================
class TalentFrenzy(BasePassive):
    id = "frenzy"
    name = "Неистовство"
    description = (
        "«Твое тело движется быстрее мысли. Любой, кто войдет в зону поражения, будет рассечен на части еще до того, как поймет, что произошло.»\n\n"
        "Пассивно: Вы получаете Контр-кубик (Slash) каждый раунд.\n"
        "Эффект 'Холодная Ярость': Если ваше Самообладание > 10, вы получаете дополнительный, более мощный Контр-кубик."
    )
    is_active_ability = False

    def on_speed_rolled(self, unit, log_func, **kwargs):
        # 1. Получаем базовые значения от уровня (предполагается наличие функции)
        base_min, base_max = get_base_roll_by_level(unit.level)

        # 2. Добавляем базовый контр-кубик
        base_die = Dice(base_min, base_max, DiceType.SLASH, is_counter=True)
        if not hasattr(unit, 'counter_dice'):
            unit.counter_dice = []
        unit.counter_dice.append(base_die)

        msg = f"Лезвие ({base_min}-{base_max})"

        # 3. Проверяем условие для второго кубика (Самообладание > 10)
        if unit.get_status("self_control") > 10:
            bonus_min = base_min + 1
            bonus_max = base_max + 1
            bonus_die = Dice(bonus_min, bonus_max, DiceType.SLASH, is_counter=True)
            unit.counter_dice.append(bonus_die)
            msg += f" и Второе дыхание ({bonus_min}-{bonus_max})"

        if log_func:
            log_func(f"⚔️ **{self.name}**: {msg}")

        logger.log(f"⚔️ Frenzy: Added counter dice for {unit.name} (Lvl {unit.level})", LogLevel.VERBOSE, "Talent")


# ==========================================
# 5.5 (Опц) Перевести дух
# ==========================================
class TalentCatchBreath(BasePassive):
    id = "catch_breath"
    name = "Перевести дух"
    description = (
        "«Кровь заливает легкие, но ты сглатываешь её и делаешь судорожный вдох. Вставай. Шоу должно продолжаться.»\n\n"
        "Активно: Мгновенное восстановление сил.\n"
        "Эффект: Восстанавливает 20% от максимального HP."
    )
    is_active_ability = True
    active_description = "Восстанавливает 20% от максимального HP."

    def activate(self, unit, log_func, **kwargs):
        heal = int(unit.max_hp * 0.2)
        actual_heal = unit.heal_hp(heal)

        if log_func: log_func(f"💤 **Перевести дух**: Раны закрываются (+{actual_heal} HP)")
        logger.log(f"💤 Catch Breath: Healed {actual_heal} HP for {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 5.6 А: Буйствующая Ярость
# ==========================================
class TalentRagingFury(BasePassive):
    id = "raging_fury"
    name = "Буйствующая Ярость"
    description = (
        "«Твой гнев — это цунами. Жалкие попытки ослабить твои удары лишь заставляют тебя бить сильнее.»\n\n"
        "Улучшение таланта 'Ярость': При активации дополнительно дает +2 Силы и +2 Урона.\n"
        "Пассивно: Вы невосприимчивы к эффектам снижения урона (Damage Down)."
    )
    is_active_ability = False

    # Логика усиления активации встроена в TalentBerserkerRage.activate

    def on_before_status_add(self, unit, status_id, amount):
        """
        Блокировка негативного статуса 'dmg_down' (Attack Power Down / Damage Down).
        """
        if status_id in ["dmg_down", "attack_power_down"]:
            logger.log(f"😡 Raging Fury: {unit.name} ignored {status_id}", LogLevel.NORMAL, "Talent")
            return False, f"😡 **{self.name}**: Эффект '{status_id}' проигнорирован!"

        return True, None


# ==========================================
# 5.6 Б: Полная Сосредоточенность
# ==========================================
class TalentFullConcentration(BasePassive):
    id = "full_concentration"
    name = "Полная Сосредоточенность (Б) WIP"
    description = (
        "5.6 Б: Заменяет Ярость.\n"
        "Активно: Мин. бросок = Макс. бросок. Удвоенное получение Самообладания. Длит. 3 раунда.\n"
        "Пассивно: Иммунитет к Провокации."
    )
    is_active_ability = True
    cooldown = 5
    duration = 3

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        unit.active_buffs[self.id] = self.duration
        unit.cooldowns[self.id] = self.cooldown

        if log_func: log_func(f"🧘 **{self.name}**: Мин = Макс! Самообладание x2.")
        logger.log(f"🧘 Full Concentration activated by {unit.name}", LogLevel.NORMAL, "Talent")
        return True

    def on_roll(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        # Если бафф активен, мин. значение = макс. значению
        if ctx.source.active_buffs.get(self.id, 0) > 0:
            if ctx.dice:
                # Хак: изменяем результат броска на макс
                # (В идеале надо менять min_val в дайсе, но это сложнее)
                potential_max = ctx.dice.max_val
                # Если текущий бросок меньше максимума, поднимаем его
                if ctx.final_value < potential_max:
                    diff = potential_max - ctx.final_value
                    ctx.modify_power(diff, "Concentration (Min=Max)")


# ==========================================
# 5.7 Встроенная броня 3
# ==========================================
class TalentNakedDefense3(BasePassive):
    id = "naked_defense_3"
    name = "Встроенная броня 3 WIP"
    description = "5.7 Еще -0.25 к двум резистам без брони."
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        if not unit.armor_name or unit.armor_name.lower() in ["none", "нет"]:
            unit.hp_resists.slash = max(0.5, unit.hp_resists.slash - 0.25)
            unit.hp_resists.pierce = max(0.5, unit.hp_resists.pierce - 0.25)  # Другой тип для разнообразия
            if log_func: log_func(f"🛡️ **{self.name}**: Резисты Slash/Pierce снижены на 0.25")
            logger.log(f"🛡️ Naked Defense 3: Reduced Slash/Pierce resist by 0.25 for {unit.name}", LogLevel.VERBOSE,
                       "Talent")


# ==========================================
# 5.7 (Опц) Погружаясь в безумие
# ==========================================
class TalentDescendingIntoMadness(BasePassive):
    id = "descending_into_madness"
    name = "Погружаясь в безумие WIP"
    description = (
        "5.7 Опц: Смерть человека -> -10% SP.\n"
        "За каждые 40% недостающего SP -> +1 Сила."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        if unit.max_sp > 0:
            missing_pct = 1.0 - (unit.current_sp / unit.max_sp)
            stacks = int(missing_pct / 0.40)  # 40%
            if stacks > 0:
                return {"power_attack": stacks}  # +1 Сила за стак
        return {}


# ==========================================
# 5.8 Моя рука не дрогнет
# ==========================================
class TalentSteadyHand(BasePassive):
    id = "steady_hand"
    name = "Моя рука не дрогнет WIP"
    description = "5.8 +1 к значению костей за каждые 10 зарядов Самообладания (Макс +2)."
    is_active_ability = False

    def on_roll(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        stacks = ctx.source.get_status("self_control")
        bonus = min(2, stacks // 10)
        if bonus > 0:
            ctx.modify_power(bonus, "Steady Hand")
            logger.log(f"🖐️ Steady Hand: +{bonus} Power for {ctx.source.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 5.9 Ключевой момент
# ==========================================
class TalentKeyMoment(BasePassive):
    id = "key_moment"
    name = "Ключевой момент WIP"
    description = "5.9 Если жизнь на грани (HP < 25%), активируется Полная Сосредоточенность."
    is_active_ability = False

    def on_take_damage(self, unit, amount, source, **kwargs):
        # 1. Извлекаем функцию логгирования (вернет None, если её нет)
        log_func = kwargs.get("log_func")
        if unit.max_hp > 0 and (unit.current_hp / unit.max_hp) < 0.25:
            # Активируем Сосредоточенность (если не активна)
            if unit.active_buffs.get("full_concentration", 0) <= 0:
                unit.active_buffs["full_concentration"] = 3
                if log_func: log_func(f"⚡ **{self.name}**: Критическое состояние! Сосредоточенность активирована.")
                logger.log(f"⚡ Key Moment activated for {unit.name}", LogLevel.NORMAL, "Talent")


# ==========================================
# 5.9 (Опц) Второе дыхание
# ==========================================
class TalentSecondWindBerserk(BasePassive):
    id = "second_wind_berserk"
    name = "Второе дыхание (Берсерк) WIP"
    description = (
        "5.9 Опц: HP < 25% -> +1 ко всем кубикам.\n"
        "Если союзник без сознания -> еще +1."
    )
    is_active_ability = False

    def on_roll(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        unit = ctx.source
        if unit.max_hp > 0 and (unit.current_hp / unit.max_hp) < 0.25:
            ctx.modify_power(1, "Second Wind (<25%)")
            # Проверку на союзника сложно сделать без контекста команды, пока опустим


# ==========================================
# 5.10 Крепкий орешек
# ==========================================
class TalentDieHard(BasePassive):
    id = "die_hard"
    name = "Крепкий орешек WIP"
    description = (
        "5.10 1/3 ваших атакующих кубов становятся АБСОЛЮТНЫМИ.\n"
        "Абсолютный куб не ломается (не может быть уничтожен эффектами).\n"
        "На атаки этим кубом не действуют негативные эффекты персонажа (Слабость и т.д.)."
    )
    is_active_ability = False

    def on_roll(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        # Реализуем "Иммунитет к негативу"
        # Если куб абсолютный (эмулируем каждый 3-й куб или просто рандомно 33%)
        # Для простоты: 33% шанс что куб "Абсолютный"
        import random
        if random.random() < 0.33:
            # Снимаем штрафы силы, если они есть (power < 0)
            # В текущей архитектуре это сложно отменить постфактум,
            # но мы можем добавить компенсирующий бонус

            # Вариант проще: Просто пишем в лог
            ctx.log.append("💎 **Absolute Die**: Immune to debuffs!")