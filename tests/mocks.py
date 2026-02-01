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

    def get_status(self, status_id):
        return self.statuses.get(status_id, 0)

    def remove_status(self, status_id, amount):
        current = self.statuses.get(status_id, 0)
        new_val = max(0, current - amount)
        self.statuses[status_id] = new_val

    def heal_hp(self, amount):
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp

    def take_damage(self, amount, damage_type=None):
        self.current_hp -= amount
        return amount

    def apply_mechanics_filter(self, method_name, val, *args, **kwargs):
        return val


class MockResists:
    def __init__(self):
        self.slash = 1.0
        self.pierce = 1.0
        self.blunt = 1.0


class MockDice:
    def __init__(self, dtype=DiceType.SLASH, min_val=1, max_val=10):
        self.dtype = dtype
        self.min_val = min_val
        self.max_val = max_val
        self.final_value = 0 # Результат броска


class MockContext:
    def __init__(self, source, target=None, dice=None):
        self.source = source
        self.target = target
        self.dice = dice
        self.damage_multiplier = 1.0
        self.log = []
        self.is_critical = False

        self.final_value = 0
        self.base_value = 0  # Для тестов паралича

    # [FIX] Метод должен реально менять значение
    def modify_power(self, val, reason=""):
        self.final_value += val
        self.log.append(f"Modify Power: {val} ({reason})")

    def iter_mechanics(self):
        # Этот метод обычно не у контекста, а у юнита, но пусть будет заглушка
        return []