from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from core.enums import UnitType


@dataclass
class UnitBaseMixin:
    """
    Базовая информация, уровень, базовые параметры и модификаторы.
    """
    # === ОСНОВНАЯ ИНФОРМАЦИЯ (STATIC) ===
    name: str = "default"
    level: int = 1
    rank: int = 9
    unit_type: str = UnitType.FIXER.value
    avatar: Optional[str] = None
    biography: str = ""
    total_xp: int = 0

    # === ФИНАНСЫ (DYNAMIC) ===
    money_log: List[Dict[str, Any]] = field(default_factory=list)

    # === МОДИФИКАТОРЫ (PCT/FLAT) ===
    implants_hp_pct: int = 0
    implants_sp_pct: int = 0
    implants_stagger_pct: int = 0
    talents_hp_pct: int = 0
    talents_sp_pct: int = 0
    talents_stagger_pct: int = 0

    implants_hp_flat: int = 0
    implants_sp_flat: int = 0
    implants_stagger_flat: int = 0

    # === БАЗОВЫЕ ПАРАМЕТРЫ (CONFIG) ===
    base_intellect: int = 1
    base_hp: int = 20
    base_sp: int = 20
    base_speed_min: int = 1
    base_speed_max: int = 4
