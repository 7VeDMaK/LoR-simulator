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
    name = "2.1 Врожденный дар"
    description = (
        "Прокачивая данный талант, персонаж вкладывает в данную ветку еще 4 таланта.\n"
        "Эффект: Вы получаете бонус +1 ко всем характеристикам и +2 к навыкам.\n"
        "Каждые 10 уровней персонажа этот бонус увеличивается (Максимум +5 / +10 на 50 уровне)."
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
    name = "2.2 Глаза Небожителя"
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
        if diff >= 5:
            u_type = getattr(target, "unit_type", "Неизвестно")
            rank = getattr(target, "rank", 9)
            details.append(f"🏴 **Тип/Ранг**: {u_type} | Ранг {rank}")

        # ТИР 2: Слабые карты (Tier 1) (10+)
        if diff >= 10:
            c_str = ", ".join(cards_by_tier[1]) if cards_by_tier[1] else "Нет"
            details.append(f"🃏 **Слабые карты (T1)**: {c_str}")

        # ТИР 3: Средние карты (Tier 2) + Предметы (15+)
        if diff >= 15:
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
        if diff >= 20:
            c_str = ", ".join(cards_by_tier[3]) if cards_by_tier[3] else "Нет"
            details.append(f"🃏 **Сильные карты (T3)**: {c_str}")

            weapon_id = getattr(target, "weapon_id", "none")
            weapon_name = "Нет оружия"
            from logic.weapon_definitions import WEAPON_REGISTRY
            if weapon_id in WEAPON_REGISTRY:
                weapon_name = WEAPON_REGISTRY[weapon_id].name
            details.append(f"⚔️ **Оружие**: {weapon_name}")

        # ТИР 5: Мощные карты (Tier 4+) + Аугментации (25+)
        if diff >= 25:
            c_str = ", ".join(cards_by_tier[4]) if cards_by_tier[4] else "Нет"
            details.append(f"🃏 **Мощные карты (T4+)**: {c_str}")

            augs = getattr(target, "augmentations", [])
            aug_str = resolve_names(augs, AUGMENTATION_REGISTRY)
            details.append(f"🦾 **Аугментации**: {aug_str}")

        # ТИР 6: Таланты (30+)
        if diff >= 30:
            talents = getattr(target, "talents", [])
            tal_str = resolve_names(talents, TALENT_REGISTRY)
            details.append(f"🧠 **Таланты**: {tal_str}")

        # ТИР 7: Пассивные навыки (35+)
        if diff >= 35:
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
    description = (
        "Удар, который игнорирует плотность материи и стойкость духа.\n"
        "При расчете урона к множителю сопротивления цели прибавляется +0.2.\n"
        "(Пример: 0.5 (Endured) -> 0.7, цель получает больше урона)."
    )
    is_active_ability = False

    def on_calculate_damage_multiplier(self, multiplier, attacker, target, dice):
        new_mult = multiplier + 0.2
        logger.log(
            f"⚔️ {self.name}: Сопротивление цели изменено ({multiplier:.1f} -> {new_mult:.1f})",
            LogLevel.VERBOSE,
            "Talent"
        )
        return new_mult


# ==========================================
# 2.4 Мгновенное Озарение
# ==========================================
class TalentCopycatInsight(BasePassive):
    id = "copycat_insight"
    name = "2.4 Мгновенное Озарение"
    description = (
        "Достаточно одного взгляда, чтобы превзойти чужую технику.\n"
        "Активно (КД: 3 сцены): Создать в руке временную копию любой карты раунда. Стоимость: 0."
    )
    is_active_ability = True
    cooldown = 3

    # Логика активации реализуется через UI выбора карты, здесь только пассивная структура


# ==========================================
# 2.5 Право Первенства
# ==========================================
class TalentHeirPriority(BasePassive):
    id = "heir_priority"
    name = "2.5 Право Первенства"
    description = (
        "Истинный мастер диктует темп битвы с первого шага.\n"
        "В начале битвы: +2 Спешки на 3 раунда.\n"
        "Доп. урон равен разнице в скорости (Макс +8)."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        unit.add_status("haste", 2, duration=3)
        if log_func:
            log_func(f"⚡ {self.name}: Получено +2 Спешки на 3 раунда.")
        logger.log(f"⚡ {self.name}: {unit.name} gains Haste II", LogLevel.NORMAL, "Talent")

    def on_hit(self, ctx, **kwargs):
        if ctx.target:
            diff = max(0, ctx.source.speed - ctx.target.speed)
            bonus = min(8, diff)
            if bonus > 0:
                ctx.damage += bonus
                ctx.log.append(f"⚡ **Право Первенства**: +{bonus} урона (Разница скоростей)")


# ======================================================================================
# РЕФЕРЕНСНЫЕ ТАЛАНТЫ (2.6 - 2.10)
# ======================================================================================

# ==========================================
# 2.6 Пример для подражания!
# ==========================================
class TalentIdealStandard(BasePassive):
    id = "ideal_standard"
    name = "2.6 Пример для подражания!"
    description = (
        "За каждого живого союзника: +2 к характеристикам (макс 5).\n"
        "При оглушении персонажа союзники получают +3 Power на 2 хода."
    )


# ==========================================
# 2.7 Насмешка
# ==========================================
class TalentArrogantTaunt(BasePassive):
    id = "arrogant_taunt"
    name = "2.7 Насмешка"
    description = (
        "+5 к Красноречию.\n"
        "Активно: позволяет выбрать цели, которые будут обязаны атаковать выбранного персонажа."
    )

    def on_calculate_stats(self, unit) -> dict:
        return {"eloquence": 5}


# ==========================================
# 2.8 Сюжетная броня
# ==========================================
class TalentMainCharacterShell(BasePassive):
    id = "main_character_shell"
    name = "2.8 Сюжетная броня"
    description = (
        "+25% к Выдержке.\n"
        "1 раз за битву: при летальном уроне — 1 HP, полное восстановление выдержки и неуязвимость на раунд."
    )

    def on_calculate_stats(self, unit) -> dict:
        return {"stagger_resist_pct": 25}


# ==========================================
# 2.9 Muted
# ==========================================
class TalentSilenceExecution(BasePassive):
    id = "silence_execution"
    name = "2.9 Muted"
    description = (
        "Активно (КД: 5 сцен): Уничтожить кубик скорости противника "
        "(кроме Массовых атак) без использования карт."
    )
    is_active_ability = True
    cooldown = 5


# ==========================================
# 2.10 Да мы только начали!
# ==========================================
class TalentJustWarmingUp(BasePassive):
    id = "just_warming_up"
    name = "2.10 Да мы только начали!"
    description = "За каждое проигранное столкновение: +1 к Мощи в следующей сцене на один ход."


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

    def on_calculate_damage_multiplier(self, multiplier, attacker, target, dice):
        # Проверяем, выпало ли минимальное или максимальное значение на кости
        if hasattr(dice, 'last_roll'):
            if dice.last_roll == dice.min_val or dice.last_roll == dice.max_val:
                logger.log(f"⚫ **BLACK FLASH**: Critical Hit! (Roll: {dice.last_roll})", LogLevel.NORMAL, "Talent")
                return multiplier * 1.5
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