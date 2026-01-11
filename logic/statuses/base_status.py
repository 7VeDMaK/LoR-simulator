# logic/statuses/base_status.py
from logic.base_effect import BaseEffect


class StatusEffect(BaseEffect):
    """
    Базовый класс для статусов.
    Наследует весь интерфейс от BaseEffect.
    """
    id = "base_status"

    # Можно добавить специфичные для статусов методы, если они появятся,
    # но пока BaseEffect покрывает всё.
    def on_use(self, unit, card, log_func): pass