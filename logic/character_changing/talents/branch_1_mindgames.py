from core.enums import DiceType
from core.logging import logger, LogLevel  # [NEW] Import
from logic.character_changing.passives.base_passive import BasePassive
from logic.statuses.status_constants import NEGATIVE_STATUSES


# ==========================================
# 1.1 Держать себя в руках
# ==========================================
class TalentKeepItTogether(BasePassive):
    id = "keep_it_together"
    name = "Держать себя в руках"
    description = (
        "«Даже когда мир рушится, а разум трещит по швам, ты остаёшься единственным якорем реальности. Дыши.»\n\n"
        "Пассивно: Ваш максимальный Рассудок (SP) увеличен на 20%.\n"
        "WIP Эффект: Если вы впадаете в Панику (SP <= 0), вы не теряете контроль, а получаете бонус к силе всех бросков: +(Макс. SP / 50)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"sp_pct": 20}

    # def on_roll(self, ctx, **kwargs):
    #     stack = kwargs.get("stack", 0)
    #     if ctx.source.current_sp <= 0:
    #         bonus = ctx.source.max_sp // 50
    #         if bonus > 0:
    #             ctx.modify_power(bonus, "Panic (Keep It Together)")


# ==========================================
# 1.2 Центр у равновесия
# ==========================================
class TalentCenterOfBalance(BasePassive):
    id = "center_of_balance"
    name = "Центр у равновесия"
    description = (
        "«Твоё присутствие действует лучше любых успокоительных. Рядом с тобой хаос отступает, уступая место холодной ясности.»\n\n"
        "Эффект: В начале каждого раунда восстанавливает рассудок (SP) всем союзникам (включая вас).\n"
        "Формула восстановления: 2 + (Ваш Макс. SP / 20)."
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        allies = kwargs.get("allies", [unit])  # По умолчанию только себя

        # Формула: 2 + (Макс СП / 20)
        bonus_from_max = unit.max_sp // 20
        heal_amount = 2 + bonus_from_max

        restored_count = 0
        for ally in allies:
            if ally.is_dead(): continue

            old_sp = ally.current_sp
            ally.current_sp = min(ally.max_sp, ally.current_sp + heal_amount)
            diff = ally.current_sp - old_sp

            if diff > 0: restored_count += 1

        # Логируем
        if log_func and restored_count > 0:
            log_func(f"🧠 {self.name}: Восстановлено {heal_amount} SP ({restored_count} союзникам).")

        if restored_count > 0:
            logger.log(f"🧠 Center of Balance: Healed {heal_amount} SP for {restored_count} allies", LogLevel.VERBOSE,
                       "Talent")


# ==========================================
# 1.3 Чай ("ты делаешь великолепный чай")
# ==========================================
class TalentTeaMaster(BasePassive):
    id = "tea_master"
    name = "Чайный мастер"
    description = (
        "«Ты делаешь великолепный чай», — говорят они, не подозревая, что в каждой чашке скрыта маленькая алхимия души.\n\n"
        "Эффект: В начале боя вы добавляете в колоду особые карты чая. Рецепты:\n"
        "☕ **Тёмный чай**: +15% SP.\n"
        "🍃 **Зелёный чай**: +15% SP и +20% Временных ХП.\n"
        "🍎 **Фруктовый чай**: +15% SP и +2 Спешки.\n"
        "🌸 **Чай из сакуры**: Восстанавливает 100% SP и накладывает 3 паралича.\n"
        "🍓 **Ягодный Чай**: +15% SP и +1 Выдержка.\n"
        "🫚 **Имбирный чай**: +15% SP. Снимает или предотвращает негативный эффект.\n"
        "🌺 **Красный чай**: +15% SP и +1 Сила.\n"
        "💀 **Кофе-чай**: Восстанавливает 30 SP, но имеет 1% шанс убить выпившего."
    )
    active = True

    def on_combat_start(self, unit, log_func, **kwargs):
        tea_ids = [
            "tea_dark", "tea_green", "tea_fruit",
            "tea_sakura", "tea_berry", "tea_red", "tea_ginger", "tea_coffee"
        ]
        added_count = 0
        for tid in tea_ids:
            if tid not in unit.deck:
                unit.deck.append(tid)
                added_count += 1

        if log_func:
            log_func(f"☕ **Чайный Мастер**: {added_count} видов чая добавлено в инвентарь.")

        logger.log(f"☕ Tea Master: Added {added_count} tea cards to {unit.name}", LogLevel.NORMAL, "Talent")


# ==========================================
# 1.4 Ума помрачительная сила
# ==========================================
class TalentMindPower(BasePassive):
    id = "mind_power"
    name = "Умопомрачительная сила"
    description = (
        "«Рассудок — это лишь клетка. Сожги его, и твоё тело обретет мощь, недоступную тем, кто цепляется за здравомыслие.»\n\n"
        "Активная способность: Вы можете пожертвовать своим Рассудком (SP), чтобы временно увеличить физическую силу.\n"
        "Курс обмена: 10 SP → +1 Сила (на 1 раунд). Максимум +5 Силы."
    )
    is_active_ability = True
    active_description = "10 SP → +1 Сила (на 1 раунд). Максимум +5 Силы в раунд."
    cooldown = 1

    conversion_options = {
        "10 SP -> +1 Strength": {"cost": 10, "amt": 1},
        "20 SP -> +2 Strength": {"cost": 20, "amt": 2},
        "30 SP -> +3 Strength": {"cost": 30, "amt": 3},
        "40 SP -> +4 Strength": {"cost": 40, "amt": 4},
        "50 SP -> +5 Strength": {"cost": 50, "amt": 5},
    }

    def activate(self, unit, log_func, choice_key=None, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0:
            return False

        if not choice_key or choice_key not in self.conversion_options:
            if log_func: log_func("⚠️ Выберите уровень усиления в списке.")
            return False

        data = self.conversion_options[choice_key]
        cost = data["cost"]
        amount = data["amt"]

        if unit.current_sp < cost:
            if log_func: log_func(f"❌ Недостаточно Рассудка! (Нужно {cost}, есть {unit.current_sp})")
            return False

        unit.current_sp -= cost
        unit.add_status("attack_power_up", amount, duration=1)

        if log_func:
            log_func(f"🧠 **{self.name}**: Пожертвовано {cost} SP -> Получено +{amount} Силы!")

        logger.log(f"🧠 Mind Power: {unit.name} spent {cost} SP for +{amount} Strength", LogLevel.NORMAL, "Talent")

        unit.cooldowns[self.id] = self.cooldown
        return True


# ==========================================
# 1.5 Пик рассудительности
# ==========================================
class TalentPeakSanity(BasePassive):
    id = "peak_sanity"
    name = "Пик рассудительности"
    description = (
        "«Среди какофонии криков и скрежета металла внутри царит абсолютная тишина. Кристально чистый разум отвергает грязь этого Города.»\n\n"
        "Пассивно: Пока SP > 50%, минимальное значение всех кубиков увеличено на +2.\n"
        "Эффект 'Ясность': Вы получаете заряды (Макс = SP / 50), которые автоматически тратятся для полной отмены накладываемых негативных эффектов. Восстанавливается 1 заряд раз в 5 раундов."
    )
    is_active_ability = False

    def _get_max_clarity(self, unit):
        sp = getattr(unit, 'max_sp', 20)
        return max(1, sp // 50)

    def on_combat_start(self, unit, log_func, **kwargs):
        if unit.memory.get("peak_sanity_initialized"):
            return

        max_c = self._get_max_clarity(unit)
        unit.add_status("clarity", max_c, duration=99)
        unit.memory["clarity_cooldown_counter"] = 0
        unit.memory["peak_sanity_initialized"] = True

        if log_func:
            log_func(f"✨ **Ясность**: Получено {max_c} зарядов (Максимум).")

    def on_roll(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        if ctx.source.max_sp > 0:
            ratio = ctx.source.current_sp / ctx.source.max_sp
            if ratio > 0.5:
                limit = ctx.dice.min_val + 2
                if ctx.base_value < limit:
                    diff = limit - ctx.base_value
                    ctx.modify_power(diff, "Peak Sanity (Min+2)")

    def on_round_end(self, unit, log_func=None, **kwargs):
        limit = self._get_max_clarity(unit)
        current = unit.get_status("clarity")

        if current < limit:
            counter = unit.memory.get("clarity_cooldown_counter", 0) + 1

            if counter >= 5:
                unit.add_status("clarity", 1, duration=99)
                unit.memory["clarity_cooldown_counter"] = 0
                if log_func: log_func(f"✨ **Ясность**: Регенерация +1 (5 раундов прошло).")
                logger.log(f"✨ Clarity Regen: {unit.name} +1 charge", LogLevel.VERBOSE, "Talent")
            else:
                unit.memory["clarity_cooldown_counter"] = counter

    def on_before_status_add(self, unit, status_id, amount):

        if status_id in NEGATIVE_STATUSES:
            clarity = unit.get_status("clarity")
            if clarity > 0:
                unit.remove_status("clarity", 1)
                logger.log(f"✨ Clarity Block: {unit.name} blocked {status_id}", LogLevel.NORMAL, "Talent")
                return False, f"✨ Clarity blocked **{status_id}**! (-1 stack)"

        return True, None


# ==========================================
# 1.6 Психическая нагрузка
# ==========================================
class TalentPsychicStrain(BasePassive):
    id = "psychic_strain"
    name = "Психическая нагрузка"
    description = (
        "«Тяжесть твоего сознания невыносима для одного. Делись этим бременем с каждым ударом, пока их разум не даст трещину.»\n\n"
        "Пассивно: Каждая ваша успешная атака наносит дополнительный БЕЛЫЙ урон (по Рассудку).\n"
        "Урон равен 4% от вашего максимального SP."
    )
    is_active_ability = False

    def on_hit(self, ctx, **kwargs):
        # 1. Проверяем, есть ли цель
        if not ctx.target: return

        # 2. Проверяем, что это Атакующий кубик
        if ctx.dice.dtype not in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            return

        # 3. Считаем 4% от Макс SP
        sp_dmg = int(ctx.source.max_sp * 0.04)

        if sp_dmg > 0:
            ctx.target.take_sanity_damage(sp_dmg)
            ctx.log.append(f"🧠 **{self.name}**: +{sp_dmg} SP Dmg (Белый урон)")
            logger.log(f"🧠 Psychic Strain: Dealt {sp_dmg} SP damage to {ctx.target.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 1.7 Невыносимое присутствие
# ==========================================
class TalentUnbearablePresence(BasePassive):
    id = "unbearable_presence"
    name = "Невыносимое присутствие"
    description = (
        "«Одного твоего взгляда достаточно, чтобы воздух стал тяжелым, как свинец. Враги чувствуют это кожей — дыхание бездны за их спинами.»\n\n"
        "Эффект: В начале раунда все враги, которые видят вас (нет статуса Stealth/Invisible), получают Белый урон (SP).\n"
        "Урон: 2.5% от вашего Максимального Рассудка."
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        if unit.get_status("stealth") > 0 or unit.get_status("invisible") > 0:
            return

        enemies = kwargs.get("enemies")
        if not enemies:
            op = kwargs.get("opponent")
            enemies = [op] if op else []

        dmg = int(unit.max_sp * 0.025)
        if dmg < 1 and unit.max_sp > 0: dmg = 1
        if dmg <= 0: return

        hit_count = 0
        for enemy in enemies:
            if enemy and not enemy.is_dead():
                enemy.take_sanity_damage(dmg)
                hit_count += 1

        if log_func and hit_count > 0:
            log_func(f"👁️ **{self.name}**: {hit_count} врагов подавлены аурой (-{dmg} SP)")

        if hit_count > 0:
            logger.log(f"👁️ Unbearable Presence: {hit_count} enemies took {dmg} SP damage", LogLevel.VERBOSE, "Talent")


# ==========================================
# 1.8 Эмоциональный шторм
# ==========================================
class TalentEmotionalStorm(BasePassive):
    id = "emotional_storm"
    name = "Эмоциональный шторм"
    description = (
        "«Битва — это сцена, а эмоции — топливо. Чем ярче горит пламя страсти и отчаяния, тем сильнее становятся актеры этой пьесы.»\n\n"
        "Механика: Вы получаете Эмоциональные Монеты за каждый Макс/Мин бросок и исход столкновения.\n"
        "Эмоциональный Уровень (0-5) растет по мере накопления монет, даруя мощные баффы и восстанавливая свет души."
    )
    is_active_ability = False

    def _get_threshold(self, level):
        thresholds = {0: 3, 1: 6, 2: 11, 3: 18, 4: 27}
        return thresholds.get(level, 999)

    def _gain_coin(self, unit, kind, ctx):
        if "emo_level" not in unit.memory: return
        lvl = unit.memory["emo_level"]
        if lvl >= 5: return

        unit.memory["emo_progress"] += 1
        if kind == "pos":
            unit.memory["emo_coins_pos"] += 1
            if ctx and hasattr(ctx, 'log') and ctx.log is not None:
                ctx.log.append("🟢 **Эмоции**: +1 Позитивная монета")
        else:
            unit.memory["emo_coins_neg"] += 1
            if ctx and hasattr(ctx, 'log') and ctx.log is not None:
                ctx.log.append("🔴 **Эмоции**: +1 Негативная монета")

    def on_round_start(self, unit, log_func, **kwargs):
        if not unit.memory.get("emotional_storm_initialized"):
            unit.memory["emotional_storm_initialized"] = True
            unit.memory["emo_level"] = 0
            unit.memory["emo_progress"] = 0
            unit.memory["emo_coins_pos"] = 0
            unit.memory["emo_coins_neg"] = 0
            if log_func: log_func(f"🌪️ **{self.name}**: Занавес поднимается. Отсчет эмоций начат.")

        lvl = unit.memory.get("emo_level", 0)
        if lvl > 0:
            buffs = []
            if lvl >= 1:
                unit.add_status("haste", 2, duration=1)
                buffs.append("Haste")
            if lvl >= 2:
                unit.add_status("endurance", 2, duration=1)
                buffs.append("Endurance")
            if lvl >= 3:
                unit.add_status("protection", 2, duration=1)
                buffs.append("Protection")
            if lvl >= 4:
                unit.add_status("attack_power_up", 2, duration=1)
                buffs.append("Strength")
            if lvl >= 5:
                unit.add_status("haste", 2, duration=1)
                unit.add_status("attack_power_up", 2, duration=1)
                buffs.append("MAX POWER")

            if log_func:
                log_func(f"🌪️ **Эмоции (Ур. {lvl})**: Резонанс души ({', '.join(buffs)}).")

            logger.log(f"🌪️ Emotional Storm Lvl {lvl}: Applied buffs {buffs}", LogLevel.VERBOSE, "Talent")

    def on_roll(self, ctx, **kwargs):
        if not ctx.dice: return
        if ctx.base_value == ctx.dice.max_val:
            self._gain_coin(ctx.source, "pos", ctx)
        elif ctx.base_value == ctx.dice.min_val:
            self._gain_coin(ctx.source, "neg", ctx)

    def on_clash_win(self, ctx, **kwargs):
        self._gain_coin(ctx.source, "pos", ctx)

    def on_clash_lose(self, ctx, **kwargs):
        self._gain_coin(ctx.source, "neg", ctx)

    def on_round_end(self, unit, log_func, **kwargs):
        lvl = unit.memory.get("emo_level", 0)
        progress = unit.memory.get("emo_progress", 0)

        if lvl < 5:
            req = self._get_threshold(lvl)
            if progress >= req:
                unit.memory["emo_level"] += 1
                new_lvl = unit.memory["emo_level"]
                if log_func:
                    log_func(f"⚡ **Эмоциональный Уровень повышен!** ({new_lvl - 1} -> {new_lvl}). Свет восстановлен.")

                logger.log(f"⚡ Emotional Level Up: {unit.name} reached level {new_lvl}", LogLevel.NORMAL, "Talent")

                unit.current_sp = min(unit.max_sp, unit.current_sp + 10)

        if unit.memory.get("emo_level", 0) >= 5:
            unit.active_buffs["berserker_rage"] = 2
            if log_func:
                log_func("😡 **Эмоции (MAX)**: Предел достигнут! Получен дополнительный Слот Скорости.")

        pos = unit.memory.get("emo_coins_pos", 0)
        neg = unit.memory.get("emo_coins_neg", 0)

        if log_func:
            log_func(f"🌪️ **Итог Эмоций**: 🟢 {pos} | 🔴 {neg}")

        if pos == 0 and neg == 0: return

        if pos > neg:
            heal_sp = (pos - neg) * 2
            unit.current_sp = min(unit.max_sp, unit.current_sp + heal_sp)
            if log_func: log_func(f"✨ **Позитивный резонанс**: Восстановлено {heal_sp} SP.")
        elif neg > pos:
            heal_hp = (neg - pos) * 2
            unit.heal_hp(heal_hp)
            if log_func: log_func(f"🩸 **Негативный резонанс**: Восстановлено {heal_hp} HP.")


# ==========================================
# 1.9 А: Безопасное ЭГО
# ==========================================
class TalentSafeEGO(BasePassive):
    id = "safe_ego"
    name = "Безопасное ЭГО"
    description = (
        "«Воля — это топливо. Сжигай её, чтобы сиять.»\n\n"
        "Условия:\n"
        "• Активация: Если SP > 25% от Максимума.\n"
        "• Деактивация: Если SP падает ниже 25%.\n"
        "Эффекты режима:\n"
        "• Входящий урон -20%.\n"
        "• Исходящий урон +20%.\n"
        "Цена: -50 SP в конце каждого раунда."
    )
    is_active_ability = False

    def _get_threshold(self, unit):
        return int(unit.max_sp * 0.25)

    def on_round_start(self, unit, log_func, **kwargs):
        """Проверка входа в ЭГО."""
        threshold = self._get_threshold(unit)
        is_active = unit.get_status("ego_manifested") > 0

        # Вход
        if unit.current_sp > threshold and not is_active:
            unit.add_status("ego_manifested", 1, duration=99)
            if log_func: log_func(f"🛡️ **{self.name}**: Рассудок стабилен. Э.Г.О материализовано!")
            logger.log(f"🛡️ Safe EGO: Activated for {unit.name}", LogLevel.NORMAL, "Talent")

        # Выход (если вдруг SP упало в начале раунда)
        elif unit.current_sp <= threshold and is_active:
            unit.remove_status("ego_manifested")
            if log_func: log_func(f"❄️ **{self.name}**: Рассудок угас. Э.Г.О развеялось.")

    def on_round_end(self, unit, log_func, **kwargs):
        """Плата за силу."""
        if unit.get_status("ego_manifested") > 0:
            cost = 50
            # Списываем SP
            unit.take_sanity_damage(cost)

            # Проверяем, не упали ли мы ниже порога после оплаты
            threshold = self._get_threshold(unit)
            if unit.current_sp <= threshold:
                unit.remove_status("ego_manifested")
                if log_func: log_func(f"❄️ **{self.name}**: Энергия исчерпана (-{cost} SP). Э.Г.О отключено.")
            else:
                if log_func: log_func(f"🔥 **{self.name}**: Поддержание Э.Г.О (-{cost} SP).")

    def modify_incoming_damage(self, unit, amount, damage_type, **kwargs):
        """-20% входящего урона."""
        if unit.get_status("ego_manifested") > 0:
            return int(amount * 0.8)
        return amount

    def modify_outgoing_damage(self, unit, amount, damage_type, **kwargs):
        """+20% исходящего урона."""
        if unit.get_status("ego_manifested") > 0:
            return int(amount * 1.2)
        return amount


# ==========================================
# 1.9 Б: Не теряя себя (The Mutation)
# ==========================================
class TalentControlledDistortion(BasePassive):
    id = "controlled_distortion"
    name = "Не теряя себя (Искажение)"
    description = (
        "«Форма следует за желанием. Твое тело перестраивается под твою волю.»\n\n"
        "Условия:\n"
        "• Вход: Если SP < 25% (Кризис).\n"
        "• Выход: Если SP > 75% (Покой).\n"
        "Эффекты:\n"
        "• ВСЕ Характеристики (Сила, Ловкость и т.д.) х1.5.\n"
        "Особенность: В конце хода восстанавливает 50 SP."
    )
    is_active_ability = False

    def on_round_start(self, unit, *args, **kwargs):
        log_func = kwargs.get("log_func")
        is_active = unit.get_status("distortion_form") > 0
        low = int(unit.max_sp * 0.25)
        high = int(unit.max_sp * 0.75)

        # Вход (Безумие)
        if unit.current_sp < low and not is_active:
            unit.add_status("distortion_form", 1, duration=99)
            if log_func: log_func(f"🌑 **{self.name}**: Кризис рассудка. Тело Искажается!")
            logger.log(f"🌑 Distortion Entered: {unit.name}", LogLevel.NORMAL, "Talent")

        # Выход (Умиротворение)
        elif unit.current_sp > high and is_active:
            unit.remove_status("distortion_form")
            if log_func: log_func(f"☀️ **{self.name}**: Разум успокоился. Искажение отступает.")
    #
    def on_round_end(self, unit, log_func, **kwargs):
        # Зверь успокаивается
        if unit.get_status("distortion_form") > 0:
            regen = 50
            unit.restore_sp(regen)
            if log_func: log_func(f"🩸 **{self.name}**: Искажение стабилизируется (+{regen} SP).")

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        """
        Возвращает словарь бонусов (+50% к статам).
        """
        # 1. ЗАЩИТА ОТ КРАША ПРИ ЗАГРУЗКЕ
        # Если юнит еще не до конца создан (нет атрибутов или метода статусов) — возвращаем пустоту.
        if not hasattr(unit, "attributes") or not hasattr(unit, "get_status"):
            return {}

        # 2. ПРОВЕРКА СТАТУСА
        # Если статус не активен — бонусов нет.
        if unit.get_status("distortion_form") <= 0:
            return {}

        # 3. РАСЧЕТ БОНУСОВ
        # Мы не меняем unit.attributes, мы создаем словарь добавок.
        # Чтобы получить x1.5, нам нужно вернуть +50% от текущего значения.
        modifiers = {}

        # Берем базовые атрибуты юнита (Сила, Ловкость и т.д.)
        for stat_name, value in unit.attributes.items():
            if isinstance(value, (int, float)):
                # +50% (округление вниз)
                bonus = int(value * 0.5)
                if bonus > 0:
                    modifiers[stat_name] = bonus

        # Если нужно логировать, лучше делать это редко или при изменении,
        # иначе засрет консоль, т.к. этот метод может вызываться часто.
        logger.log(f"Distortion Modifiers: {modifiers}", LogLevel.VERBOSE, "Talent")

        return modifiers