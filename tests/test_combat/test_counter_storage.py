import unittest
import sys
import os

# Путь к корню проекта
sys.path.append(os.getcwd())

from core.enums import DiceType
from tests.mocks import MockUnit, MockDice
from logic.battle_flow.clash.clash_utils import store_remaining_dice
from logic.battle_flow.onesided.onesided_utils import fetch_next_counter


class TestCounterStorage(unittest.TestCase):
    def setUp(self):
        self.unit = MockUnit(name="Afelia")
        # Инициализируем необходимые списки, если MockUnit их не создал
        if not hasattr(self.unit, 'counter_dice'):
            self.unit.counter_dice = []
        if not hasattr(self.unit, 'stored_dice'):
            self.unit.stored_dice = []

    def test_counter_dice_persistence(self):
        """
        Проверка: все контр-кубики (не только EVADE) должны сохраняться в stored_dice.
        """
        # 1. Создаем набор контр-кубиков разных типов
        counter_slash = MockDice(DiceType.SLASH)
        counter_slash.is_counter = True

        counter_block = MockDice(DiceType.BLOCK)
        counter_block.is_counter = True

        normal_atk = MockDice(DiceType.SLASH)
        normal_atk.is_counter = False

        # Очередь кубиков: [Counter Slash, Counter Block, Normal Attack]
        queue = [counter_slash, counter_block, normal_atk]

        # Симулируем ситуацию: клэш прервался на первом же кубике (idx=0)
        report = []
        store_remaining_dice(self.unit, queue, idx=0, active_cnt_tuple=None, log_list=report)

        # 2. ПРОВЕРКИ СОХРАНЕНИЯ
        # В stored_dice должны попасть только 2 контр-кубика. Обычная атака должна исчезнуть.
        self.assertEqual(len(self.unit.stored_dice), 2, "Должно быть сохранено ровно 2 контр-кубика")

        types_in_storage = [d.dtype for d in self.unit.stored_dice]
        self.assertIn(DiceType.SLASH, types_in_storage)
        self.assertIn(DiceType.BLOCK, types_in_storage)
        self.assertNotIn(normal_atk, self.unit.stored_dice)

        # 3. ПРОВЕРКА ИЗВЛЕЧЕНИЯ (One-Sided Phase)
        # Проверяем, что fetch_next_counter видит эти кубики.
        first_retrieved = fetch_next_counter(self.unit)
        self.assertEqual(first_retrieved.dtype, DiceType.SLASH)
        self.assertTrue(first_retrieved.is_counter)

        second_retrieved = fetch_next_counter(self.unit)
        self.assertEqual(second_retrieved.dtype, DiceType.BLOCK)

        # После извлечения хранилище должно быть пустым
        self.assertEqual(len(self.unit.stored_dice), 0)

    def test_active_recycled_counter_storage(self):
        """
        Проверка: если контр-кубик выиграл и находится в active_counter, он тоже должен сохраниться.
        """
        recycled_counter = MockDice(DiceType.PIERCE)
        recycled_counter.is_counter = True

        # active_cnt_tuple = (die, is_counter_source)
        active_tuple = (recycled_counter, True)

        report = []
        store_remaining_dice(self.unit, queue=[], idx=0, active_cnt_tuple=active_tuple, log_list=report)

        self.assertEqual(len(self.unit.stored_dice), 1)
        self.assertEqual(self.unit.stored_dice[0].dtype, DiceType.PIERCE)
        print("✅ Active Recycled Counter saved successfully")


if __name__ == '__main__':
    unittest.main()