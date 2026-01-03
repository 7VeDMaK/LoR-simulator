from logic.passives.base_passive import BasePassive

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

# === РЕЕСТР ===
AUGMENTATION_REGISTRY = {
    "aug_back_speed": AugBackSpeed()
}