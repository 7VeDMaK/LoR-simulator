from core.logging import logger, LogLevel  # [NEW] Import
from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# 10.1 А: Электрик
# ==========================================
class TalentElectrician(BasePassive):
    id = "electrician"
    name = "Электрик (А)"
    description = (
        "10.1 А: Инженерия +3.\n"
        "Вы можете создавать базовое электрическое оружие."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {"engineering": 3}


# ==========================================
# 10.1 Б: Игра по болевым точкам
# ==========================================
class TalentPainPoints(BasePassive):
    id = "pain_points"
    name = "Игра по болевым точкам (Б)"
    description = "10.1 Б: Сила удара (навык) +3."
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {"power_attack": 3}


# ==========================================
# 10.2 А: Механическая энергия
# ==========================================
class TalentMechanicalEnergy(BasePassive):
    id = "mechanical_energy"
    name = "Механическая энергия (А)"
    description = "10.2 А: Атаки, дающие Заряд, дают дополнительно +1 Заряд."
    is_active_ability = False


# ==========================================
# 10.2 Б: Болевой шок
# ==========================================
class TalentPainShock(BasePassive):
    id = "pain_shock"
    name = "Болевой шок (Б)"
    description = "10.2 Б: Каждый атакующий кубик, накладывающий Разрыв, добавляет +1 Разрыв (длительность 99)."
    is_active_ability = False

    def on_hit(self, ctx, **kwargs):
        if ctx.target and ctx.target.get_status("rupture") > 0:
            ctx.target.add_status("rupture", 1, duration=99)
            if ctx.log: ctx.log.append("⚡ **10.2 Б (Болевой шок)**: +1 Разрыв (длительность 99)!")
            logger.log(f"⚡ Pain Shock: Added +1 rupture to {ctx.target.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 10.3 А: Аварийная защита
# ==========================================
class TalentEmergencyProtection(BasePassive):
    id = "emergency_protection"
    name = "Аварийная защита (А)"
    description = (
        "10.3 А: Активно: Конвертировать весь Заряд в Барьер (1 Заряд = 5 Барьера).\n"
        "Барьер имеет ваши резисты и работает как доп. здоровье на 1 раунд."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        charge = unit.get_status("charge")
        if charge <= 0: return False

        barrier_amt = charge * 5
        unit.remove_status("charge", charge)
        unit.add_status("barrier", barrier_amt, duration=1)

        if log_func: log_func(f"🛡️ **{self.name}**: {charge} Заряда -> {barrier_amt} Барьера.")

        logger.log(f"🛡️ Emergency Protection: Converted {charge} Charge to {barrier_amt} Barrier for {unit.name}",
                   LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 10.3 А (Опц): Статическое электричество
# ==========================================
class TalentStaticElectricity(BasePassive):
    id = "static_electricity"
    name = "Статическое электричество"
    description = (
        "10.3 А (Опц): Раненый вами враг получает урон электричеством (Ваш Заряд / 5) в конце раунда."
    )
    is_active_ability = False


# ==========================================
# 10.3 Б: Входя в Ритм
# ==========================================
class TalentEnteringRhythm(BasePassive):
    id = "entering_rhythm"
    name = "Входя в Ритм (Б)"
    description = (
        "10.3 Б: Победа в столкновении всеми костями страницы -> +1 Ритм.\n"
        "Ритм: Каждые 2 эффекта Ритма прибавляют +1 Урон наносимым атакам."
    )
    is_active_ability = False

    def on_clash_win(self, ctx, **kwargs):
        # Получаем текущее значение Ритма
        current_rhythm = ctx.source.get_status("rhythm")
        
        # Полностью сбрасываем текущий статус
        if current_rhythm > 0:
            ctx.source.remove_status("rhythm", current_rhythm)
        
        # Добавляем новое значение: старое + 1, с длительностью 99
        new_rhythm_value = current_rhythm + 1
        ctx.source.add_status("rhythm", new_rhythm_value, duration=99)
        
        # Логирование срабатывания таланта
        logger.log(f"🎵 {self.name} activated for {ctx.source.name}!", LogLevel.NORMAL, "Talent")
        
        if ctx.log: 
            if current_rhythm > 0:
                ctx.log.append(f"🎵 **{self.name}**: Ритм обновлен ({current_rhythm} -> {new_rhythm_value})!")
            else:
                ctx.log.append(f"🎵 **{self.name}**: +1 Ритм!")
        
        logger.log(f"🎵 {self.name}: Rhythm updated to {new_rhythm_value} for {ctx.source.name}", LogLevel.VERBOSE, "Talent")

    def modify_outgoing_damage(self, unit, amount, damage_type, stack=0, log_list=None):
        # Получаем текущее количество Ритма 
        rhythm_stack = unit.get_status("rhythm")
        if rhythm_stack > 0:
            bonus_dmg = rhythm_stack // 2
            if bonus_dmg > 0:
                if log_list is not None:
                    log_list.append(f"🎵 Ритм (+{bonus_dmg})")
                return amount + bonus_dmg
        return amount



# ========================================== ПОМЕНЯТЬ ВСЕ ОН ТЕЙК ДМАГЕ
# 10.3 Б (Опц): Грязные приёмы
# ==========================================
class TalentDirtyTricks(BasePassive):
    id = "dirty_tricks"
    name = "Грязные приёмы"
    description = "10.3 Б (Опц): Победа в столкновении -> Цель получает +1 Понижение урона (Dmg Down, длительность 2)."
    is_active_ability = False

    def on_clash_win(self, ctx, **kwargs):
        # Применяем эффект на цель (врага)
        if ctx.target:
            ctx.target.add_status("dmg_down", 1, duration=2)
            
            # Логирование срабатывания таланта
            logger.log(f"💢 {self.name} activated for {ctx.source.name}!", LogLevel.NORMAL, "Talent")
            
            if ctx.log:
                ctx.log.append(f"💢 **{self.name}**: {ctx.target.name} получил Понижение урона!")
            
            logger.log(f"💢 {self.name}: Applied Dmg Down to {ctx.target.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 10.4: Играя на нервах (Общий)
# ==========================================
class TalentPlayingOnNerves(BasePassive):
    id = "playing_on_nerves"
    name = "Играя на нервах"
    description = "10.4 Пассивно: Каждая 3-я кость накладывает 5 Разрыва и +1 Количество."
    is_active_ability = False

    def on_hit(self, ctx, **kwargs):
        # Инициализируем счетчик если его нет
        if not hasattr(ctx.source, '_nerve_counter'):
            ctx.source._nerve_counter = 0
        
        # Увеличиваем счетчик
        ctx.source._nerve_counter += 1
        
        # Проверяем каждый третий кубик
        if ctx.source._nerve_counter % 3 == 0:
            if ctx.target:
                # Накладываем 5 Разрыва
                ctx.target.add_status("rupture", 5, duration=3)
                
                # Логирование срабатывания таланта
                logger.log(f"🎭 {self.name} activated for {ctx.source.name}!", LogLevel.NORMAL, "Talent")
                
                if ctx.log:
                    ctx.log.append(f"🎭 **{self.name}**: +5 Разрыва на {ctx.target.name}!")
                
                logger.log(f"🎭 {self.name}: Applied 5 Rupture to {ctx.target.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 10.5 А: Перенапряжение
# ==========================================
class TalentOvervoltage(BasePassive):
    id = "overvoltage"
    name = "Перенапряжение (А)"
    description = "10.5 А: Мощная атака, расходующая Заряд для усиления."
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        if log_func: log_func("⚡ **Перенапряжение**: Атака заряжена (Заглушка).")
        logger.log(f"⚡ Overvoltage activated for {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 10.5 А (Опц): Электро-магнитное поле
# ==========================================
class TalentEMField(BasePassive):
    id = "em_field"
    name = "Электро-магнитное поле"
    description = "10.5 А (Опц): При получении Заряда -> Даете 1/2 от полученного случайному союзнику."
    is_active_ability = False


# ==========================================
# 10.5 Б: С осторожностью
# ==========================================
class TalentWithCaution(BasePassive):
    id = "with_caution"
    name = "С осторожностью (Б)"
    description = (
        "10.5 Б: Проигрыш столкновения -> Получаете Protection 1 на 2 хода."
    )
    is_active_ability = False

    def on_clash_lose(self, ctx, **kwargs):
        # При проигрыше в столкновении
        ctx.source.add_status("protection", 1, duration=2)
        
        # Логирование срабатывания таланта
        logger.log(f"🛡️ {self.name} activated for {ctx.source.name}!", LogLevel.NORMAL, "Talent")
        
        if ctx.log:
            ctx.log.append(f"🛡️ **{self.name}**: +1 Защиты (2 хода)!")
        
        logger.log(f"🛡️ {self.name}: Applied 1 Protection to {ctx.source.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 10.5 Б (Опц): Меткий глаз
# ==========================================
class TalentSharpEye(BasePassive):
    id = "sharp_eye"
    name = "Меткий глаз"
    description = (
        "10.5 Б (Опц): Огнестрел: При проигрыше понижает мин/макс бросок врага на 1/2 от вашего броска."
    )
    is_active_ability = False

    def on_clash_lose(self, ctx, **kwargs):
        # Проверяем, использует ли персонаж дальнюю карту атаки
        if ctx.source and ctx.target and ctx.source.current_card:
            card = ctx.source.current_card
            
            # Проверяем, является ли карта дальней/огнестрельной
            is_ranged = True
            
            # Проверяем только свойства карты
            if hasattr(card, 'card_range'):
                is_ranged = card.card_range == 'ranged'
            elif hasattr(card, 'range'):
                is_ranged = card.range == 'ranged'
            
            # Если дальняя атака и есть значение броска
            if is_ranged and hasattr(ctx, 'final_value'):
                my_roll = ctx.final_value
                damage = my_roll // 2  # Половина от броска
                
                if damage > 0:
                    # Наносим урон даже при проигрыше (прямое вычитание HP)
                    if ctx.target:
                        ctx.target.current_hp = max(0, ctx.target.current_hp - damage)
                    
                    # Логирование срабатывания таланта
                    logger.log(f"🎯 {self.name} activated for {ctx.source.name}!", LogLevel.NORMAL, "Talent")
                    
                    if ctx.log:
                        ctx.log.append(f"🎯 **{self.name}**: Нанесено {damage} урона (половина от {my_roll})!")
                    
                    logger.log(f"🎯 {self.name}: Dealt {damage} damage to {ctx.target.name} despite losing", LogLevel.VERBOSE, "Talent")


# ==========================================
# 10.6 А: Командный игрок
# ==========================================
class TalentTeamPlayer(BasePassive):
    id = "team_player"
    name = "Командный игрок (А)"
    description = "10.6 А: Ваши союзники получают пассивное умение 'Аварийная защита' (10.3)."
    is_active_ability = False


# ==========================================
# 10.6 Б: Арест
# ==========================================
class TalentArrest(BasePassive):
    id = "arrest"
    name = "Арест (Б)"
    description = (
        "10.6 Б: Надеть наручники целевому союзнику.\n"
        "Наручники: -20 ко всем атрибутам, спас-броски с помехой."
    )
    is_active_ability = True  # Активное действие "Надеть"

    def _get_battle_targets(self):
        """Возвращает всех участников боя (левая + правая команды), если симулятор запущен."""
        try:
            from ui.simulator.logic.simulator_logic import get_teams  # type: ignore
            l_team, r_team = get_teams()
            return (l_team or []) + (r_team or [])
        except Exception:
            return []

    @property
    def conversion_options(self):
        """Строим список всех доступных целей (любой юнит в текущем бою)."""
        options = {}
        for u in self._get_battle_targets():
            if not u or not hasattr(u, "name"):  # safety
                continue
            suffix = ""
            if u.get_status("arrested") > 0:
                suffix = " [уже в наручниках]"
            options[u.name] = f"{u.name}{suffix}"
        return options

    def activate(self, unit, log_func, choice_key=None, **kwargs):
        # Если цель не выбрана, просим выбрать через меню
        if not choice_key:
            if log_func:
                opts = ", ".join(self.conversion_options.values()) or "нет доступных целей"
                log_func(f"⚠️ Выберите цель для {self.name}: {opts}")
            return False

        target = None
        for u in self._get_battle_targets():
            if u and getattr(u, "name", None) == choice_key:
                target = u
                break

        if not target:
            if log_func:
                log_func(f"⚠️ Цель не найдена: {choice_key}")
            return False

        # Нельзя выбрать самого себя
        if target is unit:
            if log_func:
                log_func("⚠️ Нельзя выбрать самого себя")
            return False

        # Тоггл: если уже в наручниках — снимаем
        if target.get_status("arrested") > 0:
            target.remove_status("arrested", target.get_status("arrested"))
            if log_func:
                log_func(f"⛓️ **{self.name}**: Наручники сняты с {target.name}.")
            logger.log(f"⛓️ {self.name}: Removed arrested from {target.name}", LogLevel.NORMAL, "Talent")
            return True

        # Накладываем статус наручников
        target.add_status("arrested", 1, duration=99)

        logger.log(f"⛓️ {self.name} activated for {target.name}!", LogLevel.NORMAL, "Talent")
        if log_func:
            log_func(f"⛓️ **{self.name}**: Наручники надеты на {target.name}! (-20 к атрибутам, длит. 99)")
        logger.log(f"⛓️ {self.name}: Applied arrested status to {target.name}", LogLevel.VERBOSE, "Talent")
        return True


# ==========================================
# 10.7 А: Батарейка
# ==========================================
class TalentBattery(BasePassive):
    id = "battery"
    name = "Батарейка (А)"
    description = (
        "10.7 А: Рецепт Тяжелой брони (хранит 30 Заряда).\n"
        "Трата Заряда -> Накладывает 1 Разрыв атаками."
    )
    is_active_ability = False


# ==========================================
# 10.7 А (Опц): Заземление
# ==========================================
class TalentGrounding(BasePassive):
    id = "grounding"
    name = "Заземление"
    description = (
        "10.7 А (Опц): Активно (20 Заряда): Сбросить негативные эффекты.\n"
        "+2 Спешка, +2 Сила до конца раунда. КД: 8."
    )
    is_active_ability = True
    cooldown = 8

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False
        charge = unit.get_status("charge")
        if charge < 20: return False

        # Логика
        unit.remove_status("charge",
                           20)  # Тратит или просто требует наличие? "Если вы имеете... вы можете". Пусть тратит для баланса?
        # Текст: "Если имеете... можете сбросить". Обычно такие мощные эффекты тратят ресурс.

        unit.add_status("haste", 2, duration=1)
        unit.add_status("strength", 2, duration=1)
        # Очистка дебаффов (заглушка)

        unit.cooldowns[self.id] = self.cooldown
        if log_func: log_func(f"⚡ **Заземление**: Дебаффы сняты, +Stats!")

        logger.log(f"⚡ Grounding activated for {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 10.7 Б: Финт
# ==========================================
class TalentFeint(BasePassive):
    id = "feint"
    name = "Финт (Б)"
    description = "10.7 Б: Каждая 3-я кость понижает значение кости врага на 2."
    is_active_ability = False

    def on_roll(self, ctx, **kwargs):
        # Отслеживаем, сколько костей бросил юнит, и каждая 3-я усиливает бросок
        if not hasattr(ctx.source, "_feint_counter"):
            ctx.source._feint_counter = 0

        ctx.source._feint_counter += 1

        if ctx.source._feint_counter % 3 == 0:
            # Эквивалент понижения вражеской кости на 2: добавляем себе +2 к силе броска
            ctx.modify_power(2, "Финт")
            if ctx.log is not None:
                ctx.log.append(f"🎭 **{self.name}**: -2 к кости врага (эффект учтён)")
            logger.log(f"🎭 Feint: +2 power applied for {ctx.source.name} on 3rd die", LogLevel.NORMAL, "Talent")


# ==========================================
# 10.7 Б (Опц): Уязвимая точка
# ==========================================
class TalentWeakPointEnergy(BasePassive):
    id = "weak_point_energy"
    name = "Уязвимая точка (Б)"
    description = "10.7 Б (Опц): Атаки накладывают Уязвимость (+25% урона) на след. раунд."
    is_active_ability = False

    def on_hit(self, ctx, **kwargs):
        if ctx.target:
            ctx.target.add_status("weak", 1, duration=2)
            
            logger.log(f"💔 {self.name} activated for {ctx.source.name}!", LogLevel.NORMAL, "Talent")
            
            if ctx.log:
                ctx.log.append(f"💔 **{self.name}**: {ctx.target.name} получит Слабость в следующем раунде (+25% урона)!")
            
            logger.log(f"💔 {self.name}: Applied weak status to {ctx.target.name} for next round", LogLevel.VERBOSE, "Talent")


# ==========================================
# 10.8: (Мастер Разрыва)
# ==========================================
class TalentRuptureApplication(BasePassive):
    id = "rupture_application"
    name = "Мастер Разрыва"
    description = "10.8 Пассивно: Попадание по врагу без Разрыва -> Накладывает 10 Разрыв"
    is_active_ability = False

    def on_hit(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        if ctx.target and ctx.target.get_status("rupture") <= 0:
            # Накладываем статус (заглушка, так как rupture имеет стаки и каунт)
            # В движке rupture - это int. Эмуляция Count сложнее.
            ctx.target.add_status("rupture", 10, duration=99)
            if ctx.log: ctx.log.append("🩸 **10.8**: Наложен начальный Разрыв.")
            logger.log(f"🩸 Rupture Application: Applied initial rupture to {ctx.target.name}", LogLevel.VERBOSE,
                       "Talent")


# ==========================================
# 10.9 А: Разрывая пространство
# ==========================================
class TalentRiftingSpace(BasePassive):
    id = "rifting_space"
    name = "Разрывая пространство (А)"
    description = (
        "10.9 А: Атака (тратит 30 Заряда): Накладывает 10 Разрыва (Кол-во 2).\n"
        "Если нет заряда: Самоурон (100% от кубика).\n"
        "Попадание: Накладывает 'Пространственный разрыв'."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        if log_func: log_func("🌌 **Разрывая пространство**: Атака инициирована.")
        logger.log(f"🌌 Rifting Space activated by {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 10.9 А (Опц): Конденсатор
# ==========================================
class TalentCapacitor(BasePassive):
    id = "capacitor"
    name = "Конденсатор"
    description = "10.9 А (Опц): Ваш отряд не теряет Заряд в конце раунда."
    is_active_ability = False


# ==========================================
# 10.9 Б: Ахиллесова пята
# ==========================================
class TalentAchillesHeel(BasePassive):
    id = "achilles_heel"
    name = "Ахиллесова пята (Б)"
    description = (
        "10.9 Б: Начало боя: Выберите резист врага -> Понизить на 0.25 (+25%DMG)."
    )
    is_active_ability = True
    cooldown = 99

    def _get_battle_targets(self):
        """Возвращает всех участников боя (враги), аналогично Аресту."""
        try:
            from ui.simulator.logic.simulator_logic import get_teams  # type: ignore
            l_team, r_team = get_teams()
            return (l_team or []) + (r_team or [])
        except Exception:
            return []

    @property
    def conversion_options(self):
        """Формирует ключи выбора с типом урона: Имя::slash|pierce|blunt."""
        options = {}
        for u in self._get_battle_targets():
            if not u or not hasattr(u, "name"):
                continue
            # Берём hp_resists, если есть, иначе пропускаем
            resists_obj = getattr(u, "hp_resists", None)
            if not resists_obj:
                continue

            resists = {
                "slash": getattr(resists_obj, "slash", 1.0),
                "pierce": getattr(resists_obj, "pierce", 1.0),
                "blunt": getattr(resists_obj, "blunt", 1.0),
            }

            for r_type, val in resists.items():
                key = f"{u.name}::{r_type}"
                options[key] = f"{u.name} — {r_type}: {val:.2f} → {val + 0.25:.2f}"
        return options

    def activate(self, unit, log_func, choice_key=None, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0:
            return False
        # Если выбор не сделан, просим выбрать (как в Аресте)
        if not choice_key:
            if log_func:
                opts = ", ".join(self.conversion_options.values()) or "нет доступных врагов"
                log_func(f"⚠️ Выберите врага и тип резиста для {self.name}: {opts}")
            return False

        if "::" not in choice_key:
            if log_func:
                log_func(f"⚠️ Некорректный выбор: {choice_key}")
            return False

        target_name, resist_type = choice_key.split("::", 1)

        target = None
        for u in self._get_battle_targets():
            if u and getattr(u, "name", None) == target_name:
                target = u
                break

        if not target:
            if log_func:
                log_func(f"⚠️ Враг не найден: {target_name}")
            return False

        # Нельзя выбрать самого себя
        if target is unit:
            if log_func:
                log_func("⚠️ Нельзя выбрать самого себя")
            return False

        resists_obj = getattr(target, "hp_resists", None)
        if not resists_obj or not hasattr(resists_obj, resist_type):
            if log_func:
                log_func(f"⚠️ Резист не найден: {resist_type}")
            return False

        old_value = getattr(resists_obj, resist_type, 1.0)
        # Накладываем длительный эффект 99 раундов вместо прямого изменения
        target.add_status(f"{resist_type}_resist_down", 1, duration=99)

        logger.log(
            f"⚔️ {self.name}: Applied {resist_type}_resist_down to {target.name}",
            LogLevel.NORMAL, "Talent"
        )
        if log_func:
            log_func(f"⚔️ **{self.name}**: {target.name} получает эффект {resist_type} Resist Down на 99!")
        unit.cooldowns[self.id] = self.cooldown

        return True



# ==========================================
# 10.9 Б (Опц): Без Ошибок
# ==========================================
class TalentNoMistakes(BasePassive):
    id = "no_mistakes"
    name = "Без Ошибок"
    description = "10.9 Б (Опц): Все броски = 5 + 1d15."
    is_active_ability = False

    def modify_check_parameters(self, unit, stat_key: str, params: dict) -> dict:
        """Изменяем ВСЕ проверки на 5 + d15."""
        params["die_max"] = 15
        params["base_bonus"] = 5
        return params


# ==========================================
# 10.10 А: Короткое замыкание
# ==========================================
class TalentShortCircuit(BasePassive):
    id = "short_circuit"
    name = "Короткое замыкание (А)"
    description = "10.10 А: Разрыв наносит доп. урон в начале раунда, не тратя свой заряд."
    is_active_ability = False


# ==========================================
# 10.10 Б: Гордость Seven
# ==========================================
class TalentPrideOfSeven(BasePassive):
    id = "pride_of_seven"
    name = "Гордость Seven (Б)"
    description = (
        "10.10 Б: Атака 'Разбить алмаз' (1 раз за бой).\n"
        "Попадание: Снимает 50% макс. Выдержки, накладывает 4 Паралича.\n"
        "Пассивно: Каждая 3-я кость при победе -> 1 Паралич."
    )
    is_active_ability = False
