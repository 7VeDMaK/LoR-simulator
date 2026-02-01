from core.logging import logger, LogLevel  # [NEW] Import
from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# 13.1 Best Friends Forever
# ==========================================
class TalentBestFriendsForever(BasePassive):
    id = "best_friends_forever"
    name = "Best Friends Forever"
    description = (
        "13.1 Вы получаете знания о базовом роботостроении.\n"
        "Эффект: Вы можете создавать простых роботов-спутников (Макс. 1).\n"
        "Пассивно: +2 к Инженерии."
    )
    is_active_ability = True

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"engineering": 2}

    def activate(self, unit, log_func, **kwargs):
        if log_func: log_func("🤖 **Создание робота**: Меню крафта спутника (Заглушка).")
        logger.log(f"🤖 Robot Crafting Menu opened by {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 13.2 Little Big Trouble
# ==========================================
class TalentLittleBigTrouble(BasePassive):
    id = "little_big_trouble"
    name = "Little Big Trouble"
    description = (
        "13.2 Знания о том, как лучше собрать робота.\n"
        "Эффект: Увеличение урона/брони/качества робота. Открывает слоты модулей."
    )
    is_active_ability = False


# ==========================================
# 13.2 (Опц) Расширитель ячеек
# ==========================================
class TalentCellExpander(BasePassive):
    id = "cell_expander"
    name = "Расширитель ячеек"
    description = "13.2 Опц: Максимальное количество модулей робота повышается до 2."
    is_active_ability = False


# ==========================================
# 13.3 To hell with the first law!
# ==========================================
class TalentNoFirstLaw(BasePassive):
    id = "no_first_law"
    name = "To hell with the first law!"
    description = (
        "13.3 Базовый ИИ для робота.\n"
        "Эффект: Робот принимает самостоятельные решения, улучшение характеристик."
    )
    is_active_ability = False


# ==========================================
# 13.4 Яркий талант
# ==========================================
class TalentBrightTalent(BasePassive):
    id = "bright_talent"
    name = "Яркий талант"
    description = (
        "13.4 Бросок Инженерии теперь имеет формулу 1d10+10.\n"
        "Пассивно: +3 к Инженерии."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"engineering": 3}

    def modify_check_parameters(self, unit, stat_key: str, params: dict) -> dict:
        """Изменяем проверки инженерии на d10+10."""
        if stat_key == "engineering":
            params["die_max"] = 10
            params["base_bonus"] = 10
        return params


# ==========================================
# 13.5 Smaller Lighter Faster
# ==========================================
class TalentSmallerLighterFaster(BasePassive):
    id = "smaller_lighter_faster"
    name = "Smaller Lighter Faster"
    description = (
        "13.5 Ваш робот научился использовать разные типы вооружения.\n"
        "Можно встраивать дополнительные модификации."
    )
    is_active_ability = False


# ==========================================
# 13.5 (Опц) Фрейм-апгрейд
# ==========================================
class TalentFrameUpgrade(BasePassive):
    id = "frame_upgrade"
    name = "Фрейм-апгрейд"
    description = "13.5 Опц: Максимальное количество модулей робота повышается до 3."
    is_active_ability = False


# ==========================================
# 13.6 Сделано на века
# ==========================================
class TalentMadeToLast(BasePassive):
    id = "made_to_last"
    name = "Сделано на века"
    description = "13.6 Повышает финальное качество снаряжения и модификаций на 1."
    is_active_ability = False


# ==========================================
# 13.7 Chimera Core
# ==========================================
class TalentChimeraCore(BasePassive):
    id = "chimera_core"
    name = "Chimera Core"
    description = (
        "13.7 Робот может трансформировать тело (переключение форм).\n"
        "Максимальное количество форм: 2."
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        if log_func: log_func("🔄 **Трансформация**: Робот меняет форму (Заглушка).")
        logger.log(f"🔄 Chimera Core transformation for {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 13.8 Upshot Robot
# ==========================================
class TalentUpshotRobot(BasePassive):
    id = "upshot_robot"
    name = "Upshot Robot"
    description = (
        "13.8 Робот адаптируется и запоминает паттерны врага.\n"
        "Эффект: Бонусы в столкновении с уже известным типом врага.\n"
        "Пассивно: +3 к Мудрости."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"wisdom": 3}


# ==========================================
# 13.8 (Опц) Квантовый хаб
# ==========================================
class TalentQuantumHub(BasePassive):
    id = "quantum_hub"
    name = "Квантовый хаб"
    description = "13.8 Опц: Максимальное количество модулей робота повышается до 4."
    is_active_ability = False


# ==========================================
# 13.9 Jack-of-All-Trades Mode
# ==========================================
class TalentJackOfAllTrades(BasePassive):
    id = "jack_of_all_trades"
    name = "Jack-of-All-Trades Mode"
    description = (
        "13.9 Активация нескольких базовых модулей сразу с меньшим риском перегрева.\n"
        "'Если что-то взорвалось — значит, сработало!'"
    )
    is_active_ability = True


# ==========================================
# 13.10 А: Machina Ex Deo
# ==========================================
class TalentMachinaExDeo(BasePassive):
    id = "machina_ex_deo"
    name = "Machina Ex Deo (А)"
    description = (
        "13.10 А: Финальная эволюция. Вы получаете навык 'Iron Warden'.\n"
        "Активно: Робот становится вашей оболочкой, усиливая выносливость, скорость и урон.\n"
        "Вы сражаетесь как единое целое."
    )
    is_active_ability = True
    cooldown = 99

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        # Эмуляция слияния (мощные баффы)
        unit.add_status("attack_power_up", 3, duration=3)
        unit.add_status("endurance", 3, duration=3)
        unit.add_status("haste", 3, duration=3)

        unit.cooldowns[self.id] = self.cooldown
        if log_func: log_func("🤖 **Iron Warden**: Слияние с роботом! Характеристики усилены.")
        logger.log(f"🤖 Iron Warden activated for {unit.name}", LogLevel.NORMAL, "Talent")
        return True


# ==========================================
# 13.10 B: Exogenesis Protocol
# ==========================================
class TalentExogenesisProtocol(BasePassive):
    id = "exogenesis_protocol"
    name = "Exogenesis Protocol (Б)"
    description = (
        "13.10 Б: Оптимизация канала связи.\n"
        "Количество роботов возрастает до 2."
    )
    is_active_ability = False


# ==========================================
# 13.10 (Опц) Система многоцелевого подключения
# ==========================================
class TalentMultiConnection(BasePassive):
    id = "multi_connection"
    name = "Система многоцелевого подключения"
    description = (
        "13.10 Опц: Если взяты все навыки на модули -> Ограничение модулей снято.\n"
        "Количество зависит только от навыков."
    )
    is_active_ability = False