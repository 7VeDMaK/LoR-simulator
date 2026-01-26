from logic.character_changing.passives.base_passive import BasePassive
from core.logging import logger, LogLevel
from core.enums import DiceType


class PassiveStances(BasePassive):
    """
    Система стоек Лейлы.
    Персонаж может выбрать одну из четырех стоек:
    - Режущая (Slash): +1 мощность к Slash урону
    - Колющая (Pierce): +1 мощность к Pierce урону
    - Дробящая (Blunt): +1 мощность к Blunt урону
    - Защита (Block/Evade): +1 мощность к Block и Evade
    КД: 2 сцены
    """
    id = "stances"
    name = "Боевые Стойки"
    description = (
        "Активно: Выбрать одну из четырех стоек для боя (КД: 2).\n"
        "Режущая: +1 мощность Slash\n"
        "Колющая: +1 мощность Pierce\n"
        "Дробящая: +1 мощность Blunt\n"
        "Защита: +1 мощность Block/Evade"
    )
    is_active_ability = True
    cooldown = 2

    @property
    def conversion_options(self):
        """Формирует меню выбора стоек."""
        current_stance = self._get_current_stance()
        
        options = {
            "slash": "🔪 Режущая (Slash)" + (" [активна]" if current_stance == "slash" else ""),
            "pierce": "🗡️ Колющая (Pierce)" + (" [активна]" if current_stance == "pierce" else ""),
            "blunt": "⚒️ Дробящая (Blunt)" + (" [активна]" if current_stance == "blunt" else ""),
            "block": "🛡️ Защита (Block/Evade)" + (" [активна]" if current_stance == "block" else ""),
        }
        return options

    def _get_current_stance(self):
        """Определяет текущую активную стойку."""
        # Проверяем какие статусы стоек активны
        stances = ["stance_slash", "stance_pierce", "stance_blunt", "stance_block"]
        for unit_with_stance in self._get_all_units():
            for stance_id in stances:
                if unit_with_stance.get_status(stance_id) > 0:
                    return stance_id.replace("stance_", "")
        return None

    def _get_all_units(self):
        """Получает всех юнитов в бою (вспомогательный метод)."""
        try:
            from ui.simulator.logic.simulator_logic import get_teams
            l_team, r_team = get_teams()
            return (l_team or []) + (r_team or [])
        except Exception:
            return []

    def activate(self, unit, log_func, choice_key=None, **kwargs):
        """Активирует выбранную стойку и меняет колоду карт."""
        # Проверяем кулдаун
        if unit.cooldowns.get(self.id, 0) > 0:
            if log_func:
                log_func(f"⏳ **{self.name}**: На восстановлении ({unit.cooldowns[self.id]} раунд)")
            return False

        # Если выбор не сделан, просим выбрать
        if not choice_key:
            if log_func:
                opts = ", ".join(self.conversion_options.values())
                log_func(f"⚠️ Выберите боевую стойку: {opts}")
            return False

        # Валидация выбора
        valid_stances = ["slash", "pierce", "blunt", "block"]
        if choice_key not in valid_stances:
            if log_func:
                log_func(f"⚠️ Некорректная стойка: {choice_key}")
            return False

        # Снимаем все предыдущие стойки
        for stance in valid_stances:
            status_id = f"stance_{stance}"
            if unit.get_status(status_id) > 0:
                unit.remove_status(status_id, unit.get_status(status_id))

        # Активируем новую стойку (длительность 99 = "пока не переключимся")
        stance_status_id = f"stance_{choice_key}"
        unit.add_status(stance_status_id, 1, duration=99)

        # ===== СМЕНА КОЛОДЫ КАРТ =====
        deck_mapping = {
            "slash": "layla_slash_stance_cards.json",
            "pierce": "layla_pierce_stance_cards.json",
            "blunt": "layla_blunt_stance_cards.json",
            "block": "layla_defense_stance_cards.json"
        }
        
        deck_file = deck_mapping.get(choice_key)
        if deck_file:
            self._load_deck_from_file(unit, deck_file)

        # Логируем
        stance_names = {
            "slash": "🔪 Режущая",
            "pierce": "🗡️ Колющая",
            "blunt": "⚒️ Дробящая",
            "block": "🛡️ Защита"
        }
        stance_name = stance_names.get(choice_key, "Неизвестная")

        logger.log(
            f"⚔️ {self.name}: {unit.name} принял стойку {stance_name}",
            LogLevel.NORMAL, "Passive"
        )
        if log_func:
            log_func(f"⚔️ **{self.name}**: Активирована {stance_name} стойка! (+1 мощность, колода сменена)")

        # Установляем кулдаун
        unit.cooldowns[self.id] = self.cooldown

        return True

    def _load_deck_from_file(self, unit, filename: str):
        """Загружает колоду карт из JSON файла."""
        import json
        import os
        
        filepath = os.path.join("data", "cards", filename)
        
        try:
            if not os.path.exists(filepath):
                logger.log(
                    f"⚠️ Файл колоды не найден: {filepath}",
                    LogLevel.NORMAL, "Passive"
                )
                return
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cards_list = data.get("cards", [])
            
            # Заменяем колоду на новую (список ID карт)
            unit.deck = [card.get("id") for card in cards_list if card.get("id")]
            
            logger.log(
                f"🃏 {self.name}: Загружена колода из {filename} ({len(unit.deck)} карт)",
                LogLevel.NORMAL, "Passive"
            )
            
        except Exception as e:
            logger.log(
                f"⚠️ Ошибка загрузки колоды из {filename}: {e}",
                LogLevel.NORMAL, "Passive"
            )

    def modify_outgoing_damage(self, unit, amount, damage_type, stack=0, log_list=None, **kwargs):
        """
        Применяет бонус +1 мощность в зависимости от активной стойки.
        """
        # Определяем какая стойка активна
        stance_to_type = {
            "stance_slash": "slash",
            "stance_pierce": "pierce",
            "stance_blunt": "blunt",
        }

        # Проверяем каждую стойку
        for status_id, stance_type in stance_to_type.items():
            if unit.get_status(status_id) > 0:
                if damage_type == stance_type:
                    if log_list is not None:
                        log_list.append(f"⚔️ **{self.name}**: +1 мощность ({stance_type})")
                    return amount + 1
                break

        # Проверяем стойку Защиты (Block/Evade)
        if unit.get_status("stance_block") > 0:
            if damage_type in ["block", "evade"]:
                if log_list is not None:
                    log_list.append(f"🛡️ **{self.name}**: +1 мощность ({damage_type})")
                return amount + 1

        return amount

    def on_roll(self, ctx, **kwargs):
        """Добавляем +1 power к кубу соответствующего типа через контекст."""
        die = ctx.dice
        if not die:
            return

        dtype = die.dtype
        
        # Логируем для отладки
        logger.log(
            f"🔍 Stances on_roll: {ctx.source.name}, dice type: {dtype}",
            LogLevel.VERBOSE, "Stances"
        )

        # Slash / Pierce / Blunt атакующие кубы
        if dtype in (DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT):
            if dtype == DiceType.SLASH and ctx.source.get_status("stance_slash") > 0:
                ctx.modify_power(1, "Боевые Стойки: Slash")
                logger.log(f"⚔️ Applied Slash stance bonus", LogLevel.NORMAL, "Stances")
            elif dtype == DiceType.PIERCE and ctx.source.get_status("stance_pierce") > 0:
                ctx.modify_power(1, "Боевые Стойки: Pierce")
                logger.log(f"⚔️ Applied Pierce stance bonus", LogLevel.NORMAL, "Stances")
            elif dtype == DiceType.BLUNT and ctx.source.get_status("stance_blunt") > 0:
                ctx.modify_power(1, "Боевые Стойки: Blunt")
                logger.log(f"⚔️ Applied Blunt stance bonus", LogLevel.NORMAL, "Stances")

        # Block / Evade защитные кубы
        elif dtype in (DiceType.BLOCK, DiceType.EVADE):
            if ctx.source.get_status("stance_block") > 0:
                ctx.modify_power(1, "Боевые Стойки: Block/Evade")
                logger.log(f"🛡️ Applied Block/Evade stance bonus", LogLevel.NORMAL, "Stances")

    def modify_power(self, unit, current_power, card_type=None, **kwargs):
        """
        Применяет бонус +1 к мощности куба при активной стойке.
        Этот метод вызывается при расчете мощности броска.
        """
        # Определяем какая стойка активна
        if card_type:
            card_type = card_type.lower()
            
            # Проверяем атаку по типу карты
            if card_type == "slash" and unit.get_status("stance_slash") > 0:
                return current_power + 1
            elif card_type == "pierce" and unit.get_status("stance_pierce") > 0:
                return current_power + 1
            elif card_type == "blunt" and unit.get_status("stance_blunt") > 0:
                return current_power + 1
            elif card_type in ["block", "evade"] and unit.get_status("stance_block") > 0:
                return current_power + 1
        
        return current_power


