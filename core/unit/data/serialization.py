import copy
import json

# Для type hinting
from core.dice import Dice
from core.resistances import Resistances


class UnitSerializationMixin:
    """
    Методы сохранения и загрузки состояния юнита.
    """

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
        """Применяет динамические данные."""
        self.current_hp = state.get("current_hp", self.current_hp)
        self.current_sp = state.get("current_sp", self.current_sp)
        self.current_stagger = state.get("current_stagger", self.current_stagger)
        self.death_count = state.get("death_count", 0)
        self.overkill_damage = state.get("overkill_damage", 0)

        self.resources = copy.deepcopy(state.get("resources", {}))
        self.active_buffs = copy.deepcopy(state.get("active_buffs", {}))
        self._status_effects = copy.deepcopy(state.get("_status_effects", {}))
        self.delayed_queue = copy.deepcopy(state.get("delayed_queue", []))
        self.memory = copy.deepcopy(state.get("memory", {}))
        self.money_log = copy.deepcopy(state.get("money_log", []))
        self.deck = list(state.get("deck", []))

        # Sanitize cooldowns
        for target, source_key in [(self.card_cooldowns, "card_cooldowns"), (self.cooldowns, "cooldowns")]:
            raw = state.get(source_key, {})
            target.clear()
            for k, v in raw.items():
                target[k] = int(v) if isinstance(v, (int, float)) else 0

        # Восстановление слотов и кубиков
        raw_slots = state.get("active_slots", [])
        self.active_slots = [self._deserialize_slot(s) for s in raw_slots] if raw_slots else []

        self.stored_dice = [Dice.from_dict(d) for d in state.get("stored_dice", [])]
        self.counter_dice = [Dice.from_dict(d) for d in state.get("counter_dice", [])]

    def to_dict(self):
        """Полная сериализация."""

        def safe_dict_copy(d):
            if not d: return {}
            try:
                return json.loads(json.dumps(d, default=str))
            except TypeError:
                return {}

        return {
            "name": self.name, "level": self.level, "rank": self.rank, "avatar": self.avatar,
            "base_intellect": self.base_intellect, "total_xp": self.total_xp,
            "pct_mods": {
                "imp_hp": self.implants_hp_pct, "imp_sp": self.implants_sp_pct, "imp_stg": self.implants_stagger_pct,
                "tal_hp": self.talents_hp_pct, "tal_sp": self.talents_sp_pct, "tal_stg": self.talents_stagger_pct,
            },
            "flat_mods": {
                "imp_hp": self.implants_hp_flat, "imp_sp": self.implants_sp_flat, "imp_stg": self.implants_stagger_flat
            },
            **self.get_dynamic_state(),
            "base_stats": {
                "current_hp": self.current_hp, "current_sp": self.current_sp,
                "current_stagger": self.current_stagger
            },
            "defense": {
                "armor_name": self.armor_name, "armor_type": self.armor_type,
                "armor_id": getattr(self, 'armor_id', 'none'),
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
            "relationships": self.relationships.copy(),
            "unit_type": self.unit_type,
        }

    @classmethod
    def from_dict(cls, data: dict):
        # Создаем экземпляр (name обязателен)
        u = cls(name=data.get("name", "Unknown"))

        # Base
        u.level = data.get("level", 1)
        u.rank = data.get("rank", 9)
        u.avatar = data.get("avatar", None)
        u.base_intellect = data.get("base_intellect", 1)
        u.total_xp = data.get("total_xp", 0)
        u.biography = data.get("biography", "")
        u.unit_type = data.get("unit_type", "fixer")
        # Stats & Mods
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

        # RPG
        defense = data.get("defense", {})
        u.armor_id = defense.get("armor_id", "none")
        u.armor_name = defense.get("armor_name", "Suit")
        u.armor_type = defense.get("armor_type", "Medium")
        u.hp_resists = Resistances.from_dict(defense.get("hp_resists", {}))
        u.stagger_resists = Resistances.from_dict(defense.get("stagger_resists", {}))
        u.weapon_id = defense.get("weapon_id", "none")
        
        # Применяем броню из реестра, если ID есть
        try:
            from logic.armor_definitions import ARMOR_REGISTRY
            if u.armor_id and u.armor_id in ARMOR_REGISTRY:
                armor = ARMOR_REGISTRY[u.armor_id]
                u.armor_name = armor.name
                u.hp_resists.slash = armor.hp_resists["slash"]
                u.hp_resists.pierce = armor.hp_resists["pierce"]
                u.hp_resists.blunt = armor.hp_resists["blunt"]
                u.stagger_resists.slash = armor.stagger_resists["slash"]
                u.stagger_resists.pierce = armor.stagger_resists["pierce"]
                u.stagger_resists.blunt = armor.stagger_resists["blunt"]
        except ImportError:
            pass  # Если ARMOR_REGISTRY недоступен, используем сохраненные значения

        if "attributes" in data: u.attributes.update(data["attributes"])
        if "skills" in data: u.skills.update(data["skills"])
        if "intellect" in u.attributes: del u.attributes["intellect"]  # Legacy cleanup

        u.passives = data.get("passives", [])
        u.talents = data.get("talents", [])
        u.augmentations = data.get("augmentations", [])
        u.level_rolls = data.get("level_rolls", {})
        u.relationships = data.get("relationships", {})

        # Dynamic apply
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
