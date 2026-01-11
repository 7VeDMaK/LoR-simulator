# logic/character_changing/passives/base_passive.py
from logic.base_effect import BaseEffect

class BasePassive(BaseEffect):
    """
    Базовый класс для Пассивок и Талантов.
    """
    id = "base_passive"
    is_active_ability = False
    cooldown = 0
    duration = 0