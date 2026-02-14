import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType, CardType
from logic.battle_flow.executor import execute_single_action
from logic.battle_flow.mass_attack import process_mass_attack
from logic.battle_flow.priorities import get_action_priority
from tests.mocks import MockUnit, MockDice


class TestMassAttackInteractions(unittest.TestCase):

    def create_unit(self, name):
        u = MockUnit(name)
        u.is_dead = MagicMock(return_value=False)
        u.is_staggered = MagicMock(return_value=False)
        u.card_cooldowns = {}
        u.deck = []
        u.active_slots = []
        u.current_card = None
        return u

    def create_mass_action(self, source, targets, is_summation, speed, dice_vals):
        card = MagicMock()
        card.name = f"Mass_{'Sum' if is_summation else 'Ind'}_{speed}"
        card.card_type = CardType.MASS_SUMMATION.value if is_summation else CardType.MASS_INDIVIDUAL.value
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
            # [FIX] Приводим к нижнему регистру, чтобы executor.py распознал "mass"
            'card_type': str(card.card_type).lower(),
            'slot_data': slot,
            'is_left': True,
            'opposing_team': targets
        }

    def prepare_unit_defense(self, unit, dice_vals):
        """Настраивает защиту юнита, давая ему карту в активный слот."""
        card = MagicMock()
        card.name = "Def_Card"
        # [FIX] Устанавливаем tier, чтобы не падал executor при наложении кулдауна
        card.tier = 1
        card.id = "def_card_id"

        card.dice_list = []
        for val in dice_vals:
            d = MockDice(DiceType.BLOCK)
            d.min_val = val
            d.max_val = val
            card.dice_list.append(d)

        # Обновляем слот
        if unit.active_slots:
            unit.active_slots[0]['card'] = card
        else:
            unit.active_slots = [{'card': card, 'speed': 5}]
        unit.current_card = card

    def sort_actions(self, actions):
        return sorted(
            actions,
            key=lambda x: (get_action_priority(x['slot_data']['card']), x['slot_data']['speed']),
            reverse=True
        )

    # === ТЕСТЫ ===

    def test_mass_vs_mass_clash(self):
        """
        Сценарий: Битва двух Mass Attack (Summation).
        Unit A (Spd 10) vs Unit B (Spd 1).
        """
        unit_a = self.create_unit("Unit_A_Fast")
        unit_b = self.create_unit("Unit_B_Slow")

        # A: Summation [10, 10] = 20
        act_a = self.create_mass_action(unit_a, [unit_b], True, 10, [10, 10])

        # B: Summation [5, 5] = 10 (Слабее и медленнее)
        act_b = self.create_mass_action(unit_b, [unit_a], True, 1, [5, 5])

        # [FIX] Убрали prepare_unit_defense, чтобы B защищался своей картой Mass Attack (act_b),
        # а не заменял её на "Def_Card".

        actions = self.sort_actions([act_a, act_b])
        self.assertEqual(actions[0]['label'], act_a['label'])

        executed_slots = set()
        engine = MagicMock()
        engine._process_card_self_scripts = MagicMock()

        # Роллы возвращают min_val
        def mock_roll(u, t, die, **kwargs): return MagicMock(final_value=die.min_val, log=[])

        engine._create_roll_context.side_effect = mock_roll

        # 1. Ход Unit A
        report_a = execute_single_action(engine, actions[0], executed_slots)

        # Проверяем, что A победил
        self.assertIn("Hit", report_a[0]['outcome'])
        # Проверяем, что слот B помечен как использованный (защищался)
        self.assertIn((unit_b.name, 0), executed_slots)

        # 2. Ход Unit B (должен быть пропущен)
        res_b = execute_single_action(engine, actions[1], executed_slots)

        self.assertEqual(res_b, [], "Unit B не должен атаковать, так как потратил карту на защиту.")
        print("✅ Mass vs Mass: Быстрая атака отменила медленную.")

    def test_mass_summation_logic_details(self):
        """
        Проверка математики Summation.
        Attack: [5, 5, 5] = 15 vs Defense: [6, 6] = 12 -> Hit.
        """
        attacker = self.create_unit("Attacker")
        defender = self.create_unit("Defender")

        act = self.create_mass_action(attacker, [defender], True, 10, [5, 5, 5])
        self.prepare_unit_defense(defender, [6, 6])

        engine = MagicMock()
        engine._process_card_self_scripts = MagicMock()
        engine._create_roll_context.side_effect = lambda u, t, d, **k: MagicMock(final_value=d.min_val, log=[])

        executed_slots = set()
        report = process_mass_attack(engine, act, [defender], "Test", executed_slots)

        # Проверка отчета
        summ_entry = report[0]
        self.assertEqual(summ_entry['left']['val'], 15)
        self.assertEqual(summ_entry['right']['val'], 12)
        self.assertIn("Hit", summ_entry['outcome'])

        # Проверка нанесения урона: должно быть 3 вызова (для каждого кубика атаки)
        self.assertEqual(engine._apply_damage.call_count, 3)
        print("✅ Mass Summation Logic: Сумма рассчитана верно, урон прошел.")

    def test_mass_individual_logic_details(self):
        """
        Проверка логики Individual.
        Attack: [10, 2, 8] vs Defense: [5, 5].
        """
        attacker = self.create_unit("Attacker")
        defender = self.create_unit("Defender")

        act = self.create_mass_action(attacker, [defender], False, 10, [10, 2, 8])
        self.prepare_unit_defense(defender, [5, 5])

        engine = MagicMock()
        engine._process_card_self_scripts = MagicMock()
        engine._create_roll_context.side_effect = lambda u, t, d, **k: MagicMock(final_value=d.min_val if d else 0,
                                                                                 log=[])

        executed_slots = set()
        report = process_mass_attack(engine, act, [defender], "Test", executed_slots)

        self.assertEqual(len(report), 3, "Должно быть 3 взаимодействия")

        # 1. Hit (10 > 5)
        self.assertIn("Hit", report[0]['outcome'])
        # 2. Blocked (2 < 5)
        self.assertIn("Blocked", report[1]['outcome'])
        # 3. Hit (8 > None)
        self.assertIn("Hit", report[2]['outcome'])
        self.assertEqual(report[2]['right']['dice'], "None")

        print("✅ Mass Individual Logic: Обработаны победы, поражения и удары по беззащитному.")


if __name__ == '__main__':
    unittest.main()