from logic.passives.base_passive import BasePassive


# ==========================================
# 4.1 Без Клятвы Гиппократа (ОБЩИЙ)
# ==========================================
class TalentNoHippocraticOath(BasePassive):
    id = "no_hippocratic_oath"
    name = "Без Клятвы Гиппократа"
    description = (
        "4.1 Спас-броски на введение медикаментов +3.\n"
        "Ограничение: Вы не можете носить тяжелую и среднюю броню (только лёгкую)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        # Условно добавляем к медицине, хотя в ТЗ "спас броски на введение"
        return {"medicine": 3}


# ==========================================
# ПОДКЛАСС: ХОРОШИЙ ВРАЧ
# ==========================================

class TalentGoodAsNew(BasePassive):
    id = "good_as_new"
    name = "Как новенький!"
    description = (
        "4.2 (Хороший) При лечении союзника: он получает 2 Спешки.\n"
        "С 4.4: +1 Защита.\n"
        "С 4.6: +1 Сила, +1 Стойкость.\n"
        "Если вылечили до фулла: +1 к броскам (с 4.5 -> +2, с 4.8 -> +3)."
    )
    is_active_ability = False


class TalentRemedyGood(BasePassive):
    id = "remedy_good"
    name = "Remedy (Универсальное лекарство)"
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
        return True


class TalentPills(BasePassive):
    id = "pills"
    name = "Таблетки"
    description = (
        "4.4 (Хороший) Создание таблеток (вне боя/в бою).\n"
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        if log_func: log_func("💊 Меню таблеток открыто (Логика крафта).")
        return True


class TalentStimulants(BasePassive):
    id = "stimulants"
    name = "Стимуляторы"
    description = (
        "4.5 (Хороший) Инъекции боевых стимуляторов.\n"
        "Лимит: 5 шт (8 с навыком 4.10)."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        if log_func: log_func("💉 Меню стимуляторов открыто.")
        return True


class TalentYouWontDieGood(BasePassive):
    id = "you_wont_die_good"
    name = "Ты не умрёшь"
    description = (
        "4.6 Стабилизация критического состояния без броска.\n"
        "Спасение от летального исхода за счет Универсальных лекарств."
    )
    is_active_ability = False


class TalentCarefulNeutralization(BasePassive):
    id = "careful_neutralization"
    name = "Аккуратное обезвреживание"
    description = (
        "4.7 (Хороший) Платок со снотворным.\n"
        "Активно (2 куба): Если у врага <10% HP, мгновенно усыпить.\n"
        "Вне боя: Мгновенное усыпление при успешной внезапной атаке."
    )
    is_active_ability = True


class TalentDoingGoodWork(BasePassive):
    id = "doing_good_work"
    name = "Творя благое дело"
    description = (
        "4.8 (Хороший) После использования стимулятора/лекарства на союзника:\n"
        "Вы получаете 1 Силу, 1 Спешку, 1 Выдержку (Макс 2)."
    )
    is_active_ability = False


class TalentNotToday(BasePassive):
    id = "not_today"
    name = "Не сегодня!"
    description = (
        "4.9 (Хороший) Реакция: Вколоть препарат союзнику перед получением фатального урона.\n"
        "Броски препаратов получают +5 Спешки."
    )
    is_active_ability = False


class TalentMadGoodDoctor(BasePassive):
    id = "mad_good_doctor"
    name = "Ваш безумный добрый доктор"
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
    name = "Токсикология (Оружие)"
    description = (
        "4.2 (Плохой) Оружие покрыто ядом.\n"
        "При попадании: +2 Яда.\n"
        "Эффекты яда: 10 (Слабость), 30 (Дебаффы), 50 (Урон), 80 (Сильные дебаффы), 100 (Слепота)."
    )
    is_active_ability = False

    def on_combat_start(self, unit, log_func, **kwargs):
        if log_func: log_func(f"☠️ **{self.name}**: Оружие отравлено.")


class TalentRemedyBad(BasePassive):
    id = "remedy_bad"
    name = "Remedy (Лекарство)"
    description = (
        "4.3 То же, что и у хорошего врача: Универсальное лекарство (25 HP)."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        unit.heal_hp(25)
        if log_func: log_func("💊 **Remedy**: Восстановлено 25 HP.")
        return True


class TalentOrganStriking(BasePassive):
    id = "organ_striking"
    name = "Бьём по органам"
    description = "4.4 (Плохой) Весь ваш урон увеличен на 25%."
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        # Заглушка: +25% к множителю урона
        return {"damage_deal_mult": 0.25}


class TalentAdvancedToxicology(BasePassive):
    id = "advanced_toxicology"
    name = "Токсикология (Яды)"
    description = (
        "4.5 (Плохой) Создание и введение особых ядов (атакой).\n"
        "Лимит: 5 шт (8 с навыком 4.10)."
    )
    is_active_ability = True


class TalentYouWontDieBad(BasePassive):
    id = "you_wont_die_bad"
    name = "Ты не умрёшь"
    description = "4.6 Стабилизация состояния (аналогично ветке хорошего врача)."
    is_active_ability = False


class TalentMedicalJargon(BasePassive):
    id = "medical_jargon"
    name = "Медицинский жаргон"
    description = (
        "4.7 (Плохой) Харизма +3.\n"
        "Все броски харизмы проходят с преимуществом."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {"eloquence": 3}


class TalentChristmasTree(BasePassive):
    id = "christmas_tree"
    name = "Смотрите, ёлочка"
    description = (
        "4.8 (Плохой) Мощь костей +1 за каждые 3 уникальных негативных эффекта на цели (макс +2)."
    )
    is_active_ability = False


class TalentInsaneZeal(BasePassive):
    id = "insane_zeal"
    name = "Безумное рвение"
    description = (
        "4.9 (Плохой) При атаке по цели с HP < 50%: 50% шанс наложить Кровотечение (макс 4)."
    )
    is_active_ability = False


class TalentGeniusToxicologist(BasePassive):
    id = "genius_toxicologist"
    name = "Гений токсиколог"
    description = (
        "4.10 (Плохой) Смертельный яд.\n"
        "Эффект: 150 Яда и 3 Хрупкости."
    )
    is_active_ability = True
    cooldown = 99

    def activate(self, unit, log_func, **kwargs):
        if log_func: log_func("☠️ **Смертельный яд**: Применен! (150 Poison, 3 Fragile)")
        return True