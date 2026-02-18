import unittest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.getcwd())

from core.enums import DiceType
from tests.mocks import MockUnit, MockDice
from logic.battle_flow.onesided.onesided import process_onesided


class TestOneSidedCounters(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock()

        # Атакующий (2 атакующих кубика)
        self.attacker = MockUnit("Attacker")
        self.a1 = MockDice(DiceType.SLASH)
        self.a2 = MockDice(DiceType.PIERCE)
        self.attacker.current_card = MagicMock()
        self.attacker.current_card.dice_list = [self.a1, self.a2]
        self.attacker.current_card.name = "Attack Card"

        # Защитник (Будем настраивать в тестах)
        self.defender = MockUnit("Defender")
        self.defender.current_card = MagicMock()
        self.defender.current_card.dice_list = []  # Нет обычных кубиков
        self.defender.current_card.name = "Idle"

        # Инициализируем списки, которых может не быть в MockUnit по умолчанию
        self.defender.stored_dice = []
        self.defender.counter_dice = []

    def test_single_counter_activation(self):
        """
        Тест 1: Базовая активация. Атака vs Контр-кубик.
        Должен произойти 'clash', а не 'onesided'.
        """
        # Даем защитнику 1 контр-кубик
        c1 = MockDice(DiceType.SLASH)
        c1.is_counter = True
        self.defender.counter_dice = [c1]

        # Мокаем setup, чтобы исключить Speed Break
        with patch('logic.battle_flow.onesided.onesided.setup_onesided_parameters',
                   return_value={
                       "adv_atk": False, "adv_def": False,
                       "destroy_def": False, "defender_breaks_attacker": False,
                       "on_use_logs": []
                   }):
            # Мокаем резолв клэша. Допустим, контр-кубик выиграл и остался.
            with patch('logic.battle_flow.onesided.onesided.resolve_counter_clash') as mock_resolve:
                mock_resolve.return_value = {
                    "outcome": "Counter Win",
                    "val_atk": 5, "val_cnt": 10,
                    "counter_spent": False,  # [ВАЖНО] Кубик выжил
                    "details": []
                }

                report = process_onesided(self.engine, self.attacker, self.defender, "Test", 5, 5)

                # Проверки
                self.assertEqual(len(report), 2)  # 2 атаки

                # Первая атака должна быть типа 'clash' (Counter)
                self.assertEqual(report[0]['type'], 'clash')
                self.assertIn("(Counter)", report[0]['round'])

                # Убеждаемся, что вызвалась функция резолва
                mock_resolve.assert_called()

    def test_counter_recycle_mechanic(self):
        """
        Тест 2: Механика Recycle.
        Один контр-кубик побеждает первую атаку (не тратится) и перехватывает вторую.
        """
        c1 = MockDice(DiceType.BLOCK)
        c1.is_counter = True
        self.defender.counter_dice = [c1]  # Всего ОДИН кубик

        with patch('logic.battle_flow.onesided.onesided.setup_onesided_parameters',
                   return_value={"adv_atk": False, "adv_def": False, "destroy_def": False,
                                 "defender_breaks_attacker": False, "on_use_logs": []}):
            with patch('logic.battle_flow.onesided.onesided.resolve_counter_clash') as mock_resolve:
                # Настраиваем так, что кубик НЕ тратится оба раза
                mock_resolve.return_value = {
                    "outcome": "Counter Block", "val_atk": 4, "val_cnt": 8,
                    "counter_spent": False, "details": []
                }

                report = process_onesided(self.engine, self.attacker, self.defender, "Test", 5, 5)

                # Должно быть 2 отчета, и оба - Clash с одним и тем же типом кубика
                self.assertEqual(report[0]['type'], 'clash')
                self.assertEqual(report[1]['type'], 'clash')

                # Проверяем, что во втором раунде защитник все еще имеет кубик (а не Empty/Hurt)
                self.assertNotEqual(report[1]['right']['dice'], "None")
                print("✅ Counter Dice successfully recycled for second attack.")

    def test_counter_loss_and_depletion(self):
        """
        Тест 3: Проигрыш контр-кубика.
        Первый контр-кубик проигрывает (spent=True). Вторая атака должна пройти чисто (Hit), так как кубиков больше нет.
        """
        c1 = MockDice(DiceType.SLASH)
        self.defender.counter_dice = [c1]

        with patch('logic.battle_flow.onesided.onesided.setup_onesided_parameters',
                   return_value={"adv_atk": False, "adv_def": False, "destroy_def": False,
                                 "defender_breaks_attacker": False, "on_use_logs": []}):
            with patch('logic.battle_flow.onesided.onesided.resolve_counter_clash') as mock_resolve:
                # Первый раз кубик тратится
                mock_resolve.side_effect = [
                    {"outcome": "Counter Lose", "val_atk": 10, "val_cnt": 2, "counter_spent": True, "details": []}
                ]

                # Мокаем чистое попадание (unopposed), которое должно произойти во 2-й раз
                with patch('logic.battle_flow.onesided.onesided.resolve_unopposed_hit',
                           return_value={"val_atk": 5, "outcome": "Direct Hit", "details": []}):
                    report = process_onesided(self.engine, self.attacker, self.defender, "Test", 5, 5)

                    # 1 раунд: Clash (Counter)
                    self.assertEqual(report[0]['type'], 'clash')
                    self.assertIn("(Counter)", report[0]['round'])

                    # 2 раунд: OneSided (Hit) - так как контр-кубик кончился
                    self.assertEqual(report[1]['type'], 'onesided')
                    self.assertIn("(Hit)", report[1]['round'])
                    print("✅ Counter Dice spent correctly, allowing subsequent direct hit.")

    def test_stored_priority_over_generated(self):
        """
        Тест 4: Приоритет Stored Dice.
        Если есть Stored (с прошлого клэша) и Counter (с пассивки), сначала берется Stored.
        """
        stored_die = MockDice(DiceType.EVADE)  # Stored
        passive_die = MockDice(DiceType.SLASH)  # Counter Passive

        self.defender.stored_dice = [stored_die]
        self.defender.counter_dice = [passive_die]

        with patch('logic.battle_flow.onesided.onesided.setup_onesided_parameters',
                   return_value={"adv_atk": False, "adv_def": False, "destroy_def": False,
                                 "defender_breaks_attacker": False, "on_use_logs": []}):
            with patch('logic.battle_flow.onesided.onesided.resolve_counter_clash') as mock_resolve:
                mock_resolve.return_value = {"outcome": "Test", "val_atk": 0, "val_cnt": 0, "counter_spent": True,
                                             "details": []}

                process_onesided(self.engine, self.attacker, self.defender, "Test", 5, 5)

                # Проверяем аргументы первого вызова resolve_counter_clash
                # Аргумент 4 (индекс 3, если считать self) или 5-й по счету в вызове - это active_counter_die
                args, _ = mock_resolve.call_args_list[0]
                used_die = args[4]

                self.assertEqual(used_die.dtype, DiceType.EVADE)
                self.assertIs(used_die, stored_die)
                print("✅ Stored Dice took priority over Passive Counter Dice.")

    def test_missing_attacker_card_is_skipped(self):
        """
        Тест 5: Если у атакующего нет current_card, process_onesided должен безопасно завершиться.
        """
        self.attacker.current_card = None

        report = process_onesided(self.engine, self.attacker, self.defender, "Test", 5, 5)

        self.assertEqual(report, [])
        self.engine._process_card_self_scripts.assert_not_called()


if __name__ == '__main__':
    unittest.main()