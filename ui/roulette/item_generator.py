"""
Генератор случайных предметов для рулетки Рейна
Основан на системе рангов и прогрессии из Механик Снаряжения
"""

import random
from typing import List, Dict, Any
from dataclasses import dataclass
from .item_names import WEAPON_NAMES, ARMOR_NAMES
from .item_effects import (
    WEAPON_EFFECTS,
    ARMOR_EFFECTS,
    RANK_RARITY,
    RARITY_NAMES,
    ITEM_TIERS,
    DICE_MODIFIERS,
    WEAPON_CLASSES,
    ARMOR_CLASSES,
    WEAPON_PASSIVES,
    WEAPON_ACTIVES,
    ARMOR_PASSIVES,
    ARMOR_ACTIVES,
)


@dataclass
class Item:
    """Представление предмета"""
    name: str
    item_type: str  # "weapon" или "armor"
    item_class: str  # Light / Medium / Heavy
    rank: int
    rarity: str  # "common", "uncommon", "rare", "epic", "legendary"
    tier: int  # Тир качества (0-6): S, A, B, C, D, E, F
    power_modifiers: Dict[str, int]
    passive_effect: str
    active_effect: str
    effects: List[str]
    description: str
    price_multiplier: float  # Множитель цены от тира


class ItemGenerator:
    """Генератор предметов на основе ранга юнита"""
    
    def __init__(self):
        pass

    def _roll_dice_modifier(self, item_type: str) -> str:
        if item_type == "weapon":
            modifier_pool = ["pierce", "slash", "blunt", "all"]
        else:
            modifier_pool = ["evade", "block", "all"]

        modifier_key = random.choice(modifier_pool)
        modifier_name = DICE_MODIFIERS[modifier_key]
        return f"Бонус к кубикам: {modifier_name}"

    def _roll_power_modifiers(self, item_type: str, item_rank: int) -> Dict[str, int]:
        if item_type == "weapon":
            modifier_pool = ["power_pierce", "power_slash", "power_blunt", "power_all"]
        else:
            modifier_pool = ["power_evade", "power_block", "power_all"]

        base_value = 1 + max(0, (6 - item_rank) // 3)
        mod_count = random.randint(1, 2)
        chosen = random.sample(modifier_pool, k=mod_count)
        modifiers = {}
        for key in chosen:
            modifiers[key] = min(4, base_value + random.randint(0, 1))
        return modifiers
    
    def generate_weapons(self, unit_rank: int, count: int = 3) -> List[Item]:
        """
        Генерирует набор оружия для рулетки на основе ранга юнита
        
        Args:
            unit_rank: Ранг юнита (0-9)
            count: Количество предметов для генерации
        
        Returns:
            Список предметов (оружия)
        """
        weapons = []
        weapon_types = list(WEAPON_NAMES.keys())
        
        # Генерируем предметы с рангами от юнита до ниже
        for i in range(count):
            # Вариируем ранги: от ранга юнита до немного ниже
            item_rank = max(0, unit_rank - i)
            
            # Случайно выбираем тип оружия
            weapon_type = random.choice(weapon_types)
            
            # Случайно выбираем название для выбранного типа
            weapon_name = random.choice(WEAPON_NAMES[weapon_type])
            
            effects = list(WEAPON_EFFECTS.get(item_rank, ["Неизвестный эффект"]))
            effects.append(self._roll_dice_modifier("weapon"))
            rarity = RANK_RARITY.get(item_rank, "common")
            
            # Генерируем случайный тир качества (0-6)
            tier = random.randint(0, 6)
            tier_data = ITEM_TIERS[tier]
            
            item = Item(
                name=f"{weapon_name} (Ранг {item_rank})",
                item_type="weapon",
                item_class=random.choice(WEAPON_CLASSES),
                rank=item_rank,
                rarity=rarity,
                tier=tier,
                power_modifiers=self._roll_power_modifiers("weapon", item_rank),
                passive_effect=random.choice(WEAPON_PASSIVES),
                active_effect=random.choice(WEAPON_ACTIVES),
                effects=effects,
                description=f"Оружие типа {weapon_type.capitalize()}",
                price_multiplier=tier_data["price_multiplier"]
            )
            weapons.append(item)
        
        return weapons
    
    def generate_armor(self, unit_rank: int, count: int = 3) -> List[Item]:
        """
        Генерирует набор брони для рулетки на основе ранга юнита
        
        Args:
            unit_rank: Ранг юнита (0-9)
            count: Количество предметов для генерации
        
        Returns:
            Список предметов (брони)
        """
        armor = []
        armor_types = list(ARMOR_NAMES.keys())
        
        for i in range(count):
            item_rank = max(0, unit_rank - i)
            
            # Случайно выбираем тип брони
            armor_type = random.choice(armor_types)
            
            # Случайно выбираем название для выбранного типа
            armor_name = random.choice(ARMOR_NAMES[armor_type])
            
            effects = list(ARMOR_EFFECTS.get(item_rank, ["Неизвестный эффект"]))
            effects.append(self._roll_dice_modifier("armor"))
            rarity = RANK_RARITY.get(item_rank, "common")
            
            # Генерируем случайный тир качества (0-6)
            tier = random.randint(0, 6)
            tier_data = ITEM_TIERS[tier]
            
            item = Item(
                name=f"{armor_name} (Ранг {item_rank})",
                item_type="armor",
                item_class=random.choice(ARMOR_CLASSES),
                rank=item_rank,
                rarity=rarity,
                tier=tier,
                power_modifiers=self._roll_power_modifiers("armor", item_rank),
                passive_effect=random.choice(ARMOR_PASSIVES),
                active_effect=random.choice(ARMOR_ACTIVES),
                effects=effects,
                description=f"Броня типа {armor_type.capitalize()}",
                price_multiplier=tier_data["price_multiplier"]
            )
            armor.append(item)
        
        return armor
    
    def generate_all_items(self, unit_rank: int, weapon_count: int = 3, armor_count: int = 3) -> Dict[str, List[Item]]:
        """
        Генерирует полный набор возможных предметов
        
        Args:
            unit_rank: Ранг юнита
            weapon_count: Количество вариантов оружия
            armor_count: Количество вариантов брони
        
        Returns:
            Словарь с оружием и бронёй
        """
        return {
            "weapons": self.generate_weapons(unit_rank, weapon_count),
            "armor": self.generate_armor(unit_rank, armor_count),
        }

