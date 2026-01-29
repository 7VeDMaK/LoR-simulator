import copy
import random

from core.enums import DiceType, CardType
from core.library import Library
from core.logging import logger, LogLevel
from logic.character_changing.passives.base_passive import BasePassive

# ======================================================================================
# ВЕТКА 2: ЛУЧШИЙ ИЗ ЛУЧШИХ (The Honored One)
# ======================================================================================

# ==========================================
# 2.1 Врожденный дар
# ==========================================
class TalentInnateTalent(BasePassive):
    id = "innate_talent"
    name = "Врожденный дар"
    description = (
        "Прокачивая данный талант, персонаж вкладывает в данную ветку еще 4 таланта.\n"
        "Эффект: Вы получаете бонус +1 ко всем характеристикам и +2 к навыкам.\n"
        "Каждые 10 уровней персонажа этот бонус увеличивается (Максимум +4 / +8 на 40 уровне)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        # Базовый стек: 1 (1-9 ур), 2 (10-19 ур) и т.д.
        base_stack = 1 + (unit.level // 10)

        attr_bonus = min(base_stack, 5)        # Максимум +5
        skill_bonus = min(base_stack * 2, 10)  # Максимум +10

        # Логируем расчет (на уровне DEBUG/VERBOSE, чтобы не спамить)
        logger.log(
            f"🧬 {self.name}: Уровень {unit.level} -> Бонус Характеристик +{attr_bonus}, Навыков +{skill_bonus}",
            LogLevel.VERBOSE,
            "Talent"
        )

        return {
            "all_attributes": attr_bonus,
            "all_skills": skill_bonus
        }


# ==========================================
# 2.2 Глаза Небожителя
# ==========================================
class TalentCelestialEyes(BasePassive):
    id = "celestial_eyes"
    name = "Глаза Небожителя"
    description = (
        "Активно (Цель - Враг): Проводит глубокий анализ цели.\n"
        "Бросок: 1d20 + Мудрость против 1d20 + Мудрость цели.\n"
        "Чем выше разница, тем больше информации раскрывается:\n"
        "5+: Статус | 10+: Карты Т1 | 15+: Карты Т2 + Предметы\n"
        "20+: Карты Т3 + Оружие | 25+: Карты Т4+ + Аугментации | 30+: Таланты | 35+: Пассивки.\n"
        "Пассивно: +2 к проверкам навыков (Skill Checks)."
    )
    is_active_ability = True
    selection_type = "enemy"
    cooldown = 1

    def modify_skill_check_result(self, unit, stat_key, current_value) -> int:
        """
        Пассивный эффект: +2 к любым проверкам навыков.
        """
        logger.log(f"👁️ {self.name}: +2 к проверке '{stat_key}'", LogLevel.VERBOSE, "Talent")
        return current_value + 2

    def activate(self, unit, log_func, **kwargs):
        # Импортируем реестры ВНУТРИ функции, чтобы избежать Circular Import
        from logic.character_changing.augmentations.augmentations import AUGMENTATION_REGISTRY
        from logic.character_changing.passives import PASSIVE_REGISTRY
        from logic.character_changing.talents import TALENT_REGISTRY

        # 1. Получаем цель
        target = kwargs.get("target")
        if not target:
            if log_func: log_func("⚠️ Выберите врага для анализа.")
            return False

        # 2. Расчет бросков
        my_wis = unit.attributes.get("wisdom", 0)
        my_roll = random.randint(1, 20) + my_wis

        target_wis = getattr(target, "attributes", {}).get("wisdom", 0)
        target_roll = random.randint(1, 20) + target_wis

        diff = my_roll - target_roll

        # 3. Подготовка данных (Сортировка карт и предметов)
        deck_ids = getattr(target, "deck", [])
        cards_by_tier = {1: [], 2: [], 3: [], 4: []}
        found_items = []

        for cid in deck_ids:
            card = Library.get_card(cid)
            if card:
                # [FIX] Проверяем, является ли карта предметом
                is_item = False
                if card.card_type == CardType.ITEM:
                    is_item = True
                elif isinstance(card.card_type, str) and card.card_type.upper() == "ITEM":
                    is_item = True

                if is_item:
                    # Если предмет — добавляем в список предметов, а НЕ в карты по тирам
                    found_items.append(card.name)
                else:
                    # Если обычная карта — сортируем по тиру
                    t = card.tier
                    tier_key = 4
                    if t <= 1:
                        tier_key = 1
                    elif t == 2:
                        tier_key = 2
                    elif t == 3:
                        tier_key = 3
                    cards_by_tier[tier_key].append(card.name)

        # Хелпер для получения имен из ID
        def resolve_names(ids_list, registry):
            names = []
            for i in ids_list:
                obj = registry.get(i)
                if obj:
                    names.append(obj.name)
                else:
                    names.append(i)
            return ", ".join(names) if names else "Нет"

        # 4. Формирование отчета
        header = f"👁️ **АНАЛИЗ**: {unit.name} [{my_roll}] vs {target.name} [{target_roll}] (Разница: {diff})"
        details = []

        # Базовая информация
        bio = getattr(target, "biography", "") or getattr(target, "description", "Нет описания")
        details.append(f"📜 **Био**: {bio}")

        # ТИР 1: Фракция (UnitType) и Ранг (5+)
        if diff >= 3:
            u_type = getattr(target, "unit_type", "Неизвестно")
            rank = getattr(target, "rank", 9)
            details.append(f"🏴 **Тип/Ранг**: {u_type} | Ранг {rank}")

        # ТИР 2: Слабые карты (Tier 1) (10+)
        if diff >= 7:
            c_str = ", ".join(cards_by_tier[1]) if cards_by_tier[1] else "Нет"
            details.append(f"🃏 **Слабые карты (T1)**: {c_str}")

        # ТИР 3: Средние карты (Tier 2) + Предметы (15+)
        if diff >= 12:
            c_str = ", ".join(cards_by_tier[2]) if cards_by_tier[2] else "Нет"
            details.append(f"🃏 **Средние карты (T2)**: {c_str}")

            # Добавляем предметы из отдельного списка unit.consumables (если есть)
            extra_items = getattr(target, "consumables", [])
            for it in extra_items:
                c = Library.get_card(it)
                name = c.name if c else it
                if name not in found_items:
                    found_items.append(name)

            item_str = ", ".join(found_items) if found_items else "Нет"
            details.append(f"💊 **Предметы**: {item_str}")

        # ТИР 4: Сильные карты (Tier 3) + Оружие (20+)
        if diff >= 16:
            c_str = ", ".join(cards_by_tier[3]) if cards_by_tier[3] else "Нет"
            details.append(f"🃏 **Сильные карты (T3)**: {c_str}")

            weapon_id = getattr(target, "weapon_id", "none")
            weapon_name = "Нет оружия"
            from logic.weapon_definitions import WEAPON_REGISTRY
            if weapon_id in WEAPON_REGISTRY:
                weapon_name = WEAPON_REGISTRY[weapon_id].name
            details.append(f"⚔️ **Оружие**: {weapon_name}")

        # ТИР 5: Мощные карты (Tier 4+) + Аугментации (25+)
        if diff >= 20:
            c_str = ", ".join(cards_by_tier[4]) if cards_by_tier[4] else "Нет"
            details.append(f"🃏 **Мощные карты (T4+)**: {c_str}")

            augs = getattr(target, "augmentations", [])
            aug_str = resolve_names(augs, AUGMENTATION_REGISTRY)
            details.append(f"🦾 **Аугментации**: {aug_str}")

        # ТИР 6: Таланты (30+)
        if diff >= 25:
            talents = getattr(target, "talents", [])
            tal_str = resolve_names(talents, TALENT_REGISTRY)
            details.append(f"🧠 **Таланты**: {tal_str}")

        # ТИР 7: Пассивные навыки (35+)
        if diff >= 30:
            passives = getattr(target, "passives", [])
            pas_str = resolve_names(passives, PASSIVE_REGISTRY)
            details.append(f"⚛️ **Пассивки**: {pas_str}")

        # Вывод
        if log_func:
            log_func(header)
            for line in details:
                log_func(line)

        logger.log(f"👁️ Celestial Eyes: Full Scan on {target.name} (Diff {diff})", LogLevel.NORMAL, "Talent")
        unit.cooldowns[self.id] = self.cooldown
        return True


# ==========================================
# 2.3 Разрез Пустоты
# ==========================================
class TalentVoidCleave(BasePassive):
    id = "void_cleave"
    name = "Разрез Пустоты"
    description = (
        "Удар, который игнорирует плотность материи и стойкость духа.\n"
        "При расчете урона к множителю сопротивления цели прибавляется +0.1.\n"
        "(Пример: 0.5 (Endured) -> 0.6, цель получает больше урона)."
    )
    is_active_ability = False

    def on_calculate_damage_multiplier(self, unit, multiplier, **kwargs):
        """
        [FIX] Исправлена сигнатура метода.
        Аргументы: unit (attacker), multiplier (current_res), kwargs (attacker, target, dice...)
        """
        new_mult = multiplier + 0.1
        logger.log(
            f"⚔️ {self.name}: Сопротивление цели изменено ({multiplier:.2f} -> {new_mult:.2f})",
            LogLevel.VERBOSE,
            "Talent"
        )
        return new_mult


# ==========================================
# 2.4 Золотая Репутация
# ==========================================
class TalentGoldenReputation(BasePassive):
    id = "golden_reputation"
    name = "Золотая Репутация"
    description = (
        "Ваше имя известно в высших кругах, а статус открывает многие двери.\n"
        "Эффект: Вы получаете скидку 20% у торговцев и особые реплики в диалогах.\n"
        "Дает +5 К красноречию"
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {"eloquence": 5}


# ==========================================
# 2.5 Мгновенное Озарение
# ==========================================
class TalentCopycatInsight(BasePassive):
    id = "copycat_insight"
    name = "Мгновенное Озарение"
    description = (
        "Достаточно одного взгляда, чтобы превзойти чужую технику.\n"
        "Активно (КД: 3 сцены): Выберите цель (Враг/Союзник) и одну из её доступных карт.\n"
        "Вы получаете временную копию этой карты в руку на этот раунд.\n"
        "Карта исчезает при использовании или в конце раунда."
    )
    is_active_ability = True
    selection_type = "all"
    requires_card_selection = True
    cooldown = 3

    def on_round_end(self, unit, log_func, **kwargs):
        """
        Удаляем временные карты, если они не были использованы за ход.
        """
        temp_cards = unit.memory.get("copycat_active_cards", [])
        if not temp_cards:
            return

        removed_count = 0
        new_deck = []

        # Пересобираем колоду без временных карт этого таланта
        for card_id in unit.deck:
            if card_id in temp_cards:
                removed_count += 1
                # Удаляем также из глобальной библиотеки, чтобы не засорять память
                if hasattr(Library, "delete_card"):
                    Library.delete_card(card_id)
            else:
                new_deck.append(card_id)

        unit.deck = new_deck
        unit.memory["copycat_active_cards"] = []  # Очищаем список

        if removed_count > 0 and log_func:
            # log_func здесь обычно нет (это пассивный хук), но для структуры оставим
            pass

    def activate(self, unit, log_func, **kwargs):
        target = kwargs.get("target")
        card_id = kwargs.get("selected_card_id")

        if not target or not card_id:
            if log_func: log_func("⚠️ Нужно выбрать цель и карту!")
            return False

        original_card = Library.get_card(card_id)
        if not original_card:
            if log_func: log_func(f"❌ Ошибка: карта {card_id} не найдена.")
            return False

        # 1. Создаем копию
        copied_card = copy.deepcopy(original_card)

        # 2. Настраиваем свойства "Одноразовости"
        # exhaust_on_use удалит карту из руки ПОСЛЕ использования в бою
        copied_card.exhaust_on_use = True
        copied_card.description = f"[Временная] {copied_card.description}"

        # 3. Регистрируем уникальную временную карту
        temp_id = f"{card_id}_copy_{unit.name}_{len(unit.deck)}_{random.randint(100, 999)}"

        # Используем метод регистрации (если добавлен) или обычный register + ручная установка ID
        copied_card.id = temp_id
        Library.register(copied_card)  # Регистрируем в памяти

        # 4. Добавляем в руку
        unit.deck.append(temp_id)

        # 5. Запоминаем ID, чтобы удалить в конце раунда (если не юзнули)
        if "copycat_active_cards" not in unit.memory:
            unit.memory["copycat_active_cards"] = []
        unit.memory["copycat_active_cards"].append(temp_id)

        if log_func:
            log_func(f"👁️ **Озарение**: Скопирована '{original_card.name}'!")
            log_func(f"⏳ Карта исчезнет в конце раунда.")

        logger.log(f"👁️ Copycat: {unit.name} copied {card_id} as {temp_id}", LogLevel.NORMAL, "Talent")

        unit.cooldowns[self.id] = self.cooldown
        return True

# ======================================================================================
# РЕФЕРЕНСНЫЕ ТАЛАНТЫ (2.6 - 2.10)
# ======================================================================================

# ==========================================
# 2.6 Пример для подражания!
# ==========================================
class TalentIdealStandard(BasePassive):
    id = "ideal_standard"
    name = "Пример для подражания!"
    description = (
        "В битвах с союзниками получаете баффы за каждого:\n"
        "1-й союзник: +2 Endurance | 2-й: +2 Attack Power | 3-й: +2 Haste\n"
        "4-й и 5-й: +1 к каждому баффу (макс 5 союзников).\n"
        "При оглушении: союзники получают +3 Vulnerable, Attack Power Down, Bind на 2 хода."
    )
    is_active_ability = False

    def _count_active_allies(self, unit):
        """Подсчитывает активных союзников на поле боя (живые и не оглушенные)."""
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
                logger.log(f"🔍 Ideal Standard: {unit.name} team not found", LogLevel.VERBOSE, "Talent")
                return 0
            
            # Подсчитываем активных союзников (не считая себя)
            active_allies = 0
            for ally in my_team:
                # Пропускаем самого себя (проверяем по имени)
                if ally.name == unit.name:
                    continue
                
                # Считаем союзника активным, если он жив и не оглушен
                is_alive = ally.current_hp > 0
                is_staggered = ally.is_staggered() if callable(getattr(ally, 'is_staggered', None)) else False
                
                if is_alive and not is_staggered:
                    active_allies += 1
            
            # Максимум 5 союзников
            return min(active_allies, 5)
            
        except Exception as e:
            logger.log(f"⚠️ Ideal Standard count error: {e}", LogLevel.VERBOSE, "Talent")
            return 0

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
                return []
            
            # Собираем активных союзников
            allies = []
            for ally in my_team:
                if ally.name == unit.name:
                    continue
                
                is_alive = ally.current_hp > 0
                is_staggered = ally.is_staggered() if callable(getattr(ally, 'is_staggered', None)) else False
                
                if is_alive and not is_staggered:
                    allies.append(ally)
            
            return allies
            
        except Exception as e:
            logger.log(f"⚠️ Ideal Standard allies error: {e}", LogLevel.VERBOSE, "Talent")
            return []

    def on_round_start(self, unit, *args, **kwargs):
        """
        В начале раунда выдает баффы в зависимости от количества активных союзников.
        Также сбрасывает флаг дебаффов для новых падений.
        """
        # Сбрасываем флаг дебаффов (позволяет таланту срабатывать при каждом новом падении)
        unit.memory["ideal_standard_debuff_applied"] = False
        
        alive_count = self._count_active_allies(unit)
        
        if alive_count == 0:
            return
        
        # Базовые баффы
        endurance_bonus = 0
        attack_power_bonus = 0
        haste_bonus = 0
        
        # 1-й союзник: +2 Endurance
        if alive_count >= 1:
            endurance_bonus = 2
        
        # 2-й союзник: +2 Attack Power
        if alive_count >= 2:
            attack_power_bonus = 2
        
        # 3-й союзник: +2 Haste
        if alive_count >= 3:
            haste_bonus = 2
        
        # 4-й и 5-й союзники: +1 к каждому баффу
        extra_allies = max(0, alive_count - 3)
        if extra_allies > 0:
            endurance_bonus += extra_allies
            attack_power_bonus += extra_allies
            haste_bonus += extra_allies
        
        # Применяем статусы на раунд
        if endurance_bonus > 0:
            unit.add_status("endurance", endurance_bonus, duration=1)
        if attack_power_bonus > 0:
            unit.add_status("strength", attack_power_bonus, duration=1)
        if haste_bonus > 0:
            unit.add_status("haste", haste_bonus, duration=1)
        
        # Формируем описание баффов для лога
        buffs_desc = []
        if endurance_bonus > 0:
            buffs_desc.append(f"+{endurance_bonus} Endurance")
        if attack_power_bonus > 0:
            buffs_desc.append(f"+{attack_power_bonus} Power")
        if haste_bonus > 0:
            buffs_desc.append(f"+{haste_bonus} Haste")
        
        logger.log(
            f"👥 {self.name}: {unit.name} с {alive_count} союзниками -> {', '.join(buffs_desc)}",
            LogLevel.NORMAL,
            "Talent"
        )

    def on_take_damage(self, *args, **kwargs):
        """
        Отслеживаем момент падения персонажа (когда HP опускается до 0).
        Если персонаж упал, применяем дебаффы к союзникам СРАЗУ.
        НЕ срабатывает, если активна Сюжетная броня (статус main_character_shell).
        """
        # Извлекаем аргументы
        unit = args[0] if len(args) > 0 else kwargs.get("unit")
        damage = args[1] if len(args) > 1 else kwargs.get("damage", 0)
        
        if not unit:
            return damage
        
        # Проверяем наличие статуса Сюжетной брони (талант 2.8)
        has_plot_armor = unit.get_status("main_character_shell") > 0
        
        # УСЛОВИЕ АКТИВАЦИИ: Статуса main_character_shell НЕТ
        if has_plot_armor:
            # Сюжетная броня активна - дебаффы к союзникам НЕ применяются
            logger.log(
                f"👥 {self.name}: {unit.name} защищён Сюжетной бронёй - дебаффы союзникам не применены",
                LogLevel.VERBOSE,
                "Talent"
            )
            return damage
        
        # Сюжетной брони нет - проверяем условия для дебаффов
        # Проверяем, приведет ли урон к падению персонажа
        will_fall = unit.current_hp - damage <= 0
        
        # Проверяем, не применяли ли мы уже дебаффы за это падение
        already_debuffed = unit.memory.get("ideal_standard_debuff_applied", False)
        
        if will_fall and not already_debuffed:
            # Помечаем, что дебаффы будут применены
            unit.memory["ideal_standard_debuff_applied"] = True
            
            # Получаем активных союзников и применяем дебаффы СРАЗУ
            allies = self._get_active_allies(unit)
            if allies:
                debuffed_count = 0
                for ally in allies:
                    # Применяем негативные статусы напрямую на союзников (демотивация)
                    ally.add_status("vulnerable", 3, duration=2)
                    ally.add_status("attack_power_down", 3, duration=2)
                    ally.add_status("bind", 3, duration=2)
                    debuffed_count += 1
                
                if debuffed_count > 0:
                    logger.log(
                        f"👥 {self.name}: {unit.name} получает летальный урон! "
                        f"{debuffed_count} союзников демотивированы! (+3 Vulnerable/-3 Power/+3 Bind на 2 хода)",
                        LogLevel.NORMAL,
                        "Talent"
                    )
        
        return damage




# ==========================================
# 2.7 Насмешка
# ==========================================
class TalentArrogantTaunt(BasePassive):
    id = "arrogant_taunt"
    name = "Насмешка"
    description = (
        "+5 к Красноречию.\n"
        "Активно: Выберите персонажа на поле боя.\n"
        "Цель получает +2 Power и +4 Vulnerable на 1 ход.\n"
        "(Можно использовать на себя или союзников/врагов)"
    )
    is_active_ability = True
    cooldown = 1  # Кулдаун 1 ход

    def on_calculate_stats(self, unit) -> dict:
        return {"eloquence": 5}

    def _get_battle_targets(self):
        """Получает всех юнитов на поле боя."""
        try:
            from ui.simulator.logic.simulator_logic import get_teams
            l_team, r_team = get_teams()
            return (l_team or []) + (r_team or [])
        except Exception:
            return []

    @property
    def conversion_options(self):
        """Список всех доступных целей (включая себя)."""
        options = {}
        for u in self._get_battle_targets():
            if not u or not hasattr(u, "name"):
                continue
            # Показываем только живых персонажей
            if getattr(u, "current_hp", 0) > 0:
                options[u.name] = f"{u.name} ({u.current_hp} HP)"
        return options

    def activate(self, unit, log_func, choice_key=None, **kwargs):
        """
        Накладывает +2 Power и +4 Vulnerable на выбранного персонажа на 1 ход.
        """
        # Если цель не выбрана
        if not choice_key:
            if log_func:
                opts = ", ".join(self.conversion_options.values()) or "нет доступных целей"
                log_func(f"⚠️ Выберите цель для {self.name}: {opts}")
            return False

        # Ищем цель по имени
        target = None
        for u in self._get_battle_targets():
            if u and getattr(u, "name", None) == choice_key:
                target = u
                break

        if not target:
            if log_func:
                log_func(f"⚠️ Цель не найдена: {choice_key}")
            return False

        # Проверяем, что цель жива
        if getattr(target, "current_hp", 0) <= 0:
            if log_func:
                log_func(f"⚠️ {target.name} не может быть целью (HP <= 0)")
            return False

        # Применяем баффы/дебаффы
        target.add_status("strength", 2, duration=1)
        target.add_status("vulnerable", 4, duration=1)
        
        if log_func:
            target_text = "себя" if target is unit else target.name
            log_func(
                f"😤 **{self.name}**: {unit.name} → {target_text}: "
                f"+2 Power, +4 Vulnerable (1 ход)"
            )
        
        logger.log(
            f"😤 Arrogant Taunt: {unit.name} applied to {target.name} (+2 Power, +4 Vulnerable)",
            LogLevel.NORMAL,
            "Talent"
        )
        
        unit.cooldowns[self.id] = self.cooldown
        return True


# ==========================================
# 2.8 Сюжетная броня
# ==========================================
class TalentMainCharacterShell(BasePassive):
    id = "main_character_shell"
    name = "Сюжетная броня"
    description = (
        "+25% к значению Выдержки.\n"
        "HP и Stagger не могут опуститься ниже 1 (одноразово на всю битву)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {"stagger_resist_pct": 25}

    def on_combat_start(self, unit, *args, **kwargs):
        """
        Накладываем статус защиты в начале каждого боя.
        """
        # Сбрасываем флаг использования для нового боя
        unit.memory["main_character_shell_used"] = False
        
        # Накладываем защитный статус
        unit.add_status("main_character_shell", 1, duration=999)
        logger.log(
            f"🛡️ Main Character Shell: {unit.name} activated plot armor",
            LogLevel.NORMAL,
            "Talent"
        )
    
    def on_scene_start(self, unit, *args, **kwargs):
        """
        В начале каждой новой сцены проверяем, использовалась ли защита.
        Если да - больше не восстанавливаем статус.
        Если нет - восстанавливаем статус (он мог быть удален системой).
        """
        was_used = unit.memory.get("main_character_shell_used", False)
        
        if was_used:
            # Защита уже использовалась - не восстанавливаем
            logger.log(
                f"🛡️ Main Character Shell: {unit.name} protection already consumed",
                LogLevel.VERBOSE,
                "Talent"
            )
        else:
            # Защита еще не использовалась - восстанавливаем статус на случай, если он был удален
            current_status = unit.get_status("main_character_shell")
            if current_status == 0:
                unit.add_status("main_character_shell", 1, duration=999)
                logger.log(
                    f"🛡️ Main Character Shell: {unit.name} protection restored at scene start",
                    LogLevel.VERBOSE,
                    "Talent"
                )
    
    def on_take_damage(self, *args, **kwargs):
        """
        Отслеживаем момент срабатывания защиты.
        Когда HP падает до 1 из-за защиты - помечаем, что защита была использована.
        """
        unit = args[0] if len(args) > 0 else kwargs.get("unit")
        damage = args[1] if len(args) > 1 else kwargs.get("damage", 0)
        
        if not unit:
            return damage
        
        # Проверяем, есть ли активная защита
        has_protection = unit.get_status("main_character_shell") > 0
        
        # Если защита активна и урон привел бы к смерти
        if has_protection and unit.current_hp - damage <= 0:
            # Помечаем, что защита использована (будет удалена в начале следующей сцены)
            unit.memory["main_character_shell_used"] = True
            logger.log(
                f"🛡️ Main Character Shell: {unit.name} protection triggered and will be removed next scene",
                LogLevel.NORMAL,
                "Talent"
            )
        
        return damage


# ==========================================
# 2.9 Muted
# ==========================================
class TalentSilenceExecution(BasePassive):
    id = "silence_execution"
    name = "Muted"
    description = (
        "Активно (КД: 5 сцен): Выберите врага и кубик его скорости для уничтожения.\n"
        "Нельзя уничтожить кубики с картами 3+ уровня или массовыми атаками."
    )
    is_active_ability = True
    cooldown = 5


# ==========================================
# 2.10 Да мы только начали!
# ==========================================
class TalentJustWarmingUp(BasePassive):
    id = "just_warming_up"
    name = "Да мы только начали!"
    description = "За каждое проигранное столкновение: +1 к Силе (Strength) в следующей сцене на один ход."
    is_active_ability = False

    def on_clash_lose(self, ctx, **kwargs):
        """
        Считаем количество проигранных столкновений.
        """
        unit = ctx.source
        
        # Увеличиваем счетчик проигрышей
        if "lost_clashes" not in unit.memory:
            unit.memory["lost_clashes"] = 0
        
        unit.memory["lost_clashes"] += 1
        
        ctx.log.append(
            f"🔥 **{self.name}**: {unit.name} набирается опыта... (Проиграно: {unit.memory['lost_clashes']})"
        )
        
        logger.log(
            f"🔥 Just Warming Up: {unit.name} lost clash, total losses = {unit.memory['lost_clashes']}",
            LogLevel.VERBOSE,
            "Talent"
        )

    def on_scene_start(self, unit, log_func, **kwargs):
        """
        В начале новой сцены дает +Strength равный количеству проигранных столкновений.
        """
        lost_count = unit.memory.get("lost_clashes", 0)
        if lost_count <= 0:
            return
        
        # Добавляем Strength (мощь атакующих кубов: Slash, Blunt, Pierce)
        unit.add_status("strength", lost_count, duration=1)
        
        if log_func:
            log_func(f"🔥 **{self.name}**: {unit.name} разогрелся! (+{lost_count} Strength на 1 ход)")
        
        logger.log(
            f"🔥 Just Warming Up: {unit.name} gains +{lost_count} Strength for 1 turn",
            LogLevel.NORMAL,
            "Talent"
        )
        
        # Сбрасываем счетчик проигрышей после использования
        unit.memory["lost_clashes"] = 0


# ======================================================================================
# ОПЦИОНАЛЬНЫЕ ТАЛАНТЫ
# ======================================================================================

# ==========================================
# Опц. А: Искра Сверхчеловека (Black Flash)
# ==========================================
class TalentBlackFlashSpark(BasePassive):
    id = "black_flash_spark"
    name = "Искра Сверхчеловека (Black Flash)"
    description = (
        "Когда концентрация достигает пика, каждый удар становится критическим.\n"
        "Мин. или Макс. базовое значение кубика наносит x1.5 урона."
    )
    is_active_ability = False

    def on_calculate_damage_multiplier(self, unit, multiplier, **kwargs):
        """
        Увеличивает множитель урона в 1.5 раза, если выпал мин. или макс. ролл.
        """
        dice = kwargs.get("dice")

        # Проверяем, что кубик есть и у него есть результат
        if dice and hasattr(dice, 'result'):
            # Сравниваем результат (result) с границами кубика
            if dice.result == dice.min_val or dice.result == dice.max_val:
                new_mult = multiplier * 1.5
                logger.log(
                    f"⚫ **BLACK FLASH**: {unit.name} поймал ритм! (Ролл: {dice.result}) Урон x1.5",
                    LogLevel.NORMAL,
                    "Talent"
                )
                return new_mult

        return multiplier


# ==========================================
# Опц. Б: Синяя Вспышка
# ==========================================
class TalentBlueFlashStep(BasePassive):
    id = "blue_flash_step"
    name = "Синяя Вспышка (Опц.)"
    description = (
        "Разница скоростей >= 2: Помеха врагу на первый кубик.\n"
        "Разница скоростей >= 6: Первый кубик врага ломается (Break)."
    )
    is_active_ability = False

    def on_clash_start(self, ctx, **kwargs):
        diff = ctx.source.speed - ctx.target.speed
        if diff >= 6:
            if ctx.opponent_dice:
                ctx.opponent_dice.is_broken = True
                ctx.log.append("🔵 **Синяя Вспышка**: Скорость за гранью! Кубик врага уничтожен.")
                logger.log(f"🔵 Blue Flash: Broken enemy dice due to speed diff ({diff})", LogLevel.NORMAL, "Talent")
        elif diff >= 2:
            ctx.add_opponent_debuff("disadvantage")
            ctx.log.append("🔵 **Синяя Вспышка**: Враг не поспевает (Помеха).")
            logger.log(f"🔵 Blue Flash: Applied disadvantage (diff {diff})", LogLevel.VERBOSE, "Talent")