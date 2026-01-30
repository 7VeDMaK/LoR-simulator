from core.logging import logger, LogLevel  # [NEW] Import
from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# 4.1 Без Клятвы Гиппократа (ОБЩИЙ)
# ==========================================
class TalentNoHippocraticOath(BasePassive):
    id = "no_hippocratic_oath"
    name = "Без Клятвы Гиппократа WIP"
    description = (
        "4.1 Спас-броски на введение медикаментов +3.\n"
        "Ограничение: Вы не можете носить тяжелую и среднюю броню (только лёгкую)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        # Условно добавляем к медицине, хотя в ТЗ "спас броски на введение"
        return {"medicine": 3}


# ==========================================
# ПОДКЛАСС: ХОРОШИЙ ВРАЧ
# ==========================================

class TalentGoodAsNew(BasePassive):
    id = "good_as_new"
    name = "Как новенький! WIP"
    description = (
        "4.2 (Хороший) При лечении союзника: он получает 2 Спешки.\n"
        "С 4.4: +1 Защита.\n"
        "С 4.6: +1 Сила, +1 Стойкость.\n"
        "Если вылечили до фулла: +1 к броскам (с 4.5 -> +2, с 4.8 -> +3)."
    )
    is_active_ability = False


class TalentRemedyGood(BasePassive):
    id = "remedy_good"
    name = "Remedy (Универсальное лекарство) WIP"
    description = (
        "4.3 Активно: Создать/Использовать универсальное лекарство.\n"
        "Восстанавливает 25 HP/SP (зависит от контекста).\n"
        "Лимит: Кол-во навыков ветки / 2."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        # Простая заглушка лечения
        heal = 25
        unit.heal_hp(heal)
        if log_func: log_func(f"💊 **Remedy**: Восстановлено {heal} HP.")
        logger.log(f"💊 Remedy used by {unit.name}: Healed {heal} HP", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 4.4 Сыры
# ==========================================
class TalentCheese(BasePassive):
    id = "cheese"
    name = "Сыры"
    description = (
        "«Время превращает молоко в золото, а золото — в тяжесть. Один кусочек дарит силы, но целый круг может стать твоим последним ужином.»\n\n"
        "Пассивно: В начале боя вы получаете набор особых Сыров в руку.\n"
        "Механика 'Сытость': Поедание сыров накапливает стаки.\n"
        "• >15 стаков: Вы получаете штрафы к Скорости и Уклонению.\n"
        "• >20 стаков: Ваш желудок не выдерживает (периодический урон)."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        cheese_ids = [
            "cheese_parmesan", "cheese_edam", "cheese_cheddar",
            "cheese_gouda", "cheese_maasdam", "cheese_emmental"
        ]

        added = 0
        for cid in cheese_ids:
            # Проверка, чтобы не дублировать, если талант сработал дважды
            if cid not in unit.deck:
                unit.deck.append(cid)
                added += 1

        if log_func and added > 0:
            log_func(f"🧀 **Сыровар**: {added} головок сыра добавлено в инвентарь.")

        if added > 0:
            logger.log(f"🧀 Cheese Maker: Added {added} cheese cards to {unit.name}", LogLevel.NORMAL, "Talent")


# ==========================================
# 4.5 Конфетки
# ==========================================
class TalentConfete(BasePassive):
    id = "confete"
    name = "Конфетки"
    description = (
        "«В городе, пропитанном дымом и кровью, сахар — это самый дешевый антидепрессант. Съешь одну, пока зубы еще на месте.»\n\n"
        "Пассивно: В начале боя ваш инвентарь пополняется элитным набором сладостей.\n"
        "Ассортимент: Пралине, Марципан, Суфле, Грильяж, Ганаш, Помадка и Вафли.\n"
        "Каждая сладость дает уникальный кратковременный бонус."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        candy_ids = [
            "candy_praline", "candy_marzipan", "candy_souffle",
            "candy_grillage", "candy_ganache", "candy_fudge", "candy_waffles"
        ]

        added = 0
        for cid in candy_ids:
            if cid not in unit.deck:
                unit.deck.append(cid)
                added += 1

        if log_func and added > 0:
            log_func(f"🍬 **Кондитер**: {added} сладостей рассовано по карманам.")

        if added > 0:
            logger.log(f"🍬 Confectioner: Added {added} candy cards to {unit.name}", LogLevel.NORMAL, "Talent")

class TalentYouWontDieGood(BasePassive):
    id = "you_wont_die_good"
    name = "Ты не умрёшь WIP"
    description = (
        "4.6 Стабилизация критического состояния без броска.\n"
        "Спасение от летального исхода за счет Универсальных лекарств."
    )
    is_active_ability = False


class TalentCarefulNeutralization(BasePassive):
    id = "careful_neutralization"
    name = "Аккуратное обезвреживание WIP"
    description = (
        "4.7 (Хороший) Платок со снотворным.\n"
        "Активно (2 куба): Если у врага <10% HP, мгновенно усыпить.\n"
        "Вне боя: Мгновенное усыпление при успешной внезапной атаке."
    )
    is_active_ability = True


class TalentDoingGoodWork(BasePassive):
    id = "doing_good_work"
    name = "Творя благое дело WIP"
    description = (
        "4.8 (Хороший) После использования стимулятора/лекарства на союзника:\n"
        "Вы получаете 1 Силу, 1 Спешку, 1 Выдержку (Макс 2)."
    )
    is_active_ability = False


class TalentNotToday(BasePassive):
    id = "not_today"
    name = "Не сегодня! WIP"
    description = (
        "4.9 (Хороший) Реакция: Вколоть препарат союзнику перед получением фатального урона.\n"
        "Броски препаратов получают +5 Спешки."
    )
    is_active_ability = False


class TalentMadGoodDoctor(BasePassive):
    id = "mad_good_doctor"
    name = "Ваш безумный добрый доктор WIP"
    description = (
        "4.10 (Хороший) Автоматическое усиление препаратов (1d4).\n"
        "1: +1 Сила, 2: +1 Спешка, 3: +1 Выдержка, 4: Всё вместе на 3 раунда."
    )
    is_active_ability = False


# ==========================================
# ПОДКЛАСС: ПЛОХОЙ ВРАЧ (ТОКСИКОЛОГ)
# ==========================================

class TalentToxicologyWeapon(BasePassive):
    id = "toxicology_weapon"
    name = "Токсикология (Оружие) WIP"
    description = (
        "4.2 (Плохой) Оружие покрыто ядом.\n"
        "При попадании: +2 Яда.\n"
        "Эффекты яда: 10 (Слабость), 30 (Дебаффы), 50 (Урон), 80 (Сильные дебаффы), 100 (Слепота)."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        if log_func: log_func(f"☠️ **{self.name}**: Оружие отравлено.")
        logger.log(f"☠️ Toxicology Weapon active for {unit.name}", LogLevel.VERBOSE, "Talent")


class TalentRemedyBad(BasePassive):
    id = "remedy_bad"
    name = "Remedy (Лекарство) WIP"
    description = (
        "4.3 То же, что и у хорошего врача: Универсальное лекарство (25 HP)."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        unit.heal_hp(25)
        if log_func: log_func("💊 **Remedy**: Восстановлено 25 HP.")
        logger.log(f"💊 Remedy used by {unit.name}: Healed 25 HP", LogLevel.NORMAL, "Talent")
        return True


class TalentOrganStriking(BasePassive):
    id = "organ_striking"
    name = "Бьём по органам WIP"
    description = "4.4 (Плохой) Весь ваш урон увеличен на 25%."
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        # Заглушка: +25% к множителю урона
        return {"damage_deal_mult": 0.25}


class TalentAdvancedToxicology(BasePassive):
    id = "advanced_toxicology"
    name = "Токсикология (Яды) WIP"
    description = (
        "4.5 (Плохой) Создание и введение особых ядов (атакой).\n"
        "Лимит: 5 шт (8 с навыком 4.10)."
    )
    is_active_ability = True


class TalentYouWontDieBad(BasePassive):
    id = "you_wont_die_bad"
    name = "Ты не умрёшь WIP"
    description = "4.6 Стабилизация состояния (аналогично ветке хорошего врача)."
    is_active_ability = False


class TalentMedicalJargon(BasePassive):
    id = "medical_jargon"
    name = "Медицинский жаргон WIP"
    description = (
        "4.7 (Плохой) Харизма +3.\n"
        "Все броски харизмы проходят с преимуществом."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"eloquence": 3}


class TalentChristmasTree(BasePassive):
    id = "christmas_tree"
    name = "Смотрите, ёлочка WIP"
    description = (
        "4.8 (Плохой) Мощь костей +1 за каждые 3 уникальных негативных эффекта на цели (макс +2)."
    )
    is_active_ability = False


class TalentInsaneZeal(BasePassive):
    id = "insane_zeal"
    name = "Безумное рвение WIP"
    description = (
        "4.9 (Плохой) При атаке по цели с HP < 50%: 50% шанс наложить Кровотечение (макс 4)."
    )
    is_active_ability = False


class TalentGeniusToxicologist(BasePassive):
    id = "genius_toxicologist"
    name = "Гений токсиколог WIP"
    description = (
        "4.10 (Плохой) Смертельный яд.\n"
        "Эффект: 150 Яда и 3 Хрупкости."
    )
    is_active_ability = True
    cooldown = 99

    def activate(self, unit, log_func, **kwargs):
        if log_func: log_func("☠️ **Смертельный яд**: Применен! (150 Poison, 3 Fragile)")
        logger.log(f"☠️ Deadly Poison activated by {unit.name}", LogLevel.NORMAL, "Talent")
        return True

#todo all branch