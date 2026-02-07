import sys
import os

# Чтобы видеть корень проекта
sys.path.append(os.getcwd())

from core.enums import DiceType


class MockUnit:
    """Имитация Юнита с поддержкой всех необходимых атрибутов для скриптов."""

    def __init__(self, name="Test Dummy", level=1, max_hp=100):
        self.name = name
        self.level = level

        # Основные характеристики
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.max_sp = 100
        self.current_sp = 100
        self.max_stagger = 100
        self.current_stagger = 100

        # Словари данных
        self.resources = {}
        self.modifiers = {}
        self.skills = {}
        self.attributes = {}

        self.statuses = {}
        self.memory = {}
        self.cooldowns = {}

        # Списки и логика
        self.talents = []
        self.passives = []
        self.counter_dice = []
        self.hand = []

        # Объекты сцены
        self.hp_resists = MockResists()
        self.current_die = None
        self.scene = None
        self.team_id = 0

    def is_dead(self):
        return self.current_hp <= 0

    def add_status(self, status_id, amount, duration=None, delay=0):
        """
        Поддержка delay для statuses.py.
        """
        if delay > 0:
            return True, "Delayed"

        current = self.statuses.get(status_id, 0)
        self.statuses[status_id] = current + amount
        return True, "Applied"

    def get_status(self, status_id):
        return self.statuses.get(status_id, 0)

    def take_sanity_damage(self, amount):
        self.current_sp = max(0, self.current_sp - amount)

    def remove_status(self, status_id, amount=999):
        """
        [FIX] amount теперь необязателен (по умолчанию снимает всё/много),
        чтобы поддерживать вызовы вида u.remove_status("burn").
        """
        current = self.statuses.get(status_id, 0)
        if amount >= 999:
            new_val = 0
        else:
            new_val = max(0, current - amount)
        self.statuses[status_id] = new_val

    def heal_hp(self, amount):
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp

    def restore_sp(self, amount):
        old_sp = self.current_sp
        self.current_sp = min(self.max_sp, self.current_sp + amount)
        return self.current_sp - old_sp

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
        self.final_value = 0
        self.is_broken = False


class MockContext:
    def __init__(self, source, target=None, dice=None, card=None):
        self.source = source
        self.target = target
        self.dice = dice
        self.card = card
        self.damage_multiplier = 1.0
        self.log = []
        self.is_critical = False

        self.final_value = 0
        self.base_value = 0
        self.clash_diff = 0
        self.target_die_result = 0

        self.opponent_ctx = None

    def modify_power(self, val, reason=""):
        self.final_value += val
        self.log.append(f"Modify Power: {val} ({reason})")

    def iter_mechanics(self):
        return []