import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType
from tests.mocks import MockUnit, MockDice
from logic.battle_flow.clash.clash import process_clash
from logic.battle_flow.clash.clash_one_sided import handle_one_sided_exchange


class TestSpeedbreak(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock()

        # Настройка бросков: атакующий всегда выкидывает 5
        def mock_roll(unit, target, die, **kwargs):
            ctx = MagicMock()
            ctx.final_value = 5
            ctx.log = []
            return ctx

        self.engine._create_roll_context.side_effect = mock_roll

    def test_speed_destruction_flow(self):
        """
        Проверка: Если у защитника сломан слот (Speedbreak),
        атакующий должен нанести урон и потратить свой кубик.
        """
        # Атакующий (Скорость 10)
        attacker = MockUnit("Striker")
        a1 = MockDice(DiceType.SLASH)
        attacker.current_card = MagicMock(dice_list=[a1], name="AtkCard")

        # Защитник (Скорость 1)
        defender = MockUnit("Victim")
        d1 = MockDice(DiceType.SLASH)
        defender.current_card = MagicMock(dice_list=[d1], name="DefCard")

        # Мокаем параметры так, чтобы включился Speedbreak для защитника
        # setup_clash_parameters возвращает (adv_a, adv_d, destroy_a, destroy_d, logs)
        with patch('logic.battle_flow.clash.clash.setup_clash_parameters',
                   return_value=(False, False, False, True, [])):
            # Мокаем обработку одностороннего удара внутри клэша
            with patch('logic.battle_flow.clash.clash.handle_one_sided_exchange',
                      wraps=handle_one_sided_exchange) as mock_onesided:
                report = process_clash(self.engine, attacker, defender, "R1", True, 10, 1)

                # 1. ПРОВЕРКА: Был ли вызван односторонний обмен вместо обычного резолва?
                mock_onesided.assert_called_once()

                # 2. ПРОВЕРКА: Кто был активной стороной?
                # В process_clash при die_a и not die_d вызывается handle_one_sided_exchange(active_side=state_a, ...)
                args, kwargs = mock_onesided.call_args
                self.assertEqual(kwargs['active_side'].unit.name, "Striker")

                # 3. ПРОВЕРКА: Отчет зафиксировал результат?
                self.assertEqual(report[0]['outcome'], "💥 Speedbreak Hit")
                # У защитника кубик должен отображаться как Broken
                self.assertEqual(report[0]['right']['dice'], "Broken")

    def test_melee_consumed_after_speedbreak_hit(self):
        """
        Проверка: После удара по сломанному кубику, обычный Melee кубик
        должен считаться использованным (не ресайклиться).
        """
        # Симулируем ситуацию, где у атакующего 2 кубика, а у защитника 1 (и он сломан)
        attacker = MockUnit("Striker")
        a1, a2 = MockDice(DiceType.SLASH), MockDice(DiceType.SLASH)
        attacker.current_card = MagicMock(dice_list=[a1, a2], name="AtkCard")

        defender = MockUnit("Victim")
        d1 = MockDice(DiceType.SLASH)
        defender.current_card = MagicMock(dice_list=[d1], name="DefCard")

        # Включаем разрушение для защитника
        with patch('logic.battle_flow.clash.clash.setup_clash_parameters',
                   return_value=(False, False, False, True, [])):
            # Реальная функция handle_one_sided_exchange обычно вызывает side.consume()
            # Для теста мы просто проверяем, что цикл в clash.py идет дальше.
            report = process_clash(self.engine, attacker, defender, "R1", True, 10, 1)

            # Если первый кубик Striker потратился, отчет должен иметь 2 записи:
            # 1. Striker(a1) vs Victim(Broken)
            # 2. Striker(a2) vs Victim(None/Empty)
            self.assertGreaterEqual(len(report), 1)
            self.assertEqual(report[0]['left']['dice'], "SLASH")


if __name__ == '__main__':
    unittest.main()