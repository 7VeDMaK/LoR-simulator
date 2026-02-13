import unittest
import sys
import os

# Путь к корню проекта
sys.path.append(os.getcwd())

from core.enums import DiceType
from core.logging import logger, LogLevel
from tests.mocks import MockUnit, MockDice, MockContext

# Импортируем реальную логику
from logic.battle_flow.clash.clash_resolution import resolve_clash_round
from logic.battle_flow.interactions import resolve_interaction


class MockEngine:
    def __init__(self):
        self.logs = []

    def log(self, text, level=LogLevel.NORMAL, category="Test"):
        self.logs.append(text)

    def _handle_clash_win(self, ctx):
        pass

    def _handle_clash_lose(self, ctx):
        pass

    def _handle_clash_draw(self, ctx):
        self.log(f"Draw: {ctx.source.name}")

    def _resolve_clash_interaction(self, winner_ctx, loser_ctx, diff):
        return resolve_interaction(self, winner_ctx, loser_ctx, diff)

    def _apply_damage(self, source_ctx, target_ctx, resource_type):
        # ВНИМАНИЕ: Здесь берется final_value. Если это Атака vs Атака,
        # то final_value не меняется (полный урон).
        amount = source_ctx.final_value
        target = target_ctx.source

        if resource_type == "hp":
            target.take_damage(amount)
        elif resource_type == "stagger":
            target.take_stagger_damage(amount)
        return amount

    def _deal_direct_damage(self, source_ctx, target_unit, amount, resource_type):
        if resource_type == "stagger":
            target_unit.take_stagger_damage(amount)
        return amount


class TestComplexClashScenarios(unittest.TestCase):
    def setUp(self):
        self.engine = MockEngine()
        self.attacker = MockUnit(name="Zafiel", max_hp=100, max_stagger=50)
        self.defender = MockUnit(name="Roland", max_hp=100, max_stagger=50)

    def _create_contexts(self, atk_val, def_val, atk_type, def_type):
        die_a = MockDice(dtype=atk_type)
        die_d = MockDice(dtype=def_type)

        ctx_a = MockContext(self.attacker, self.defender, die_a)
        ctx_a.final_value = atk_val

        ctx_d = MockContext(self.defender, self.attacker, die_d)
        ctx_d.final_value = def_val

        return ctx_a, ctx_d, die_a, die_d

    # =========================================================================
    # СЦЕНАРИЙ 1: НИЧЬЯ (Draw)
    # =========================================================================
    def test_clash_draw(self):
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(10, 10, DiceType.SLASH, DiceType.SLASH)
        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        self.assertIn("Draw", result["outcome"])
        self.assertEqual(self.attacker.current_hp, 100)
        self.assertEqual(self.defender.current_hp, 100)

    # =========================================================================
    # СЦЕНАРИЙ 2: МОЩНЫЙ БЛОК (Counter-Stagger)
    # =========================================================================
    def test_heavy_block_counter(self):
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(5, 20, DiceType.BLUNT, DiceType.BLOCK)
        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        self.assertIn("🛡️ Blocked", result["outcome"])
        expected_stagger = 50 - 15  # 35
        self.assertEqual(self.attacker.current_stagger, expected_stagger)

    # =========================================================================
    # СЦЕНАРИЙ 3: ПРОБИТИЕ БЛОКА (Chip Damage)
    # =========================================================================
    def test_block_chip_damage(self):
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(20, 15, DiceType.PIERCE, DiceType.BLOCK)
        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        self.assertIn("Win (Hit)", result["outcome"])
        self.assertEqual(self.defender.current_hp, 95)  # 100 - (20-15) = 95

    # =========================================================================
    # СЦЕНАРИЙ 4: ИДЕАЛЬНЫЙ УВОРОТ (Stagger Restore)
    # =========================================================================
    def test_evade_stagger_restore(self):
        self.defender.current_stagger = 20
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(5, 15, DiceType.BLUNT, DiceType.EVADE)
        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        self.assertIn("Evades!", result["outcome"])
        self.assertTrue(result["recycle_d"])
        self.assertEqual(self.defender.current_stagger, 35)  # 20 + 15

    # =========================================================================
    # СЦЕНАРИЙ 5: СЕРИЯ УДАРОВ (Симуляция)
    # =========================================================================
    def test_sequence_simulation(self):
        # Раунд 1: Атака (10) vs Блок (5) -> Урон 5
        ctx_a1, ctx_d1, die_a1, die_d1 = self._create_contexts(10, 5, DiceType.SLASH, DiceType.BLOCK)
        resolve_clash_round(self.engine, ctx_a1, ctx_d1, die_a1, die_d1)

        self.assertEqual(self.defender.current_hp, 95)  # -5 HP

        # Раунд 2: Атака (15) vs Атака (8) -> Урон 15 (Полный!)
        # Если бы урон был по разнице, было бы 95 - 7 = 88. Но в LoR полный урон.
        ctx_a2, ctx_d2, die_a2, die_d2 = self._create_contexts(15, 8, DiceType.SLASH, DiceType.SLASH)
        resolve_clash_round(self.engine, ctx_a2, ctx_d2, die_a2, die_d2)

        self.assertEqual(self.defender.current_hp, 80)  # 95 - 15

        print("✅ Sequence Test Passed: HP 100 -> 95 -> 80")


if __name__ == '__main__':
    unittest.main()