class PassiveFearOfHealing(BasePassive):
    """
    Страх перед лечением.
    Броски на медицину получают -5.
    """
    id = "fear_of_healing"
    name = "Страх перед лечением"
    description = "Броски на медицину получают -5."
    is_active_ability = False

    def modify_skill_check_result(self, unit, stat_key: str, current_result: int) -> int:
        """Модифицирует результат проверки медицины."""
        if stat_key == "medicine":
            logger.log(
                f"🩹 {self.name}: {unit.name} получает -5 к проверке медицины",
                LogLevel.NORMAL, "Passive"
            )
            return current_result - 5
        return current_result


class PassiveNotEconomicallyMinded(BasePassive):
    """
    Не экономического склада ума.
    Броски кубика на красноречие получают -2.
    """
    id = "not_economically_minded"
    name = "Не экономического склада ума"
    description = "Броски кубика на красноречие получают -2."
    is_active_ability = False

    def modify_skill_check_result(self, unit, stat_key: str, current_result: int) -> int:
        """Модифицирует результат проверки красноречия."""
        if stat_key == "eloquence":
            logger.log(
                f"💬 {self.name}: {unit.name} получает -2 к проверке красноречия",
                LogLevel.NORMAL, "Passive"
            )
            return current_result - 2
        return current_result


