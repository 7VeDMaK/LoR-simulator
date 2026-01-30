from core.enums import DiceType
from logic.character_changing.passives.base_passive import BasePassive


class Augmentation(BasePassive):
    """Базовый класс для аугментаций."""
    pass

# === СПИННОЙ УСКОРИТЕЛЬ ===
class AugBackSpeed(Augmentation):
    id = "aug_back_speed"
    name = "Спинной ускоритель (MK-1)"
    description = "Кибернетический имплант позвоночника. Повышает скорость реакции.\nЭффект: +10 Скорости."

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"speed": 10}

class AugBlessingOfWind(Augmentation):
    id = "aug_blessing_of_wind" # Важно: этот ID должен совпадать с тем, что в unit.augmentations
    name = "Тату 'Благословение Ветра'"
    description = "Пассивно: +1 к Атаке и Уклонению за каждые 5 Дыма. Лимит Дыма увеличен на 5."

    def on_combat_start(self, unit, log_func, **kwargs):
        unit.memory['smoke_limit_bonus'] = 5
        if log_func: log_func(f"🌬️ **{self.name}**: Лимит дыма увеличен до 15")

    def on_roll(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        smoke = ctx.source.get_status("smoke")
        # Если дыма меньше 5, бонуса нет
        if smoke < 5: return

        # Бонус: 1 за 5, 2 за 10, 3 за 15, 4 за 20, 5 за 25
        bonus = smoke // 5

        # Работает только на Атакующие кубики и Уклонение
        # (Slash, Pierce, Blunt, Evade)
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT, DiceType.EVADE]:
            ctx.modify_power(bonus, f"Blessing ({smoke})")

# === [NEW] ТАТУ "ИСТЕРИКА КУПЦА" ===
class AugMerchantHysteria(Augmentation):
    id = "aug_merchant_hysteria"
    name = "Тату 'Истерика Купца'"
    description = "Позволяет изменять голос Лилит куда эластичнее.\nЭффект: +5 Красноречия. Открывает карту 'Крик Демона'."

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"eloquence": 5}

    def on_combat_start(self, unit, log_func, **kwargs):
        # Добавляем карту, если её нет
        card_id = "demon_scream"
        # Проверяем, есть ли карта уже в деке
        if card_id not in unit.deck:
            unit.deck.append(card_id)
            if log_func:
                log_func(f"📢 **{self.name}**: Карта '{card_id}' добавлена в руку.")


class StrizhAugmentation(Augmentation):
    id = "aug_strizh"
    name = "Легкий экзоскелет 'СТРИЖ'"
    description = " лёгкий экзоскелет СТРИЖ со шлемом и противогазом Акробатика +6 Даёт статус спешки +1 каждый ход"

    def on_calculate_stats(self, unit, *args, **kwargs):
        return {"acrobatics": 6}

    def on_round_start(self, unit, log_func, **kwargs):
        unit.add_status("haste", 1, 1)
        if log_func:
            log_func(f"⚡ **{unit.name}**: Экзоскелет активирует сервоприводы (Спешка +1).")


# === [NEW] СТЕЛС-МОДУЛЬ "ПРИЗРАК" ===
class AugStealthModule(Augmentation):
    id = "aug_stealth_module"
    name = "Стелс-модуль 'Призрак'"
    description = (
        "Система активного камуфляжа.\n"
        "Эффект: +10 Скорости, +10 Акробатики (Уворот).\n"
        "Аварийный режим: При HP <= 25% активирует Невидимость на 3 хода (1 раз за бой)."
    )

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {
            "speed": 10,
            "acrobatics": 10  # Навык, отвечающий за уворот
        }

    def on_take_damage(self, unit, amount, source, **kwargs):
        # Проверяем, срабатывал ли модуль в этом бою
        if unit.memory.get("aug_stealth_triggered", False):
            return

        # Проверка порога здоровья (<= 25%)
        # Используем current_hp, так как урон уже нанесен (обычно)
        if unit.max_hp > 0 and (unit.current_hp / unit.max_hp) <= 0.25:
            # Активируем невидимость
            unit.add_status("invisibility", 1, duration=3)

            # Ставим флаг срабатывания
            unit.memory["aug_stealth_triggered"] = True

# === РЕЕСТР ===
AUGMENTATION_REGISTRY = {
    "aug_back_speed": AugBackSpeed(),
    "aug_blessing_of_wind": AugBlessingOfWind(),
    "aug_merchant_hysteria": AugMerchantHysteria(),
    "aug_strizh": StrizhAugmentation(),
    "aug_stealth_module": AugStealthModule(),
}