import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Добавляем корень проекта
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType
from logic.scripts.card_power import (
    modify_roll_power, convert_status_to_power, lima_ram_logic
)


class TestCardPower(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnit(name="Striker", level=1, max_hp=100)
        self.target = MockUnit(name="Sandbag", max_hp=100)
        self.dice = MockDice(DiceType.BLUNT)
        self.ctx = MockContext(self.unit, target=self.target, dice=self.dice)

    # ==========================================
    # 1. modify_roll_power
    # ==========================================
    @patch('logic.scripts.card_power._check_conditions', return_value=True)
    @patch('logic.scripts.card_power._resolve_value')
    def test_modify_roll_power_success(self, mock_resolve, mock_cond):
        """Тест: Успешное увеличение силы броска."""
        mock_resolve.return_value = 5  # Утилита вернула +5

        params = {"stat": "strength", "reason": "Test Bonus"}
        modify_roll_power(self.ctx, params)

        self.assertEqual(self.ctx.final_value, 5)
        # Проверяем, что в лог попала наша причина
        self.assertTrue(any("Test Bonus" in log for log in self.ctx.log))

    @patch('logic.scripts.card_power._check_conditions', return_value=False)
    def test_modify_roll_power_conditions_fail(self, mock_cond):
        """Тест: Условия не выполнены -> сила не меняется."""
        params = {"value": 5}
        modify_roll_power(self.ctx, params)

        self.assertEqual(self.ctx.final_value, 0)

    # ==========================================
    # 2. convert_status_to_power
    # ==========================================
    def test_convert_status_to_power(self):
        """Тест: Конвертация статуса 'charge' в силу (1 к 1)."""
        self.unit.add_status("charge", 5)

        params = {"status": "charge", "factor": 1.0}
        convert_status_to_power(self.ctx, params)

        # Сила +5
        self.assertEqual(self.ctx.final_value, 5)
        # Статус должен исчезнуть (или уменьшиться на 5)
        self.assertEqual(self.unit.get_status("charge"), 0)
        self.assertIn("Consumed Charge", self.ctx.log[0])

    def test_convert_status_factor(self):
        """Тест: Конвертация с множителем (10 стаков * 0.5 = 5 силы)."""
        self.unit.add_status("smoke", 10)

        params = {"status": "smoke", "factor": 0.5}
        convert_status_to_power(self.ctx, params)

        self.assertEqual(self.ctx.final_value, 5)
        self.assertEqual(self.unit.get_status("smoke"), 0)

    def test_convert_no_status(self):
        """Тест: Нет статусов -> нет бонуса."""
        params = {"status": "charge"}
        convert_status_to_power(self.ctx, params)

        self.assertEqual(self.ctx.final_value, 0)

    # ==========================================
    # 3. lima_ram_logic (Таран Лимы)
    # ==========================================
    def test_lima_ram_logic_basic(self):
        """Тест: Лима ур.3, Haste 5 -> (base 2 * lvl_mult 1) = +2."""
        self.unit.level = 3  # mult = 3/3 = 1
        self.unit.add_status("haste", 5)  # base = 2

        lima_ram_logic(self.ctx, {})

        self.assertEqual(self.ctx.final_value, 2)
        # Haste должен сгореть
        self.assertEqual(self.unit.get_status("haste"), 0)

    def test_lima_ram_logic_high_level(self):
        """Тест: Лима ур.9, Haste 20 -> (base 5 * lvl_mult 3) = +15."""
        self.unit.level = 9  # mult = 9/3 = 3
        self.unit.add_status("haste", 20)  # base = 5 (max)

        lima_ram_logic(self.ctx, {})

        self.assertEqual(self.ctx.final_value, 15)
        self.assertEqual(self.unit.get_status("haste"), 0)

    def test_lima_ram_logic_low_level(self):
        """Тест: Лима ур.1 (меньше 3) -> множитель 0 -> бонус 0."""
        self.unit.level = 1  # mult = 1/3 = 0
        self.unit.add_status("haste", 10)

        lima_ram_logic(self.ctx, {})

        self.assertEqual(self.ctx.final_value, 0)
        # Haste все равно сгорает по логике скрипта
        self.assertEqual(self.unit.get_status("haste"), 0)


if __name__ == '__main__':
    unittest.main()