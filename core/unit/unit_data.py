# core/unit_data.py
import json
import copy  # [NEW] Нужно для deepcopy
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
    Отвечает только за хранение полей и сериализацию.
    """
    # === ОСНОВНАЯ ИНФОРМАЦИЯ ===
    name: str
    level: int = 1
    rank: int = 9
    avatar: Optional[str] = None
    biography: str = ""

    # [НОВОЕ] Накопленный опыт (чтобы не терять прогресс)
    total_xp: int = 0

    # === ФИНАНСЫ ===
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

    # === РАСЧЕТНЫЕ ПАРАМЕТРЫ ===
    max_hp: int = 20
    current_hp: int = 20
    max_sp: int = 20
    current_sp: int = 20
    max_stagger: int = 10
    current_stagger: int = 10

    deck: List[str] = field(default_factory=list)
    card_cooldowns: Dict[str, int] = field(default_factory=dict)

    # === БОЕВАЯ СИСТЕМА ===
    computed_speed_dice: List[Tuple[int, int]] = field(default_factory=list)
    active_slots: List[Dict] = field(default_factory=list)
    current_card: Optional['Card'] = None

    stored_dice: List = field(default_factory=list)
    counter_dice: List = field(default_factory=list)

    # === СИСТЕМА СПОСОБНОСТЕЙ ===
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

    # === ВНУТРЕННЕЕ СОСТОЯНИЕ ===
    _status_effects: Dict[str, List[Dict]] = field(default_factory=dict)
    delayed_queue: List[dict] = field(default_factory=list)
    resources: Dict[str, int] = field(default_factory=dict)
    modifiers: Dict[str, int] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)

    death_count: int = 0
    overkill_damage: int = 0

    def to_dict(self):
        """
        Сериализует юнита в словарь.
        [FIX] Использует deepcopy для изменяемых словарей, чтобы снимки истории
        не менялись при изменении текущего юнита.
        """
        return {
            "name": self.name, "level": self.level, "rank": self.rank, "avatar": self.avatar,
            "base_intellect": self.base_intellect,
            "total_xp": self.total_xp,
            "pct_mods": copy.deepcopy({
                "imp_hp": self.implants_hp_pct, "imp_sp": self.implants_sp_pct, "imp_stg": self.implants_stagger_pct,
                "tal_hp": self.talents_hp_pct, "tal_sp": self.talents_sp_pct, "tal_stg": self.talents_stagger_pct,
            }),
            "flat_mods": copy.deepcopy({
                "imp_hp": self.implants_hp_flat, "imp_sp": self.implants_sp_flat, "imp_stg": self.implants_stagger_flat
            }),
            "deck": list(self.deck),
            "stored_dice": [d.to_dict() for d in self.stored_dice],
            "counter_dice": [d.to_dict() for d in self.counter_dice],
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
            # [FIX] Deepcopy critical dynamic fields
            "card_cooldowns": copy.deepcopy(self.card_cooldowns),
            "attributes": copy.deepcopy(self.attributes),
            "skills": copy.deepcopy(self.skills),
            "passives": list(self.passives),
            "talents": list(self.talents),
            "augmentations": list(self.augmentations),
            "level_rolls": copy.deepcopy(self.level_rolls),
            "cooldowns": copy.deepcopy(self.cooldowns),
            "active_buffs": copy.deepcopy(self.active_buffs),
            "resources": copy.deepcopy(self.resources),
            "biography": self.biography,
            "money_log": copy.deepcopy(self.money_log),
            "death_count": self.death_count,
            "overkill_damage": self.overkill_damage,

            # [FIX] СТАТУСЫ И ПАМЯТЬ — САМОЕ ВАЖНОЕ ДЛЯ ОТКАТА
            "_status_effects": copy.deepcopy(self._status_effects),
            "delayed_queue": copy.deepcopy(self.delayed_queue),
            "memory": copy.deepcopy(self.memory),
            "active_slots": [self._serialize_slot(s) for s in self.active_slots]
        }

    @classmethod
    def from_dict(cls, data: dict):
        u = cls(name=data.get("name", "Unknown"))

        u.level = data.get("level", 1)
        u.rank = data.get("rank", 9)
        u.avatar = data.get("avatar", None)
        u.base_intellect = data.get("base_intellect", 1)
        u.total_xp = data.get("total_xp", 0)

        from core.dice import Dice

        raw_stored = data.get("stored_dice", [])
        u.stored_dice = []
        for d_data in raw_stored:
            if isinstance(d_data, dict):
                u.stored_dice.append(Dice.from_dict(d_data))

        raw_counter = data.get("counter_dice", [])
        u.counter_dice = []
        for d_data in raw_counter:
            if isinstance(d_data, dict):
                u.counter_dice.append(Dice.from_dict(d_data))

        u.biography = data.get("biography", "")
        u.money_log = data.get("money_log", [])
        u.deck = data.get("deck", [])

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

        # Sanitize Card Cooldowns
        raw_card_cd = data.get("card_cooldowns", {})
        u.card_cooldowns = {}
        if isinstance(raw_card_cd, dict):
            for k, v in raw_card_cd.items():
                if isinstance(v, (int, float)):
                    u.card_cooldowns[k] = int(v)
                elif isinstance(v, list):  # Если это список (новая система), берем как есть
                    u.card_cooldowns[k] = v
                else:
                    u.card_cooldowns[k] = 0

        base = data.get("base_stats", {})
        u.current_hp = base.get("current_hp", 20)
        u.current_sp = base.get("current_sp", 20)
        u.current_stagger = base.get("current_stagger", 10)

        u.resources = data.get("resources", {})

        defense = data.get("defense", {})
        u.armor_name = defense.get("armor_name", "Suit")
        u.armor_type = defense.get("armor_type", "Medium")
        u.hp_resists = Resistances.from_dict(defense.get("hp_resists", {}))
        u.stagger_resists = Resistances.from_dict(defense.get("stagger_resists", {}))
        u.weapon_id = defense.get("weapon_id", "none")

        u.death_count = data.get("death_count", 0)
        u.overkill_damage = data.get("overkill_damage", 0)

        if "attributes" in data: u.attributes.update(data["attributes"])
        if "skills" in data: u.skills.update(data["skills"])
        if "intellect" in u.attributes: del u.attributes["intellect"]

        u.passives = data.get("passives", [])
        u.talents = data.get("talents", [])
        u.augmentations = data.get("augmentations", [])
        u.level_rolls = data.get("level_rolls", {})

        # Sanitize Ability Cooldowns
        raw_cd = data.get("cooldowns", {})
        u.cooldowns = {}
        if isinstance(raw_cd, dict):
            for k, v in raw_cd.items():
                if isinstance(v, (int, float)):
                    u.cooldowns[k] = int(v)
                else:
                    u.cooldowns[k] = 0

        u.active_buffs = data.get("active_buffs", {})
        u._status_effects = data.get("_status_effects", {})
        u.delayed_queue = data.get("delayed_queue", [])
        u.memory = data.get("memory", {})

        raw_slots = data.get("active_slots", [])
        if raw_slots:
            u.active_slots = [cls._deserialize_slot(s) for s in raw_slots]

        return u

    def _serialize_slot(self, slot):
        # Копируем словарь слота, чтобы не менять оригинал
        s_copy = copy.deepcopy(slot)
        card_obj = s_copy.get('card')
        if card_obj and hasattr(card_obj, 'id'):
            s_copy['card'] = card_obj.id
        elif card_obj:
            s_copy['card'] = None
        return s_copy

    @classmethod
    def _deserialize_slot(cls, slot_data):
        from core.library import Library
        card_val = slot_data.get('card')
        if card_val and isinstance(card_val, str):
            found_card = Library.get_card(card_val)
            if found_card.id != "unknown":
                slot_data['card'] = found_card
            else:
                slot_data['card'] = None
        return slot_data