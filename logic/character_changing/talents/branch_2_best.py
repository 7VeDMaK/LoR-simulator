import copy
import random

from core.enums import DiceType, CardType
from core.library import Library
from core.logging import logger, LogLevel
from logic.character_changing.passives.base_passive import BasePassive


# ======================================================================================
# КОРЕНЬ (ROOT)
# ======================================================================================

class TalentScanner(BasePassive):
    id = "scanner"
    name = "2.0 Сканер"
    description = (
        "Пассивно: Вы всегда видите точные значения HP, SP, Stagger и Сопротивления всех врагов.\n"
        "Вы видите стрелки агрессии (кто кого бьет) до выбора карт."
    )
    is_active_ability = False


# ======================================================================================
# ВЕТКА А: "ИДЕАЛ" (The Paragon) — Подготовка и Тело
# ======================================================================================

class TalentDeepPockets(BasePassive):
    id = "deep_pockets"
    name = "2.1.A Походный Рюкзак"
    description = (
        "Ваш лимит колоды увеличивается на +1 карту каждого ранга.\n"
        "Вы можете менять колоду в любой момент вне боя."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {"deck_size_bonus": 3}


class TalentLogistics(BasePassive):
    id = "logistics"
    name = "2.2.A Эффективная Логистика"
    description = (
        "Лимит колоды увеличивается ещё на +1 за каждые 10 очков Интеллекта.\n"
        "Пассивно: в первом ходу КД всех карт снижается на 1"
    )
    is_active_ability = False


class TalentAceOfAllTrades(BasePassive):
    id = "ace_of_all_trades"
    name = "2.3.A Туз всех мастей"
    description = (
        "Вы получаете бонус к МИНИМАЛЬНОМУ значению всех кубиков.\n"
        "Бонус равен: (Сумма всех ваших атрибутов / 40).\n"
        "Пример: Сумма статов 120 -> +3 к мин. роллу (1~10 станет 4~10)."
    )
    is_active_ability = False


class TalentSynergy(BasePassive):
    id = "skill_synergy"
    name = "2.4.A Синергия Навыков"
    description = (
        "За каждые 2 навыка уровня 'Мастер' (10+), вы получаете +4 HP и +4 SP.\n"
        "Ваше мастерство закаляет дух и тело."
    )
    is_active_ability = False


class TalentTireless(BasePassive):
    id = "tireless_paragon"
    name = "2.5.A Неутомимый"
    description = (
        "Завершение любой боевой сцены полностью восстанавливает Stagger (Выдержку).\n"
        "Иммунитет к эффектам 'Обездвиживание' (Bind) и 'Медлительность'."
    )
    is_active_ability = False


class TalentMomentum(BasePassive):
    id = "momentum"
    name = "2.6.A На Волне"
    description = (
        "Если в прошлом раунде вы выиграли все столкновения (Clash Win),\n"
        "в этом раунде вы получаете +1 Мощи (Power) и +1 Скорости (Haste)."
    )
    is_active_ability = False


class TalentLimitBreaker(BasePassive):
    id = "limit_breaker"
    name = "2.7.A Предел Совершенства"
    description = (
        "Максимальный лимит (кап) прокачки атрибутов повышается на +10.\n"
        "Ваши тренировки выходят за грань человеческих возможностей."
    )
    is_active_ability = False


class TalentPlotArmor(BasePassive):
    id = "plot_armor"
    name = "2.8.A Сюжетная Броня"
    description = (
        "1 раз за вылазку: При получении летального урона вы остаетесь с 1 HP,\n"
        "получаете 'Неуязвимость' до конца раунда и полностью восстанавливаете Stagger."
    )
    is_active_ability = False


class TalentUniversalSoldier(BasePassive):
    id = "universal_soldier"
    name = "2.9.A Универсальный Солдат"
    description = (
        "Пассивно: Если сумма ваших атрибутов > 120 (уровень ~10-12), вы получаете +1 Слот Действия в начале боя (на 3 хода).\n"
        "Если сумма > 180 (уровень ~20), Слот Действия дается навсегда."
    )
    is_active_ability = False


class TalentDominant(BasePassive):
    id = "dominant"
    name = "2.10.A Доминант (Финал А)"
    description = (
        "Если ваша сумма статов выше суммы статов врага:\n"
        "Вы наносите +25% Урона и получаете -25% Урона от него.\n"
        "Ваши атаки нельзя перехватить (Unopposed), если вы бьете первым."
    )
    is_active_ability = False


# ======================================================================================
# ВЕТКА Б: "КУКЛОВОД" (The Puppeteer) — Разум и Манипуляция
# ======================================================================================

class TalentViciousMockery(BasePassive):
    id = "vicious_mockery"
    name = "2.1.B Злой Язык"
    description = (
        "Красноречие считается боевым атрибутом.\n"
        "Любая ваша атака наносит дополнительный урон по Рассудку (SP),\n"
        "равный (Красноречие / 5)."
    )
    is_active_ability = False

    # def on_hit(self, ctx: RollContext, **kwargs):
    #     """
    #     Срабатывает при успешном попадании атакой.
    #     Наносит доп. урон по SP врага.
    #     """
    #     target = context.target
    #     if not target: return
    #
    #     # 1. Получаем значение Красноречия (Eloquence)
    #     # skill_value берется из unit.skills (словарь)
    #     eloquence = unit.skills.get("eloquence", 0)
    #
    #     # 2. Считаем урон
    #     sp_damage = int(eloquence / 5)
    #
    #     if sp_damage > 0:
    #         # Логируем
    #         if context.log is not None:
    #             context.log.append(f"👅 **Злой Язык**: {sp_damage} SP урона")
    #
    #         logger.log(f"👅 Vicious Mockery ({unit.name}) deals {sp_damage} SP dmg to {target.name}", LogLevel.VERBOSE,
    #                    "Talent")
    #
    #         # 3. Наносим урон по SP
    #         # Используем внутреннюю функцию, она обрабатывает смерть/панику корректно
    #         _apply_resource_damage(target, sp_damage, "sp", context)


class TalentVerbalBarrier(BasePassive):
    id = "verbal_barrier"
    name = "2.2.B Словесный Барьер"
    description = (
        "При использовании Защиты (Block/Evade) вы получаете бонус +1 к кубику\n"
        "за каждые 5 очков Красноречия.\n"
        "При использовании Атаки вы получаете бонус +1 к кубику\n"
        "за каждые 5 очков Интеллекта."
    )
    is_active_ability = False

    def modify_dice_value(self, unit, dice_value: int, dice_obj, context) -> int:
        """
        Модифицирует значение кубика перед броском.
        """
        if not dice_obj:
            return dice_value

        # Получаем строковое имя типа кубика (SLASH, BLOCK и т.д.)
        d_type = dice_obj.dtype.name

        # 1. ЗАЩИТА (BLOCK, EVADE) -> Зависит от Красноречия
        if d_type in ["BLOCK", "EVADE"]:
            eloquence = unit.skills.get("eloquence", 0)
            bonus = int(eloquence / 5)  # +1 за каждые 5 очков
            return dice_value + bonus

        # 2. АТАКА (SLASH, PIERCE, BLUNT) -> Зависит от Интеллекта
        elif d_type in ["SLASH", "PIERCE", "BLUNT"]:
            # Используем Интеллект как боевой стат для "умника"
            intellect = unit.attributes.get("intellect", 0)
            bonus = int(intellect / 5)
            return dice_value + bonus

        return dice_value

<<<<<<< HEAD
class TalentTacticalAnalysis(BasePassive):
    id = "tactical_analysis"
    name = "2.3.B Тактический Анализ (Ур. 2)"
=======
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
    name = "2.3 Разрез Пустоты"
>>>>>>> c916355f0910085208ccc685d7a0ae93ec550744
    description = (
        "Расширение модуля Сканера.\n"
        "Пассивно: Вы видите ПАССИВНЫЕ способности врага и их описания.\n"
        "Вы видите диапазон Скорости (Speed Dice) и состав колоды врага (какие карты у него есть)."
    )
    is_active_ability = False

<<<<<<< HEAD

class TalentKnowYourEnemy(BasePassive):
    id = "know_your_enemy"
    name = "2.4.B Познай Врага"
    description = (
        "Если вы атакуете врага, чьи статы вам известны (через Сканер),\n"
        "вы получаете +1 Clash Power.\n"
        "Бонус растет на +1 каждый раунд боя с этим врагом (макс +5)."
    )
    is_active_ability = False


class TalentCardShuffler(BasePassive):
    id = "card_shuffler"
    name = "2.5.B Карточный Шулер"
    description = (
        "Активно (1 раз за бой): Выберите 2 карты в вашем сбросе.\n"
        "Они мгновенно возвращаются в руку, их стоимость становится 0 на этот ход."
    )
    is_active_ability = True


class TalentPredictiveAlgo(BasePassive):
    id = "predictive_algo"
    name = "2.6.B Предиктивные Алгоритмы (Ур. 3)"
    description = (
        "Финальное улучшение аналитического модуля.\n"
        "В начале раунда вы видите СТРЕЛКИ намерений (кто кого бьет) и\n"
        "конкретные КАРТЫ, которые враг положил в слоты, до фазы битвы."
    )
    is_active_ability = False


class TalentExposeWeakness(BasePassive):
    id = "expose_weakness"
    name = "2.7.B Вскрытие Защиты"
=======
    def on_calculate_damage_multiplier(self, unit, multiplier, **kwargs):
        """
        [FIX] Исправлена сигнатура метода.
        Аргументы: unit (attacker), multiplier (current_res), kwargs (attacker, target, dice...)
        """
        new_mult = multiplier + 0.2
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
    name = "2.4 Золотая Репутация"
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
    name = "2.5 Мгновенное Озарение"
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
    name = "2.6 Пример для подражания!"
>>>>>>> c916355f0910085208ccc685d7a0ae93ec550744
    description = (
        "Активно (Free Action): Укажите на врага. Следующая атака союзника по нему\n"
        "будет считать сопротивление цели как 'Fatal' (x2.0 урон).\n"
        "Кулдаун: 3 хода."
    )
    is_active_ability = True


class TalentPokerFace(BasePassive):
    id = "poker_face_rework"
    name = "2.8.B Хладнокровие"
    description = (
        "Вы иммунны к Панике.\n"
        "Если ваше SP падает ниже 30%, вы получаете +3 Power (Clash),\n"
        "так как ваши действия становятся абсолютно нечитаемыми."
    )
    is_active_ability = False


class TalentMerchantOfDeath(BasePassive):
    id = "merchant_of_death"
    name = "2.9.B Торговец Смертью"
    description = (
        "Активно: Потратить Кредиты (Уровень врага * 50), чтобы подкупить его.\n"
        "Обычный враг покидает бой. Элитный враг получает Stagger на 1 ход.\n"
        "Не работает на Боссов и Монстров (Искажения)."
    )
    is_active_ability = True


class TalentPuppetMaster(BasePassive):
    id = "puppet_master"
    name = "2.10.B Кукловод (Финал Б)"
    description = (
        "Пассивно: 1 раз за раунд, когда враг атакует кого-то,\n"
        "вы можете перенаправить эту атаку на любую другую цель (кроме самого атакующего).\n"
        "Вы управляете хаосом битвы."
    )
    is_active_ability = False


# ======================================================================================
# ОПЦИОНАЛЬНЫЕ ТАЛАНТЫ (OPTIONAL)
# Можно брать в дополнение к любой ветке при выполнении условий
# ======================================================================================

class TalentImprovisation(BasePassive):
    id = "opt_improvisation"
    name = "Импровизация (Опц.)"
    description = (
        "Требование: Интеллект 30+.\n"
        "Если у вас в руке нет карт Атаки, вы создаете временную карту 'Импровизированный удар'\n"
        "(Cost 0, 4-8 Blunt, On Hit: Draw 1)."
    )
    is_active_ability = False


class TalentSocialEngineer(BasePassive):
    id = "opt_social_eng"
    name = "Социальная Инженерия (Опц.)"
    description = (
        "Требование: Красноречие 40+.\n"
        "В начале боя вы можете выбрать одного врага. Он не будет атаковать вас 2 раунда,\n"
        "пока вы не атакуете его. (Не работает на Искажения)."
    )
    is_active_ability = False


class TalentHoarder(BasePassive):
    id = "opt_hoarder"
    name = "Барахольщик (Опц.)"
    description = (
        "Требование: Нет.\n"
        "Вы получаете специальный слот 'Карман'. В него можно положить 1 расходник (Граната/Хилка),\n"
        "который применяется мгновенно (Free Action) и не тратит слот действия."
    )
    is_active_ability = False


# ======================================================================================
# УЛЬТИМЕЙТ
# ======================================================================================

class TalentForesight(BasePassive):
    id = "foresight"
    name = "2.11 Твоя следующая фраза..."
    description = (
        "Ультимативная способность (1 раз за бой).\n"
        "Активно: Нажмите ПОСЛЕ бросков кубиков (но до урона).\n"
        "Время отматывается в начало раунда. Вы сохраняете память о бросках врага,\n"
        "а враг обязан перебросить кубики с помехой (Disadvantage, выбирается худший)."
    )
    is_active_ability = True