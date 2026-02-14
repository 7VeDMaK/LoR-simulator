import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType
from tests.mocks import MockUnit, MockDice
from logic.battle_flow.clash.clash import process_clash
from logic.battle_flow.clash.clash_one_sided import handle_one_sided_exchange


class TestSpeedbreakScenarios(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock()

        # Стандартный бросок для тестов
        def mock_roll(unit, target, die, **kwargs):
            ctx = MagicMock()
            ctx.final_value = 7
            ctx.log = []
            return ctx

        self.engine._create_roll_context.side_effect = mock_roll

    def test_speedbreak_melee_consumption(self):
        """
        Сценарий 1: Melee атака по сломанному кубику.
        Ожидание: Атакующий наносит удар, кубик тратится (idx увеличивается).
        """
        attacker = MockUnit("Striker")
        a1 = MockDice(DiceType.SLASH)
        attacker.current_card = MagicMock(dice_list=[a1], name="AtkCard")

        defender = MockUnit("Victim")
        d1 = MockDice(DiceType.BLOCK)
        defender.current_card = MagicMock(dice_list=[d1], name="DefCard")

        # Настраиваем Speedbreak: у защитника destroy_d = True
        # setup_clash_parameters возвращает (adv_a, adv_d, destroy_a, destroy_d, logs)
        with patch('logic.battle_flow.clash.clash.setup_clash_parameters',
                   return_value=(False, False, False, True, [])):
            with patch('logic.battle_flow.clash.clash.handle_one_sided_exchange',
                   wraps=handle_one_sided_exchange) as mock_exchange:
                report = process_clash(self.engine, attacker, defender, "R1", True, 10, 2)

                # Проверяем, что удар был нанесен
                mock_exchange.assert_called_once()
                # Проверяем, что клэш завершился (кубик потрачен, итерация закончилась)
                self.assertEqual(len(report), 1)
                print("✅ Melee consumed after speedbreak hit.")

    def test_multiple_dice_vs_speedbreak(self):
        """
        У Striker 2 кубика. У Victim 1 сломанный кубик.
        Ожидание: 2 удара в отчете. 1-й по 'Broken', 2-й по '-' (пусто).
        """
        attacker = MockUnit("Striker")
        a1, a2 = MockDice(DiceType.SLASH), MockDice(DiceType.SLASH)
        attacker.current_card = MagicMock(dice_list=[a1, a2], name="Atk")

        defender = MockUnit("Victim")
        d1 = MockDice(DiceType.SLASH)
        defender.current_card = MagicMock(dice_list=[d1], name="Def")

        # Включаем Speedbreak для защитника
        with patch('logic.battle_flow.clash.clash.setup_clash_parameters',
                   return_value=(False, False, False, True, [])):
            report = process_clash(self.engine, attacker, defender, "R1", True, 10, 2)

            # ПРОВЕРКА: Должно быть 2 взаимодействия
            self.assertEqual(len(report), 2, f"Expected 2 hits for 2 dice, got {len(report)}")

            # 1-й кубик ударил по сломанному
            self.assertEqual(report[0]['right']['dice'], "Broken")
            # 2-й кубик ударил в пустоту (так как d1 уже был поглощен)
            self.assertEqual(report[1]['right']['dice'], "-")

            print("✅ Speedbreak correctly consumes slot and continues to void.")

    def test_counter_preserved_on_speedbreak_void(self):
        """
        Сценарий 3: Контр-кубик против сломанного слота.
        Ожидание: Контр-кубик НЕ атакует в пустоту/сломанный слот и сохраняется.
        """
        attacker = MockUnit("CounterUser")
        c1 = MockDice(DiceType.SLASH)
        c1.is_counter = True
        attacker.current_card = MagicMock(dice_list=[c1], name="CounterCard")

        defender = MockUnit("Victim")
        d1 = MockDice(DiceType.SLASH)
        defender.current_card = MagicMock(dice_list=[d1], name="DefCard")

        with patch('logic.battle_flow.clash.clash.setup_clash_parameters',
                   return_value=(False, False, False, True, [])):
            report = process_clash(self.engine, attacker, defender, "R1", True, 10, 2)

            # В clash.py есть проверка: if getattr(die_a, "is_counter", False) -> break
            # Значит в отчете не должно быть 'clash' записи с уроном, а должен быть 'Saved'
            # (зависит от реализации store_remaining)

            # Проверяем лог (через отчет или сохраненные кубики)
            self.assertEqual(len(attacker.stored_dice), 1)
            self.assertIs(attacker.stored_dice[0], c1)
            print("✅ Counter die correctly preserved instead of hitting a Broken slot.")


if __name__ == '__main__':
    unittest.main()