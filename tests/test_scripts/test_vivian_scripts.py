import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Добавляем корень проекта
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType

# Предполагаем, что вы сохранили этот код в logic/scripts/vivien_scripts.py
# Если файл называется иначе, поправьте импорт
from logic.scripts.vivian_scripts import (
    damage_self_by_roll, heal_self_by_roll, damage_self_clash_diff
)


class TestVivienScripts(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnit(name="Vivien", max_hp=100)
        self.unit.current_hp = 100
        self.dice = MockDice(DiceType.SLASH)
        self.ctx = MockContext(self.unit, dice=self.dice)

    # ==========================================
    # 1. Мазохизм (Урон от своего броска)
    # ==========================================
    def test_damage_self_by_roll(self):
        """Тест: Вивьен получает урон, равный значению кубика."""
        self.ctx.final_value = 15

        damage_self_by_roll(self.ctx)

        # 100 - 15 = 85
        self.assertEqual(self.unit.current_hp, 85)
        self.assertTrue(any("Мазохизм" in msg for msg in self.ctx.log))

    def test_damage_self_by_roll_zero(self):
        """Тест: При нулевом броске урон не наносится."""
        self.ctx.final_value = 0
        damage_self_by_roll(self.ctx)
        self.assertEqual(self.unit.current_hp, 100)

    # ==========================================
    # 2. Вампиризм (Лечение от броска)
    # ==========================================
    def test_heal_self_by_roll(self):
        """Тест: Вивьен лечится на значение кубика."""
        self.unit.current_hp = 50
        self.ctx.final_value = 20

        heal_self_by_roll(self.ctx)

        # 50 + 20 = 70
        self.assertEqual(self.unit.current_hp, 70)
        self.assertTrue(any("Вампиризм" in msg for msg in self.ctx.log))

    def test_heal_self_by_roll_cap(self):
        """Тест: Лечение не превышает максимум HP."""
        self.unit.current_hp = 90
        self.ctx.final_value = 20

        heal_self_by_roll(self.ctx)

        # 90 + 20 -> 110, но cap 100
        self.assertEqual(self.unit.current_hp, 100)

    # ==========================================
    # 3. Коллекция шрамов (Урон от разницы клэша)
    # ==========================================
    def test_damage_self_clash_diff_direct(self):
        """Тест: Урон берется из готового clash_diff."""
        # Эмулируем ситуацию, когда движок передал diff
        self.ctx.clash_diff = 8

        damage_self_clash_diff(self.ctx)

        # 100 - 8 = 92
        self.assertEqual(self.unit.current_hp, 92)
        self.assertTrue(any("Коллекция шрамов" in msg for msg in self.ctx.log))

    def test_damage_self_clash_diff_calculated(self):
        """Тест: Урон вычисляется (Мой бросок - Бросок врага)."""
        # clash_diff нет, но есть броски
        self.ctx.final_value = 18
        self.ctx.target_die_result = 12
        # Diff = 6

        damage_self_clash_diff(self.ctx)

        # 100 - 6 = 94
        self.assertEqual(self.unit.current_hp, 94)

    def test_damage_self_clash_diff_negative(self):
        """Тест: Если разница отрицательная или 0 (ничья/проигрыш), урон 0."""
        self.ctx.final_value = 10
        self.ctx.target_die_result = 15  # Проиграла клэш (по идее скрипт On Win не сработает, но проверим логику)

        damage_self_clash_diff(self.ctx)

        self.assertEqual(self.unit.current_hp, 100)


if __name__ == '__main__':
    unittest.main()