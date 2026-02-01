import os
import json
import random

from core.logging import logger, LogLevel  # [NEW] Import
from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# 7.1 Сделка с фортуной
# ==========================================
class TalentDealWithFortune(BasePassive):
    id = "deal_with_fortune"
    name = "Сделка с фортуной"
    description = (
        "«Говорят, удача любит смелых. Ложь. Удача любит тех, кто платит по счетам. Ты подписал контракт, и теперь кости ложатся так, как нужно тебе.»\n\n"
        "Пассивно: Ваша Удача (Luck) значительно повышена.\n"
        "Бонус: +3 плоского значения и +20% от базового показателя."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        # Получаем текущую удачу (базовую или от других источников, если они уже посчитаны)
        # Обычно attributes или skills
        base_luck = unit.skills.get("luck", 0)
        # print(base_luck)
        flat_bonus = 3
        pct_bonus = int(base_luck * 0.20)

        total_bonus = flat_bonus + pct_bonus

        # Логируем только при изменении или дебаге
        # logger.log(f"🍀 Fortune: Base {base_luck} -> Bonus {total_bonus}", LogLevel.VERBOSE, "Talent")

        return {"luck": total_bonus}


# ==========================================
# 7.2 Второй шанс
# ==========================================
class TalentSecondChance(BasePassive):
    id = "second_chance"
    name = "Второй шанс"
    description = (
        "«Ошибка? Смертельный промах? Нет. В твоей истории этого никогда не было. Время на секунду замирает, позволяя переписать неудачную строчку сценария.»\n\n"
        "Активно (1 раз в 3 хода): Позволяет перебросить неудачный бросок.\n"
        "Механически: Дает статус 'Преимущество' (Advantage) на следующий бросок."
    )
    is_active_ability = True
    cooldown = 3  # Фактически одноразовое в рамках боя

    def activate(self, unit, *args, **kwargs):
        log_func = kwargs.get("log_func")
        if unit.cooldowns.get(self.id, 0) > 0:
            if log_func: log_func("❌ Вы уже использовали второй шанс в этом бою.")
            return False

        # Даем преимущество (механика переброса реализована через Advantage в системе)
        unit.add_status("advantage", 1, duration=1)
        unit.cooldowns[self.id] = self.cooldown

        if log_func:
            log_func(f"🍀 **{self.name}**: Судьба делает шаг назад. Следующий бросок с Преимуществом!")

        logger.log(f"🍀 Second Chance: {unit.name} gains Advantage for 1 turn", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 7.3 Последовательная удача
# ==========================================
class TalentSequentialLuck(BasePassive):
    id = "sequential_luck"
    name = "Последовательная удача"
    description = (
        "«Неудача — это не конец. Это долг, который мир обязан тебе вернуть. Копи свои провалы, чтобы в нужный момент обналичить их чистым золотом успеха.»\n\n"
        "Пассивно: Компенсация неудач.\n"
        "Эффект: При провале проверки вы получаете очки Удачи (20 - результат броска).\n"
        "Активно (в меню проверок): Можно потратить накопленную Удачу, чтобы превратить провал в успех."
    )
    is_active_ability = False
    #Реализация в UI чеке


# ==========================================
# 7.4 Lucky Bastard (Везучий ублюдок)
# ==========================================
class TalentLuckyBastard(BasePassive):
    id = "lucky_bastard"
    name = "Везучий ублюдок"
    description = (
        "«Пуля прошла сквозь волосы, нож застрял в пряжке ремня, а граната оказалась бракованной. Ты не бессмертен, ты просто... статистическая погрешность.»\n\n"
        "Пассивно: 'Дуракам везет'.\n"
        "При получении урона: 20% шанс, что урон будет снижен вдвое.\n\n"
        "Пассивно: 'Заначка'.\n"
        "В начале боя: 25% шанс обнаружить в инвентаре случайный полезный расходник (Item)."
    )
    is_active_ability = False

    def modify_incoming_damage(self, unit, amount: int, damage_type, **kwargs) -> int:
        """
        Перехватываем урон ДО его нанесения.
        """
        if amount <= 0:
            return amount

        # Бросаем 1d5
        roll = random.randint(1, 5)

        # Если выпала 5 (20% шанс)
        if roll == 5:
            new_amount = amount // 2

            # Логгирование (если передана функция лога)
            # Примечание: modify_incoming_damage может не иметь доступа к ctx.log напрямую,
            # поэтому пишем в системный логгер, а визуально игрок увидит просто сниженный урон.
            logger.log(
                f"🍀 Lucky Bastard: Damage reduced {amount} -> {new_amount} (Rolled 5)",
                LogLevel.NORMAL,
                "Talent"
            )
            return new_amount

        return amount

    def on_combat_start(self, unit, *args, **kwargs):
        log_func = kwargs.get("log_func")
        """
        Механика поиска временных предметов.
        """
        # Сбрасываем память о предыдущем предмете на всякий случай
        if "lucky_bastard_item" in unit.memory:
            # Если вдруг с прошлого боя остался (краш игры и т.д.), лучше почистить
            old_item = unit.memory.pop("lucky_bastard_item")
            if old_item in unit.deck:
                unit.deck.remove(old_item)

        # 1. Проверка шанса (25%)
        if random.random() > 0.25:
            return

        # 2. Список файлов для лута
        target_files = [
            "candy_cards.json",
            "cheese_cards.json",
            "tea_cards.json",
            "consumables_cards.json"
        ]

        loot_pool = []
        base_path = os.path.join("data", "cards")

        # 3. Парсинг файлов
        for filename in target_files:
            filepath = os.path.join(base_path, filename)

            if not os.path.exists(filepath):
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if "id" in item:
                                loot_pool.append(item["id"])
            except Exception as e:
                logger.log(f"🍀 Lucky Bastard Error reading {filename}: {e}", LogLevel.ERROR, "Talent")

        # 4. Выдача награды
        if loot_pool:
            found_id = random.choice(loot_pool)

            # Добавляем в руку/колоду
            unit.deck.append(found_id)

            # === ЗАПОМИНАЕМ, ЧТОБЫ УДАЛИТЬ ПОТОМ ===
            unit.memory["lucky_bastard_item"] = found_id

            # Красивое имя для лога
            item_name = found_id.replace("_", " ").title()

            if log_func:
                log_func(f"🍀 **{self.name}**: Порылся в карманах и нашел... {item_name}! (Временно)")

            logger.log(f"🍀 Lucky Bastard: Found temporary {found_id}", LogLevel.NORMAL, "Talent")
        else:
            if log_func:
                log_func(f"🍀 **{self.name}**: В карманах только дырки...")

    def on_combat_end(self, unit, *args, **kwargs):
        log_func = kwargs.get("log_func")
        """
        Удаляем временный предмет в конце боя.
        """
        temp_item = unit.memory.get("lucky_bastard_item")

        if temp_item:
            # Проверяем, есть ли он еще в колоде (вдруг игрок его уже использовал и он сгорел?)
            if temp_item in unit.deck:
                unit.deck.remove(temp_item)

                if log_func:
                    log_func(f"💨 **{self.name}**: Найденный предмет потерялся в суматохе.")

                logger.log(f"🍀 Lucky Bastard: Removed temporary {temp_item}", LogLevel.NORMAL, "Talent")

            # Очищаем память
            unit.memory.pop("lucky_bastard_item", None)


# ==========================================
# 7.5 Не удача, а мастерство (Not luck, it's just skill)
# ==========================================
class TalentJustSkill(BasePassive):
    id = "not_luck_just_skill"
    name = "Не удача, а мастерство"
    description = (
        "«Ты называешь это чудом? Я называю это расчетом. Когда другие закрывают глаза и молятся, ты просто делаешь то, что должен... чуть более виртуозно, чем обычно.»\n\n"
        "Пассивно: Вы получаете 2 Золотых кости (максимум растет от талантов 7.7 и 7.9).\n"
        "Механика: В меню проверок можно потратить кость, чтобы добавить **1d5+5** к результату.\n"
        "Восстановление: +1 кость при Критическом Провале (1) в проверках."
    )
    is_active_ability = False

    def get_max_charges(self, unit):
        """Динамический расчет максимума."""
        charges = 2
        # Используем безопасную проверку ID, так как talent может быть строкой или объектом
        if "azino_777" in unit.talents: charges += 1
        if "ace_sleeve" in unit.talents: charges += 1
        return charges

    def on_check_roll(self, unit, attribute, context, **kwargs):
        """
        Ленивая инициализация (Lazy Init).
        Срабатывает при ЛЮБОМ броске (атака, навык, характеристика).
        """

        # Проверяем, инициализирована ли память для этого таланта
        if "golden_dice_current" not in unit.memory:
            # Если нет — инициализируем полным зарядом
            max_c = self.get_max_charges(unit)
            unit.memory["golden_dice_current"] = max_c

            logger.log(f"🎲 Golden Dice initialized to {max_c} for {unit.name}", LogLevel.NORMAL, "Talent")

        # P.S. Логика восстановления при "1" находится в UI (components.py),
        # чтобы показать игроку красивое уведомление (Toast).


## ==========================================
# 7.6 Поднять ставки
# ==========================================
class TalentRaiseStakes(BasePassive):
    id = "raise_stakes"
    name = "Поднять ставки"
    description = (
        "«В казино всегда выигрывает заведение... если только ты не станешь заведением. Брось кости так, чтобы они раскололись.»\n\n"
        "Активно (КД: 7): Бросок 1d21.\n"
        "💀 **1-6 (Провал):** Вы получаете статус 'Банкрот' (Входящий урон x1.5 на 3 раунда), теряете 10% HP и 10 Удачи.\n"
        "🎰 **7, 14, 21 (Джекпот):** След. 3 раунда наносит x2 урон. Восст. (Результат) Удачи. Получаете +(Результат/7) к Силе, Скорости и Стойкости.\n"
        "🎲 **Остальное:** Случайный бафф (+1 Сила, Стойкость или Скорость)."
    )
    is_active_ability = True
    cooldown = 7

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0:
            if log_func: log_func(f"⏳ **{self.name}**: Крупье тасует колоду ({unit.cooldowns[self.id]} х).")
            return False

        # Бросок 1d21
        roll = random.randint(1, 21)
        unit.cooldowns[self.id] = self.cooldown

        # === ВАРИАНТ 1: ПРОВАЛ (1-6) ===
        if 1 <= roll <= 6:
            # 1. Потеря HP
            hp_loss = int(unit.max_hp * 0.10)
            unit.current_hp = max(1, unit.current_hp - hp_loss)

            # 2. Потеря Удачи
            current_luck = unit.resources.get("luck", 0)
            unit.resources["luck"] = max(0, current_luck - 10)

            # 3. Статус уязвимости (реализуем через метку в памяти или статус)
            # Вешаем статус-маркер "raise_stakes_fail" на 1 раунд
            unit.add_status("raise_stakes_fail", 1, duration=3)

            if log_func:
                log_func(f"💀 **{self.name}**: ПРОВАЛ (Roll {roll})! -{hp_loss} HP, {current_luck} -10 Удачи. Вы уязвимы (x1.5 Dmg)!")
            logger.log(f"🎰 Raise Stakes FAIL: {unit.name} rolled {roll}. Took dmg & luck drain.", LogLevel.NORMAL, "Talent")

        # === ВАРИАНТ 2: ДЖЕКПОТ (7, 14, 21) ===
        elif roll in [7, 14, 21]:
            multiplier = roll // 7 # 1, 2 или 3

            # 1. Восстановление Удачи
            current_luck = unit.resources.get("luck", 0)
            unit.resources["luck"] = current_luck + roll

            # 2. Баффы
            unit.add_status("attack_power_up", multiplier, duration=3)
            unit.add_status("endurance", multiplier, duration=3)
            unit.add_status("haste", multiplier, duration=3) # Speed

            # 3. Усиление атаки (маркер)
            unit.add_status("raise_stakes_crit", 1, duration=3)

            if log_func:
                log_func(f"🎰 **{self.name}**: ДЖЕКПОТ ({roll})! {current_luck}+{roll} Удачи, +{multiplier} ко всем статам! След. удар x2!")
            logger.log(f"🎰 Raise Stakes JACKPOT: {unit.name} rolled {roll}. Buffs applied.", LogLevel.NORMAL, "Talent")

        # === ВАРИАНТ 3: ОБЫЧНЫЙ УСПЕХ ===
        else:
            # Случайный бафф
            buff = random.choice(["attack_power_up", "endurance", "haste"])
            unit.add_status(buff, 1, duration=3)

            if log_func:
                log_func(f"🎲 **{self.name}**: Ставка сыграла ({roll}). Получено +1 {buff.capitalize()}.")
            logger.log(f"🎰 Raise Stakes Normal: {unit.name} rolled {roll}. +1 {buff}.", LogLevel.VERBOSE, "Talent")

        return True

    # --- ХУКИ ДЛЯ РЕАЛИЗАЦИИ ЭФФЕКТОВ ---

    def modify_incoming_damage(self, unit, amount: int, damage_type, **kwargs) -> int:
        """Реализация эффекта ПРОВАЛА: Входящий урон x1.5"""
        if unit.get_status("raise_stakes_fail") > 0:
            new_amount = int(amount * 1.5)
            # Логируем (если нужно, но в modify_incoming_damage сложно вывести в UI лог)
            return new_amount
        return amount

    def on_hit(self, ctx, **kwargs):
        """Реализация эффекта ДЖЕКПОТА: Исходящий урон x2"""
        # Проверяем наличие маркера
        if ctx.source.get_status("raise_stakes_crit") > 0:
            ctx.damage_multiplier *= 2.0
            ctx.log.append("🎰 **Джекпот**: Урон удвоен!")


# ==========================================
# 7.7 Азино три топора (Azino 777)
# ==========================================
class TalentAzino777(BasePassive):
    id = "azino_777"
    name = "Азино три топора"
    description = (
        "«Казино всегда в выигрыше... пока ты не станешь казино.»\n\n"
        "Активно: Крутить слоты [X] [X] [X]. Стоимость фиксации: 7 / 49 / 343 Удачи.\n"
        "Пассивные бонусы от выпавших чисел (Стаки: 1x -> 1, 2x -> 4, 3x -> 9):\n"
        "• [1] **Паралич** (Дебафф)\n"
        "• [2] **Сила** (Бафф)\n"
        "• [3] **Скорость** (Бафф)\n"
        "• [4] **Смерть** (Урон -5% / -20% / -45% от макс. HP/SP/Stagger)\n"
        "• [5] **Стойкость** (Бафф)\n"
        "• [6] **Урон** (Damage Up)\n"
        "• [7] **Восст. Удачи** (+7/+28/+63)\n\n"
        "Комбинации:\n"
        "🎰 **7-7-7:** Бессмертие, Фулл Хил, Макс Роллы.\n"
        "😈 **6-6-6:** Сила Зверя (Урон x1.66, но урон по себе).\n"
        "💀 **1-1-1:** Потеря всей удачи и 50% HP."
    )
    is_active_ability = True

    def calculate_cost(self, fixed_values: list) -> int:
        """Считает стоимость фиксации: 7 -> 49 -> 343."""
        count = sum(1 for v in fixed_values if v > 0)
        cost = 0
        if count >= 1: cost = 7
        if count >= 2: cost = 49
        if count >= 3: cost = 343
        return cost

    def _apply_slot_passives(self, unit, slots, log_func=None):
        """
        Применяет эффекты от выпавших чисел.
        Логика: 1 совпадение = 1 стак, 2 = 4 стака, 3 = 9 стаков.
        """
        counts = {i: slots.count(i) for i in range(1, 8)}
        effects_applied = []

        for num, count in counts.items():
            if count == 0: continue

            # Формула квадратичного скалирования
            magnitude = count ** 2

            if num == 1:  # Паралич
                unit.add_status("paralysis", magnitude, duration=99)
                effects_applied.append(f"[1] Paralysis +{magnitude}")

            elif num == 2:  # Сила
                unit.add_status("attack_power_up", magnitude, duration=3)
                effects_applied.append(f"[2] Strength +{magnitude}")

            elif num == 3:  # Скорость
                unit.add_status("haste", magnitude, duration=3)
                effects_applied.append(f"[3] Haste +{magnitude}")


            elif num == 4:  # Смерть (Процентный урон)

                # База 5% -> Итого 5% / 20% / 45%

                pct = magnitude * 5

                # Расчет значений для каждого бара отдельно

                dmg_hp = int(unit.max_hp * (pct / 100.0))

                dmg_sp = int(unit.max_sp * (pct / 100.0)) if hasattr(unit, 'max_sp') else 0

                # Применяем урон

                # Используем take_damage для корректной обработки (триггеры, логи)

                unit.take_damage(dmg_hp)

                # Урон по рассудку

                if dmg_sp > 0:
                    unit.take_sanity_damage(dmg_sp)

                # Урон по Stagger (прямое вычитание или метод)

                if hasattr(unit, 'current_stagger') and hasattr(unit, 'max_stagger'):
                    dmg_stagger = int(unit.max_stagger * (pct / 100.0))

                    unit.current_stagger = max(0, unit.current_stagger - dmg_stagger)

                effects_applied.append(f"[4] Death -{pct}% (HP/SP/Stagger)")

            elif num == 5:  # Стойкость
                unit.add_status("endurance", magnitude, duration=3)
                effects_applied.append(f"[5] Endurance +{magnitude}")

            elif num == 6:  # Урон
                unit.add_status("dmg_up", magnitude, duration=3)
                effects_applied.append(f"[6] Dmg Up +{magnitude}")

            elif num == 7:  # Удача
                luck_gain = magnitude * 7  # 7 / 28 / 63
                if "luck" in unit.resources:
                    unit.resources["luck"] += luck_gain
                effects_applied.append(f"[7] Luck +{luck_gain}")

        if log_func and effects_applied:
            log_func(f"🎲 **Эффекты слотов**: {', '.join(effects_applied)}")

    def perform_spin(self, unit, fixed_values: list, log_func=None):
        """Основная логика крутки."""
        # 1. Списание стоимости
        cost = self.calculate_cost(fixed_values)
        if unit.resources.get("luck", 0) < cost:
            if log_func: log_func(f"❌ Недостаточно Удачи! Нужно {cost}.")
            return False

        unit.resources["luck"] -= cost

        # 2. Генерация
        final_slots = []
        for val in fixed_values:
            if val > 0:
                final_slots.append(val)
            else:
                final_slots.append(random.randint(1, 7))

        slots_str = " | ".join([f"[{x}]" for x in final_slots])
        if log_func: log_func(f"🎰 **Вращение...** {slots_str}")

        # 3. Применение пассивных эффектов чисел (баффы/дебаффы)
        self._apply_slot_passives(unit, final_slots, log_func)

        # 4. Обработка особых комбинаций (ДЖЕКПОТЫ)
        if final_slots == [7, 7, 7]:
            unit.heal_hp(9999)
            unit.restore_stagger(9999)
            unit.add_status("azino_jackpot", 1, duration=7)
            msg = "💰 **ДЖЕКПОТ!!!** МУЗЫКА НАЧАЛАСЬ! (Бессмертие 7 ходов, Full Restore)"
            logger.log(f"🎰 Azino JACKPOT for {unit.name}", LogLevel.NORMAL, "Talent")
            if log_func: log_func(msg)

        elif final_slots == [6, 6, 6]:
            unit.add_status("azino_beast", 1, duration=6)
            msg = "😈 **666**: Число Зверя. (Сила растет, но кровь льется)"
            if log_func: log_func(msg)

        elif final_slots == [1, 1, 1]:
            unit.resources["luck"] = 0
            dmg = unit.current_hp // 2
            unit.take_damage(dmg)
            msg = "💀 **1-1-1**: Тотальный крах. Удача обнулена, HP уполовинено."
            if log_func: log_func(msg)

        # Сохраняем слоты в память (для использования в чеках или отображения)
        unit.memory["azino_slots"] = final_slots
        return True


class TalentBlessedByFate(BasePassive):
    id = "blessed_by_fate"  # ID оставил старый для совместимости, можно сменить на lucky_coin
    name = "Счастливая монета"
    description = (
        "«Орел — ты король мира. Решка — ты труп. Судьба не любит полумер.»\n\n"
        "Ресурс: **Счастливая монета**. Восстанавливается 1 шт в начале сцены и при трате Золотой Кости (7.5).\n\n"
        "⚔️ **Активно (Бой, КД: 3):** Подбросить монету для следующей атаки.\n"
        "• **Орел (50%):** Ваш бросок становится 999 (Ломает кубик врага).\n"
        "• **Решка (50%):** Ваш бросок становится 0 (Слом своего оружия, -15% HP).\n\n"
        "🎲 **В проверках (UI):** Потратить монету вместо броска.\n"
        "• **Орел:** Авто-успех (Результат = Сложность).\n"
        "• **Решка:** Крит. Провал (1). (Активирует талант 7.5)."
    )
    is_active_ability = True
    cooldown = 3

    def on_scene_start(self, unit, log_func, **kwargs):
        """Начало дня/сцены - даем 1 монетку."""
        unit.memory["lucky_coin_count"] = 1
        if log_func: log_func("🪙 Вы нашли Счастливую монетку в кармане.")

    def on_combat_start(self, unit, log_func, **kwargs):
        """Страховка инициализации."""
        if "lucky_coin_count" not in unit.memory:
            unit.memory["lucky_coin_count"] = 1

    def activate(self, unit, log_func, **kwargs):
        """
        Боевая активация: Вешаем статус, который сработает на след. ударе.
        """
        # Проверка КД
        if unit.cooldowns.get(self.id, 0) > 0:
            if log_func: log_func(f"⏳ Монетка еще звенит ({unit.cooldowns[self.id]} ход.)")
            return False

        # Проверка наличия монетки (Опционально: если мы хотим тратить ресурс и в бою тоже)
        # Если "Активка раз в 3 хода" - значит ресурс не тратится, а тратится только КД.
        # Но если "Монетка" это предмет - надо тратить.
        # Давай сделаем так: В БОЮ это кулдаун (вы достаете ту самую монету).
        # В ЧЕКАХ это расходник (вы "тратите" удачу).

        unit.add_status("lucky_coin_status", 1, duration=3)
        unit.cooldowns[self.id] = self.cooldown

        if log_func:
            log_func(f"🪙 **{self.name}**: Монета подброшена в воздух... Следующий удар решит всё!")
        logger.log(f"🪙 Lucky Coin activated by {unit.name}", LogLevel.NORMAL, "Talent")
        return True

    # === ХУК ДЛЯ СИНЕРГИИ ===
    # Нам нужно отловить момент траты Золотой Кости, чтобы дать Монетку.
    # Это сложно сделать напрямую, если код 7.5 не вызывает хуки.
    # Поэтому мы добавим метод add_coin, который будем вызывать из 7.5 или UI.

    @staticmethod
    def add_coin(unit, amount=1):
        current = unit.memory.get("lucky_coin_count", 0)
        unit.memory["lucky_coin_count"] = current + amount
        logger.log(f"🪙 {unit.name} gained {amount} Lucky Coin(s). Total: {current + amount}", LogLevel.NORMAL, "Talent")


# ==========================================
# 7.9 Туз в рукаве
# ==========================================
class TalentAceSleeve(BasePassive):
    id = "ace_sleeve"
    name = "Туз в рукаве"
    description = (
        "«Хороший игрок помнит карты. Лучший — прячет их. Гений — играет теми, которых в колоде даже не было.»\n\n"
        "Пассивно: Ваша высокая Удача (Характеристика) раскрывает скрытый потенциал тела и разума.\n"
        "За каждые **10** ед. Характеристики Удачи вы получаете **+7** к параметрам в цикле:\n"
        "1. Стойкость и Психика\n"
        "2. Сила и Мудрость\n"
        "3. Ловкость\n"
        "(Далее повтор цикла)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        current_luck = unit.skills.get("luck", 0)

        # Количество шагов усиления (10 удачи = 1 шаг)
        steps = current_luck // 10

        if steps <= 0:
            return {}

        bonuses = {
            "strength": 0,
            "endurance": 0,
            "agility": 0,
            "wisdom": 0,
            "psych": 0
        }

        for i in range(steps):
            cycle_index = i % 3

            if cycle_index == 0:
                bonuses["endurance"] += 7
                bonuses["psych"] += 7
            elif cycle_index == 1:
                bonuses["strength"] += 7
                bonuses["wisdom"] += 7
            elif cycle_index == 2:
                bonuses["agility"] += 7

        return bonuses

# ==========================================
# 7.10 "Я знаю точно невозможное возможно!"
# ==========================================
class TalentImpossiblePossible(BasePassive):
    id = "impossible_possible"
    name = "Я знаю точно невозможное возможно!"
    description = (
        "«Границы существуют лишь в головах тех, кто боится их перешагнуть. Ты же просто идешь вперед, и мир прогибается под тобой.»\n\n"
        "Пассивно:\n"
        "• **+50** к Характеристике Удачи.\n"
        "• Все лимиты характеристик и навыков увеличены на **10**.\n"
        "• **+10** ко всем результатам проверок (Skill Checks)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        # Прямой бонус к характеристике
        return {"luck": 50}