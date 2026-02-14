import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import CardType, DiceType
from logic.battle_flow.executor import execute_single_action
from logic.battle_flow.priorities import get_action_priority
from tests.mocks import MockUnit, MockDice


class TestRangedOffensiveScenarios(unittest.TestCase):

    # [FIX] Выносим метод создания юнита в класс, чтобы он был доступен везде
    def create_unit(self, name, speed=5):
        u = MockUnit(name)
        u.is_dead = MagicMock(return_value=False)
        u.is_staggered = MagicMock(return_value=False)
        u.card_cooldowns = {}
        u.deck = []
        return u

    def setUp(self):
        self.engine = MagicMock()

        # Теперь используем self.create_unit
        self.u_ranged = self.create_unit("Ranger")
        self.u_offensive = self.create_unit("Berserker")
        self.u_melee = self.create_unit("Knight")
        self.u_target = self.create_unit("DummyTarget")

    def create_action(self, source, target, card_type, speed, label=""):
        """Создает действие и настраивает карту юнита."""
        card = MagicMock()
        card.name = label or f"{card_type}_Card"
        card.card_type = card_type.lower()
        card.id = f"{card.name}_id"
        card.tier = 1
        card.dice_list = [MockDice(DiceType.SLASH)]
        source.current_card = card

        # Настраиваем слот атакующего
        source.active_slots = [{'card': card, 'speed': speed, 'destroy_on_speed': False}]

        return {
            'label': card.name,
            'source': source,
            'source_idx': 0,
            'target_unit': target,
            'target_slot_idx': 0,
            'card_type': card_type.lower(),
            'slot_data': {'card': card, 'speed': speed, 'destroy_on_speed': False},
            'is_left': True,
            'opposing_team': [target]
        }

    def prepare_target_slot(self, target, card_type="melee", speed=4):
        """Дает цели карту, чтобы она могла ответить на клэш."""
        card = MagicMock()
        card.name = "DefCard"
        card.card_type = card_type
        card.id = "def_card"
        card.tier = 1
        card.dice_list = [MockDice(DiceType.BLOCK)]
        target.active_slots = [{'card': card, 'speed': speed, 'destroy_on_speed': False}]
        target.current_card = card

    def sort_actions(self, actions):
        return sorted(
            actions,
            key=lambda x: (get_action_priority(x['slot_data']['card']), x['slot_data']['speed']),
            reverse=True
        )

    # === ТЕСТЫ ===

    def test_ranged_vs_melee_interception(self):
        """
        1. Ranged vs Melee (целят друг в друга).
        Ranged (3000) должен атаковать первым. Melee (1000) пропускает ход.
        """
        act_ranged = self.create_action(self.u_ranged, self.u_melee, "Ranged", 2, "Snipe")
        act_melee = self.create_action(self.u_melee, self.u_ranged, "Melee", 8, "Slash")

        self.u_melee.active_slots[0] = act_melee['slot_data']

        actions = self.sort_actions([act_ranged, act_melee])

        self.assertEqual(actions[0]['label'], "Snipe")

        executed_slots = set()

        # Выполняем Ranged. Ожидаем Clash.
        with patch.object(self.engine, '_resolve_card_clash', return_value=[]) as mock_clash:
            execute_single_action(self.engine, actions[0], executed_slots)
            mock_clash.assert_called_once()
            self.assertIn((self.u_ranged.name, 0), executed_slots)
            self.assertIn((self.u_melee.name, 0), executed_slots)

        # Выполняем Melee. Он должен быть пропущен.
        res = execute_single_action(self.engine, actions[1], executed_slots)
        self.assertEqual(res, [], "Melee действие должно быть пропущено")
        print("✅ Ranged перехватил инициативу у Melee.")

    def test_offensive_vs_melee_priority(self):
        """
        2. Offensive vs Melee.
        Offensive (2000) бьет быстрее Melee (1000).
        """
        act_off = self.create_action(self.u_offensive, self.u_melee, "Offensive", 5, "Rush")
        act_mel = self.create_action(self.u_melee, self.u_offensive, "Melee", 10, "Guard")

        self.u_melee.active_slots[0] = act_mel['slot_data']

        actions = self.sort_actions([act_off, act_mel])

        self.assertEqual(actions[0]['label'], "Rush")

        executed_slots = set()
        with patch.object(self.engine, '_resolve_card_clash', return_value=[]):
            execute_single_action(self.engine, actions[0], executed_slots)

        self.assertIn((self.u_melee.name, 0), executed_slots)

        res = execute_single_action(self.engine, actions[1], executed_slots)
        self.assertEqual(res, [])
        print("✅ Offensive (Rush) опередил Melee (Guard).")

    def test_ranged_vs_offensive(self):
        """
        3. Ranged vs Offensive.
        Ranged (3000) > Offensive (2000).
        """
        act_rng = self.create_action(self.u_ranged, self.u_offensive, "Ranged", 3, "Shot")
        act_off = self.create_action(self.u_offensive, self.u_ranged, "Offensive", 7, "Dash")

        self.u_offensive.active_slots[0] = act_off['slot_data']

        actions = self.sort_actions([act_rng, act_off])
        self.assertEqual(actions[0]['label'], "Shot")

        executed_slots = set()
        with patch.object(self.engine, '_resolve_card_clash', return_value=[]):
            execute_single_action(self.engine, actions[0], executed_slots)

        self.assertIn((self.u_offensive.name, 0), executed_slots)
        print("✅ Ranged перестрелял Offensive.")

    def test_ranged_vs_ranged_speed_tie(self):
        """
        4. Ranged vs Ranged.
        Оба имеют приоритет 3000. Решает Скорость.
        """
        # [FIX] Теперь вызываем через self.create_unit
        ranger_fast = self.create_unit("FastRanger")
        ranger_slow = self.create_unit("SlowRanger")

        act_fast = self.create_action(ranger_fast, ranger_slow, "Ranged", 8, "FastShot")
        act_slow = self.create_action(ranger_slow, ranger_fast, "Ranged", 3, "SlowShot")

        ranger_slow.active_slots = [act_slow['slot_data']]
        ranger_fast.active_slots = [act_fast['slot_data']]

        actions = self.sort_actions([act_fast, act_slow])

        self.assertEqual(actions[0]['label'], "FastShot")

        executed_slots = set()
        with patch.object(self.engine, '_resolve_card_clash', return_value=[]):
            execute_single_action(self.engine, actions[0], executed_slots)

        self.assertIn((ranger_slow.name, 0), executed_slots)

        res = execute_single_action(self.engine, actions[1], executed_slots)
        self.assertEqual(res, [])
        print("✅ Ranged дуэль решена по Скорости.")

    def test_pile_up_on_target(self):
        """
        5. Куча мала: Ranged, Offensive и Melee бьют одну цель.
        """
        self.prepare_target_slot(self.u_target)

        act_rng = self.create_action(self.u_ranged, self.u_target, "Ranged", 5, "Ranged")
        act_off = self.create_action(self.u_offensive, self.u_target, "Offensive", 5, "Offensive")
        act_mel = self.create_action(self.u_melee, self.u_target, "Melee", 5, "Melee")

        actions = self.sort_actions([act_rng, act_off, act_mel])

        self.assertEqual([a['label'] for a in actions], ["Ranged", "Offensive", "Melee"])

        executed_slots = set()

        # 1. Ranged (Clash)
        with patch.object(self.engine, '_resolve_card_clash', return_value=[]) as m_clash:
            execute_single_action(self.engine, actions[0], executed_slots)
            m_clash.assert_called_once()

        # 2. Offensive (One-Sided Redirected)
        with patch.object(self.engine, '_resolve_one_sided', return_value=[]) as m_onesided:
            execute_single_action(self.engine, actions[1], executed_slots)
            args, kwargs = m_onesided.call_args
            self.assertTrue(kwargs['is_redirected'])

        # 3. Melee (One-Sided Redirected)
        with patch.object(self.engine, '_resolve_one_sided', return_value=[]) as m_onesided_2:
            execute_single_action(self.engine, actions[2], executed_slots)
            args, kwargs = m_onesided_2.call_args
            self.assertTrue(kwargs['is_redirected'])

        print("✅ Приоритеты корректно распределили типы атак по занятой цели.")


if __name__ == '__main__':
    unittest.main()