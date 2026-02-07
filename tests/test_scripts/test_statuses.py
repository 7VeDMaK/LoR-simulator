import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from logic.scripts.statuses import (
    apply_status, steal_status, multiply_status,
    remove_status_script, remove_all_positive,
    apply_status_by_roll, remove_random_status,
    apply_slot_debuff
)


class TestStatusScripts(unittest.TestCase):

    def setUp(self):
        self.source = MockUnit(name="Caster", max_hp=100)
        self.target = MockUnit(name="Target", max_hp=100)
        self.ctx = MockContext(self.source, target=self.target)
        self.ctx.base_value = 10  # Default base roll
        self.ctx.final_value = 15  # Default final roll

    # ==========================================
    # 1. apply_status
    # ==========================================
    @patch('logic.scripts.statuses._check_conditions', return_value=True)
    @patch('logic.scripts.statuses._get_targets')
    @patch('logic.scripts.statuses._resolve_value')
    # We patch NEGATIVE_STATUSES directly where it is imported in the module
    @patch('logic.statuses.status_constants.NEGATIVE_STATUSES', ["burn", "bleed", "paralysis"])
    def test_apply_status_basic(self, mock_resolve, mock_targets, mock_cond):
        """Test: Apply status successfully."""
        mock_targets.return_value = [self.target]
        mock_resolve.return_value = 5  # 5 stacks

        params = {"status": "burn", "stack": 5}
        apply_status(self.ctx, params)

        self.assertEqual(self.target.get_status("burn"), 5)
        self.assertTrue(any("🧪" in msg for msg in self.ctx.log))

    @patch('logic.scripts.statuses._check_conditions', return_value=True)
    @patch('logic.scripts.statuses._get_targets')
    @patch('logic.statuses.status_constants.NEGATIVE_STATUSES', ["burn"])
    def test_apply_status_lycoris_immune(self, mock_targets, mock_cond):
        """Test: Red Lycoris blocks negative statuses."""
        mock_targets.return_value = [self.target]
        self.target.add_status("red_lycoris", 1)

        params = {"status": "burn"}  # burn is negative
        apply_status(self.ctx, params)

        self.assertEqual(self.target.get_status("burn"), 0)
        self.assertTrue(any("Immune" in msg for msg in self.ctx.log))

    @patch('logic.scripts.statuses._check_conditions', return_value=True)
    @patch('logic.scripts.statuses._get_targets')
    def test_apply_status_min_roll_fail(self, mock_targets, mock_cond):
        """Test: Fails if base roll < min_roll."""
        self.ctx.base_value = 5
        params = {"status": "haste", "min_roll": 10}

        apply_status(self.ctx, params)

        self.assertEqual(self.target.get_status("haste"), 0)

    # ==========================================
    # 2. steal_status
    # ==========================================
    def test_steal_status(self):
        """Test: Stealing status from target to source."""
        self.target.add_status("power_up", 3)
        self.source.add_status("power_up", 0)

        params = {"status": "power_up"}
        steal_status(self.ctx, params)

        # Target loses all
        self.assertEqual(self.target.get_status("power_up"), 0)
        # Source gains
        self.assertEqual(self.source.get_status("power_up"), 3)
        self.assertIn("stole 3 power_up", self.ctx.log[0])

    # ==========================================
    # 3. multiply_status
    # ==========================================
    @patch('logic.scripts.statuses._get_targets')
    def test_multiply_status(self, mock_targets):
        """Test: Multiplies existing status (e.g., Burn x2)."""
        mock_targets.return_value = [self.target]
        self.target.add_status("burn", 10)

        # x2
        params = {"status": "burn", "multiplier": 2.0}
        multiply_status(self.ctx, params)

        # 10 * 2 = 20. Added 10.
        self.assertEqual(self.target.get_status("burn"), 20)
        self.assertIn("x2.0", self.ctx.log[0])

    # ==========================================
    # 4. remove_status_script & remove_all_positive
    # ==========================================
    @patch('logic.scripts.statuses._check_conditions', return_value=True)
    @patch('logic.scripts.statuses._get_targets')
    @patch('logic.scripts.statuses._resolve_value', return_value=5)
    def test_remove_status_script(self, mock_resolve, mock_targets, mock_cond):
        """Test: Removing specific amount of status."""
        mock_targets.return_value = [self.target]
        self.target.add_status("bind", 10)

        params = {"status": "bind", "amount": 5}
        remove_status_script(self.ctx, params)

        self.assertEqual(self.target.get_status("bind"), 5)  # 10 - 5

    @patch('logic.scripts.statuses._get_targets')
    def test_remove_all_positive(self, mock_targets):
        """Test: Removes known positive buffs."""
        mock_targets.return_value = [self.target]
        self.target.add_status("strength", 5)  # strength (attack_power_up logic in mocks usually)
        self.target.add_status("protection", 3)
        self.target.add_status("burn", 10)  # Negative, should stay

        # Mocking the constants list inside the function logic requires us
        # to ensure MockUnit uses the same keys.
        # Let's assume MockUnit just stores what we give it.
        # The script checks specific strings like "protection".

        remove_all_positive(self.ctx, {"target": "target"})

        self.assertEqual(self.target.get_status("protection"), 0)
        self.assertEqual(self.target.get_status("burn"), 10)

    # ==========================================
    # 5. apply_status_by_roll
    # ==========================================
    @patch('logic.scripts.statuses._check_conditions', return_value=True)
    @patch('logic.scripts.statuses._get_targets')
    def test_apply_status_by_roll(self, mock_targets, mock_cond):
        """Test: Amount = roll value."""
        mock_targets.return_value = [self.source]
        self.ctx.final_value = 8

        params = {"status": "poise"}
        apply_status_by_roll(self.ctx, params)

        self.assertEqual(self.source.get_status("poise"), 8)

    # ==========================================
    # 6. remove_random_status
    # ==========================================
    @patch('random.choice')
    def test_remove_random_status(self, mock_choice):
        """Test: Removes one random non-ignored status."""
        # Setup: 1 ignored (ammo), 2 valid (burn, bind)
        self.target.statuses = {
            "ammo": 5,
            "burn": 10,
            "bind": 3
        }

        # Force choice to be 'burn'
        mock_choice.return_value = "burn"

        remove_random_status(self.ctx, {"amount": 2})

        self.assertEqual(self.target.get_status("burn"), 8)  # 10 - 2
        self.assertEqual(self.target.get_status("ammo"), 5)  # Ignored


if __name__ == '__main__':
    unittest.main()