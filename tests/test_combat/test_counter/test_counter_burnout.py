import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Добавляем путь к корню проекта
sys.path.append(os.getcwd())

from core.enums import DiceType
from tests.mocks import MockUnit, MockDice
from logic.battle_flow.onesided.onesided import process_onesided


class TestCounterBurnout(unittest.TestCase):

    @patch('logic.battle_flow.onesided.onesided.resolve_unopposed_hit')
    @patch('logic.battle_flow.onesided.onesided.fetch_next_counter')
    @patch('logic.battle_flow.onesided.onesided.setup_onesided_parameters')
    def test_counter_die_is_skipped(self, mock_setup, mock_fetch, mock_resolve_hit):
        """
        Проверяем, что кубик с флагом is_counter пропускается в фазе One-Sided,
        если у врага нет активной защиты.
        """
        # 1. Mocks Setup
        # Параметры боя (стандартные)
        mock_setup.return_value = {
            "adv_atk": False,
            "adv_def": False,
            "destroy_def": False,
            "defender_breaks_attacker": False,
            "on_use_logs": []
        }
        # У защитника НЕТ контр-кубиков (иначе был бы Clash)
        mock_fetch.return_value = None

        # Результат удара (для обычных кубиков)
        mock_resolve_hit.return_value = {
            "val_atk": 10,
            "outcome": "Hit",
            "details": []
        }

        engine = MagicMock()
        attacker = MockUnit("Zafiel")
        defender = MockUnit("Rat")

        # 2. Подготовка карт и кубиков
        # Контр-кубик (должен сгореть)
        counter_die = MockDice(DiceType.SLASH)
        counter_die.is_counter = True

        # Обычный кубик (должен ударить)
        normal_die = MockDice(DiceType.BLUNT)
        normal_die.is_counter = False

        # Карта атакующего
        card = MagicMock()
        card.dice_list = [counter_die, normal_die]
        card.name = "Test Card"
        attacker.current_card = card

        defender.current_card = MagicMock()  # Карта защитника не важна

        # 3. ЗАПУСК
        report = process_onesided(engine, attacker, defender, "R1", 5, 3)

        # 4. ПРОВЕРКИ

        # Проверяем, что в отчете только 1 действие (от normal_die)
        # Если бы counter_die сработал, было бы 2.
        self.assertEqual(len(report), 1, "Report should contain only 1 entry (Normal Die)")

        entry = report[0]
        self.assertEqual(entry["left"]["dice"], "BLUNT", "The processed die should be the Normal one")

        # Проверяем, что resolve_unopposed_hit был вызван ровно 1 раз (для normal_die)
        mock_resolve_hit.assert_called_once()

        # Проверяем аргументы вызова (убеждаемся, что вызвано именно с normal_die)
        args, _ = mock_resolve_hit.call_args
        # args[3] это die в сигнатуре resolve_unopposed_hit(engine, source, target, die, ...)
        processed_die = args[3]
        self.assertEqual(processed_die, normal_die)
        self.assertFalse(getattr(processed_die, "is_counter", False))

        print("✅ Test Passed: Counter Die was successfully ignored in One-Sided phase.")

    @patch('logic.battle_flow.onesided.onesided.resolve_unopposed_hit')
    @patch('logic.battle_flow.onesided.onesided.fetch_next_counter')
    @patch('logic.battle_flow.onesided.onesided.setup_onesided_parameters')
    def test_recycled_counter_die_is_skipped(self, mock_setup, mock_fetch, mock_resolve_hit):
        """
        Проверяем, что кубик с флагом recycled (вернувшийся с клэша) тоже пропускается.
        """
        mock_setup.return_value = {
            "adv_atk": False, "adv_def": False, "destroy_def": False,
            "defender_breaks_attacker": False, "on_use_logs": []
        }
        mock_fetch.return_value = None

        engine = MagicMock()
        attacker = MockUnit("Zafiel")
        defender = MockUnit("Rat")

        # Кубик, который вернулся после победы (recycled)
        recycled_die = MockDice(DiceType.EVADE)  # Тип не важен
        recycled_die.recycled = True
        recycled_die.is_counter = False  # Даже если флаг is_counter снят, recycled говорит сам за себя

        card = MagicMock()
        card.dice_list = [recycled_die]
        attacker.current_card = card
        defender.current_card = MagicMock()

        # ЗАПУСК
        report = process_onesided(engine, attacker, defender, "R1", 5, 3)

        # ПРОВЕРКИ
        self.assertEqual(len(report), 0, "Recycled die should be skipped")
        mock_resolve_hit.assert_not_called()
        print("✅ Test Passed: Recycled Die was ignored.")


if __name__ == '__main__':
    unittest.main()