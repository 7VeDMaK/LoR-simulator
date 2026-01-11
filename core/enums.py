from enum import Enum

class DiceType(Enum):
    SLASH = "Slash"
    PIERCE = "Pierce"
    BLUNT = "Blunt"
    BLOCK = "Block"
    EVADE = "Evade"

class CardType(Enum):
    MELEE = "Melee"           # 1000
    OFFENSIVE = "Offensive"   # 2000 (Новая)
    RANGED = "Ranged"         # 3000
    MASS_SUMMATION = "Mass Summation"
    MASS_INDIVIDUAL = "Mass Individual"
    ON_PLAY = "On Play"
    ITEM = "Item"