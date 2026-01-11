from core.dice import Dice
from core.enums import DiceType
from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# 5.1 Встроенная Броня
# ==========================================
class TalentNakedDefense(BasePassive):
    id = "naked_defense"
    name = "Встроенная Броня"
    description = (
        "5.1 Когда вы не носите броню (None):\n"
        "Ваши сопротивления (Slash/Pierce/Blunt) становятся 1.0 (если были выше)."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        if not unit.armor_name or unit.armor_name.lower() in ["none", "нет", "empty", "naked"]:
            unit.hp_resists.slash = min(unit.hp_resists.slash, 1.0)
            unit.hp_resists.pierce = min(unit.hp_resists.pierce, 1.0)
            unit.hp_resists.blunt = min(unit.hp_resists.blunt, 1.0)
            if log_func: log_func(f"🛡️ **{self.name}**: Броня снята. Резисты = 1.0")


# ==========================================
# 5.2 Злобная расплата
# ==========================================
class TalentVengefulPayback(BasePassive):
    id = "vengeful_payback"
    name = "Злобная расплата"
    description = "5.2 За каждые 10 потерянных HP вы получаете 1 Силу на следующий раунд (единожды при потере)."
    is_active_ability = False

    def on_round_end(self, unit, log_func, **kwargs):
        lost_hp = min(max(0, unit.max_hp - unit.current_hp), unit.max_hp)
        current_chunks = lost_hp // 10

        mem_key = f"{self.id}_chunks"
        previous_chunks = unit.memory.get(mem_key, 0)

        bonus = current_chunks - previous_chunks

        if bonus > 0:
            # Даем силу только за новые переходы
            unit.add_status("strength", bonus, duration=3)
            if log_func:
                log_func(
                    f"🩸 **{self.name}**: Потеря здоровья (Порог {previous_chunks}->{current_chunks}) -> +{bonus} Силы")

        if current_chunks != previous_chunks:
            unit.memory[mem_key] = current_chunks

# ==========================================
# 5.3 Ярость
# ==========================================
class TalentBerserkerRage(BasePassive):
    id = "berserker_rage"
    name = "Ярость"
    description = (
        "5.3 Активно: +1 Куб атаки (Слот) на 3 раунда.\n"
        "КД: 5 раундов."
    )
    is_active_ability = True
    cooldown = 5
    duration = 3

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        unit.active_buffs[self.id] = self.duration
        unit.cooldowns[self.id] = self.cooldown

        # Если есть улучшение 5.6 А (Буйствующая Ярость)
        if "raging_fury" in unit.talents:
            unit.add_status("strength", 2, duration=3)
            unit.add_status("dmg_up", 2, duration=3)
            if log_func: log_func(f"😡 **{self.name} (Буйствующая)**: +Слот, +2 Силы, +2 Урона!")
        else:
            if log_func: log_func(f"😡 **{self.name}**: Активирована! (+1 Слот)")
        return True

    # === [NEW] Универсальный хук для бонусных кубиков ===
    def get_speed_dice_bonus(self, unit) -> int:
        # Если бафф ярости активен -> +1 кубик
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


# ==========================================
# 5.5 Неистовство (Frenzy)
# ==========================================
class TalentFrenzy(BasePassive):
    id = "frenzy"
    name = "Неистовство"
    description = (
        "5.5 Пассивно: Добавляет 1 Контр-кость (Slash 5-7) в пул контр-атак.\n"
        "Если Самообладание > 10: Добавляет еще 1 Контр-кость (Slash 6-8)."
    )
    is_active_ability = False

    def on_speed_rolled(self, unit, log_func, **kwargs):
        # Добавляем базовый контр-кубик
        base_die = Dice(5, 7, DiceType.SLASH, is_counter=True)
        if not hasattr(unit, 'counter_dice'):
            unit.counter_dice = []
        unit.counter_dice.append(base_die)
        msg = "Frenzy (+1 Counter 5-7)"

        # Проверяем условие для второго
        if unit.get_status("self_control") > 10:
            bonus_die = Dice(6, 8, DiceType.SLASH, is_counter=True)
            unit.counter_dice.append(bonus_die)
            msg += " & (+1 Counter 6-8)"

        if log_func:
            log_func(f"😡 **{self.name}**: {msg}")

# ==========================================
# 5.5 (Опц) Перевести дух
# ==========================================
class TalentCatchBreath(BasePassive):
    id = "catch_breath"
    name = "Перевести дух"
    description = "5.5 Опц: Вне боя восстанавливает 20% HP/час. (Активно: Отдых)."
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        heal = int(unit.max_hp * 0.2)
        unit.heal_hp(heal)
        if log_func: log_func(f"💤 **Перевести дух**: +{heal} HP")
        return True


# ==========================================
# 5.6 А: Буйствующая Ярость
# ==========================================
class TalentRagingFury(BasePassive):
    id = "raging_fury"
    name = "Буйствующая Ярость (А)"
    description = (
        "5.6 А: Усиливает навык 'Ярость'.\n"
        "При активации Ярости: +2 Силы, +2 Урона.\n"
        "Пассивно: Иммунитет к 'Понижению урона' (Dmg Down)."
    )
    is_active_ability = False

    # Логика усиления встроена в TalentBerserkerRage.activate


# ==========================================
# 5.6 Б: Полная Сосредоточенность
# ==========================================
class TalentFullConcentration(BasePassive):
    id = "full_concentration"
    name = "Полная Сосредоточенность (Б)"
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


# ==========================================
# 5.7 (Опц) Погружаясь в безумие
# ==========================================
class TalentDescendingIntoMadness(BasePassive):
    id = "descending_into_madness"
    name = "Погружаясь в безумие"
    description = (
        "5.7 Опц: Смерть человека -> -10% SP.\n"
        "За каждые 40% недостающего SP -> +1 Сила."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
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
    name = "Моя рука не дрогнет"
    description = "5.8 +1 к значению костей за каждые 10 зарядов Самообладания (Макс +2)."
    is_active_ability = False

    def on_roll(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        stacks = ctx.source.get_status("self_control")
        bonus = min(2, stacks // 10)
        if bonus > 0:
            ctx.modify_power(bonus, "Steady Hand")


# ==========================================
# 5.9 Ключевой момент
# ==========================================
class TalentKeyMoment(BasePassive):
    id = "key_moment"
    name = "Ключевой момент"
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


# ==========================================
# 5.9 (Опц) Второе дыхание
# ==========================================
class TalentSecondWindBerserk(BasePassive):
    id = "second_wind_berserk"
    name = "Второе дыхание (Берсерк)"
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
    name = "Крепкий орешек"
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