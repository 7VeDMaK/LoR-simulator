import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType
from logic.battle_flow.clash.clash import process_clash


# === CUSTOM MOCKS FOR OVERKILL ===

class OverkillMockUnit:
    """Mock Unit that allows negative HP."""

    def __init__(self, name, hp=10):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.stagger = 20
        self.active_slots = []
        self.current_card = None
        self.counter_dice = []
        self.passive_counter_queue = []
        self.stored_dice = []
        self.current_die = None

    def is_dead(self):
        # Even if "dead", the object persists for mechanics
        return self.hp <= 0

    def is_staggered(self):
        return False

    def take_damage(self, amount):
        # [CRITICAL] Standard subtraction, allowing negatives
        self.hp -= amount


class MockDice:
    def __init__(self, val):
        self.dtype = DiceType.SLASH
        self.min_val = val
        self.max_val = val
        self.is_counter = False


class TestOverkillMechanics(unittest.TestCase):

    def setUp(self):
        self.engine = MagicMock()

        # 1. Mock Rolls
        def mock_roll(u, t, die, **kwargs):
            ctx = MagicMock()
            ctx.source = u
            ctx.target = t
            ctx.final_value = die.min_val
            ctx.log = []
            return ctx

        self.engine._create_roll_context.side_effect = mock_roll

        # 2. Mock Interaction Resolution (Damage application)
        def mock_resolve_interaction(ctx_atk, ctx_def, diff):
            damage = diff  # Simple difference calculation

            # Identify who takes damage (usually loser of clash)
            target = None
            if ctx_def:
                target = ctx_def.source
            elif ctx_atk and ctx_atk.target:
                target = ctx_atk.target

            if target and hasattr(target, 'take_damage'):
                target.take_damage(damage)
            return damage

        self.engine._resolve_clash_interaction.side_effect = mock_resolve_interaction

        # 3. Mock One-Sided Exchange (since unit will run out of dice after death)
        def mock_onesided(eng, active_side, passive_side, detail_logs):
            die = active_side.resolve_current_die()
            target = passive_side.unit
            if die:
                dmg = die.min_val
                if target:
                    target.take_damage(dmg)
                return f"Hit ({dmg} dmg)"
            return "Skip"

        self.mock_onesided_patcher = patch('logic.battle_flow.clash.clash_one_sided.handle_one_sided_exchange',
                                           side_effect=mock_onesided)
        self.mock_onesided = self.mock_onesided_patcher.start()

    def tearDown(self):
        self.mock_onesided_patcher.stop()

    def test_overkill_accumulation(self):
        """
        Scenario: Attacker deals massive damage.
        Attacker: 3 Dice [20, 20, 20]
        Defender: 1 Dice [5], HP = 10

        1. Clash 1: 20 vs 5 -> Defender takes 15 dmg. HP: 10 -> -5. (Dead)
        2. Clash 2: 20 vs (Empty) -> Defender takes 20 dmg. HP: -5 -> -25.
        3. Clash 3: 20 vs (Empty) -> Defender takes 20 dmg. HP: -25 -> -45.
        """
        attacker = OverkillMockUnit("Killer", hp=100)
        defender = OverkillMockUnit("Victim", hp=10)

        attacker.current_card = MagicMock()
        attacker.current_card.dice_list = [MockDice(20), MockDice(20), MockDice(20)]

        defender.current_card = MagicMock()
        defender.current_card.dice_list = [MockDice(5)]

        # Execute Clash
        report = process_clash(self.engine, attacker, defender, "Round 1", True, 10, 5)

        # Verification
        self.assertEqual(len(report), 3, "Combat should continue for all attacker dice.")

        expected_hp = 10 - 15 - 20 - 20  # -45
        self.assertEqual(defender.hp, expected_hp,
                         f"HP should accumulate negative value. Got {defender.hp}, expected {expected_hp}")

        print(f"✅ Overkill Test Passed. Final HP: {defender.hp}")


if __name__ == '__main__':
    unittest.main()
    #todo доделать тест + оверкилл