class PassiveTopographicCretinism(BasePassive):
    """
    Топографический кретинизм.
    Броски на мудрость получают -3.
    """
    id = "topographic_cretinism"
    name = "Топографический кретинизм"
    description = "Броски на мудрость получают -3."
    is_active_ability = False

    def modify_skill_check_result(self, unit, stat_key: str, current_result: int) -> int:
        """Модифицирует результат проверки мудрости."""
        if stat_key == "wisdom":
            logger.log(
                f"🧭 {self.name}: {unit.name} получает -3 к проверке мудрости",
                LogLevel.NORMAL, "Passive"
            )
            return current_result - 3
        return current_result


class PassiveSharpMind(BasePassive):
    """
    Острый Разум.
    Броски кубика на Психический порог получают +4.
    """
    id = "sharp_mind"
    name = "Острый Разум"
    description = "Броски кубика на Психический порог получают +4."
    is_active_ability = False

    def modify_skill_check_result(self, unit, stat_key: str, current_result: int) -> int:
        """Модифицирует результат проверки психического порога."""
        if stat_key == "psych":
            logger.log(
                f"🧠 {self.name}: {unit.name} получает +4 к проверке психического порога",
                LogLevel.NORMAL, "Passive"
            )
            return current_result + 4
        return current_result


class PassiveLowEndurance(BasePassive):
    """
    Малая выносливость.
    Продолжительные битвы даются тяжело.
    После 6-й сцены сражений получает +2 Bind и +2 Attack Power Down до конца битвы.
    """
    id = "low_endurance"
    name = "Малая выносливость"
    description = (
        "Продолжительные битвы даются тяжело.\n"
        "После 6-й сцены: +2 Bind, +2 Attack Power Down (до конца битвы)."
    )
    is_active_ability = False

    def on_round_start(self, unit, *args, **kwargs):
        """Проверяет номер сцены и накладывает дебафы после 6-й сцены."""
        try:
            import streamlit as st
            current_round = st.session_state.get('round_number', 1)
            
            # Если это 6-я или более поздняя сцена
            if current_round >= 6:
                # Проверяем, не наложены ли уже дебафы (чтобы не накладывать каждый раунд заново)
                if not hasattr(unit, '_low_endurance_applied'):
                    # Накладываем дебафы с длительностью 99 (до конца битвы)
                    unit.add_status("bind", 2, duration=99)
                    unit.add_status("attack_power_down", 2, duration=99)
                    
                    # Помечаем, что дебафы уже наложены
                    unit._low_endurance_applied = True
                    
                    logger.log(
                        f"💔 {self.name}: {unit.name} измотан длительным боем! (+2 Bind, +2 Attack Power Down)",
                        LogLevel.NORMAL, "Passive"
                    )
        except Exception as e:
            # Если streamlit не доступен (например, в тестах), игнорируем
            logger.log(f"⚠️ Low Endurance check error: {e}", LogLevel.VERBOSE, "Passive")
            pass


