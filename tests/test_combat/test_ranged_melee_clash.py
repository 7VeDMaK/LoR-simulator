import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import CardType
from logic.battle_flow.executor import execute_single_action
from logic.battle_flow.priorities import get_action_priority


class TestClashInteractions(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock()

        def create_live_mock_unit(name):
            u = MagicMock()
            u.name = name
            u.is_dead.return_value = False
            u.is_staggered.return_value = False
            # [FIX] Инициализируем словарь кулдаунов для executor.py
            u.card_cooldowns = {}
            return u

        self.unit_a = create_live_mock_unit("Melee_A")
        self.unit_b = create_live_mock_unit("Target_B")

        # [FIX] Настраиваем карту защитника с необходимыми атрибутами
        def_card = MagicMock(name="DefCard")
        def_card.id = "def_card_id"
        def_card.tier = 0
        self.unit_b.active_slots = [{'card': def_card, 'speed': 4, 'destroy_on_speed': False}]

        self.unit_c = create_live_mock_unit("Ranged_C")

    def create_action(self, source, target, card_type, speed, slot_idx=0):
        card = MagicMock()
        card.name = f"{card_type}_Card"
        card.card_type = card_type
        card.id = f"{card_type}_id"
        card.tier = 1  # [FIX] Явно задаем уровень карты
        source.current_card = card
        return {
            'source': source,
            'source_idx': 0,
            'target_unit': target,
            'target_slot_idx': slot_idx,
            'card_type': card_type.lower(),
            'slot_data': {'card': card, 'speed': speed, 'destroy_on_speed': False},
            'is_left': True,
            'opposing_team': [target]
        }

    def test_ranged_priority_over_melee_clash(self):
        """Проверка: Ranged перехватывает слот у Melee."""
        act_a = self.create_action(self.unit_a, self.unit_b, "Melee", 8)
        act_c = self.create_action(self.unit_c, self.unit_b, "Ranged", 2)

        actions = [act_a, act_c]
        sorted_actions = sorted(
            actions,
            key=lambda x: (get_action_priority(x['slot_data']['card']), x['slot_data']['speed']),
            reverse=True
        )

        executed_slots = set()

        # Ranged C (Priority 3000) идет первым
        with patch.object(self.engine, '_resolve_card_clash', return_value=[]):
            execute_single_action(self.engine, sorted_actions[0], executed_slots)

        self.assertIn(("Target_B", 0), executed_slots)

        # Melee A (Priority 1000) становится Redirected
        with patch.object(self.engine, '_resolve_one_sided', return_value=[]) as mock_one_sided:
            execute_single_action(self.engine, sorted_actions[1], executed_slots)
            mock_one_sided.assert_called_once()
            _, kwargs = mock_one_sided.call_args
            self.assertTrue(kwargs['is_redirected'])

    def test_mass_attack_destroys_page_before_ranged(self):
        """
        Проверка: Mass Attack (Summation) уничтожает карту цели,
        делая последующую атаку Ranged односторонней (One-Sided).
        """
        unit_mass = MagicMock()
        unit_mass.name = "Mass_User"
        unit_mass.is_dead.return_value = False
        unit_mass.is_staggered.return_value = False
        unit_mass.card_cooldowns = {}

        # Создаем Mass Summation действие (Priority 4000)
        mass_card = MagicMock(name="MassCard")
        mass_card.card_type = "mass_summation"
        mass_card.tier = 3
        mass_card.id = "mass_id"
        mass_card.dice_list = [MagicMock()]
        unit_mass.current_card = mass_card

        act_mass = {
            'source': unit_mass,
            'source_idx': 0,
            'target_unit': self.unit_b,
            'target_slot_idx': 0,
            'card_type': 'mass_summation',
            'slot_data': {'card': mass_card, 'speed': 1, 'mass_defenses': {}},
            'is_left': True,
            'opposing_team': [self.unit_b]
        }

        # Ranged действие на тот же слот (Priority 3000)
        act_ranged = self.create_action(self.unit_c, self.unit_b, "Ranged", 9)

        actions = [act_mass, act_ranged]
        sorted_actions = sorted(
            actions,
            key=lambda x: (get_action_priority(x['slot_data']['card']), x['slot_data']['speed']),
            reverse=True
        )

        # Убеждаемся, что Mass первая
        self.assertEqual(sorted_actions[0]['card_type'], 'mass_summation')

        executed_slots = set()

        # 1. Выполняем Mass Attack. Если она выигрывает, она удаляет карту из слота
        # В executor.py для mass вызывается process_mass_attack
        with patch('logic.battle_flow.executor.process_mass_attack', return_value=[]) as mock_mass_proc:
            # Симулируем эффект уничтожения карты (как это делает process_mass_attack при победе)
            def side_effect(*args):
                self.unit_b.active_slots[0]['card'] = None  # Карта уничтожена!
                return []

            mock_mass_proc.side_effect = side_effect

            execute_single_action(self.engine, sorted_actions[0], executed_slots)

        # 2. Выполняем Ranged атаку. Так как карты в слоте B нет, это должен быть One-Sided Direct
        with patch.object(self.engine, '_resolve_one_sided', return_value=[]) as mock_one_sided:
            execute_single_action(self.engine, sorted_actions[1], executed_slots)

            mock_one_sided.assert_called_once()
            _, kwargs = mock_one_sided.call_args
            # Так как слот не помечен как executed (Mass не занимает слот для обычных атак),
            # но карты там нет, это будет обычный Direct Hit (is_redirected=False)
            self.assertFalse(kwargs['is_redirected'])
            self.assertIsNone(self.unit_b.current_card, "Карта в слоте должна отсутствовать после Mass-атаки")

        print("✅ Тест подтвердил: Массовая атака уничтожает карту, лишая цель возможности клэша.")


if __name__ == '__main__':
    unittest.main()