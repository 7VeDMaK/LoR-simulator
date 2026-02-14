import unittest
import sys
import os
from unittest.mock import MagicMock, patch

from logic.scripts.card_dice import add_preset_dice

sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType
# Импортируем НОВЫЕ скрипты
from logic.scripts.statuses import consume_status_apply


class TestAxisRefactored(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnit(name="Axis", max_hp=100)
        self.target = MockUnit(name="Enemy", max_hp=100)
        self.ctx = MockContext(self.unit, target=self.target)
        self.ctx.log = []

    def test_consume_status_logic(self):
        """Проверяем механику Plot Armor (снятие WinCon -> дебафф)."""
        # Даем врагу статус
        self.target.add_status("win_condition", 5)

        params = {
            "consume_status": "win_condition",
            "apply_status": "fragile",
            "apply_amount": 2,
            "apply_target": "target"
        }

        # Патчим утилиты внутри скрипта
        with patch('logic.scripts.statuses._get_targets', return_value=[self.target]):
            consume_status_apply(self.ctx, params)

            # Статус должен уменьшиться на 1 (5 -> 4)
            self.assertEqual(self.target.get_status("win_condition"), 4)
            # Дебафф наложен
            self.assertEqual(self.target.get_status("fragile"), 2)

    def test_add_preset_dice(self):
        """Проверяем механику Мелких Неудач (добавление кубиков)."""
        card = MagicMock()
        card.dice_list = []
        self.unit.current_card = card

        params = {
            "dice": [
                {"min": 5, "max": 10, "type": "Slash"},
                {"min": 2, "max": 4, "type": "Block"}
            ]
        }

        add_preset_dice(self.ctx, params)

        self.assertEqual(len(card.dice_list), 2)
        self.assertEqual(card.dice_list[0].dtype, DiceType.SLASH)
        self.assertEqual(card.dice_list[1].dtype, DiceType.BLOCK)

    def test_unity_share_dice(self):
        """Проверяем механику Unity (раздача кубиков)."""
        # Карта-источник
        card_source = MagicMock()
        d1 = MockDice(DiceType.PIERCE)
        card_source.dice_list = [d1]
        self.unit.current_card = card_source

        # Карты в руке
        card_unity = MagicMock()
        card_unity.flags = ["unity"]
        card_unity.dice_list = []

        card_other = MagicMock()
        card_other.flags = []  # Нет флага
        card_other.dice_list = []

        self.unit.hand = [card_source, card_unity, card_other]

        share_dice_with_hand(self.ctx, {"flag": "unity"})

        # Карте с флагом кубик пришел
        self.assertEqual(len(card_unity.dice_list), 1)
        self.assertEqual(card_unity.dice_list[0].dtype, DiceType.PIERCE)

        # Карте без флага - нет
        self.assertEqual(len(card_other.dice_list), 0)


if __name__ == '__main__':
    unittest.main()