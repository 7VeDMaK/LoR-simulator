import sys
import os

# Чтобы видеть корень проекта
sys.path.append(os.getcwd())

from core.enums import DiceType


class MockUnit:
    """Имитация Юнита с поддержкой HP, урона и текущего действия."""

    def __init__(self, name="Test Dummy", level=1, max_hp=100):
        self.name = name
        self.level = level
        self.talents = []
        self.attributes = {}
        self.statuses = {}
        self.counter_dice = []
        self.passives = []
        self.talents = []
        self.hp_resists = MockResists()

        self.max_hp = max_hp
        self.current_hp = max_hp
        self.cooldowns = {}

        # [NEW] Текущий кубик, который разыгрывает юнит
        self.current_die = None

    def add_status(self, status_id, amount, duration=None):
        current = self.statuses.get(status_id, 0)
        self.statuses[status_id] = current + amount

    def heal_hp(self, amount):
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp

    # [NEW] Метод получения урона (для рефлекта)
    def take_damage(self, amount, damage_type=None):
        self.current_hp -= amount
        return amount


class MockResists:
    def __init__(self):
        self.slash = 1.0
        self.pierce = 1.0
        self.blunt = 1.0


class MockDice:
    def __init__(self, dtype=DiceType.SLASH, value=0, flags=None):
        self.dtype = dtype
        self.final_value = value
        self.flags = flags or []


class MockContext:
    def __init__(self, source, target=None, dice=None):
        self.source = source
        self.target = target
        self.dice = dice
        self.damage_multiplier = 1.0
        self.log = []
        self.is_critical = False

    def modify_power(self, val, reason=""):
        pass

    def iter_mechanics(self):
        """Возвращает список всех активных пассивок/талантов."""
        return self.passives