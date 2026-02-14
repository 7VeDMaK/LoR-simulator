import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType
from logic.battle_flow.clash.clash import process_clash


# === MOCKS ===
class MockDice:
    def __init__(self, dtype, val):
        self.dtype = dtype
        self.min_val = val
        self.max_val = val
        self.is_counter = False


class MockUnit:
    def __init__(self, name):
        self.name = name
        self.active_slots = []
        self.current_card = None
        self.stored_dice = []  # Сюда сохраняются кубики (defensive)

        # [FIX] Добавлены атрибуты для поддержки логики контр-кубиков
        self.counter_dice = []
        self.passive_counter_queue = []
        self.current_die = None  # Для отслеживания активного кубика

    def is_dead(self): return False

    def is_staggered(self): return False

    def restore_stagger(self, val): return val


class TestDefensivePreservation(unittest.TestCase):

    def setUp(self):
        self.engine = MagicMock()

        # Настройка роллов: возвращаем min_val кубика
        def mock_roll(u, t, die, **kwargs):
            val = die.min_val
            ctx = MagicMock()
            ctx.final_value = val
            ctx.log = []
            ctx.source = u  # Важно для логгера
            return ctx

        self.engine._create_roll_context.side_effect = mock_roll

        # Мок нанесения урона
        self.engine._resolve_clash_interaction.return_value = 5
        self.engine._handle_clash_win = MagicMock()
        self.engine._handle_clash_lose = MagicMock()
        self.engine._handle_clash_draw = MagicMock()

    def test_evade_recycle_on_win(self):
        """
        Проверка: Evade (10) vs 2x Attack (5).
        Ожидание: Evade выигрывает первый раз, РЕСАЙКЛИТСЯ, и выигрывает второй раз.
        """
        attacker = MockUnit("Attacker")
        defender = MockUnit("Defender")

        # Атакующий: 2 слабых удара (5)
        atk_card = MagicMock()
        atk_card.dice_list = [MockDice(DiceType.SLASH, 5), MockDice(DiceType.SLASH, 5)]
        attacker.current_card = atk_card

        # Защитник: 1 сильный уворот (10)
        def_card = MagicMock()
        def_card.dice_list = [MockDice(DiceType.EVADE, 10)]
        defender.current_card = def_card

        # Запускаем клэш
        # Нужно замокать handle_one_sided_exchange, чтобы он не падал, если вдруг вызовется
        with patch('logic.battle_flow.clash.clash.handle_one_sided_exchange', return_value="Hit"):
            report = process_clash(self.engine, attacker, defender, "R1", True, 5, 5)

        self.assertEqual(len(report), 2, "Должно быть 2 столкновения (Evade должен выжить).")

        # Clash 1: 5 vs 10 (Evade) -> Evade Wins & Recycles
        self.assertIn("Evades!", report[0]['outcome'])
        self.assertTrue(report[0].get('recycle_d', False) or "Recycle" in report[0]['outcome'])

        # Clash 2: 5 vs 10 (Evade) -> Evade Wins again
        self.assertIn("Evades!", report[1]['outcome'])

        # Проверяем, что во втором раунде использовался тот же тип кубика
        self.assertEqual(report[1]['right']['dice'], "EVADE")

        print("✅ Evade корректно сохранился (Recycled) после победы.")

    def test_block_consumed_on_win(self):
        """
        Проверка: Block (10) vs 2x Attack (5).
        Ожидание: Block выигрывает первый раз, но ИСЧЕЗАЕТ.
        Второй удар бьет в пустоту.
        """
        attacker = MockUnit("Attacker")
        defender = MockUnit("Defender")

        # Атакующий: 2 слабых удара
        atk_card = MagicMock()
        atk_card.dice_list = [MockDice(DiceType.SLASH, 5), MockDice(DiceType.SLASH, 5)]
        attacker.current_card = atk_card

        # Защитник: 1 сильный блок
        def_card = MagicMock()
        def_card.dice_list = [MockDice(DiceType.BLOCK, 10)]
        defender.current_card = def_card

        # Мокаем обработку удара в пустоту
        with patch('logic.battle_flow.clash.clash.handle_one_sided_exchange',
                   return_value="Direct Hit") as mock_onesided:
            report = process_clash(self.engine, attacker, defender, "R1", True, 5, 5)

            # Если 2-й удар был one-sided, то в отчете может быть 1 запись clash и 1 onesided,
            # либо 2 записи clash где у защитника "None".
            # В вашей реализации clash.py вызывает handle_one_sided_exchange и пишет результат в outcome.

            self.assertEqual(len(report), 2)

            # Clash 1: 5 vs 10 (Block) -> Blocked
            self.assertIn("Blocked", report[0]['outcome'])

            # Clash 2: Вызов one_sided
            mock_onesided.assert_called()

            # Либо проверяем, что правый кубик "-" или "None"
            r_dice = report[1]['right']['dice']
            self.assertTrue(r_dice in ["-", "None", "Broken"],
                            f"Второй удар должен быть по пустому слоту. Got: {r_dice}")

        print("✅ Block корректно потратился (Consumed) даже после победы.")

    def test_unused_dice_storage(self):
        """
        Проверка: У защитника 3 кубика. Атакующий бьет 1 раз.
        Ожидание: 1-й кубик тратится на клэш. 2-й и 3-й сохраняются в stored_dice.
        """
        attacker = MockUnit("Attacker")
        defender = MockUnit("Defender")

        # 1 Атака
        attacker.current_card = MagicMock(dice_list=[MockDice(DiceType.SLASH, 5)])

        # 3 Защиты
        d1 = MockDice(DiceType.BLOCK, 5)
        d2 = MockDice(DiceType.EVADE, 5)
        d3 = MockDice(DiceType.BLOCK, 5)
        defender.current_card = MagicMock(dice_list=[d1, d2, d3])

        # Мокаем store_remaining_dice
        with patch('logic.battle_flow.clash.clash_state.store_remaining_dice') as mock_store:
            process_clash(self.engine, attacker, defender, "R1", True, 5, 5)

            # Ищем вызов для defender
            found = False
            for call in mock_store.call_args_list:
                args, _ = call
                if args[0] == defender:
                    found = True
                    queue = args[1]
                    idx = args[2]
                    # Очередь [d1, d2, d3], idx=1 (d1 использован) -> сохранятся d2, d3
                    self.assertEqual(idx, 1, "Индекс должен указывать на 2-й элемент (индекс 1)")
                    self.assertEqual(queue[1], d2)
                    self.assertEqual(queue[2], d3)

            self.assertTrue(found, "Функция сохранения кубиков защитника должна быть вызвана.")

        print("✅ Оставшиеся кубики корректно отправлены на сохранение.")

    def test_counter_block_recycle(self):
        """
        Проверка: Counter Block (10) vs Attack (5).
        Ожидание: Так как это COUNTER, он должен ресайклиться при победе.
        """
        attacker = MockUnit("Attacker")
        defender = MockUnit("Defender")

        atk_card = MagicMock(dice_list=[MockDice(DiceType.SLASH, 5), MockDice(DiceType.SLASH, 5)])
        attacker.current_card = atk_card

        # Counter Block
        cnt_block = MockDice(DiceType.BLOCK, 10)
        cnt_block.is_counter = True  # [ВАЖНО] Флаг контр-кубика
        defender.current_card = MagicMock(dice_list=[cnt_block])

        # Нужно замокать handle_one_sided, на случай если тест упадет и перейдет в one-sided
        with patch('logic.battle_flow.clash.clash.handle_one_sided_exchange', return_value="Hit"):
            report = process_clash(self.engine, attacker, defender, "R1", True, 5, 5)

        self.assertEqual(len(report), 2, "Counter Block должен выдержать 2 удара.")

        # Clash 1
        self.assertIn("Blocked", report[0]['outcome'])
        # Clash 2 (тоже Blocked, а не One-Sided/Hit)
        self.assertIn("Blocked", report[1]['outcome'])

        # В деталях первого раунда должно быть упоминание о ресайкле
        logs_str = str(report[0]['details'])
        self.assertIn("Counter Recycled", logs_str)

        print("✅ Counter Block корректно ресайклится при победе.")


if __name__ == '__main__':
    unittest.main()