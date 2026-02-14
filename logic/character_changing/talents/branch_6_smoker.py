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
    active_description = "Конвертация накопленного Дыма в усиления (Баффы на 3 раунда). CD 0"


    conversion_options = {
        "4 Дыма -> +1 Сила": {"label": "4 Smoke -> 1 Strength", "cost": 4, "stat": "attack_power_up", "amt": 1, "dur": 3},
        "3 Дыма -> +1 Скорость (Haste)": {"label": "3 Smoke -> 1 Haste", "cost": 3, "stat": "haste", "amt": 1, "dur": 3},
        "4 Дыма -> +1 Стойкость": {"label": "4 Smoke -> 1 Endurance", "cost": 4, "stat": "endurance", "amt": 1, "dur": 3},
        "3 Дыма -> +5 Самообладания": {"label": "3 Smoke -> 5 Self-Control", "cost": 3, "stat": "self_control", "amt": 5, "dur": 99},
        "3 Дыма -> +1 Защита": {"label": "3 Smoke -> 1 Protection", "cost": 3, "stat": "protection", "amt": 1, "dur": 3},
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
    name = "Дымовая завеса"
    description = (
        "«В одну секунду ты здесь, в следующую — всё вокруг тонет в серой мгле. Пусть они стреляют в тени, пока ты заходишь со спины.»\n\n"
        "Активно (4 сцены): Выпускает облако дыма, ослепляя врагов.\n"
        "Эффект: Накладывает 3 Дыма на всех врагов.\n"
        "Пассивно: +5 к Акробатике.\n"
        "Апгрейды (ветка Дыма):\n"
        "• С талантом 6.5 (Самосохранение/Очищение): Эффект +2 Дыма (Итого 5), Акробатика +2 (Итого 7).\n"
        "• С талантом 6.7 (Обработка легких/Нарния): Перезарядка снижена на 1 (2 сцены)."
    )
    is_active_ability = True
    active_description = "Накладывает 3 Дыма на врагов. CD 3. С 6.5 +2 дыма. С 6.7 CD 2"
    base_cooldown = 3

    def _has_upgrade_6_5(self, unit):
        """Проверка наличия талантов 6.5 для усиления эффекта."""
        return "self_preservation" in unit.talents or "cleansing" in unit.talents

    def _has_upgrade_6_7(self, unit):
        """Проверка наличия талантов 6.7 для снижения КД."""
        return "lung_processing" in unit.talents or "to_narnia" in unit.talents

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        # База +5, с апгрейдом +7
        bonus = 7 if self._has_upgrade_6_5(unit) else 5
        return {"acrobatics": bonus}

    def activate(self, unit, log_func, **kwargs):
        # 1. Проверка кулдауна
        if unit.cooldowns.get(self.id, 0) > 0:
            if log_func: log_func(f"❌ {self.name}: Способность перезаряжается.")
            return False

        # 2. Поиск врагов (автоматически или через аргументы)
        enemies = kwargs.get("enemies")
        if enemies is None:
            try:
                import streamlit as st
                if hasattr(st, 'session_state'):
                    l_team = st.session_state.get('team_left', [])
                    r_team = st.session_state.get('team_right', [])
                    if unit in l_team:
                        enemies = r_team
                    elif unit in r_team:
                        enemies = l_team
            except ImportError:
                pass

        if not enemies:
            if log_func: log_func(f"⚠️ {self.name}: Нет целей.")
            return False

        # 3. Эффект
        # База 3, с апгрейдом 5
        smoke_amt = 5 if self._has_upgrade_6_5(unit) else 3
        applied_count = 0

        for enemy in enemies:
            # Проверка на смерть
            is_dead = False
            if hasattr(enemy, 'is_dead'):
                is_dead = enemy.is_dead() if callable(enemy.is_dead) else enemy.is_dead

            if not is_dead:
                enemy.add_status("smoke", smoke_amt, duration=99)
                applied_count += 1

        # 4. Установка КД
        # База 4, с апгрейдом 3
        cooldown_val = self.base_cooldown
        if self._has_upgrade_6_7(unit):
            cooldown_val -= 1

        unit.cooldowns[self.id] = cooldown_val

        if log_func:
            log_func(f"💨 **{self.name}**: Дымовая завеса! {applied_count} врагов получили +{smoke_amt} Дыма.")

        logger.log(f"💨 Smoke Screen: Applied {smoke_amt} smoke to {applied_count} enemies", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 6.4 Переработка
# ==========================================
class TalentRecycling(BasePassive):
    id = "recycling"
    name = "Переработка"
    description = (
        "«Неиспользованные движения не исчезают. Они становятся частью завесы.»\n\n"
        "Пассивно: В конце раунда вы собираете остатки энергии.\n"
        "Эффект: За каждый неиспользованный Контр-кубик (Блок/Уклонение) вы получаете +1 Дым на следующий раунд."
    )
    is_active_ability = False

    def on_round_end(self, unit, log_func, **kwargs):
        """
        Конвертация оставшихся кубиков в дым.
        """
        # Считаем оставшиеся в слотах кубики (движок обычно очищает их ПОСЛЕ этого хука)
        if not hasattr(unit, 'counter_dice'):
            return

        unused_count = len(unit.counter_dice)

        if unused_count > 0:
            # Начисляем дым (duration=99, так как это постоянный ресурс до траты)
            unit.add_status("smoke", unused_count, duration=99)

            if log_func:
                log_func(f"♻️ **{self.name}**: Сохранено движений: {unused_count}. Превращены в +{unused_count} Дыма.")

            logger.log(f"♻️ Recycling: Converted {unused_count} unused dice to Smoke for {unit.name}", LogLevel.VERBOSE,
                       "Talent")

# ==========================================
# 6.5 Самосохранение
# ==========================================
class TalentSelfPreservation(BasePassive):
    id = "self_preservation"
    name = "Самосохранение"
    description = (
        "«Организм отвергает всё лишнее. Вместе с густым дымом из пор выходит яд, огонь и слабость.»\n\n"
        "Активно (КД: 2 сцены): Очищение организма.\n"
        "Стоимость: 2 Дыма.\n"
        "Эффект:\n"
        "• Снижает стаки всех DoT-эффектов (Ожог, Кровотечение, Яд, Гниение) на 5.\n"
        "• Снижает стаки всех Дебаффов (Хрупкость, Слабость, Связывание, Паралич) на 2.\n"
        "• Если был снят хоть один эффект: +1 Спешка (Haste)."
    )
    is_active_ability = True
    active_description = "2 Дыма за -5 к DoT-эффектам, -2 к дебаффам, +1 спешка при снятии"
    cooldown = 2

    # Списки того, что мы умеем чистить
    DOT_STATUSES = ["burn", "bleed", "poison", "rot", "decay"]
    DEBUFF_STATUSES = [
        "fragile", "weak", "vulnerable", "bind", "paralysis",
        "attack_power_down", "endurance_down"
    ]

    def activate(self, unit, log_func, **kwargs):
        # 1. Проверка КД
        if unit.cooldowns.get(self.id, 0) > 0:
            if log_func: log_func(f"❌ {self.name}: Способность перезаряжается.")
            return False

        # 2. Проверка стоимости
        cost = 2
        if unit.get_status("smoke") < cost:
            if log_func: log_func(f"❌ {self.name}: Нужно {cost} Дыма.")
            return False

        # 3. Списание ресурсов
        unit.remove_status("smoke", cost)
        unit.cooldowns[self.id] = self.cooldown

        # 4. Очистка
        cleansed_something = False
        details = []

        # Чистим DoT (снимаем по 5 стаков)
        for status_id in self.DOT_STATUSES:
            val = unit.get_status(status_id)
            if val > 0:
                remove_amt = 5
                unit.remove_status(status_id, remove_amt)
                details.append(f"-{min(val, remove_amt)} {status_id}")
                cleansed_something = True

        # Чистим Дебаффы (снимаем по 2 стака)
        for status_id in self.DEBUFF_STATUSES:
            val = unit.get_status(status_id)
            if val > 0:
                remove_amt = 2
                unit.remove_status(status_id, remove_amt)
                details.append(f"-{min(val, remove_amt)} {status_id}")
                cleansed_something = True

        # 5. Бонус за успех
        if cleansed_something:
            unit.add_status("haste", 1, duration=1)
            msg_tail = ", ".join(details)
            if log_func:
                log_func(f"🚑 **{self.name}**: Организм очищен ({msg_tail}). +1 Спешка.")
            logger.log(f"🚑 Self Preservation: Cleansed {details} from {unit.name}", LogLevel.NORMAL, "Talent")
        else:
            if log_func:
                log_func(f"🚑 **{self.name}**: Дым выпущен, но очищать было нечего.")

        return True


# ==========================================
# 6.5 (Опционально) Очищение
# ==========================================
class TalentCleansing(BasePassive):
    id = "cleansing"
    name = "Очищение"
    description = (
        "«Дым уносит с собой не только боль, но и усталость. Каждый выдох — это маленькое перерождение.»\n\n"
        "Пассивно: При любой потере зарядов Дыма (трата или рассеивание) вы восстанавливаетесь.\n"
        "За каждый 1 потерянный Дым:\n"
        "• +2% от Макс. HP\n"
        "• +2% от Макс. Stagger\n"
        "• +2 SP (Рассудок)"
    )
    is_active_ability = False

    def on_status_removed(self, unit, status_id, amount, **kwargs):
        """
        Срабатывает автоматически при вызове unit.remove_status().
        """
        # Проверяем, что это Дым
        if status_id != "smoke" or amount <= 0:
            return

        log_func = kwargs.get("log_func")

        # 1. Расчет (2% за стак)
        hp_per_stack = max(1, int(unit.max_hp * 0.02))
        stagger_per_stack = max(1, int(unit.max_stagger * 0.02))
        sp_per_stack = 2

        total_hp = hp_per_stack * amount
        total_stagger = stagger_per_stack * amount
        total_sp = sp_per_stack * amount

        # 2. Лечение
        # Передаем source=unit, чтобы обойти свои же блокировки (типа Клятвы Идола)
        real_hp = unit.heal_hp(total_hp, source=unit)

        # Stagger
        old_stg = unit.current_stagger
        unit.current_stagger = min(unit.max_stagger, unit.current_stagger + total_stagger)
        real_stg = unit.current_stagger - old_stg

        # SP
        real_sp = 0
        if hasattr(unit, "restore_sp"):
            real_sp = unit.restore_sp(total_sp)

        # 3. Лог (опционально, чтобы не спамить при -1 в конце хода можно добавить проверку amount > 1)
        # Но для наглядности оставим всегда
        logger.log(
            f"✨ Cleansing: +{real_hp} HP, +{real_stg} Stagger, +{real_sp} SP (Removed {amount} Smoke)",
            LogLevel.VERBOSE, "Talent"
        )


# ==========================================
# 6.6 Опытный курильщик
# ==========================================
class TalentExperiencedSmoker(BasePassive):
    id = "experienced_smoker"
    name = "Опытный курильщик"
    description = (
        "«Легкие чернее ночи, но крепче стали. Ты привык жить в тумане, и он стал твоей естественной средой.»\n\n"
        "Пассивно: Получаемый урон снижен на 20%.\n"
        "Начало боя:\n"
        "• Вы получаете +5 Дыма.\n"
        "• Максимальный лимит Дыма увеличен на +5 (Итого 15).\n"
        "Апгрейд (с талантом 6.10 'Дым и зеркала'):\n"
        "• Урон снижен на 25%.\n"
        "• Старт с +8 Дыма."
    )
    is_active_ability = False

    def _has_upgrade(self, unit):
        return "smoke_and_mirrors" in unit.talents

    def on_combat_start(self, unit, log_func, **kwargs):
        # 1. Стартовый дым
        amt = 8 if self._has_upgrade(unit) else 5
        unit.add_status("smoke", amt, duration=99)

        # 2. Увеличение лимита (записываем в память, SmokeStatus это прочитает)
        # Используем +=, чтобы стакалось с другими возможными бонусами
        current_bonus = unit.memory.get("smoke_limit_bonus", 0)
        unit.memory["smoke_limit_bonus"] = current_bonus + 5

        if log_func:
            log_func(f"🚬 **{self.name}**: Старт с {amt} Дыма. Лимит расширен (+5).")

        logger.log(f"🚬 Experienced Smoker: +{amt} Smoke, Limit +5 for {unit.name}", LogLevel.VERBOSE, "Talent")

    def modify_incoming_damage(self, unit, amount: int, damage_type, **kwargs) -> int:
        """Снижение входящего урона."""
        if amount <= 0: return amount

        # База 20%, с ультой 25%
        multiplier = 0.75 if self._has_upgrade(unit) else 0.80

        new_amount = int(amount * multiplier)

        if new_amount < amount:
            logger.log(
                f"🚬 Experienced Smoker: Reduced damage {amount} -> {new_amount} (x{multiplier})",
                LogLevel.VERBOSE, "Talent"
            )

        return new_amount


# ==========================================
# 6.7 Обработка лёгких
# ==========================================
class TalentLungProcessing(BasePassive):
    id = "lung_processing"
    name = "Обработка лёгких"
    description = (
        "«Обычный человек задохнулся бы. Ты же просто дышишь полной грудью. "
        "Твоя кровь насыщается не кислородом, а чем-то куда более горючим.»\n\n"
        "Пассивно: Максимальный лимит Дыма увеличен на +5 (Итого 20).\n"
        "Гипероксигенация: Пока на вас 15 или более зарядов Дыма:\n"
        "• Все ваши кубики получают +2 к Силе (Clash Power).\n"
        "• Наносимый урон увеличен на 30%."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        # Увеличиваем лимит дыма еще на 5
        current_bonus = unit.memory.get("smoke_limit_bonus", 0)
        unit.memory["smoke_limit_bonus"] = current_bonus + 5

        if log_func:
            log_func(f"🫁 **{self.name}**: Лёгкие расширены. Лимит Дыма +5.")

    def on_roll(self, ctx, **kwargs):
        """Бонус к силе при высоком уровне дыма."""
        # Проверяем стаки дыма у владельца
        smoke = ctx.source.get_status("smoke")
        if smoke >= 15:
            ctx.modify_power(2, "Lung Processing (15+ Smoke)")

    def modify_outgoing_damage(self, unit, amount, damage_type, **kwargs):
        """Бонус к урону при высоком уровне дыма."""
        smoke = unit.get_status("smoke")
        if smoke >= 15:
            # +30% урона
            new_amount = int(amount * 1.30)
            logger.log(
                f"🫁 Lung Processing: Boosted damage {amount} -> {new_amount} (+30%)",
                LogLevel.VERBOSE, "Talent"
            )
            return new_amount
        return amount


# ==========================================
# 6.7 (Опционально) В Нарнию и обратно
# ==========================================
class TalentToNarnia(BasePassive):
    id = "to_narnia"
    name = "В Нарнию и обратно WIP"
    description = (
        "«Они шагают в туман сильными и уверенными. Но там, внутри, время и пространство искажены.»\n\n"
        "Пассивно: Первое наложение Дыма на врага за бой вызывает шок.\n"
        "Эффект: Накладывает на цель:\n"
        "• 5 Понижения Силы атаки\n"
        "• 5 Понижения Стойкости\n"
        "• 5 Связывания (Bind, -Скорость)\n"
        "Длительность: 1 раунд."
    )
    is_active_ability = False

    def _apply_narnia_effect(self, unit, target):
        """
        Внутренняя логика проверки и наложения эффекта.
        unit: Владелец таланта (Смокер)
        target: Кому прилетел статус
        source: Кто наложил статус
        """
        # 1. Проверяем источник (должны быть МЫ)

        # 2. Проверяем цель (должен быть ВРАГ)
        # (unit != target уже проверено в source != unit, но is_enemy надежнее)
        # if not self.is_enemy(unit, target):
        #     return

        # 3. Проверяем память (только 1 раз за бой на этого врага)
        visited_enemies = unit.memory.get("narnia_victims", [])
        target_id = id(target) # Используем ID объекта для уникальности

        if target_id in visited_enemies:
            return

        # 4. НАКЛАДЫВАЕМ ДЕБАФФЫ
        # Важно: source=unit, чтобы сохранить цепочку ответственности
        debuff_dur = 19
        target.add_status("attack_power_down", 5, duration=debuff_dur, source=unit)
        target.add_status("endurance_down", 5, duration=debuff_dur, source=unit)
        target.add_status("bind", 5, duration=debuff_dur, source=unit)

        # 5. Запоминаем жертву
        visited_enemies.append(target_id)
        unit.memory["narnia_victims"] = visited_enemies

        # Лог
        logger.log(f"🚪 To Narnia: Triggered on {getattr(target, 'name', 'Enemy')}", LogLevel.NORMAL, "Talent")

    # --- ХУКИ ---

    def on_status_applied_global(self, unit, target, status_id, amount, **kwargs):
        """
        ГЛОБАЛЬНЫЙ ХУК: Срабатывает, когда КТО-ТО (target) получает статус.
        Мы (unit) наблюдаем за этим.
        """
        # Реагируем только на Дым
        if status_id == "smoke":
            self._apply_narnia_effect(unit, target)


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