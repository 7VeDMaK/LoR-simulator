from core.logging import logger, LogLevel  # [NEW] Import
from logic.character_changing.passives.base_passive import BasePassive


class PassiveSevereTraining(BasePassive):
    id = "severe_training"
    name = "Суровые тренировки"
    description = "При повышении уровня прирост здоровья фиксирован на 10, а рассудка на 5. Броски кубиков игнорируются."

    def calculate_level_growth(self, unit) -> dict:
        # Считаем количество уровней (записей в level_rolls)
        count = len(unit.level_rolls)
        return {
            "hp": count * 10,
            "sp": count * 5,
            "logs": [f"🏋️ Суровые тренировки: +10 HP / +5 SP за уровень"]
        }


class PassiveAdaptation(BasePassive):
    id = "adaptation"
    name = "Адаптация"
    description = "Накапливает уровни (стаки) статуса 'Адаптация'. Ур 1-5. Дает пробивание резистов и игнор урона."

    def on_round_start(self, unit, log_func, **kwargs):
        current = unit.get_status("adaptation")
        if current < 4:
            unit.add_status("adaptation", 1, duration=99)
            if log_func:
                log_func(f"🧬 Адаптация: Рост -> Уровень {current + 1}")

            logger.log(f"🧬 Adaptation: {unit.name} stack increased to {current + 1}", LogLevel.VERBOSE, "Passive")
        else:
            unit.add_status("adaptation", 0, duration=99)


class PassiveBlueHyacinth(BasePassive):
    id = "blue_hyacinth_passive"
    name = "Синий Гиацинт"
    description = (
        "«Скорбь — это не слабость. Это тяжесть, что ломает хребты».\n"
        "Активная: На 1 ход превращает полученный урон в силу.\n"
        "Восстанавливает 10% от максимального здоровья и не даёт умереть\n"
        "При получении урона восстанавливает 5 SP и накладывает на врага 1 'Слабость' (Weakness)."
    )

    # Делаем абилку прожимаемой
    is_active_ability = True
    cooldown = 5  # Перезарядка 5 хода
    duration = 1  # Длительность эффекта

    def activate(self, unit, log_func, **kwargs):

        if unit.cooldowns.get(self.id, 0) > 0:
            return False
        """Логика при нажатии кнопки."""
        unit.add_status("hyacinth_bloom", 1, duration=self.duration)
        unit.cooldowns[self.id] = self.cooldown
        logger.log(f"💙 {unit.name}: Расцветает Синий Гиацинт!", LogLevel.NORMAL, "Talent")
        return f"Синий Гиацинт активирован на {self.duration} хода."

    def on_hit(self, unit, attacker, damage_val, **kwargs):
        """Реакция на получение урона (Пассивная часть, пока активен статус)."""
        if unit.get_status("hyacinth_bloom") > 0:
            unit.restore_sp(5)

            # 2. Наказываем врага
            if attacker and attacker != unit:
                attacker.add_status("weakness", 1, duration=5)  # Снижение атаки
                logger.log(
                    f"🥀 Hyacinth: {attacker.name} ослаблен скорбью.",
                    LogLevel.VERBOSE,
                    "Passive"
                )

    def on_round_end(self, unit, log_func, **kwargs):
        # Опционально: лечение в конце хода, если цветок активен
        if unit.get_status("hyacinth_bloom") > 0:
            heal = int(unit.max_hp * 0.1)
            unit.heal_hp(heal)