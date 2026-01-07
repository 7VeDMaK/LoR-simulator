from logic.character_changing.passives.base_passive import BasePassive
from core.enums import DiceType
from logic.context import RollContext # Needed for type hinting if used

class Augmentation(BasePassive):
    """Базовый класс для аугментаций."""
    pass

# === СПИННОЙ УСКОРИТЕЛЬ ===
class AugBackSpeed(Augmentation):
    id = "aug_back_speed"
    name = "Спинной ускоритель (MK-1)"
    description = "Кибернетический имплант позвоночника. Повышает скорость реакции.\nЭффект: +10 Скорости."

    def on_calculate_stats(self, unit) -> dict:
        return {"speed": 10}

# === [MOVED] ТАТУ "БЛАГОСЛОВЕНИЕ ВЕТРА" ===
# Перенесено сюда, так как это аугментация (Тату).
class AugBlessingOfWind(Augmentation):
    id = "aug_blessing_of_wind" # Важно: этот ID должен совпадать с тем, что в unit.augmentations
    name = "Тату 'Благословение Ветра'"
    description = "Пассивно: +1 к Атаке и Уклонению за каждые 5 Дыма. Лимит Дыма увеличен на 5."

    def on_combat_start(self, unit, log_func, **kwargs):
        # Увеличиваем лимит дыма в памяти юнита. SmokeStatus это увидит.
        unit.memory['smoke_limit_bonus'] = 5
        if log_func: log_func(f"🌬️ **{self.name}**: Лимит дыма увеличен до 15")

    def on_roll(self, ctx):
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

    def on_calculate_stats(self, unit) -> dict:
        return {"eloquence": 5}

    def on_combat_start(self, unit, log_func, **kwargs):
        # Добавляем карту, если её нет
        card_id = "demon_scream"
        # Проверяем, есть ли карта уже в деке
        if card_id not in unit.deck:
            # ВАЖНО: Добавляем в 'runtime' деку (unit.deck), которая используется в бою.
            # Если нужно сохранить навсегда, это требует сохранения юнита, но для боя достаточно этого.
            unit.deck.append(card_id)
            if log_func:
                log_func(f"📢 **{self.name}**: Карта '{card_id}' добавлена в руку.")

# === РЕЕСТР ===
AUGMENTATION_REGISTRY = {
    "aug_back_speed": AugBackSpeed(),
    "aug_blessing_of_wind": AugBlessingOfWind(),
    "aug_merchant_hysteria": AugMerchantHysteria(),
}