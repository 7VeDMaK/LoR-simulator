import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Добавляем корень проекта
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext
# Импортируем тестируемую функцию
from logic.scripts.card_scripts import restore_resource


class MockUnitRestorable(MockUnit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_sp = 100
        self.current_sp = 50
        self.max_stagger = 50
        self.current_stagger = 20

    def restore_sp(self, amount, source=None, **kwargs):
        old_sp = self.current_sp
        self.current_sp = min(self.max_sp, self.current_sp + amount)
        return self.current_sp - old_sp


class TestCardScripts(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnitRestorable(name="Healer", max_hp=100)
        self.unit.current_hp = 50
        self.ctx = MockContext(self.unit)
        self.ctx.log = []

    def test_restore_hp_heal(self):
        """Тест: Лечение HP (положительное значение)."""
        # Используем with для явного патчинга
        with patch('logic.scripts.card_scripts._check_conditions', return_value=True) as mock_cond, \
                patch('logic.scripts.card_scripts._get_targets') as mock_targets, \
                patch('logic.scripts.card_scripts._resolve_value') as mock_resolve:
            mock_targets.return_value = [self.unit]
            mock_resolve.return_value = 20  # Принудительно возвращаем 20

            params = {"type": "hp"}
            restore_resource(self.ctx, params)

            self.assertEqual(self.unit.current_hp, 70)  # 50 + 20
            self.assertIn("💚", self.ctx.log[0])

    def test_restore_hp_drain(self):
        """Тест: Отнятие HP (отрицательное значение)."""
        with patch('logic.scripts.card_scripts._check_conditions', return_value=True), \
                patch('logic.scripts.card_scripts._get_targets') as mock_targets, \
                patch('logic.scripts.card_scripts._resolve_value') as mock_resolve:
            mock_targets.return_value = [self.unit]
            mock_resolve.return_value = -10

            params = {"type": "hp"}
            restore_resource(self.ctx, params)

            self.assertEqual(self.unit.current_hp, 40)  # 50 - 10
            self.assertIn("💔", self.ctx.log[0])

    def test_restore_sp_recover(self):
        """Тест: Восстановление SP."""
        with patch('logic.scripts.card_scripts._check_conditions', return_value=True), \
                patch('logic.scripts.card_scripts._get_targets') as mock_targets, \
                patch('logic.scripts.card_scripts._resolve_value') as mock_resolve:
            mock_targets.return_value = [self.unit]
            mock_resolve.return_value = 15

            params = {"type": "sp"}
            restore_resource(self.ctx, params)

            self.assertEqual(self.unit.current_sp, 65)  # 50 + 15
            self.assertIn("🧠", self.ctx.log[0])

    def test_restore_sp_drain(self):
        """Тест: Урон по SP."""
        with patch('logic.scripts.card_scripts._check_conditions', return_value=True), \
                patch('logic.scripts.card_scripts._get_targets') as mock_targets, \
                patch('logic.scripts.card_scripts._resolve_value') as mock_resolve:
            mock_targets.return_value = [self.unit]
            mock_resolve.return_value = -10

            # Шпионим за методом юнита
            self.unit.take_sanity_damage = MagicMock()

            params = {"type": "sp"}
            restore_resource(self.ctx, params)

            self.unit.take_sanity_damage.assert_called_with(10)
            self.assertIn("🤯", self.ctx.log[0])

    def test_restore_stagger(self):
        """Тест: Восстановление Stagger."""
        with patch('logic.scripts.card_scripts._check_conditions', return_value=True), \
                patch('logic.scripts.card_scripts._get_targets') as mock_targets, \
                patch('logic.scripts.card_scripts._resolve_value') as mock_resolve:
            mock_targets.return_value = [self.unit]
            mock_resolve.return_value = 25

            params = {"type": "stagger"}
            restore_resource(self.ctx, params)

            self.assertEqual(self.unit.current_stagger, 45)  # 20 + 25
            self.assertIn("🛡️", self.ctx.log[0])


if __name__ == '__main__':
    unittest.main()