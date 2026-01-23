# core/unit/unit_data.py
import json
import copy
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

from core.dice import Dice

try:
    from core.card import Card
except ImportError:
    Card = Any

from core.resistances import Resistances


@dataclass
class UnitData:
    """
    Базовый класс данных юнита.
    """
    # === ОСНОВНАЯ ИНФОРМАЦИЯ (STATIC) ===
    name: str
    level: int = 1
    rank: int = 9
    avatar: Optional[str] = None
    biography: str = ""
    total_xp: int = 0

    # === ФИНАНСЫ (DYNAMIC) ===
    money_log: List[Dict[str, Any]] = field(default_factory=list)

    # === МОДИФИКАТОРЫ ===
    implants_hp_pct: int = 0
    implants_sp_pct: int = 0
    implants_stagger_pct: int = 0
    talents_hp_pct: int = 0
    talents_sp_pct: int = 0
    talents_stagger_pct: int = 0
    implants_hp_flat: int = 0
    implants_sp_flat: int = 0
    implants_stagger_flat: int = 0

    # === БАЗОВЫЕ ПАРАМЕТРЫ ===
    base_intellect: int = 1
    base_hp: int = 20
    base_sp: int = 20
    base_speed_min: int = 1
    base_speed_max: int = 4

    # === РАСЧЕТНЫЕ ПАРАМЕТРЫ (DYNAMIC) ===
    max_hp: int = 20
    current_hp: int = 20
    max_sp: int = 20
    current_sp: int = 20
    max_stagger: int = 10
    current_stagger: int = 10

    deck: List[str] = field(default_factory=list)
    card_cooldowns: Dict[str, int] = field(default_factory=dict)

    # === БОЕВАЯ СИСТЕМА (DYNAMIC) ===
    computed_speed_dice: List[Tuple[int, int]] = field(default_factory=list)
    active_slots: List[Dict] = field(default_factory=list)
    current_card: Optional['Card'] = None
    stored_dice: List = field(default_factory=list)
    counter_dice: List = field(default_factory=list)

    # === СИСТЕМА СПОСОБНОСТЕЙ (DYNAMIC) ===
    cooldowns: Dict[str, int] = field(default_factory=dict)
    active_buffs: Dict[str, int] = field(default_factory=dict)

    # === ЗАЩИТА ===
    armor_name: str = "Standard Fixer Suit"
    armor_type: str = "Medium"
    hp_resists: Resistances = field(default_factory=lambda: Resistances())
    stagger_resists: Resistances = field(default_factory=lambda: Resistances())
    weapon_id: str = "none"

    # === RPG СИСТЕМА ===
    attributes: Dict[str, int] = field(default_factory=lambda: {
        "strength": 0, "endurance": 0, "agility": 0, "wisdom": 0, "psych": 0
    })
    skills: Dict[str, int] = field(default_factory=lambda: {
        "strike_power": 0, "medicine": 0, "willpower": 0, "luck": 0,
        "acrobatics": 0, "shields": 0, "tough_skin": 0, "speed": 0,
        "light_weapon": 0, "medium_weapon": 0, "heavy_weapon": 0, "firearms": 0,
        "eloquence": 0, "forging": 0, "engineering": 0, "programming": 0
    })
    augmentations: List[str] = field(default_factory=list)
    passives: List[str] = field(default_factory=list)
    talents: List[str] = field(default_factory=list)
    level_rolls: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # === ВНУТРЕННЕЕ СОСТОЯНИЕ (DYNAMIC) ===
    _status_effects: Dict[str, List[Dict]] = field(default_factory=dict)
    delayed_queue: List[dict] = field(default_factory=list)
    resources: Dict[str, int] = field(default_factory=dict)
    modifiers: Dict[str, int] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)

    death_count: int = 0
    overkill_damage: int = 0

    # =========================================================================
    # OPTIMIZED STATE MANAGEMENT
    # =========================================================================

    def get_dynamic_state(self) -> dict:
        """Возвращает ТОЛЬКО меняющиеся данные (Delta)."""

        def safe_copy(d):
            try:
                return json.loads(json.dumps(d, default=str))
            except Exception:
                return {}

        return {
            "current_hp": self.current_hp,
            "current_sp": self.current_sp,
            "current_stagger": self.current_stagger,

            "resources": safe_copy(self.resources),
            "cooldowns": safe_copy(self.cooldowns),
            "card_cooldowns": safe_copy(self.card_cooldowns),

            "active_buffs": safe_copy(self.active_buffs),
            "_status_effects": safe_copy(self._status_effects),
            "delayed_queue": safe_copy(self.delayed_queue),

            "deck": list(self.deck),
            "active_slots": [self._serialize_slot(s) for s in self.active_slots],
            "stored_dice": [d.to_dict() for d in self.stored_dice],
            "counter_dice": [d.to_dict() for d in self.counter_dice],

            "memory": safe_copy(self.memory),
            "death_count": self.death_count,
            "overkill_damage": self.overkill_damage,
            "money_log": safe_copy(self.money_log)
        }

    def apply_dynamic_state(self, state: dict):
        """
        Применяет динамические данные.
        [CRITICAL FIX] Используем deepcopy при восстановлении, чтобы разорвать связь с историей.
        """
        from core.dice import Dice

        self.current_hp = state.get("current_hp", self.current_hp)
        self.current_sp = state.get("current_sp", self.current_sp)
        self.current_stagger = state.get("current_stagger", self.current_stagger)
        self.death_count = state.get("death_count", 0)
        self.overkill_damage = state.get("overkill_damage", 0)

        # === [FIX] DEEPCOPY ПРИ ВОССТАНОВЛЕНИИ ===
        # Это гарантирует, что если мы изменим статусы сейчас,
        # они не изменятся в сохраненном "прошлом".
        self.resources = copy.deepcopy(state.get("resources", {}))
        self.active_buffs = copy.deepcopy(state.get("active_buffs", {}))
        self._status_effects = copy.deepcopy(state.get("_status_effects", {}))
        self.delayed_queue = copy.deepcopy(state.get("delayed_queue", []))
        self.memory = copy.deepcopy(state.get("memory", {}))
        self.money_log = copy.deepcopy(state.get("money_log", []))
        self.deck = list(state.get("deck", []))

        # === SANITIZE COOLDOWNS ===
        raw_card_cd = state.get("card_cooldowns", {})
        self.card_cooldowns = {}
        for k, v in raw_card_cd.items():
            if isinstance(v, (int, float)):
                self.card_cooldowns[k] = int(v)
            else:
                self.card_cooldowns[k] = 0

        raw_cd = state.get("cooldowns", {})
        self.cooldowns = {}
        for k, v in raw_cd.items():
            if isinstance(v, (int, float)):
                self.cooldowns[k] = int(v)
            else:
                self.cooldowns[k] = 0

        # Восстановление слотов
        raw_slots = state.get("active_slots", [])
        self.active_slots = [self._deserialize_slot(s) for s in raw_slots] if raw_slots else []

        raw_stored = state.get("stored_dice", [])
        self.stored_dice = [Dice.from_dict(d) for d in raw_stored]

        raw_counter = state.get("counter_dice", [])
        self.counter_dice = [Dice.from_dict(d) for d in raw_counter]

    # === ПОЛНАЯ СЕРИАЛИЗАЦИЯ (FILE SAVE) ===
    def to_dict(self):
        def safe_dict_copy(d):
            if not d: return {}
            try:
                return json.loads(json.dumps(d, default=str))
            except TypeError:
                return {}

        return {
            "name": self.name, "level": self.level, "rank": self.rank, "avatar": self.avatar,
            "base_intellect": self.base_intellect,
            "total_xp": self.total_xp,
            "pct_mods": {
                "imp_hp": self.implants_hp_pct, "imp_sp": self.implants_sp_pct, "imp_stg": self.implants_stagger_pct,
                "tal_hp": self.talents_hp_pct, "tal_sp": self.talents_sp_pct, "tal_stg": self.talents_stagger_pct,
            },
            "flat_mods": {
                "imp_hp": self.implants_hp_flat, "imp_sp": self.implants_sp_flat, "imp_stg": self.implants_stagger_flat
            },
            # Включаем динамику
            **self.get_dynamic_state(),

            "base_stats": {
                "current_hp": self.current_hp, "current_sp": self.current_sp,
                "current_stagger": self.current_stagger
            },
            "defense": {
                "armor_name": self.armor_name, "armor_type": self.armor_type,
                "hp_resists": self.hp_resists.to_dict(),
                "stagger_resists": self.stagger_resists.to_dict(),
                "weapon_id": self.weapon_id,
            },
            "attributes": self.attributes.copy(),
            "skills": self.skills.copy(),
            "passives": list(self.passives),
            "talents": list(self.talents),
            "augmentations": list(self.augmentations),
            "level_rolls": safe_dict_copy(self.level_rolls),
            "biography": self.biography,
        }

    @classmethod
    def from_dict(cls, data: dict):
        u = cls(name=data.get("name", "Unknown"))
        u.level = data.get("level", 1)
        u.rank = data.get("rank", 9)
        u.avatar = data.get("avatar", None)
        u.base_intellect = data.get("base_intellect", 1)
        u.total_xp = data.get("total_xp", 0)
        u.biography = data.get("biography", "")

        pct = data.get("pct_mods", {})
        u.implants_hp_pct = pct.get("imp_hp", 0)
        u.implants_sp_pct = pct.get("imp_sp", 0)
        u.implants_stagger_pct = pct.get("imp_stg", 0)
        u.talents_hp_pct = pct.get("tal_hp", 0)
        u.talents_sp_pct = pct.get("tal_sp", 0)
        u.talents_stagger_pct = pct.get("tal_stg", 0)

        flat = data.get("flat_mods", {})
        u.implants_hp_flat = flat.get("imp_hp", 0)
        u.implants_sp_flat = flat.get("imp_sp", 0)
        u.implants_stagger_flat = flat.get("imp_stg", 0)

        base = data.get("base_stats", {})
        u.current_hp = data.get("current_hp", base.get("current_hp", 20))
        u.current_sp = data.get("current_sp", base.get("current_sp", 20))
        u.current_stagger = data.get("current_stagger", base.get("current_stagger", 10))

        defense = data.get("defense", {})
        u.armor_name = defense.get("armor_name", "Suit")
        u.armor_type = defense.get("armor_type", "Medium")
        u.hp_resists = Resistances.from_dict(defense.get("hp_resists", {}))
        u.stagger_resists = Resistances.from_dict(defense.get("stagger_resists", {}))
        u.weapon_id = defense.get("weapon_id", "none")

        if "attributes" in data: u.attributes.update(data["attributes"])
        if "skills" in data: u.skills.update(data["skills"])
        if "intellect" in u.attributes: del u.attributes["intellect"]

        u.passives = data.get("passives", [])
        u.talents = data.get("talents", [])
        u.augmentations = data.get("augmentations", [])
        u.level_rolls = data.get("level_rolls", {})

        # Применяем динамику (включая санитизацию)
        u.apply_dynamic_state(data)

        return u

    def _serialize_slot(self, slot):
        try:
            s_copy = slot.copy()
            card_obj = s_copy.get('card')
            if card_obj and hasattr(card_obj, 'id'):
                s_copy['card'] = card_obj.id
            elif card_obj:
                s_copy['card'] = None
            return json.loads(json.dumps(s_copy, default=str))
        except Exception:
            return {}

    @classmethod
    def _deserialize_slot(cls, slot_data):
        from core.library import Library
        slot = slot_data.copy()
        card_val = slot.get('card')
        if card_val and isinstance(card_val, str):
            found_card = Library.get_card(card_val)
            if found_card.id != "unknown":
                slot['card'] = found_card
            else:
                slot['card'] = None
        return slot