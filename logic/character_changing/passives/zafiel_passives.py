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


# === ОБНОВЛЕННАЯ ПАССИВКА: АДАПТАЦИЯ ===
class PassiveAdaptation(BasePassive):
    id = "adaptation"
    name = "Адаптация"
    description = "Накапливает уровни (стаки) статуса 'Адаптация'. Ур 1-5. Дает пробивание резистов и игнор урона."

    def on_round_start(self, unit, log_func, **kwargs):
        current = unit.get_status("adaptation")
        if current < 5:
            unit.add_status("adaptation", 1, duration=99)
            if log_func: log_func(f"🧬 Адаптация: Рост -> Уровень {current + 1}")
        else:
            # Если уже 5, просто обновляем длительность, чтобы не слетело
            unit.add_status("adaptation", 0, duration=99)