import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Добавляем корень проекта
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType
from logic.scripts.card_damage import (
    deal_effect_damage, nullify_hp_damage,
    self_harm_percent, add_hp_damage
)


class TestCardDamage(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnit(name="Attacker", max_hp=100)
        self.target = MockUnit(name="Defender", max_hp=100)

        # Настраиваем параметры для тестов Stagger и SP
        self.target.current_stagger = 50
        self.target.max_stagger = 50
        self.target.current_sp = 100

        self.dice = MockDice(DiceType.SLASH)
        self.ctx = MockContext(self.unit, target=self.target, dice=self.dice)
        self.ctx.final_value = 10  # Фиктивный результат броска для тестов

    # ==========================================
    # 1. deal_effect_damage (Основной скрипт)
    # ==========================================

    @patch('logic.scripts.card_damage._check_conditions', return_value=True)
    @patch('logic.scripts.card_damage._get_targets')
    @patch('logic.scripts.card_damage._resolve_value')
    def test_deal_hp_damage_flat(self, mock_resolve, mock_targets, mock_cond):
        """Тест: Нанесение фиксированного урона HP."""
        mock_targets.return_value = [self.target]
        mock_resolve.return_value = 15  # Утилита вернула 15 урона

        params = {"type": "hp", "value": 15}
        deal_effect_damage(self.ctx, params)

        # 100 - 15 = 85
        self.assertEqual(self.target.current_hp, 85)
        self.assertTrue(any("💔" in msg for msg in self.ctx.log))

    @patch('logic.scripts.card_damage._check_conditions', return_value=True)
    @patch('logic.scripts.card_damage._get_targets')
    def test_deal_stagger_damage_roll(self, mock_targets, mock_cond):
        """Тест: Урон по Stagger зависит от броска (stat='roll')."""
        mock_targets.return_value = [self.target]

        # Формула: base + (roll * factor) -> 2 + (10 * 0.5) = 7
        params = {"type": "stagger", "stat": "roll", "base": 2, "factor": 0.5}

        deal_effect_damage(self.ctx, params)

        # 50 - 7 = 43
        self.assertEqual(self.target.current_stagger, 43)
        self.assertTrue(any("😵" in msg for msg in self.ctx.log))

    @patch('logic.scripts.card_damage._check_conditions', return_value=True)
    @patch('logic.scripts.card_damage._get_targets')
    @patch('logic.scripts.card_damage._resolve_value', return_value=20)
    def test_deal_sp_damage_with_protection(self, mock_resolve, mock_targets, mock_cond):
        """Тест: Урон по SP и работа Mental Protection (сырная защита)."""
        mock_targets.return_value = [self.target]

        # Сценарий 1: Без защиты
        deal_effect_damage(self.ctx, {"type": "sp"})
        self.assertEqual(self.target.current_sp, 80)  # 100 - 20

        # Сценарий 2: С защитой (2 стака -> 50% резист)
        self.target.current_sp = 100  # Сброс
        self.target.add_status("mental_protection", 2)

        deal_effect_damage(self.ctx, {"type": "sp"})

        # Урон 20. Резист 50% = 10. Итог: -10 SP.
        self.assertEqual(self.target.current_sp, 90)
        self.assertTrue(any("Blocked" in msg for msg in self.ctx.log))

    # ==========================================
    # 2. nullify_hp_damage
    # ==========================================

    def test_nullify_hp_damage(self):
        """Тест: Обнуление множителя урона."""
        self.ctx.damage_multiplier = 1.0
        nullify_hp_damage(self.ctx, {})
        self.assertEqual(self.ctx.damage_multiplier, 0.0)

    # ==========================================
    # 3. self_harm_percent
    # ==========================================

    @patch('logic.scripts.card_damage._check_conditions', return_value=True)
    def test_self_harm_percent(self, mock_cond):
        """Тест: Урон по себе в % от Макс ХП."""
        self.unit.current_hp = 100
        self.unit.max_hp = 100

        # 10% от 100 = 10
        params = {"percent": 0.1}
        self_harm_percent(self.ctx, params)

        self.assertEqual(self.unit.current_hp, 90)
        self.assertTrue(any("Self Harm" in msg for msg in self.ctx.log))

    # ==========================================
    # 4. add_hp_damage (Decay)
    # ==========================================

    @patch('logic.scripts.card_damage._check_conditions', return_value=True)
    def test_add_hp_damage(self, mock_cond):
        """Тест: Доп. урон по цели в % от её Макс ХП."""
        self.target.current_hp = 80
        self.target.max_hp = 200

        # 20% от 200 = 40 урона
        params = {"percent": 0.2}
        add_hp_damage(self.ctx, params)

        # 80 - 40 = 40
        self.assertEqual(self.target.current_hp, 40)
        self.assertTrue(any("Decay" in msg for msg in self.ctx.log))


if __name__ == '__main__':
    unittest.main()