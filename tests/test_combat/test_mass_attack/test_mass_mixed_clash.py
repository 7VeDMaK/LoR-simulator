import unittest
from unittest.mock import MagicMock
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType, CardType
from logic.battle_flow.executor import execute_single_action
from logic.battle_flow.priorities import get_action_priority
from tests.mocks import MockUnit, MockDice


class TestMassMixedClash(unittest.TestCase):

    def create_unit(self, name):
        u = MockUnit(name)
        u.is_dead = MagicMock(return_value=False)
        u.is_staggered = MagicMock(return_value=False)
        u.card_cooldowns = {}
        u.deck = []
        u.active_slots = []
        u.current_card = None
        return u

    def create_mass_action(self, source, targets, card_type_enum, speed, dice_vals):
        """
        Создает действие масс атаки.
        card_type_enum: CardType.MASS_SUMMATION или CardType.MASS_INDIVIDUAL
        """
        card = MagicMock()
        is_sum = (card_type_enum == CardType.MASS_SUMMATION)
        type_str = "Sum" if is_sum else "Ind"
        card.name = f"Mass_{type_str}_{speed}"

        # [ВАЖНО] executor.py проверяет "mass" in act['card_type']
        # Поэтому мы должны передать строку в нижнем регистре
        card.card_type = card_type_enum.value
        card.tier = 3
        card.id = f"id_{card.name}"

        card.dice_list = []
        for val in dice_vals:
            d = MockDice(DiceType.SLASH)  # Масс атаки обычно атакующие
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
            # Передаем строку для executor
            'card_type': str(card.card_type).lower(),
            'slot_data': slot,
            'is_left': True,
            'opposing_team': targets
        }

    def sort_actions(self, actions):
        """Сортировка: Приоритет -> Скорость"""
        return sorted(
            actions,
            key=lambda x: (get_action_priority(x['slot_data']['card']), x['slot_data']['speed']),
            reverse=True
        )

    def test_summation_beats_individual(self):
        """
        Сценарий 1:
        Unit A (Summation, Spd 10) vs Unit B (Individual, Spd 5).

        Ожидание:
        1. A ходит первым (по скорости).
        2. B защищается своей картой Individual.
        3. Считается по правилам Summation (Сумма A vs Сумма B).
        """
        unit_a = self.create_unit("Boss_Summation")
        unit_b = self.create_unit("Boss_Individual")

        # A: Summation [10, 10] = 20. Скорость 10.
        act_a = self.create_mass_action(unit_a, [unit_b], CardType.MASS_SUMMATION, 10, [10, 10])

        # B: Individual [4, 4, 4] = 12 (в сумме). Скорость 5.
        act_b = self.create_mass_action(unit_b, [unit_a], CardType.MASS_INDIVIDUAL, 5, [4, 4, 4])

        actions = self.sort_actions([act_a, act_b])

        # Проверка порядка: A должен быть первым
        self.assertEqual(actions[0]['label'], act_a['label'])

        executed_slots = set()
        engine = MagicMock()
        engine._process_card_self_scripts = MagicMock()
        # Роллы = min_val
        engine._create_roll_context.side_effect = lambda u, t, d, **k: MagicMock(final_value=d.min_val, log=[])

        # 1. Выполняем A
        report = execute_single_action(engine, actions[0], executed_slots)

        # Проверка результата
        # Это должен быть Summation Clash
        clash_entry = report[0]
        self.assertIn("(Mass)", clash_entry['round'])  # Метка Summation

        # Сумма A (20) vs Сумма B (12) -> Hit
        self.assertEqual(clash_entry['left']['val'], 20)
        self.assertEqual(clash_entry['right']['val'], 12)
        self.assertIn("Hit", clash_entry['outcome'])

        # Слот B должен сгореть
        self.assertIn((unit_b.name, 0), executed_slots)
        self.assertIsNone(unit_b.active_slots[0]['card'])  # Уничтожена

        # 2. Ход B
        res_b = execute_single_action(engine, actions[1], executed_slots)
        self.assertEqual(res_b, [], "Unit B потерял ход.")

        print("✅ Summation (Fast) переехала Individual (Slow).")

    def test_individual_beats_summation(self):
        """
        Сценарий 2:
        Unit A (Individual, Spd 20) vs Unit B (Summation, Spd 1).

        Ожидание:
        1. A ходит первым.
        2. B защищается картой Summation (ее кубики используются для защиты).
        3. Считается по правилам Individual (Кубик vs Кубик).
        """
        unit_a = self.create_unit("Hero_Individual")
        unit_b = self.create_unit("Boss_Summation")

        # A: Individual [10, 5]. Скорость 20.
        act_a = self.create_mass_action(unit_a, [unit_b], CardType.MASS_INDIVIDUAL, 20, [10, 5])

        # B: Summation [8, 8]. Скорость 1.
        act_b = self.create_mass_action(unit_b, [unit_a], CardType.MASS_SUMMATION, 1, [8, 8])

        actions = self.sort_actions([act_a, act_b])
        self.assertEqual(actions[0]['label'], act_a['label'])

        executed_slots = set()
        engine = MagicMock()
        engine._process_card_self_scripts = MagicMock()
        engine._create_roll_context.side_effect = lambda u, t, d, **k: MagicMock(final_value=d.min_val if d else 0,
                                                                                 log=[])

        # 1. Выполняем A
        report = execute_single_action(engine, actions[0], executed_slots)

        # Должно быть 2 столкновения (по кол-ву кубиков A)
        self.assertEqual(len(report), 2)

        # Clash 1: 10 vs 8 -> Hit
        self.assertEqual(report[0]['left']['val'], 10)
        self.assertEqual(report[0]['right']['val'], 8)
        self.assertIn("Hit", report[0]['outcome'])

        # Clash 2: 5 vs 8 -> Blocked
        self.assertEqual(report[1]['left']['val'], 5)
        self.assertEqual(report[1]['right']['val'], 8)
        self.assertIn("Blocked", report[1]['outcome'])

        # Важно: При Individual атаке карта защитника НЕ уничтожается полностью (если не сказано иное),
        # но слот помечается как использованный.
        self.assertIn((unit_b.name, 0), executed_slots)
        self.assertIsNotNone(unit_b.active_slots[0]['card'], "Карта не должна исчезать при Individual (обычно)")

        # 2. Ход B
        res_b = execute_single_action(engine, actions[1], executed_slots)
        self.assertEqual(res_b, [], "Unit B все равно потерял ход, так как использовал карту для защиты.")

        print("✅ Individual (Fast) пробила Summation (Slow).")


if __name__ == '__main__':
    unittest.main()