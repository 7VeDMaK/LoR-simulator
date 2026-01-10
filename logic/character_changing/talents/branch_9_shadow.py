import random

from core.enums import DiceType
from core.tree_data import SKILL_TREE
from logic.character_changing.passives.base_passive import BasePassive
from logic.context import RollContext

# ==========================================
# 9.1 А: Атлетичность
# ==========================================
class TalentAthleticismShadow(BasePassive):
    id = "athleticism_shadow"
    name = "Атлетичность (А)"
    description = "9.1 А: Ловкость +5."
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {"agility": 5}

# ==========================================
# 9.1 Б: Месть
# ==========================================
class TalentRevenge(BasePassive):
    id = "revenge"
    name = "Месть (Б)"
    description = "9.1 Б: После получения урона -> Следующая попавшая атака наносит x1.5 урона."
    is_active_ability = False

    def on_take_damage(self, unit, amount, source, **kwargs):
        if amount > 0:
            # Просто вешаем статус. Логика урона теперь внутри RevengeDmgUpStatus.
            unit.add_status("revenge_dmg_up", 1, duration=2)
            if log_func: log_func(f"🩸 **{self.name}**: Получен урон! След. атака усилена (x1.5).")

# ==========================================
# 9.2 А: Невеликое внимание
# ==========================================
class TalentNotGreatAttention(BasePassive):
    id = "not_great_attention"
    name = "Невеликое внимание (А)"
    description = (
        "9.2 А: Легкое оружие спрятано идеально. Ночью/в тени ваши движения незаметны.\n"
        "Эффект: +3 к Ловкости (Agility)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        # Даем прямой бонус к атрибуту
        return {"agility": 3}


# ==========================================
# 9.2 Б: Грозная персона
# ==========================================
class TalentFormidablePerson(BasePassive):
    id = "formidable_person"
    name = "Грозная персона (Б)"
    description = (
        "9.2 Б: Ваш вид внушает ужас, даже когда вы молчите.\n"
        "Эффект: +5 к Красноречию (Eloquence)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        # Даем прямой бонус к навыку
        return {"eloquence": 5}


# ==========================================
# 9.3 А: Разящий Клинок
# ==========================================
class TalentSmashingBlade(BasePassive):
    id = "smashing_blade"
    name = "Разящий Клинок (А)"
    description = (
        "9.3 А: Внезапные атаки наносят x1.5 урона.\n"
        "Условия: Невидимость, Цель имеет >90% HP.\n"
        "(Если взят 9.5 А 'Шаг в тень', порог HP снижается до 75%, урон 2х).\n"
        "При Внезапной атаке: накладывает Xd6 Кровотечения (X = таланты ветки)."
    )
    is_active_ability = False

    def on_roll(self, ctx):
        unit = ctx.source
        target = ctx.target
        if not target: return

        # === 1. ОПРЕДЕЛЕНИЕ "ВНЕЗАПНОСТИ" ===
        is_sudden = False
        reasons = []

        # А. Невидимость
        if unit.get_status("invisibility") > 0:
            is_sudden = True
            reasons.append("Invisible")

        # В. Цель полна сил (>90% или >75% с талантом 9.5)
        # Проверяем наличие улучшения (9.5 А)
        threshold = 0.90
        multiplier = 1.5
        if "step_into_shadow" in unit.talents:
            threshold = 0.75
            multiplier = 2

        if target.max_hp > 0:
            hp_pct = target.current_hp / target.max_hp
            if hp_pct >= threshold:
                is_sudden = True
                reasons.append(f">{int(threshold * 100)}% HP")

        # === 2. ПРИМЕНЕНИЕ ЭФФЕКТОВ ===
        if is_sudden:
            # Множитель x2.0
            ctx.damage_multiplier = max(ctx.damage_multiplier, multiplier)

            # Наложение Кровотечения (Xd6)
            branch_9_nodes = SKILL_TREE.get("Ветка 9: Тень (А) / Кровь (Б)", [])
            x_count = 0
            for node in branch_9_nodes:
                tid = node.get("id")
                if tid and (tid in unit.talents or tid in unit.passives):
                    x_count += 1

            x_count = max(1, x_count)

            bleed_stack = 0
            rolls = []
            for _ in range(x_count):
                r = random.randint(1, 6)
                bleed_stack += r
                rolls.append(str(r))

            target.add_status("bleed", bleed_stack, duration=3)

            ctx.log.append(f"🗡️ **Sudden Attack**: x{multiplier} Dmg & {bleed_stack} Bleed ({', '.join(reasons)})")

# ==========================================
# 9.3 Б Резня (Slaughter)
# ==========================================
class TalentSlaughter(BasePassive):
    id = "slaughter"
    name = "Резня (Б)"
    description = "9.3 Б: Последний атакующий куб (Slash/Pierce) накладывает 2 + (Lvl/10) Кровотечения."
    is_active_ability = False

    def on_hit(self, ctx: RollContext):
        # 1. Проверяем тип урона (Slash или Pierce)
        if ctx.dice.dtype not in [DiceType.SLASH, DiceType.PIERCE]:
            return

        # 2. Получаем карту и проверяем, последний ли это кубик
        card = ctx.source.current_card
        if not card or not card.dice_list:
            return

        # Сравниваем текущий кубик (ctx.dice) с последним кубиком в списке карты
        last_die = card.dice_list[-1]

        # Оператор 'is' проверяет, является ли это тем же самым объектом в памяти
        if ctx.dice is last_die:
            # 3. Считаем стаки
            lvl = ctx.source.level
            bleed_amt = 2 + (lvl // 10)

            # 4. Накладываем эффект на цель (того, кого ударили)
            # В контексте атаки ctx.target - это цель (если удар был не по своей воле, это может быть None, но обычно есть)
            target = ctx.target
            if target:
                target.add_status("bleed", bleed_amt, duration=3)  # Длительность bleed стандартно убывает сама
                ctx.log.append(f"🩸 {self.name}: Последний куб -> +{bleed_amt} Bleed")

# ==========================================
# 9.3 (Опц) Trapmaster
# ==========================================
class TalentTrapmaster(BasePassive):
    id = "trapmaster WIP"
    name = "Trapmaster WIP"
    description = "9.3 Опц: Рецепты ловушек. Спас-бросок врага (Int) против вашего (Engineering)."
    is_active_ability = False


# ==========================================
# 9.4 А: Быстрый и Тихий
# ==========================================
class TalentFastAndSilent(BasePassive):
    id = "fast_and_silent"
    name = "Быстрый и Тихий (А)"
    description = (
        "9.4 А: Бесшумные шаги (радиус слышимости 0-4м).\n"
        "Пассивно: +5 к Скорости."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {"speed": 5}


# ==========================================
# 9.4 Б: Агрессивное парирование
# ==========================================
class TalentAggressiveParry(BasePassive):
    id = "aggressive_parry"
    name = "Агрессивное парирование (Б)"
    description = "9.4 Б: При ничьей (Draw) в столкновении -> Наносит урон Выдержке врага (Половина вашего броска)."
    is_active_ability = False

    def on_clash_draw(self, ctx):
        # Считаем урон (половина броска)
        dmg = ctx.final_value // 2

        if dmg > 0 and ctx.target:
            # Наносим прямой урон выдержке (Stagger)
            ctx.target.current_stagger = max(0, ctx.target.current_stagger - dmg)
            ctx.log.append(f"⚔️ **Парирование**: Враг получил {dmg} урон по Выдержке.")


# ==========================================
# 9.5 А: Шаг в тень
# ==========================================
class TalentStepIntoShadow(BasePassive):
    id = "step_into_shadow"
    name = "Шаг в тень (А)"
    description = (
        "9.5 А: Активно: Уйти в тень (Невидимость) на 3 раунда. КД: 7 раундов.\n"
        "Пассивно: Снижает порог HP для 'Разящего Клинка' до 75%, урон внезапной атаки x2."
    )
    is_active_ability = True
    cooldown = 7

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0:
            return False

        unit.add_status("invisibility", 1, duration=3)
        unit.cooldowns[self.id] = self.cooldown

        if log_func:
            log_func(f"👻 **{self.name}**: Растворился в тени (Невидимость на 3 х.)")
        return True


# ==========================================
# 9.5 Б: Вкус победы
# ==========================================
class TalentTasteOfVictory(BasePassive):
    id = "taste_of_victory"
    name = "Вкус победы (Б)"
    description = (
        "9.5 Б: Активно (на трупе): Выпотрошить.\n"
        "Восст. 15% HP. +1 Сила, +1 Спешка на 5 раундов.\n"
        "Враги теряют вдвое больше SP от ужаса."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        # Заглушка (нужен труп)
        heal = int(unit.max_hp * 0.15)
        unit.heal_hp(heal)
        unit.add_status("strength", 1, duration=5)
        unit.add_status("haste", 1, duration=5)
        if log_func: log_func(f"🍖 **Вкус победы**: +{heal} HP, баффы получены.")
        return True


# ==========================================
# 9.5 (Опц) Ловкость Рук
# ==========================================
class TalentSleightOfHand(BasePassive):
    id = "sleight_of_hand"
    name = "Ловкость Рук"
    description = (
        "9.5 Опц: Макс. метательного оружия 25.\n"
        "Метательное оружие получает 50% бонуса от навыка Огнестрела."
    )
    is_active_ability = False


# ==========================================
# 9.6 А: Кошачьи рефлексы
# ==========================================
class TalentCatReflexes(BasePassive):
    id = "cat_reflexes"
    name = "Кошачьи рефлексы (А)"
    description = (
        "9.6 А: Кость уклонения +2.\n"
        "Нельзя уничтожить кость уклонения.\n"
        "После успешного уклонения -> Атакующие кости +2 силы (МАКСИМУМ 1 раз за раунд)."
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        # Сбрасываем флаг срабатывания в начале каждого раунда
        unit.memory["cat_reflexes_triggered"] = False

    def on_roll(self, ctx):
        # +2 к Уклонению
        if ctx.dice.dtype == DiceType.EVADE:
            ctx.modify_power(2, "Cat Reflexes")

    def on_clash_win(self, ctx):
        # Если победили Уклонением и еще не получали бонус
        if ctx.dice.dtype == DiceType.EVADE:
            if not ctx.source.memory.get("cat_reflexes_triggered"):
                ctx.source.memory["cat_reflexes_triggered"] = True

                # Даем +2 Силы (Strength) до конца раунда
                ctx.source.add_status("strength", 2, duration=3)
                ctx.log.append("🐱 **Кошачьи рефлексы**: Успешное уклонение! +2 Силы.")

    def prevents_specific_die_destruction(self, unit, die) -> bool:
        # Спасает только Уклонение
        return die.dtype == DiceType.EVADE

# ==========================================
# 9.6 Б: Уроки выдержки
# ==========================================
class TalentEnduranceLessons(BasePassive):
    id = "endurance_lessons"
    name = "Уроки выдержки (Б)"
    description = "9.6 Б: Пассивно восстанавливает 2% от Макс. HP (Выдержки?) в раунд."
    is_active_ability = False

    def on_round_end(self, unit, log_func, **kwargs):
        # Написано "Выдержка... в размере 2% макс хп".
        # Видимо, реген стаггера (Stagger Resist).
        heal = int(unit.max_hp * 0.02)
        unit.restore_stagger(heal)
        if log_func: log_func(f"🛡️ **{self.name}**: +{heal} Stagger.")


# ==========================================
# 9.7 А: Глаз на опасность
# ==========================================
class TalentEyeForDanger(BasePassive):
    id = "eye_for_danger"
    name = "Глаз на опасность (А)"
    description = (
        "9.7 А: Вы нутром чуете ловушки и знаете, как они устроены.\n"
        "Акробатика +5, Инженерия +10."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {
            "acrobatics": 5,
            "engineering": 10
        }


# ==========================================
# 9.7 Б: Холоднокровие
# ==========================================
class TalentColdBlooded(BasePassive):
    id = "cold_blooded"
    name = "Холоднокровие (Б)"
    description = (
        "9.7 Б: Урон по SP (рассудку) x0.75.\n"
        "Скрытие мотивов (Мудрость врага с помехой)."
    )
    is_active_ability = False


# ==========================================
# 9.7 (Опц) Вор личностей
# ==========================================
class TalentIdentityThief(BasePassive):
    id = "identity_thief"
    name = "Вор личностей"
    description = "9.7 Опц: Создание масок, костюмов, подделка документов и личности."
    is_active_ability = False


# ==========================================
# 9.8 А: Заметая следы
# ==========================================
class TalentCoveringTracks(BasePassive):
    id = "covering_tracks"
    name = "Заметая следы (А)"
    description = (
        "9.8 А: Ловкость +7.\n"
        "Начало боя: Вы получаете Невидимость на 3 раунда.\n"
        "Успешное уклонение: Враг путается в фальшивых следах (получает 1 Bind)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        # Аппаем проверку ловкости через стат
        return {"agility": 7}

    def on_combat_start(self, unit, log_func, **kwargs):
        # Даем невидимость сразу, чтобы активировать синергию с 9.3 (Разящий Клинок)
        unit.add_status("invisibility", 1, duration=3)
        if log_func:
            log_func(f"👣 **{self.name}**: Следы скрыты (Невидимость на 2 х.)")
            #TODO переделать комбат старт проверить когда работает, добавить норм единоразовый эффект

    def on_clash_win(self, ctx):
        # Механика "Фальшивый след"
        if ctx.dice.dtype == DiceType.EVADE:
            target = ctx.target
            if target:
                target.add_status("bind", 1, duration=3)
                ctx.log.append(f"👣 **Фальшивый след**: Враг замедлен (Bind 1).")


# ==========================================
# 9.8 Б: Грамотный Адреналин
# ==========================================
class TalentCompetentAdrenaline(BasePassive):
    id = "competent_adrenaline"
    name = "Грамотный Адреналин (Б)"
    description = (
        "9.8 Б: Активно: +3 Силы, +3 Выдержки на 3 Раунда.\n"
        "КД: 2 часа."
    )
    is_active_ability = True
    cooldown = 20

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        unit.add_status("strength", 3, duration=3)
        unit.add_status("endurance", 3, duration=3)
        unit.cooldowns[self.id] = self.cooldown
        if log_func: log_func(f"💉 **Адреналин**: +3 Str/End на 3 раунда.")
        return True


# ==========================================
# 9.9 А: Нож в спину
# ==========================================
class TalentKnifeInBack(BasePassive):
    id = "knife_in_back"
    name = "Нож в спину (А)"
    description = (
        "9.9 А: После Внезапной атаки -> Враг получает 5 Хрупкости (Fragile) и 5 Кровотечения.\n"
        "(Хрупкость увеличивает входящий урон на 5 при каждом ударе)."
    )
    is_active_ability = False

    def on_hit(self, ctx):
        unit = ctx.source
        target = ctx.target
        if not target: return

        # === ЛОГИКА ОПРЕДЕЛЕНИЯ ВНЕЗАПНОСТИ (копия из 9.3) ===
        is_sudden = False

        # 1. Невидимость
        if unit.get_status("invisibility") > 0:
            is_sudden = True

        # 2. Спец. карта
        elif unit.current_card and unit.current_card.id == "shadow_ambush_card":
            is_sudden = True

        # 3. HP Порог (с учетом таланта 9.5)
        elif target.max_hp > 0:
            threshold = 0.75 if "step_into_shadow" in unit.talents else 0.90
            hp_pct = target.current_hp / target.max_hp
            if hp_pct >= threshold:
                is_sudden = True

        # === ЭФФЕКТ ===
        if is_sudden:
            # Накладываем 5 Хрупкости и 5 Кровотечения
            target.add_status("fragile", 5, duration=2)  # На этот и след. раунд
            target.add_status("bleed", 5, duration=3)

            ctx.log.append(f"🔪 **Нож в спину**: Враг открылся! (+5 Fragile, +5 Bleed)")


# ==========================================
# 9.9 Б: Притеснение
# ==========================================
class TalentOppression(BasePassive):
    id = "oppression"
    name = "Притеснение (Б)"
    description = (
        "9.9 Б: Если у цели 20+ Кровотечения (от вас) -> Она получает 4 Рассредоточенность (Disorient?) до конца раунда."
    )
    is_active_ability = False


# ==========================================
# 9.9 (Опц) Точка уязвимости
# ==========================================
class TalentVulnerabilityPoint(BasePassive):
    id = "vulnerability_point"
    name = "Точка уязвимости"
    description = (
        "9.9 Опц: (Требует броню < 0.5 резиста).\n"
        "Ваши атаки не могут нанести меньше 50% от силы броска (Минимальный урон)."
    )
    is_active_ability = False


# ==========================================
# 9.10 А: Крайние меры
# ==========================================
class TalentExtremeMeasures(BasePassive):
    id = "extreme_measures"
    name = "Крайние меры (А)"
    description = (
        "9.10 А: Набор умений.\n"
        "1. Кровяное облако (на трупе): Незаметность, но вы в крови (-25% HP).\n"
        "2. Веер клинков (Масс атака): 20 Bleed всем, 30 Bleed при попадании.\n"
        "3. Визитная карточка: Понижает атрибуты цели на 6."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        if log_func: log_func("🩸 Меню 'Крайних мер' (Заглушка).")
        return True


# ==========================================
# 9.10 Б: Мясник
# ==========================================
class TalentButcher(BasePassive):
    id = "butcher"
    name = "Мясник (Б)"
    description = (
        "9.10 Б: Все атаки накладывают x1.25 Кровотечения.\n"
        "Карты 5-го уровня накладывают 'Жидкую кровь' (расходуется вместо стаков кровотечения)."
    )
    is_active_ability = False