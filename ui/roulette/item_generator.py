"""
Генератор случайных предметов для рулетки Рейна
Основан на системе рангов и прогрессии из Механик Снаряжения
"""

import random
from typing import List, Dict, Any
from dataclasses import dataclass
from .item_names import WEAPON_NAMES, ARMOR_NAMES
from .item_effects import WEAPON_EFFECTS, ARMOR_EFFECTS, RANK_RARITY, RARITY_NAMES, ITEM_TIERS


@dataclass
class Item:
    """Представление предмета"""
    name: str
    item_type: str  # "weapon" или "armor"
    rank: int
    rarity: str  # "common", "uncommon", "rare", "epic", "legendary"
    tier: int  # Тир качества (0-6): S, A, B, C, D, E, F
    effects: List[str]
    description: str
    price_multiplier: float  # Множитель цены от тира


class ItemGenerator:
    """Генератор предметов на основе ранга юнита"""
    
    def __init__(self):
        pass
    
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
            
            effects = WEAPON_EFFECTS.get(item_rank, ["Неизвестный эффект"])
            rarity = RANK_RARITY.get(item_rank, "common")
            
            # Генерируем случайный тир качества (0-6)
            tier = random.randint(0, 6)
            tier_data = ITEM_TIERS[tier]
            
            item = Item(
                name=f"{weapon_name} (Ранг {item_rank})",
                item_type="weapon",
                rank=item_rank,
                rarity=rarity,
                tier=tier,
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
            
            effects = ARMOR_EFFECTS.get(item_rank, ["Неизвестный эффект"])
            rarity = RANK_RARITY.get(item_rank, "common")
            
            # Генерируем случайный тир качества (0-6)
            tier = random.randint(0, 6)
            tier_data = ITEM_TIERS[tier]
            
            item = Item(
                name=f"{armor_name} (Ранг {item_rank})",
                item_type="armor",
                rank=item_rank,
                rarity=rarity,
                tier=tier,
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

