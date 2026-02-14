import unittest
from unittest.mock import MagicMock
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType, CardType
from logic.battle_flow.executor import execute_single_action
from logic.battle_flow.mass_attack import process_mass_attack
from logic.battle_flow.priorities import get_action_priority


# === MOCKS ===
class MockDice:
    def __init__(self, dtype):
        self.dtype = dtype
        self.min_val = 1
        self.max_val = 10
        self.current_value = 0


class MockUnit:
    def __init__(self, name):
        self.name = name
        self.active_slots = []
        self.current_card = None

    def is_dead(self): return False

    def is_staggered(self): return False


class TestMassSumVsSumValues(unittest.TestCase):

    def create_mass_sum_action(self, source, targets, speed, dice_vals):
        card = MagicMock()
        card.name = f"MassSum_{speed}"
        card.card_type = CardType.MASS_SUMMATION.value
        card.tier = 3
        card.id = f"id_{card.name}"

        card.dice_list = []
        for val in dice_vals:
            d = MockDice(DiceType.SLASH)
            d.min_val = val
            d.max_val = val
            card.dice_list.append(d)

        slot = {'card': card, 'speed': speed, 'destroy_on_speed': False, 'mass_defenses': {}}
        source.active_slots = [slot]
        source.current_card = card

        return {
            'label': card.name,
            'source': source,
            'source_idx': 0,
            'target_unit': targets[0],
            'target_slot_idx': 0,
            'card_type': "mass_summation",
            'slot_data': slot,
            'is_left': True,
            'opposing_team': targets
        }

    def test_values_are_summed_in_clash(self):
        """
        Проверка: Unit A [10, 10] vs Unit B [5, 5].
        Тип: Оба Mass Summation.
        Ожидание: Клэш 20 vs 10. (А не два клэша 10vs5).
        """
        unit_a = MockUnit("Unit_A")
        unit_b = MockUnit("Unit_B")

        # A: 10 + 10 = 20
        act_a = self.create_mass_sum_action(unit_a, [unit_b], 10, [10, 10])

        # B: 5 + 5 = 10
        # Мы просто даем ему эту карту в слот, чтобы он ей защищался
        act_b = self.create_mass_sum_action(unit_b, [unit_a], 1, [5, 5])

        engine = MagicMock()
        engine._process_card_self_scripts = MagicMock()
        # Мок ролла возвращает min_val кубика
        engine._create_roll_context.side_effect = lambda u, t, d, **k: MagicMock(final_value=d.min_val, log=[])

        executed_slots = set()

        # Вызываем process_mass_attack напрямую (как это делает executor)
        report = process_mass_attack(engine, act_a, [unit_b], "TestRound", executed_slots)

        # === ПРОВЕРКА ===
        self.assertEqual(len(report), 1, "Должна быть ТОЛЬКО ОДНА запись о клэше (общая сумма).")

        clash_data = report[0]

        val_a = clash_data['left']['val']
        val_b = clash_data['right']['val']

        print(f"⚔️ Clash Values: A={val_a}, B={val_b}")

        self.assertEqual(val_a, 20, "Кубики атакующего (10, 10) должны суммироваться в 20.")
        self.assertEqual(val_b, 10, "Кубики защитника (5, 5) должны суммироваться в 10.")
        self.assertIn("Hit", clash_data['outcome'])


if __name__ == '__main__':
    unittest.main()