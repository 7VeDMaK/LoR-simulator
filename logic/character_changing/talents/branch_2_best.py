from logic.character_changing.passives.base_passive import BasePassive
from core.logging import logger, LogLevel


# ======================================================================================
# НОВАЯ ВЕТКА 2: ВРОЖДЕННЫЙ ГЕНИЙ
# ======================================================================================

class TalentNaturalGenius(BasePassive):
    """
    2.1 Врожденный талант
    Вы просто родились лучше других.
    """
    id = "natural_genius"
    name = "2.1 Врожденный талант"
    description = (
        "«Зачем тренироваться годами, если ты просто родился лучше других?»\n\n"
        "Пассивно: +1 ко всем характеристикам и +2 к навыкам.\n"
        "Каждые 10 уровней персонажа бонус увеличивается (Максимум +5/+10 на 50 уровне)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        """Рассчитывает бонусы на основе уровня персонажа."""
        level = getattr(unit, 'level', 1)
        
        # Каждые 10 уровней: +1 к характеристикам, +2 к навыкам
        # Уровень 1-9: 0, Уровень 10-19: +1/+2, Уровень 20-29: +2/+4, и т.д.
        bonus_tiers = level // 10  # Количество полных "десяток" уровней
        bonus_attrs = int(min(bonus_tiers, 5))  # Максимум +5
        bonus_skills = int(min(bonus_tiers * 2, 10))  # Максимум +10
        
        logger.log(
            f"🌟 {self.name}: Уровень {level} (Тир {bonus_tiers}) -> +{bonus_attrs} к характеристикам, +{bonus_skills} к навыкам",
            LogLevel.NORMAL, "Talent"
        )
        
        return {
            # Характеристики (Attributes)
            "strength": bonus_attrs,
            "endurance": bonus_attrs,
            "agility": bonus_attrs,
            "wisdom": bonus_attrs,
            "psych": bonus_attrs,
            # Навыки (Skills)
            "strike_power": bonus_skills,
            "medicine": bonus_skills,
            "willpower": bonus_skills,
            "acrobatics": bonus_skills,
            "shields": bonus_skills,
            "tough_skin": bonus_skills,
            "speed": bonus_skills,
            "light_weapon": bonus_skills,
            "medium_weapon": bonus_skills,
            "heavy_weapon": bonus_skills,
            "firearms": bonus_skills,
            "eloquence": bonus_skills,
            "forging": bonus_skills,
            "engineering": bonus_skills,
            "programming": bonus_skills,
            "luck": bonus_skills,
        }


class TalentCelestialEyes(BasePassive):
    """
    2.2 Глаза Небожителя
    Вы видите суть слабостей врагов.
    """
    id = "celestial_eyes"
    name = "2.2 Глаза Небожителя"
    description = (
        "«Ты видишь не просто движения, ты видишь саму суть их слабостей».\n\n"
        "Пассивно: Объединяет эффекты Сканера и Анализа.\n"
        "- Вы видите точные значения HP/SP, сопротивления, пассивки, колоду и карты врага.\n\n"
        "[Разрез Пустоты]: В разработке - будет игнорировать часть стойкости цели."
        #Я хз, 0.2 как-то сильно для 2.2 пассивки, Разрез анала а не пусоты у челика, типа у того же идеального воина, где реально Разрез Пустоты(Ахиллесова пята), это вообще 10.9 талант 
    )
    is_active_ability = False


class TalentWatchAndLearn(BasePassive):
    """
    2.4 Смотри и учись
    Копирование карты союзника или врага.
    """
    id = "watch_and_learn"
    name = "2.4 Смотри и учись"
    description = (
        "«Я увидел это один раз. Этого достаточно, чтобы повторить это лучше тебя».\n\n"
        "Активно (КД: 3 сцены): Выберите карту, использованную союзником или врагом в этом раунде.\n"
        "Вы создаете в руке её временную копию со стоимостью 0. Копия исчезает в конце раунда."
        #бля, что это
    )
    is_active_ability = True
    cooldown = 3

    def activate(self, unit, log_func, choice_key=None, **kwargs):
        """Активация копирования карты."""
        # Проверка кулдауна
        if unit.cooldowns.get(self.id, 0) > 0:
            if log_func:
                log_func(f"⏳ **{self.name}**: На восстановлении ({unit.cooldowns[self.id]} раунд)")
            return False

        # TODO: Реализовать выбор карты из использованных в раунде
        # Для этого нужна интеграция с системой боя
        if log_func:
            log_func(f"📋 **{self.name}**: Выберите карту для копирования (функция в разработке)")
        
        # Устанавливаем кулдаун
        unit.cooldowns[self.id] = self.cooldown
        
        logger.log(
            f"👁️ {self.name}: {unit.name} использовал 'Смотри и учись'",
            LogLevel.NORMAL, "Talent"
        )
        
        return True


class TalentRightOfTheFirst(BasePassive):
    """
    2.5 Право Первого
    Самый сильный всегда бьет первым.
    """
    id = "right_of_the_first"
    name = "2.5 Право Первого"
    description = (
        "«Самый сильный всегда бьет первым».\n\n"
        "Пассивно: В начале боя вы получаете +2 Спешки (Haste) на 3 раунда.\n"
        "Дополнительный урон на основе разницы в скорости - в разработке."
    )
    is_active_ability = False

    def on_combat_start(self, unit, *args, **kwargs):
        """Даёт бонус к скорости в начале боя."""
        unit.add_status("haste", 2, duration=3)
        logger.log(
            f"⚡ {self.name}: {unit.name} получает +2 Спешки на 3 раунда!",
            LogLevel.NORMAL, "Talent"
        )


class TalentBlackFlash(BasePassive):
    """
    Опц. А: Искра Сверхчеловека (Black Flash)
    Критические удары от минимальных/максимальных значений.
    """
    id = "black_flash"
    name = "2.5 Опц. А: Искра Сверхчеловека"
    description = (
        "«Когда твоя сила достигает пика, мир замирает на мгновение».\n\n"
        "Пассивно: Если на кубике выпадает Минимальное или Максимальное значение — "
        "удар считается критическим (эффект в разработке)."
    )
    is_active_ability = False


class TalentBlueFlash(BasePassive):
    """
    Опц. Б: Синяя Вспышка
    Преимущество от высокой скорости.
    """
    id = "blue_flash"
    name = "2.5 Опц. Б: Синяя Вспышка"
    description = (
        "Требование: Ловкость 30+.\n\n"
        "«Ваша скорость становится настолько высокой, что противник не успевает среагировать».\n\n"
        "Эффекты на основе разницы в скорости - в разработке."
    )
    is_active_ability = False

    def can_learn(self, unit) -> tuple[bool, str]:
        """Проверка требований."""
        agility = getattr(unit, 'agility', 0)
        if agility < 30:
            return False, "Требуется Ловкость 30+"
        return True, ""


class TalentRoleModel(BasePassive):
    """
    2.6 Пример для подражания!
    Бафы в зависимости от количества союзников.
    """
    id = "role_model"
    name = "2.6 Пример для подражания!"
    description = (
        "«Вместе мы сила!»\n\n"
        "В битвах с союзниками персонаж получает бафы в каждой сцене:\n"
        "• 1 союзник: +2 Стойкость\n"
        "• 2 союзника: +2 Сила атаки\n"
        "• 3 союзника: +2 Спешка\n"
        "• 4-5 союзников: +1 к каждому бафу (макс 5 союзников)\n\n"
        "⚠️ Если вы оглушены: каждый союзник получает +3 Уязвимость, -3 Сила атаки, +3 Bind на 2 хода."
    )
    is_active_ability = False

    def _count_allies(self, unit):
        """Подсчитывает количество активных союзников."""
        try:
            from ui.simulator.logic.simulator_logic import get_teams
            l_team, r_team = get_teams()
            
            # Определяем команду юнита
            my_team = None
            if unit in (l_team or []):
                my_team = l_team
            elif unit in (r_team or []):
                my_team = r_team
            
            if not my_team:
                return 0
            
            # Подсчитываем живых союзников (не считая себя)
            allies = 0
            for ally in my_team:
                if ally.name != unit.name and ally.current_hp > 0:
                    allies += 1
            
            return allies
        except Exception:
            return 0

    def on_round_start(self, unit, *args, **kwargs):
        """Применяет бафы в начале раунда в зависимости от количества союзников."""
        ally_count = self._count_allies(unit)
        
        if ally_count == 0:
            return
        
        # Базовые бафы
        endurance_bonus = 0
        atk_bonus = 0
        haste_bonus = 0
        
        if ally_count >= 1:
            endurance_bonus = 2
        if ally_count >= 2:
            atk_bonus = 2
        if ally_count >= 3:
            haste_bonus = 2
        
        # Дополнительные бафы за 4-5 союзников
        extra_allies = min(ally_count - 3, 2)
        if extra_allies > 0:
            endurance_bonus += extra_allies
            atk_bonus += extra_allies
            haste_bonus += extra_allies
        
        # Применяем бафы
        if endurance_bonus > 0:
            unit.add_status("endurance", endurance_bonus, duration=1)
        if atk_bonus > 0:
            unit.add_status("strength", atk_bonus, duration=1)
        if haste_bonus > 0:
            unit.add_status("haste", haste_bonus, duration=1)
        
        logger.log(
            f"👥 {self.name}: {unit.name} получает бафы за {ally_count} союзников "
            f"(+{endurance_bonus} Стойкость, +{atk_bonus} Сила, +{haste_bonus} Спешка)",
            LogLevel.NORMAL, "Talent"
        )
        
        # Проверка оглушения
        if unit.is_staggered():
            self._apply_ally_debuffs(unit)

    def _apply_ally_debuffs(self, unit):
        """Накладывает дебафы на союзников при оглушении."""
        try:
            from ui.simulator.logic.simulator_logic import get_teams
            l_team, r_team = get_teams()
            
            my_team = None
            if unit in (l_team or []):
                my_team = l_team
            elif unit in (r_team or []):
                my_team = r_team
            
            if not my_team:
                return
            
            for ally in my_team:
                if ally.name != unit.name and ally.current_hp > 0:
                    ally.add_status("vulnerable", 3, duration=2)
                    ally.add_status("attack_power_down", 3, duration=2)
                    ally.add_status("bind", 3, duration=2)
            
            logger.log(
                f"💔 {self.name}: {unit.name} оглушен! Союзники получают дебафы!",
                LogLevel.NORMAL, "Talent"
            )
        except Exception as e:
            logger.log(f"⚠️ {self.name}: Ошибка при наложении дебафов: {e}", LogLevel.VERBOSE, "Talent")


class TalentMockery(BasePassive):
    """
    2.7 Насмешка
    Активная способность провокации врагов.
    """
    id = "mockery"
    name = "2.7 Насмешка"
    description = (
        "«Ты серьезно думаешь, что сможешь меня задеть?»\n\n"
        "Пассивно: +5 к Красноречию.\n\n"
        "Активно: Выберите цель (включая себя). Цель получает:\n"
        "• +2 Сила атаки\n"
        "• +4 Уязвимость\n"
        "Длительность: 1 ход."
    )
    is_active_ability = True

    def on_calculate_stats(self, unit) -> dict:
        """Бонус к красноречию."""
        return {"eloquence": 5}

    def activate(self, unit, log_func, choice_key=None, **kwargs):
        """Активация насмешки на выбранную цель."""
        # TODO: Реализовать выбор цели через интерфейс
        if log_func:
            log_func(f"🎭 **{self.name}**: Выберите цель для насмешки (функция в разработке)")
        
        logger.log(
            f"🎭 {self.name}: {unit.name} использовал Насмешку",
            LogLevel.NORMAL, "Talent"
        )
        
        return True


class TalentPlotArmor(BasePassive):
    """
    2.8 Сюжетная броня
    Повышенная выдержка и воскрешение при смерти.
    """
    id = "plot_armor_v2"
    name = "2.8 Сюжетная броня"
    description = (
        "«Главный герой не может умереть в середине истории».\n\n"
        "Пассивно: +25% к максимальной Выдержке.\n\n"
        "При получении смертельного урона (1 раз за бой):\n"
        "• В следующем раунде восстанавливается вся Выдержка и 1 HP\n"
        "• Полный иммунитет к урону в этом раунде"
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        """Бонус к максимальной выдержке."""
        base_stagger = unit.max_stagger
        stagger_bonus = int(base_stagger * 0.25)
        
        logger.log(
            f"🛡️ {self.name}: +25% к Выдержке ({stagger_bonus})",
            LogLevel.VERBOSE, "Talent"
        )
        
        return {"max_stagger": stagger_bonus}

    def on_take_damage(self, unit, amount, source, **kwargs):
        """Срабатывает при получении смертельного урона."""
        # Проверяем, использовалась ли уже способность
        if hasattr(unit, '_plot_armor_used') and unit._plot_armor_used:
            return
        
        # Если HP падает до 0 или ниже
        if unit.current_hp <= 0:
            unit._plot_armor_used = True
            unit._plot_armor_revive_next_round = True
            
            logger.log(
                f"✨ {self.name}: {unit.name} получил смертельный урон! Воскрешение активировано!",
                LogLevel.NORMAL, "Talent"
            )

    def on_round_start(self, unit, *args, **kwargs):
        """Воскрешает персонажа в следующем раунде."""
        if hasattr(unit, '_plot_armor_revive_next_round') and unit._plot_armor_revive_next_round:
            unit.current_hp = 1
            unit.current_stagger = unit.max_stagger
            unit.add_status("invulnerable", 1, duration=1)  # Иммунитет к урону
            
            unit._plot_armor_revive_next_round = False
            
            logger.log(
                f"✨ {self.name}: {unit.name} воскрешен! (1 HP, полная Выдержка, иммунитет)",
                LogLevel.NORMAL, "Talent"
            )


class TalentMuted(BasePassive):
    """
    2.9 Muted
    Заглушить кубик скорости противника.
    """
    id = "muted"
    name = "2.9 Muted"
    description = (
        "«Тихо. Сиди. Не двигайся».\n\n"
        "Активно (КД: 5 сцен): Выберите любой кубик скорости противника "
        "(кроме массовой атаки) и заглушите его без использования карты.\n"
        "Цель теряет этот слот скорости."
    )
    is_active_ability = True
    cooldown = 5

    def activate(self, unit, log_func, choice_key=None, **kwargs):
        """Заглушить слот скорости врага."""
        if unit.cooldowns.get(self.id, 0) > 0:
            if log_func:
                log_func(f"⏳ **{self.name}**: На восстановлении ({unit.cooldowns[self.id]} сцен)")
            return False
        
        # TODO: Реализовать выбор слота скорости врага
        if log_func:
            log_func(f"🔇 **{self.name}**: Выберите слот скорости врага для заглушения (функция в разработке)")
        
        unit.cooldowns[self.id] = self.cooldown
        
        logger.log(
            f"🔇 {self.name}: {unit.name} использовал Muted",
            LogLevel.NORMAL, "Talent"
        )
        
        return True


class TalentJustGettingStarted(BasePassive):
    """
    2.10 Да мы только начали!
    Бафы за проигранные столкновения.
    """
    id = "just_getting_started"
    name = "2.10 Да мы только начали!"
    description = (
        "«Каждое поражение делает меня сильнее!»\n\n"
        "Требование: Все опциональные таланты ветки 2.\n\n"
        "За каждое проигранное столкновение персонаж получает в следующей сцене:\n"
        "• +1 Сила атаки на один ход"
    )
    is_active_ability = False

    def can_learn(self, unit) -> tuple[bool, str]:
        """Проверка требований - все опциональные таланты."""
        # TODO: Проверить наличие всех опциональных талантов ветки 2
        return True, ""

    def on_clash_lose(self, ctx, **kwargs):
        """Запоминает проигранное столкновение."""
        unit = ctx.source
        
        # Увеличиваем счетчик проигранных столкновений
        if not hasattr(unit, '_lost_clashes_count'):
            unit._lost_clashes_count = 0
        
        unit._lost_clashes_count += 1
        
        logger.log(
            f"💪 {self.name}: {unit.name} проиграл столкновение ({unit._lost_clashes_count} всего)",
            LogLevel.VERBOSE, "Talent"
        )

    def on_round_start(self, unit, *args, **kwargs):
        """Применяет бафы за проигранные столкновения."""
        if hasattr(unit, '_lost_clashes_count') and unit._lost_clashes_count > 0:
            stacks = unit._lost_clashes_count
            unit.add_status("attack_power_up", stacks, duration=1)
            
            logger.log(
                f"💪 {self.name}: {unit.name} получает +{stacks} Сила атаки за проигранные столкновения!",
                LogLevel.NORMAL, "Talent"
            )
            
            # Сбрасываем счетчик
            unit._lost_clashes_count = 0