class PassiveHardenedBySolitude(BasePassive):
    """
    Закалённая Одиночеством.
    В сражениях без активных союзников на поле боя,
    персонаж получает +2 к силе атаки, +2 к скорости и +2 к выносливости.
    """
    id = "hardened_by_solitude"
    name = "Закалённая Одиночеством"
    description = (
        "Привычка быть наедине с самим собой сделала более уверенным в своих действиях.\n"
        "В сражениях без активных союзников: +2 Сила атаки, +2 Спешка, +2 Стойкость."
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
                logger.log(f"🔍 Solitude: {unit.name} team not found", LogLevel.VERBOSE, "Passive")
                return False
            
            # Логируем состав команды
            logger.log(
                f"🔍 Solitude: {unit.name} team has {len(my_team)} members",
                LogLevel.VERBOSE, "Passive"
            )
            
            # Проверяем наличие других активных союзников (не оглушенных и живых)
            active_allies = 0
            for ally in my_team:
                # Логируем КАЖДОГО члена команды
                ally_name = getattr(ally, 'name', 'UNKNOWN')
                logger.log(f"🔍 Checking team member: {ally_name}", LogLevel.VERBOSE, "Passive")
                
                # Проверяем по имени, так как объекты могут быть разными экземплярами
                if ally.name == unit.name:
                    logger.log(f"🔍 Skipping self: {ally_name}", LogLevel.VERBOSE, "Passive")
                    continue
                    
                # Считаем союзника активным, если он жив и не оглушен
                is_alive = ally.current_hp > 0
                is_staggered = ally.is_staggered() if callable(getattr(ally, 'is_staggered', None)) else False
                is_not_staggered = not is_staggered
                
                logger.log(
                    f"🔍 Ally {ally_name}: HP={ally.current_hp}, Staggered={is_staggered}, Active={is_alive and is_not_staggered}",
                    LogLevel.VERBOSE, "Passive"
                )
                
                if is_alive and is_not_staggered:
                    active_allies += 1
            
            logger.log(
                f"🔍 Solitude: {unit.name} has {active_allies} active allies",
                LogLevel.VERBOSE, "Passive"
            )
            
            return active_allies > 0
            
        except Exception as e:
            logger.log(f"⚠️ Solitude check error: {e}", LogLevel.VERBOSE, "Passive")
            return False

    def on_round_start(self, unit, *args, **kwargs):
        """Применяет бонусы в начале раунда, если нет активных союзников."""
        if not self._has_active_allies(unit):
            # Применяем статусы на весь раунд
            unit.add_status("strength", 2, duration=1)
            unit.add_status("haste", 2, duration=1)
            unit.add_status("endurance", 2, duration=1)
            
            logger.log(
                f"⚔️ {self.name}: {unit.name} сражается в одиночку! (+2 Сила/Спешка/Стойкость)",
                LogLevel.NORMAL, "Passive"
            )
