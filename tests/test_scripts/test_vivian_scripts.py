import unittest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
# Импортируем НОВЫЕ скрипты
from logic.scripts.card_damage import deal_damage_by_roll, deal_damage_by_clash_diff
from logic.scripts.resources import restore_resource_by_roll


class TestVivianGeneric(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnit(name="Vivien", max_hp=100)
        self.unit.current_hp = 100
        self.ctx = MockContext(self.unit)
        self.ctx.log = []

    def test_deal_damage_by_roll(self):
        """Тест: Урон по себе от броска."""
        self.ctx.final_value = 15

        deal_damage_by_roll(self.ctx, {"target": "self"})

        self.assertEqual(self.unit.current_hp, 85)  # 100 - 15
        self.assertTrue(any("Roll Dmg" in msg for msg in self.ctx.log))

    def test_restore_resource_by_roll(self):
        """Тест: Лечение от броска."""
        self.unit.current_hp = 50
        self.ctx.final_value = 20

        restore_resource_by_roll(self.ctx, {"type": "hp", "target": "self"})

        self.assertEqual(self.unit.current_hp, 70)  # 50 + 20
        self.assertTrue(any("Roll Heal" in msg for msg in self.ctx.log))

    def test_damage_by_clash_diff(self):
        """Тест: Урон от разницы клэша."""
        # 1. Прямая разница
        self.ctx.clash_diff = 8
        deal_damage_by_clash_diff(self.ctx, {"target": "self"})
        self.assertEqual(self.unit.current_hp, 92)  # 100 - 8

        # 2. Расчетная разница
        self.unit.current_hp = 100  # Reset
        self.ctx.clash_diff = 0
        self.ctx.final_value = 20
        self.ctx.target_die_result = 10

        deal_damage_by_clash_diff(self.ctx, {"target": "self"})
        self.assertEqual(self.unit.current_hp, 90)  # 100 - (20-10)


if __name__ == '__main__':
    unittest.main()