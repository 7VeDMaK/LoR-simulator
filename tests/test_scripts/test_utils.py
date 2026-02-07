import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext
from logic.scripts.utils import (
    _get_unit_stat, _resolve_value, _get_targets, _check_conditions
)


class TestScriptUtils(unittest.TestCase):

    def setUp(self):
        self.source = MockUnit(name="Source", max_hp=100)
        self.target = MockUnit(name="Target", max_hp=100)

        # Populate some stats for testing
        self.source.current_hp = 80
        self.source.attributes = {"strength": 10, "agility": 5}
        self.source.resources = {"light": 3}
        self.source.modifiers = {"total_strength": 12}  # Modified stat

        self.target.current_hp = 50
        self.target.attributes = {"strength": 8}

        self.ctx = MockContext(self.source, target=self.target)

    # ==========================================
    # 1. _get_unit_stat
    # ==========================================
    def test_get_unit_stat_dynamic(self):
        """Test: Retrieving dynamic stats (hp, sp)."""
        self.assertEqual(_get_unit_stat(self.source, "hp"), 80)
        self.assertEqual(_get_unit_stat(self.source, "max_hp"), 100)

    def test_get_unit_stat_resource(self):
        """Test: Retrieving resources."""
        self.assertEqual(_get_unit_stat(self.source, "light"), 3)

    def test_get_unit_stat_modifier(self):
        """Test: Retrieving modifier-enhanced stats (total_strength)."""
        # Should prefer 'modifiers' dict over 'attributes'
        self.assertEqual(_get_unit_stat(self.source, "strength"), 12)

    def test_get_unit_stat_attribute_fallback(self):
        """Test: Fallback to attributes if modifier not present."""
        self.assertEqual(_get_unit_stat(self.source, "agility"), 5)

    def test_get_unit_stat_level(self):
        """Test: Retrieving unit level."""
        self.source.level = 5
        self.assertEqual(_get_unit_stat(self.source, "level"), 5)

    # ==========================================
    # 2. _resolve_value
    # ==========================================
    def test_resolve_value_flat(self):
        """Test: Simple flat value (base)."""
        params = {"base": 10}
        val = _resolve_value(self.source, self.target, params)
        self.assertEqual(val, 10)

    def test_resolve_value_scaling(self):
        """Test: Scaling from Source stat (Strength)."""
        # base 5 + (Strength 12 * 0.5) = 5 + 6 = 11
        params = {"base": 5, "stat": "strength", "factor": 0.5}
        val = _resolve_value(self.source, self.target, params)
        self.assertEqual(val, 11)

    def test_resolve_value_scale_from_target(self):
        """Test: Scaling from Target stat (Strength)."""
        # Target Strength is 8 (from attributes, no modifier set in setUp)
        # base 0 + (8 * 2.0) = 16
        params = {"base": 0, "stat": "strength", "factor": 2.0, "scale_from_target": True}
        val = _resolve_value(self.source, self.target, params)
        self.assertEqual(val, 16)

    def test_resolve_value_diff(self):
        """Test: Difference between Source and Target."""
        # Source Str (12) - Target Str (8) = 4
        # 4 * 1.0 = 4
        params = {"stat": "strength", "diff": True}
        val = _resolve_value(self.source, self.target, params)
        self.assertEqual(val, 4)

    def test_resolve_value_max_limit(self):
        """Test: Capping the value."""
        # Source HP 80. Limit 50.
        params = {"stat": "hp", "max": 50}
        val = _resolve_value(self.source, self.target, params)
        self.assertEqual(val, 50)

    # ==========================================
    # 3. _get_targets
    # ==========================================
    def test_get_targets_basic(self):
        """Test: 'self' and 'target' modes."""
        self.assertEqual(_get_targets(self.ctx, "self"), [self.source])
        self.assertEqual(_get_targets(self.ctx, "target"), [self.target])
        self.assertEqual(len(_get_targets(self.ctx, "all")), 2)

    def test_get_targets_all_allies(self):
        """Test: 'all_allies' retrieves team from session_state."""
        ally = MockUnit(name="Ally")
        team = [self.source, ally]

        mock_state = {
            'team_left': team,
            'team_right': []
        }

        with patch('streamlit.session_state', mock_state):
            targets = _get_targets(self.ctx, "all_allies")
            self.assertEqual(len(targets), 2)
            self.assertIn(ally, targets)

    # ==========================================
    # 4. _check_conditions
    # ==========================================
    def test_check_conditions_probability_success(self):
        """Test: Probability check passes."""
        with patch('random.random', return_value=0.1):  # 0.1 < 0.5
            params = {"probability": 0.5}
            self.assertTrue(_check_conditions(self.source, params))

    def test_check_conditions_probability_fail(self):
        """Test: Probability check fails."""
        with patch('random.random', return_value=0.9):  # 0.9 > 0.5
            params = {"probability": 0.5}
            self.assertFalse(_check_conditions(self.source, params))

    def test_check_conditions_req_stat(self):
        """Test: Stat requirement check."""
        # Source Str is 12

        # Req 10 (Pass)
        self.assertTrue(_check_conditions(self.source, {"req_stat": "strength", "req_val": 10}))

        # Req 20 (Fail)
        self.assertFalse(_check_conditions(self.source, {"req_stat": "strength", "req_val": 20}))


if __name__ == '__main__':
    unittest.main()