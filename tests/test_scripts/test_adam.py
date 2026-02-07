import unittest
import sys
import os

# Добавляем корень в путь
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType
from logic.scripts.adam_card_scripts import (
    adam_t1_cost, adam_t1_punish, adam_t2_combo,
    adam_t3_execution, adam_t4_wethermon_fail
)


class TestAdamScripts(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnit(name="Adam", max_hp=200)
        self.unit.current_hp = 200
        self.dice = MockDice(DiceType.SLASH)
        self.ctx = MockContext(self.unit, dice=self.dice)

    # ==========================================
    # TIER 1 & 2: Проверка стоимости в HP
    # ==========================================
    def test_adam_t1_cost(self):
        """Плата 5% HP от 200 = 10 урона."""
        adam_t1_cost(self.ctx)
        # 200 - (200 * 0.05) = 190
        self.assertEqual(self.unit.current_hp, 190)
        self.assertIn("🩸 Плата: -10 HP", self.ctx.log)

    def test_adam_t1_punish(self):
        """Наказание 5% HP от 200 = 10 урона."""
        adam_t1_punish(self.ctx)
        self.assertEqual(self.unit.current_hp, 190)
        self.assertIn("💔 Отдача: -10 HP", self.ctx.log)

    # ==========================================
    # TIER 2: Combo
    # ==========================================
    def test_adam_t2_combo(self):
        """Combo должен добавлять +3 к мощи."""
        adam_t2_combo(self.ctx)
        self.assertEqual(self.ctx.final_value, 3)

    # ==========================================
    # TIER 3: Execution (Слом кубика)
    # ==========================================
    def test_adam_t3_execution(self):
        """Execution должен ломать кубик оппонента."""
        # Создаем контекст оппонента
        enemy_unit = MockUnit(name="Enemy")
        enemy_dice = MockDice(DiceType.BLOCK)
        enemy_ctx = MockContext(enemy_unit, dice=enemy_dice)

        # Связываем контексты
        self.ctx.opponent_ctx = enemy_ctx

        adam_t3_execution(self.ctx)

        # Проверяем, что флаг слома установлен
        self.assertTrue(getattr(enemy_dice, 'is_broken', False))
        self.assertIn("⚔️ Dice Destroyed!", self.ctx.log)

    # ==========================================
    # TIER 4: Wethermon Flag
    # ==========================================
    def test_adam_t4_wethermon_fail(self):
        """Проверка установки флага провала в память юнита."""
        adam_t4_wethermon_fail(self.ctx)

        self.assertTrue(self.unit.memory.get('wethermon_failed'))
        self.assertIn("⚠️ Wethermon Check Failed! (Flag Set)", self.ctx.log)


if __name__ == '__main__':
    unittest.main()