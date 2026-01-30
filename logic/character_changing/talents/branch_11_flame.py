from core.logging import logger, LogLevel  # [NEW] Import
from logic.character_changing.passives.base_passive import BasePassive

# Список ID талантов ветки 11 (используется для расчёта прокачки)
BRANCH_11_IDS = [
    "strike_iron_hot", "spark", "cauterization", "hot_talent",
    "body_adaptation", "hearth_of_power", "ashes_to_ashes", "hellfire",
    "wildfire", "fiery_temper", "ifrit", "phoenix", "firestorm", "burn_me_down"
]


# ==========================================
# 11.1 Куй железо пока горячо
# ==========================================
class TalentStrikeWhileIronHot(BasePassive):
    id = "strike_iron_hot"
    name = "Куй железо пока горячо"
    description = (
        "11.1 Ковка +3.\n"
        "Созданное вами оружие накладывает +1 Горения (если уже имеет этот эффект)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"blacksmithing": 3}  # Условно "ковка"


# ==========================================
# 11.2 Искра
# ==========================================
class TalentSpark(BasePassive):
    id = "spark"
    name = "Искра"
    description = (
        "11.2 Активно (Атака): 'Искра'. КД 3 раунда.\n"
        "Накладывает 4 Горения.\n"
        "Скалирование: За каждые 2 таланта ветки -> Мин. ролл +1, Горение +2.\n"
        "Получает улучшения от других талантов ветки."
    )
    is_active_ability = True
    cooldown = 3

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        # Логика подсчета талантов ветки 11 для скалирования
        # Count talents in this branch excluding 11.1 (strike_iron_hot) and 11.2 (spark)
        branch_count = 0
        if hasattr(unit, "talents"):
            for t in unit.talents:
                if t in BRANCH_11_IDS and t not in ("strike_iron_hot", "spark"):
                    branch_count += 1

        # Базовое Горение = 4, за каждые 2 таланта +2 к Горению
        burn_amount = 4 + 2 * (branch_count // 2)
        # Применяем Горение к цели, если она передана в kwargs
        target = kwargs.get("target")
        if target:
            target.add_status("burn", burn_amount, duration=99)
            if log_func:
                log_func(f"🔥 {unit.name} used Spark on {target.name}: +{burn_amount} Burn")
        else:
            if log_func:
                log_func(f"🔥 {unit.name} used Spark: no target provided. (+{burn_amount} Burn would be applied)")

        # --- Create or update the Spark attack card dynamically and register it ---
        try:
            from core.card import Card
            from core.dice import Dice
            from core.enums import DiceType
            from core.library import Library

            # Calculate roll scaling: min increases by 1 per 2 talents (branch_count//2)
            min_roll = max(1, 1 + (branch_count // 2))
            # Scale max by level (simple rule): max = min + 4 + level//2
            max_roll = min_roll + 4 + max(0, unit.level // 2)

            # Build script to apply burn on hit
            burn_script = {
                "on_hit": [
                    {"script_id": "apply_status",
                     "params": {"status": "burn", "base": burn_amount, "duration": 99, "target": "target"}}
                ]
            }

            spark_card_id = "spark_attack"
            spark_card = Card(
                id=spark_card_id,
                name="Spark Attack",
                tier=1,
                card_type="Melee",
                description=f"Spark attack: deals burn +{burn_amount}",
                dice_list=[Dice(min_roll, max_roll, DiceType.BLUNT, scripts=burn_script)],
                scripts={}
            )

            Library.register(spark_card)
        except Exception:
            # If dynamic creation fails, ignore — card fallback handled elsewhere
            pass

        # Добавляем карту-атаку в колоду (выдача карты игроку при использовании)
        spark_card_id = "spark_attack"
        if hasattr(unit, "deck") and spark_card_id not in unit.deck:
            unit.deck.append(spark_card_id)
            if log_func:
                log_func(f"🃏 {unit.name} received card: {spark_card_id}")
            logger.log(f"🃏 Spark: Added {spark_card_id} to {unit.name}", LogLevel.NORMAL, "Talent")

        # Ifrit улучшение: временная иммунизация к урону от Горения на следующий раунд
        if "ifrit" in getattr(unit, "talents", []):
            unit.active_buffs["ifrit_burn_immunity"] = unit.active_buffs.get("ifrit_burn_immunity", 0) + 1
            if log_func:
                log_func("✨ Ifrit: next round immune to Burn damage.")
            logger.log(f"✨ Ifrit Immunity active for {unit.name}", LogLevel.VERBOSE, "Talent")

        unit.cooldowns[self.id] = self.cooldown
        if log_func: log_func("🔥 **Искра**: Атака проведена!")
        logger.log(f"🔥 Spark activated by {unit.name} (Burn +{burn_amount})", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 11.3 Прижигание ран
# ==========================================
class TalentCauterization(BasePassive):
    id = "cauterization"
    name = "Прижигание ран"
    description = (
        "11.3 Вы можете атаковать себя (без HP урона), накладывая эффекты карты.\n"
        "Пассивно: Горение сжигает Кровотечение (1 Горения снимает 3 Кровотечения)."
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        # Логика конвертации
        burn = unit.get_status("burn")
        bleed = unit.get_status("bleed")

        if burn > 0 and bleed > 0:
            # Сколько можем снять
            remove_bleed = burn * 3
            actual_remove = min(bleed, remove_bleed)
            unit.remove_status("bleed", actual_remove)
            if log_func: log_func(f"❤️‍🔥 **{self.name}**: Сожжено {actual_remove} Кровотечения.")
            logger.log(f"❤️‍🔥 Cauterization: Removed {actual_remove} Bleed for {unit.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 11.3 (Опц) Горячий
# ==========================================
class TalentHot(BasePassive):
    id = "hot_talent"
    name = "Горячий"
    description = (
        "11.3 Опц: Речь +3.\n"
        "Активно: 'Roast' (1d20 + Речь). Успех: 5 SP урона, Дизмораль (Помеха врагу), 1 Горение."
    )
    is_active_ability = True

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"eloquence": 3}  # Речь

    def activate(self, unit, log_func, **kwargs):
        if log_func: log_func("🎤 **Roast**: Попытка унизить врага (Логика броска).")
        logger.log(f"🎤 Roast activated by {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 11.4 Адаптация тела
# ==========================================
class TalentBodyAdaptation(BasePassive):
    id = "body_adaptation"
    name = "Адаптация тела"
    description = (
        "11.4 Ожоги заживают как обычные раны.\n"
        "Вне боя (15 мин): Восстанавливает всё HP, потерянное от Горения."
    )
    is_active_ability = False


# ==========================================
# 11.5 Очаг силы
# ==========================================
class TalentHearthOfPower(BasePassive):
    id = "hearth_of_power"
    name = "Очаг силы"
    description = (
        "11.5 За каждые 5 Горения на вас -> +1 Сила (Макс +3)."
    )
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        burn = unit.get_status("burn")
        bonus = min(3, burn // 5)
        if bonus > 0:
            unit.add_status("strength", bonus, duration=1)
            if log_func: log_func(f"💪 **{self.name}**: {burn} Горения -> +{bonus} Сила.")
            logger.log(f"💪 Hearth of Power: +{bonus} Strength for {unit.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 11.5 (Опц) Пепел к пеплу
# ==========================================
class TalentAshesToAshes(BasePassive):
    id = "ashes_to_ashes"
    name = "Пепел к пеплу"
    description = (
        "11.5 Опц: Убийство врага Горением -> Получение его атрибутов (1 к 5) на 1 час."
    )
    is_active_ability = False


# ==========================================
# 11.6 Адское пламя
# ==========================================
class TalentHellfire(BasePassive):
    id = "hellfire"
    name = "Адское пламя"
    description = (
        "11.6 Ваш Огонь наносит 1/3 урона Выдержке (SP/Stagger) врага.\n"
        "Улучшение Искры: Можно опционально снять всё Горение с себя."
    )
    is_active_ability = False


# ==========================================
# 11.7 Лесной пожар
# ==========================================
class TalentWildfire(BasePassive):
    id = "wildfire"
    name = "Лесной пожар"
    description = (
        "11.7 Смерть существа в бою -> 1/3 его Горения передается всем его союзникам."
    )
    is_active_ability = False


# ==========================================
# 11.7 (Опц) Пылкий нрав
# ==========================================
class TalentFieryTemper(BasePassive):
    id = "fiery_temper"
    name = "Пылкий нрав"
    description = (
        "11.7 Опц: Если вас бьют Ближней атакой пока вы горите -> Враг получает 2 Горения."
    )
    is_active_ability = False

    def on_take_damage(self, unit, amount, source, **kwargs):
        # 1. Извлекаем функцию логгирования (вернет None, если её нет)
        log_func = kwargs.get("log_func")
        if unit.get_status("burn") > 0:
            if source and hasattr(source, "add_status"):
                source.add_status("burn", 2, duration=99)
                if log_func:
                    log_func(f"🔥 **{self.name}**: {source.name} receives 2 Burn (retaliation)")
                logger.log(f"🔥 Fiery Temper: Retaliated 2 Burn to {source.name}", LogLevel.VERBOSE, "Talent")


# ==========================================
# 11.8 Ифрит
# ==========================================
class TalentIfrit(BasePassive):
    id = "ifrit"
    name = "Ифрит"
    description = (
        "11.8 Горение на вас восстанавливает Выдержку (1/3 от урона Горения).\n"
        "Улучшение Искры: После использования нет урона от Горения на след. раунд."
    )
    is_active_ability = False

    def modify_incoming_damage(self, unit, amount: int, damage_type: str, stack=0) -> int:
        """
        При получении урона от Горения: восстанавливаем часть Выдержки (stagger)
        и, при наличии временной иммунизации, поглощаем урон.
        """
        if damage_type != "burn" or amount <= 0:
            return amount

        # Если есть временная иммунизация от Искры — поглощаем урон и сбрасываем флаг
        immunity = unit.active_buffs.get("ifrit_burn_immunity", 0)
        if immunity > 0:
            unit.active_buffs["ifrit_burn_immunity"] = max(0, immunity - 1)
            # Восстанавливаем выдержку на 1/3 от потенциального урона
            heal = amount // 3
            if heal > 0:
                unit.current_stagger = min(unit.max_stagger, unit.current_stagger + heal)
                logger.log(f"✨ Ifrit (Immunity): Absorbed burn damage, healed {heal} Stagger", LogLevel.VERBOSE,
                           "Talent")
            return 0

        # Иначе — восстанавливаем 1/3 от урона в Stagger и пропускаем оставшийся урон
        heal = amount // 3
        if heal > 0:
            unit.current_stagger = min(unit.max_stagger, unit.current_stagger + heal)
            logger.log(f"✨ Ifrit: Healed {heal} Stagger from {amount} Burn", LogLevel.VERBOSE, "Talent")

        # Возвращаем оригинальный урон (не уменьшаем здесь — это делает burn_me_down)
        return amount


# ==========================================
# 11.9 Феникс
# ==========================================
class TalentPhoenix(BasePassive):
    id = "phoenix"
    name = "Феникс"
    description = (
        "11.9 Смерть союзника от Горения -> Воскрешение с 10% HP, снятие Горения."
    )
    is_active_ability = False


# ==========================================
# 11.9 (Опц) Огненный шторм
# ==========================================
class TalentFirestorm(BasePassive):
    id = "firestorm"
    name = "Огненный шторм"
    description = (
        "11.9 Опц: Аура (Вкл/Выкл). Наносит 3 Горения всем вокруг в начале раунда."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        # Переключатель
        if unit.active_buffs.get("firestorm_aura"):
            del unit.active_buffs["firestorm_aura"]
            if log_func: log_func("🌪️ **Огненный шторм**: Деактивирован.")
        else:
            unit.active_buffs["firestorm_aura"] = 999
            if log_func: log_func("🌪️ **Огненный шторм**: Активирован (Аура).")

        logger.log(f"🌪️ Firestorm Aura toggled for {unit.name}", LogLevel.NORMAL, "Talent")
        return True

    def on_round_start(self, unit, log_func, enemies=None, allies=None, **kwargs):
        """
        Если аура активна, накладывает 3 Горения на всех существ вокруг вас
        в начале раунда (исключая вас самого).
        """
        if not unit.active_buffs.get("firestorm_aura"):
            return

        # Собираем цели (враги + союзники), избегая дубликатов
        targets = []
        if enemies:
            targets.extend(enemies)
        if allies:
            targets.extend(allies)

        applied = []
        seen = set()
        for t in targets:
            if not t or t is unit: continue
            if t.is_dead(): continue
            if id(t) in seen: continue
            seen.add(id(t))
            # Накладываем 3 Горения с постоянной длительностью
            t.add_status("burn", 3, duration=99)
            applied.append(t.name)

        if applied and log_func:
            log_func(f"🌪️ Огненный шторм: +3 Burn -> {', '.join(applied)}")

        if applied:
            logger.log(f"🌪️ Firestorm applied burn to {len(applied)} targets", LogLevel.VERBOSE, "Talent")


# ==========================================
# 11.10 Сожги меня дотла
# ==========================================
class TalentBurnMeDown(BasePassive):
    id = "burn_me_down"
    name = "Сожги меня дотла"
    description = (
        "11.10 Урон от Горения по вам снижен вдвое (Ифрит восстанавливает от полного).\n"
        "Активно (1/день): 'Огненный смерч'. Получить 50 Горения -> Масс атака (25 Горения всем).\n"
        "Улучшение Искры: Можно получить 4+(Lvl/2) Горения при использовании."
    )
    is_active_ability = True
    cooldown = 99

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        unit.add_status("burn", 50, duration=99)
        unit.cooldowns[self.id] = self.cooldown
        if log_func: log_func("🔥 **Огненный смерч**: Вы получили 50 Горения. Атака всем врагам!")
        logger.log(f"🔥 Burn Me Down activated for {unit.name}", LogLevel.NORMAL, "Talent")
        return True

    def modify_incoming_damage(self, unit, amount: int, damage_type: str, stack=0) -> int:
        """
        Уменьшает входящий урон от Горения вдвое.
        """
        if damage_type == "burn" and amount > 0:
            new_amount = amount // 2
            logger.log(f"🔥 Burn Me Down: Reduced burn dmg {amount} -> {new_amount}", LogLevel.VERBOSE, "Talent")
            return new_amount
        return amount