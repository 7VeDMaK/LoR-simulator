from core.logging import logger, LogLevel  # [NEW] Import
from logic.character_changing.passives.base_passive import BasePassive

# ==========================================
# 8.1 Атлетичный
# ==========================================
class TalentAthletic(BasePassive):
    id = "athletic"
    name = "Атлетичный"
    description = (
        "«Дисциплина превращает тело в оружие. Там, где другие видят патовую ситуацию, ты видишь возможность для удара. Твои рефлексы отточены до автоматизма.»\n\n"
        "Пассивно: Вы постоянно поддерживаете высокий темп боя (+1 Спешка/Haste).\n"
        "Тактическое преимущество: Вы можете перенаправлять атаки (Interception) при РАВНОЙ скорости.\n"
        "(Обычно для перехвата требуется скорость строго выше, чем у цели)."
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        # Постоянный бонус к скорости каждый раунд
        unit.add_status("haste", 1, duration=1)

        if log_func:
            log_func(f"🏃 **{self.name}**: Боевая готовность (+1 Haste).")

        logger.log(f"🏃 Athletic: +1 Haste for {unit.name}", LogLevel.VERBOSE, "Talent")

    def can_redirect_on_equal_speed(self, unit) -> bool:
        """
        Хук для боевой системы. Разрешает перехват при speed == target_speed.
        """
        # Логируем на VERBOSE, чтобы не засорять основной лог частыми проверками
        logger.log(f"🏃 Athletic: {unit.name} allowed to redirect on equal speed", LogLevel.VERBOSE, "Talent")
        return True

# ==========================================
# 8.2 Быстрые руки
# ==========================================
class TalentFastHands(BasePassive):
    id = "fast_hands"
    name = "Быстрые руки"
    description = (
        "Огнестрельное оружие +3.\n"
        "В начале боя вы получаете карту 'Перезарядка' (без кубиков, действие).\n"
        "При использовании восстанавливает 6 патронов (Ammo) на 99 ходов."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"firearms": 3}

    def on_combat_start(self, unit, log_func, **kwargs):
        # Добавляем карту перезарядки в колоду, если её ещё нет
        reload_card_id = "reload_ammo"
        if reload_card_id not in unit.deck:
            unit.deck.append(reload_card_id)
            if log_func:
                log_func(f"🔫 **Быстрые руки**: Карта 'Перезарядка' добавлена в колоду.")
            logger.log(f"🔫 Fast Hands: Added reload card to {unit.name}", LogLevel.NORMAL, "Talent")


# ==========================================
# 8.3 Лидер
# ==========================================
class TalentLeader(BasePassive):
    id = "leader"
    name = "Лидер"
    description = (
        "Вы вдохновляете союзников своим присутствием.\n"
        "Пассивно: +1 к урону за каждого живого союзника (кроме себя), максимум +3.\n"
        "Союзники получают +2 к защите.\n"
        "Минус: При вашей смерти союзники получают -25% SP."
    )
    is_active_ability = False

    def _get_active_allies(self, unit):
        """Возвращает список активных союзников на поле боя."""
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
                logger.log(f"🔍 Leader: {unit.name} team not found", LogLevel.VERBOSE, "Talent")
                return []

            # Собираем живых союзников (не считая себя)
            allies = []
            for ally in my_team:
                if ally.name == unit.name:
                    continue
                if ally.current_hp > 0:
                    allies.append(ally)

            return allies

        except Exception as e:
            logger.log(f"⚠️ Leader allies error: {e}", LogLevel.VERBOSE, "Talent")
            return []

    def on_combat_start(self, unit, log_func, **kwargs):
        """Даём защиту союзникам и себе урон в начале боя"""
        alive_allies = self._get_active_allies(unit)
        
        # Даём бонус к урону себе в зависимости от количества союзников
        dmg_bonus = min(len(alive_allies), 3)
        if dmg_bonus > 0:
            unit.add_status("dmg_up", dmg_bonus, duration=999)
            logger.log(f"🚩 Leader: {unit.name} gains +{dmg_bonus} damage from {len(alive_allies)} allies", 
                      LogLevel.NORMAL, "Talent")
        
        # Даём защиту союзникам
        buffed_count = 0
        for ally in alive_allies:
            ally.add_status("protection", 2, duration=999)
            buffed_count += 1
        
        if log_func:
            if dmg_bonus > 0:
                log_func(f"🚩 **{self.name}**: Вы получили +{dmg_bonus} к урону от {len(alive_allies)} союзников.")
            if buffed_count > 0:
                log_func(f"🚩 **{self.name}**: {buffed_count} союзников получили +2 Защиты.")
        
        logger.log(f"🚩 Leader: {unit.name} buffed {buffed_count} allies with Protection", 
                  LogLevel.NORMAL, "Talent")


# ==========================================
# 8.4 Addiction is a bitch
# ==========================================
class TalentAddiction(BasePassive):
    id = "addiction_is_a_bitch"
    name = "Addiction is a bitch"
    description = (
        "Активно (Потребление вещества): Восст. 10% SP/раунд (3 раунда).\n"
        "Баффы на 3 раунда: +1 Сила, +1 Скорость, Иммунитет к Параличу."
    )
    is_active_ability = True
    cooldown = 20  # Условно 2 часа

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        duration = 3
        unit.add_status("attack_power_up", 1, duration=duration)
        unit.add_status("haste", 1, duration=duration)  # Скорость
        unit.add_status("immune_paralysis", 1, duration=duration)  # Иммунитет к параличу

        # Регенерацию SP реализуем через статус или просто мгновенно дадим часть
        heal_sp = int(unit.max_sp * 0.10)
        unit.restore_sp(heal_sp)

        unit.cooldowns[self.id] = self.cooldown
        if log_func: log_func(f"💊 **Зависимость**: Прилив сил! (+{heal_sp} SP, +Str, +Spd, Иммунитет к Параличу)")

        logger.log(f"💊 Addiction activated for {unit.name}: +{heal_sp} SP, Buffs applied (Paralysis Immunity)", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 8.5 Быстрое отступление
# ==========================================
class TalentRapidRetreat(BasePassive):
    id = "rapid_retreat"
    name = "Быстрое отступление"
    description = (
        "Тактическое отступление при критическом уроне.\n"
        "Если вы потеряли > 25% HP за раунд -> получаете статус 'Незаметный' на 1 раунд.\n"
        "(Незаметный: враги не могут вас таргетировать)"
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        """Сбрасываем счётчик урона в начале раунда"""
        unit.memory["rapid_retreat_damage_taken"] = 0

    def on_take_damage(self, unit, amount, source, **kwargs):
        """Отслеживаем накопленный урон за раунд"""
        log_func = kwargs.get("log_func")
        
        # Увеличиваем счётчик урона
        current_damage = unit.memory.get("rapid_retreat_damage_taken", 0)
        unit.memory["rapid_retreat_damage_taken"] = current_damage + amount
        
        # Проверяем порог (25% от максимального HP)
        threshold = unit.max_hp * 0.25
        total_damage = unit.memory["rapid_retreat_damage_taken"]
        
        # Если превысили порог и ещё не активировали в этом раунде
        if total_damage > threshold and not unit.memory.get("rapid_retreat_activated", False):
            unit.memory["rapid_retreat_activated"] = True
            unit.add_status("invisibility", 1, duration=2)
            
            if log_func:
                log_func(f"🏃💨 **Быстрое отступление**: Получено {int(total_damage)} урона (>{int(threshold)}) → Незаметность!")
            
            logger.log(
                f"🏃💨 Rapid Retreat: {unit.name} took {int(total_damage)} damage (>{int(threshold)}) → Invisibility",
                LogLevel.NORMAL, "Talent"
            )

    def on_round_end(self, unit, log_func, **kwargs):
        """Сбрасываем флаг активации в конце раунда"""
        unit.memory["rapid_retreat_activated"] = False
        return []


# ==========================================
# 8.6 Перезарядка (Боевая)
# ==========================================
class TalentCombatReload(BasePassive):
    id = "combat_reload"
    name = "Перезарядка (Боевая)"
    description = (
        "Боевая перезарядка под огнём противника.\n"
        "В начале боя вы получаете карту 'Боевая перезарядка' (Уворот + Блок).\n"
        "Использование восстанавливает 6 патронов (Ammo) на 99 ходов.\n"
        "Кубики защиты зависят от вашего ранга (1-13)."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        # Добавляем карту боевой перезарядки в колоду
        reload_card_id = "combat_reload"
        if reload_card_id not in unit.deck:
            unit.deck.append(reload_card_id)
            if log_func:
                log_func(f"🔫🛡️ **Боевая перезарядка**: Карта добавлена в колоду.")
            logger.log(f"🔫🛡️ Combat Reload: Added combat reload card to {unit.name}", LogLevel.NORMAL, "Talent")


# ==========================================
# 8.7 Найти уязвимость
# ==========================================
class TalentFindVulnerability(BasePassive):
    id = "find_vulnerability"
    name = "Найти уязвимость"
    description = (
        "8.7 Первая атака по врагу накладывает Метку.\n"
        "Метка: +25% урона по врагу."
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        # Очищаем флаги маркированных целей в начале раунда
        keys_to_remove = [k for k in unit.memory.keys() if k.startswith(f"marked_target_{unit.name}_")]
        for key in keys_to_remove:
            del unit.memory[key]

    def on_hit(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        # Нужно проверить, первая ли это атака за раунд.
        # Используем память юнита.
        if not ctx.target: return

        flag = f"marked_target_{ctx.source.name}_{ctx.target.name}"
        if not ctx.source.memory.get(flag):
            ctx.source.memory[flag] = True
            ctx.target.add_status("under_crosshairs", 1, duration=2)
            ctx.log.append(f"🎯 **{self.name}**: Цель помечена (Уязвимость)!")
            logger.log(f"🎯 Find weak: {ctx.target.name} marked by {ctx.source.name}", LogLevel.NORMAL,
                       "Talent")


# ==========================================
# 8.8 Одолженное время
# ==========================================
class TalentBorrowedTime(BasePassive):
    id = "borrowed_time"
    name = "Одолженное время"
    description = (
        "Спасение союзника от критической ситуации.\n"
        "Пассивно: Если союзник находится в Stagger → Восстанавливаете ему 25% Выдержки и отменяете Stagger.\n"
        "(Один раз за бой на каждого союзника)"
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        """Сбрасываем список спасённых союзников в начале боя"""
        unit.memory["borrowed_time_saved"] = []
        logger.log(f"⏰ Borrowed Time: Initialized for {unit.name}", LogLevel.VERBOSE, "Talent")

    def on_round_end(self, unit, log_func, **kwargs):
        """Проверяем союзников на Stagger и спасаем их"""
        # Получаем список уже спасённых союзников
        saved_list = unit.memory.get("borrowed_time_saved", [])
        
        # Получаем команду
        try:
            from ui.simulator.logic.simulator_logic import get_teams
            l_team, r_team = get_teams()

            my_team = None
            if unit in (l_team or []):
                my_team = l_team
            elif unit in (r_team or []):
                my_team = r_team

            if not my_team:
                return []

            # Проверяем каждого союзника
            for ally in my_team:
                # Пропускаем себя и мёртвых
                if ally.name == unit.name or ally.current_hp <= 0:
                    continue
                
                # Пропускаем уже спасённых в этом бою
                if ally.name in saved_list:
                    continue
                
                # Проверяем, находится ли в Stagger
                if ally.is_staggered():
                    # Восстанавливаем 25% выдержки
                    heal_amount = int(ally.max_stagger * 0.25)
                    ally.restore_stagger(heal_amount)
                    
                    # Добавляем в список спасённых
                    saved_list.append(ally.name)
                    unit.memory["borrowed_time_saved"] = saved_list
                    
                    if log_func:
                        log_func(f"⏰ **Одолженное время**: {ally.name} спасён от Stagger! (+{heal_amount} Выдержки)")
                    
                    logger.log(
                        f"⏰ Borrowed Time: {unit.name} saved {ally.name} from Stagger (+{heal_amount} stagger)",
                        LogLevel.NORMAL, "Talent"
                    )
        
        except Exception as e:
            logger.log(f"⚠️ Borrowed Time error: {e}", LogLevel.VERBOSE, "Talent")
        
        return []


# ==========================================
# 8.9 Железный строй
# ==========================================
class TalentIronFormation(BasePassive):
    id = "iron_formation"
    name = "Железный строй"
    description = (
        "Воинская дисциплина и коллективное мастерство.\n"
        "Пассивно: Весь отряд получает +3 ко всем навыкам.\n"
        "(Эффект суммируется от нескольких персонажей с этим талантом)\n\n"
        "Активно (КД 5): Железный строй!\n"
        "Вся команда получает Иммунитет к Стаггеру и +50 Защиты на 2 раунда."
    )
    is_active_ability = True
    cooldown = 5

    def on_combat_start(self, unit, log_func, **kwargs):
        """Применяем бонусы ко всей команде в начале боя"""
        bonus_per_leader = 3
        
        try:
            from ui.simulator.logic.simulator_logic import get_teams
            l_team, r_team = get_teams()

            # Определяем команду
            my_team = None
            if l_team and unit in l_team:
                my_team = l_team
            elif r_team and unit in r_team:
                my_team = r_team

            if not my_team:
                logger.log(f"⚔️ Iron Formation: {unit.name} team not found", LogLevel.VERBOSE, "Talent")
                return

            # Считаем количество лидеров с Iron Formation
            formation_count = 0
            for ally in my_team:
                if ally.current_hp > 0 and "iron_formation" in getattr(ally, 'talents', []):
                    formation_count += 1

            if formation_count == 0:
                return

            total_bonus = bonus_per_leader * formation_count
            
            # Список всех навыков
            all_skills = [
                "power_attack", "acrobatics", "speed", "heavy_weapon",
                "smithing", "medicine", "shields", "light_weapon",
                "firearms", "engineering", "willpower", "tough_skin",
                "medium_weapon", "persuasion", "programming"
            ]
            
            # Применяем бонусы ко всем членам команды
            for ally in my_team:
                if ally.current_hp <= 0:
                    continue
                    
                for skill in all_skills:
                    if skill in ally.skills:
                        ally.skills[skill] += total_bonus
                    else:
                        ally.skills[skill] = total_bonus
                
                logger.log(
                    f"⚔️ Iron Formation: {ally.name} receives +{total_bonus} to all skills ({formation_count} leaders)",
                    LogLevel.NORMAL, "Talent"
                )
            
            if log_func:
                log_func(f"⚔️ **Железный строй**: Команда получила +{total_bonus} ко всем навыкам!")

        except Exception as e:
            logger.log(f"⚠️ Iron Formation error: {e}", LogLevel.VERBOSE, "Talent")

    def activate(self, unit, log_func, **kwargs):
        """Активная способность: Железный строй - защита всей команды"""
        if unit.cooldowns.get(self.id, 0) > 0:
            return False

        try:
            from ui.simulator.logic.simulator_logic import get_teams
            l_team, r_team = get_teams()

            # Определяем команду
            my_team = None
            if l_team and unit in l_team:
                my_team = l_team
            elif r_team and unit in r_team:
                my_team = r_team

            if not my_team:
                logger.log(f"⚔️ Iron Formation Activate: {unit.name} team not found", LogLevel.VERBOSE, "Talent")
                return False

            # Применяем баффы всей команде
            buffed_count = 0
            for ally in my_team:
                if ally.current_hp <= 0:
                    continue
                
                # Иммунитет к стаггеру на 2 раунда
                ally.add_status("stagger_immune", 1, duration=2)
                # Защита +50 на 2 раунда
                ally.add_status("protection", 50, duration=2)
                buffed_count += 1
            
            unit.cooldowns[self.id] = self.cooldown
            
            if log_func:
                log_func(f"⚔️🛡️ **Железный строй**: Железный строй! {buffed_count} союзников получили Иммунитет к Стаггеру и +50 Защиты!")
            
            logger.log(
                f"⚔️🛡️ Iron Formation Activated: {unit.name} buffed {buffed_count} allies with Stagger Immunity and Protection",
                LogLevel.NORMAL, "Talent"
            )
            return True

        except Exception as e:
            logger.log(f"⚠️ Iron Formation Activate error: {e}", LogLevel.VERBOSE, "Talent")
            return False


# ==========================================
# 8.10 Последняя надежда
# ==========================================
class TalentLastHope(BasePassive):
    """
    Последняя надежда.
    В сражениях без активных союзников на поле боя,
    персонаж получает +3 к стойкости, +3 к силе атаки, +3 к выносливости и +3 патрона.
    """
    id = "last_hope"
    name = "Последняя надежда"
    description = (
        "Когда все союзники пали, в тебе просыпается нечеловеческая стойкость.\n"
        "В сражениях без активных союзников: +3 Стойкость, +3 Сила атаки, +3 Выносливость, +3 Патрона."
    )
    is_active_ability = False

    def _has_active_allies(self, unit):
        """Проверяет наличие активных союзников на поле боя."""
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
                logger.log(f"🔍 Last Hope: {unit.name} team not found", LogLevel.VERBOSE, "Passive")
                return False
            
            # Проверяем наличие других активных союзников (не оглушенных и живых)
            active_allies = 0
            for ally in my_team:
                # Проверяем по имени, так как объекты могут быть разными экземплярами
                if ally.name == unit.name:
                    continue
                    
                # Считаем союзника активным, если он жив и не оглушен
                is_alive = ally.current_hp > 0
                is_staggered = ally.is_staggered() if callable(getattr(ally, 'is_staggered', None)) else False
                is_not_staggered = not is_staggered
                
                if is_alive and is_not_staggered:
                    active_allies += 1
            
            logger.log(
                f"🔍 Last Hope: {unit.name} has {active_allies} active allies",
                LogLevel.VERBOSE, "Passive"
            )
            
            return active_allies > 0
            
        except Exception as e:
            logger.log(f"⚠️ Last Hope check error: {e}", LogLevel.VERBOSE, "Passive")
            return False

    def on_round_start(self, unit, log_func, **kwargs):
        """Применяет бонусы в начале раунда, если нет активных союзников."""
        if not self._has_active_allies(unit):
            # Применяем статусы на весь раунд
            unit.add_status("attack_power_up", 3, duration=1)
            unit.add_status("endurance", 3, duration=1)
            unit.add_status("protection", 3, duration=1)
            unit.add_status("ammo", 3, duration=99)
            
            if log_func:
                log_func(
                    f"⚔️💀 **{self.name}**: {unit.name} - последний выживший! "
                    f"(+3 Сила/Выносливость/Защита, +3 Патрона)"
                )
            
            logger.log(
                f"⚔️💀 {self.name}: {unit.name} fights alone! (+3 Power/Endurance/Protection, +3 Ammo)",
                LogLevel.NORMAL, "Passive"
            )