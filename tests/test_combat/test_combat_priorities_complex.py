import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import CardType
from logic.battle_flow.executor import execute_single_action
from logic.battle_flow.priorities import get_action_priority


class TestComplexCombatPriorities(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock()

        # Хелпер для создания "живого" юнита
        def create_live_mock_unit(name):
            u = MagicMock()
            u.name = name
            u.is_dead.return_value = False
            u.is_staggered.return_value = False
            u.card_cooldowns = {}
            u.deck = []
            return u

        self.unit_a = create_live_mock_unit("Unit_Melee")
        self.unit_b = create_live_mock_unit("Unit_Offensive")
        self.unit_c = create_live_mock_unit("Unit_Ranged")
        self.unit_target = create_live_mock_unit("Target_Dummy")

        # У цели всегда есть карта в слоте 0 для возможности клэша
        def_card = MagicMock(name="DefCard")
        def_card.id = "def_card_id"
        def_card.tier = 1
        self.unit_target.active_slots = [{'card': def_card, 'speed': 5, 'destroy_on_speed': False}]

    def create_action(self, source, target, card_type_str, speed, label=""):
        card = MagicMock()
        card.name = label or f"{card_type_str}_Card"
        card.card_type = card_type_str.lower()
        card.id = f"{card.name}_id"
        card.tier = 1
        card.flags = []
        source.current_card = card

        return {
            'label': card.name,
            'source': source,
            'source_idx': 0,
            'target_unit': target,
            'target_slot_idx': 0,  # Все бьют в один слот
            'card_type': card_type_str.lower(),
            'slot_data': {'card': card, 'speed': speed, 'destroy_on_speed': False},
            'is_left': True,
            'opposing_team': [target]
        }

    def sort_actions(self, actions):
        """Сортировка по логике вашего движка: Приоритет Типа -> Скорость."""
        return sorted(
            actions,
            key=lambda x: (get_action_priority(x['slot_data']['card']), x['slot_data']['speed']),
            reverse=True
        )

    def test_offensive_intercepts_melee(self):
        """
        Проверка: Offensive (2000) перехватывает клэш у Melee (1000),
        даже если Melee быстрее.
        """
        act_melee = self.create_action(self.unit_a, self.unit_target, "Melee", 10, label="Fast_Melee")
        act_offense = self.create_action(self.unit_b, self.unit_target, "Offensive", 2, label="Slow_Offensive")

        sorted_acts = self.sort_actions([act_melee, act_offense])

        # Первым должен идти Offensive (Priority 2000)
        self.assertEqual(sorted_acts[0]['label'], "Slow_Offensive")

        executed_slots = set()

        # 1. Выполняем Offensive. Он должен войти в Clash.
        with patch.object(self.engine, '_resolve_card_clash', return_value=[]):
            execute_single_action(self.engine, sorted_acts[0], executed_slots)

        # Слот цели должен быть занят
        self.assertIn(("Target_Dummy", 0), executed_slots)

        # 2. Выполняем Melee. Он должен стать One-Sided (Redirected).
        with patch.object(self.engine, '_resolve_one_sided', return_value=[]) as mock_one_sided:
            execute_single_action(self.engine, sorted_acts[1], executed_slots)

            mock_one_sided.assert_called_once()
            _, kwargs = mock_one_sided.call_args
            self.assertTrue(kwargs['is_redirected'], "Melee должен был быть перенаправлен")

    def test_mass_attack_marks_busy_for_ranged(self):
        """
        Проверка: Mass Attack (4000) выполняется первой и помечает слот цели как 'executed',
        из-за чего Ranged (3000) бьет уже в занятую цель (Redirected).
        """
        act_mass = self.create_action(self.unit_a, self.unit_target, "mass_individual", 1, label="Mass")
        act_ranged = self.create_action(self.unit_c, self.unit_target, "Ranged", 9, label="Fast_Ranged")

        sorted_acts = self.sort_actions([act_mass, act_ranged])
        executed_slots = set()

        # 1. Запуск Mass Attack.
        # В executor.py она вызывает process_mass_attack.
        with patch('logic.battle_flow.executor.process_mass_attack', return_value=[]) as mock_mass_proc:
            # Симулируем, что Mass Attack пометила слот цели как занятый
            def side_effect(engine, action, team, label, slots):
                slots.add(("Target_Dummy", 0))
                return []

            mock_mass_proc.side_effect = side_effect

            execute_single_action(self.engine, sorted_acts[0], executed_slots)

        # 2. Запуск Ranged. Слот уже в executed_slots, значит будет One-Sided Redirected.
        with patch.object(self.engine, '_resolve_one_sided', return_value=[]) as mock_onesided:
            execute_single_action(self.engine, sorted_acts[1], executed_slots)

            mock_onesided.assert_called_once()
            _, kwargs = mock_onesided.call_args
            self.assertTrue(kwargs['is_redirected'], "Стрелок должен бить по занятой цели")

    def test_speed_tie_in_same_priority(self):
        """Проверка: При одинаковом типе (Melee) решает только скорость."""
        act_slow = self.create_action(self.unit_a, self.unit_target, "Melee", 3, label="Slow")
        act_fast = self.create_action(self.unit_b, self.unit_target, "Melee", 8, label="Fast")

        sorted_acts = self.sort_actions([act_slow, act_fast])
        self.assertEqual(sorted_acts[0]['label'], "Fast")


if __name__ == '__main__':
    unittest.main()