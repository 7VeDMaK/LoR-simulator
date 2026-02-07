import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType
from logic.scripts.luck import (
    add_luck_bonus_roll, scale_roll_by_luck,
    add_power_by_luck, repeat_dice_by_luck
)


# Mock for a card
class MockCard:
    def __init__(self, name="Test Card"):
        self.name = name
        self.dice_list = []


class TestLuckScripts(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnit(name="Lucky Guy", max_hp=100)
        # Add resources manually since MockUnit might not have it initialized by default
        self.unit.resources = {}

        self.dice = MockDice(DiceType.SLASH)
        self.ctx = MockContext(self.unit, dice=self.dice)
        self.ctx.final_value = 10  # Base roll value

    # ==========================================
    # 1. add_luck_bonus_roll
    # ==========================================
    @patch('logic.scripts.luck._check_conditions', return_value=True)
    def test_add_luck_bonus_roll(self, mock_cond):
        """Test: Adds bonus based on Luck (Luck // step)."""
        self.unit.resources["luck"] = 55

        # step 10 -> 55 // 10 = 5
        params = {"step": 10}
        add_luck_bonus_roll(self.ctx, params)

        # 10 + 5 = 15
        self.assertEqual(self.ctx.final_value, 15)
        self.assertIn("Luck (55)", self.ctx.log[0])

    def test_add_luck_bonus_limit(self):
        """Test: Bonus limit enforcement."""
        self.unit.resources["luck"] = 100

        # step 10 -> 10. limit 5.
        params = {"step": 10, "limit": 5}
        add_luck_bonus_roll(self.ctx, params)

        # 10 + 5 = 15
        self.assertEqual(self.ctx.final_value, 15)

    # ==========================================
    # 2. scale_roll_by_luck
    # ==========================================
    def test_scale_roll_by_luck(self):
        """Test: Roll multiplier (Luck // step * base_val)."""
        self.unit.resources["luck"] = 30
        self.ctx.final_value = 8  # Base

        # step 10 -> 3 repeats. Bonus = 3 * 8 = 24.
        params = {"step": 10}
        scale_roll_by_luck(self.ctx, params)

        # 8 + 24 = 32
        self.assertEqual(self.ctx.final_value, 32)
        self.assertIn("Luck x3", self.ctx.log[0])

    # ==========================================
    # 3. add_power_by_luck
    # ==========================================
    def test_add_power_by_luck(self):
        """Test: Power from luck (similar to bonus_roll but different logic description)."""
        self.unit.resources["luck"] = 25

        # step 5 -> 25 // 5 = 5
        params = {"step": 5}
        add_power_by_luck(self.ctx, params)

        # 10 + 5 = 15
        self.assertEqual(self.ctx.final_value, 15)
        self.assertIn("Fortune", self.ctx.log[0])

    # ==========================================
    # 4. repeat_dice_by_luck
    # ==========================================
    def test_repeat_dice_by_luck(self):
        """Test: Adding dice copies to the card based on Luck."""
        card = MockCard("Luck Card")
        d1 = MockDice(DiceType.PIERCE)
        card.dice_list = [d1]

        self.unit.current_card = card
        self.unit.resources["luck"] = 22

        # step 10 -> 22 // 10 = 2 repeats
        params = {"step": 10}
        repeat_dice_by_luck(self.ctx, params)

        # 1 (base) + 2 (clones) = 3
        self.assertEqual(len(card.dice_list), 3)
        self.assertEqual(card.dice_list[1].dtype, DiceType.PIERCE)
        self.assertEqual(card.dice_list[2].dtype, DiceType.PIERCE)
        # Check logs (partial match due to Cyrillic in source)
        self.assertTrue(any("Luck" in msg or "Удача" in msg for msg in self.ctx.log))


if __name__ == '__main__':
    unittest.main()