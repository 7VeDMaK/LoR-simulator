from dataclasses import dataclass, field
from typing import List, Dict

from core.resistances import Resistances


@dataclass
class UnitRPGMixin:
    """
    RPG составляющая: Характеристики, Навыки, Экипировка, Резисты.
    """
    # === ЗАЩИТА И ЭКИПИРОВКА ===
    armor_name: str = "Standard Fixer Suit"
    armor_type: str = "Medium"
    weapon_id: str = "none"

    hp_resists: Resistances = field(default_factory=lambda: Resistances())
    stagger_resists: Resistances = field(default_factory=lambda: Resistances())

    # === ХАРАКТЕРИСТИКИ И НАВЫКИ ===
    attributes: Dict[str, int] = field(default_factory=lambda: {
        "strength": 0, "endurance": 0, "agility": 0, "wisdom": 0, "psych": 0
    })

    skills: Dict[str, int] = field(default_factory=lambda: {
        "strike_power": 0, "medicine": 0, "willpower": 0, "luck": 0,
        "acrobatics": 0, "shields": 0, "tough_skin": 0, "speed": 0,
        "light_weapon": 0, "medium_weapon": 0, "heavy_weapon": 0, "firearms": 0,
        "eloquence": 0, "forging": 0, "engineering": 0, "programming": 0
    })

    relationships: Dict[str, Dict] = field(default_factory=dict)

    # === ПРОГРЕССИЯ ===
    augmentations: List[str] = field(default_factory=list)
    passives: List[str] = field(default_factory=list)
    talents: List[str] = field(default_factory=list)
    level_rolls: Dict[str, Dict[str, int]] = field(default_factory=dict)