import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType
from logic.battle_flow.executor import execute_single_action
from logic.battle_flow.priorities import get_action_priority
from tests.mocks import MockUnit, MockDice


class TestInterceptionMechanics(unittest.TestCase):

    def create_unit(self, name):
        u = MockUnit(name)
        # Настраиваем моки для методов состояния
        u.is_dead = MagicMock(return_value=False)
        u.is_staggered = MagicMock(return_value=False)
        u.card_cooldowns = {}
        u.deck = []
        # [ВАЖНО] Инициализируем слоты, чтобы executor не падал при проверке len()
        u.active_slots = []
        return u

    def create_action(self, source, target, card_type, speed, label=""):
        card = MagicMock()
        card.name = label or f"{card_type}_Card"
        card.card_type = card_type.lower()
        card.id = f"{card.name}_id"
        card.tier = 1
        card.dice_list = [MockDice(DiceType.SLASH)]
        source.current_card = card

        # Обновляем слоты источника, чтобы он мог атаковать
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

    def sort_actions(self, actions):
        """Сортировка движка: Приоритет Типа -> Скорость"""
        return sorted(
            actions,
            key=lambda x: (get_action_priority(x['slot_data']['card']), x['slot_data']['speed']),
            reverse=True
        )

    def test_melee_cannot_intercept_ranged_by_speed_alone(self):
        """
        Сценарий:
        1. Melee (Spd 20) пытается перехватить Ranged (Spd 1).
        2. Ranged атакует Dummy.

        Результат:
        Ranged ходит первым из-за приоритета (3000 vs 1000).
        """
        u_melee = self.create_unit("Melee_Interceptor")
        u_ranged = self.create_unit("Ranged_Sniper")
        u_dummy = self.create_unit("Poor_Dummy")

        # Ranged хочет ударить Dummy (One-Sided)
        act_ranged = self.create_action(u_ranged, u_dummy, "Ranged", 1, "Snipe")

        # Melee хочет перехватить Ranged (бьет его)
        act_melee = self.create_action(u_melee, u_ranged, "Melee", 20, "Intercept_Attempt")

        # Настраиваем слоты (у Dummy слотов нет, он просто цель)
        u_ranged.active_slots = [act_ranged['slot_data']]
        u_melee.active_slots = [act_melee['slot_data']]

        # Сортируем действия
        actions = self.sort_actions([act_ranged, act_melee])

        # 1. ПРОВЕРКА ПОРЯДКА: Ranged должен быть первым
        self.assertEqual(actions[0]['label'], "Snipe")
        self.assertEqual(actions[1]['label'], "Intercept_Attempt")

        executed_slots = set()

        # 2. ВЫПОЛНЕНИЕ: Ranged (Ход 1)
        # Он должен успешно атаковать Dummy.
        with patch.object(MagicMock(), '_resolve_one_sided', return_value=[]) as mock_onesided:
            engine_mock = MagicMock()
            engine_mock._resolve_one_sided = mock_onesided
            engine_mock._resolve_card_clash = MagicMock()

            execute_single_action(engine_mock, actions[0], executed_slots)

            # Проверяем, что вызвался One-Sided (по Dummy)
            engine_mock._resolve_one_sided.assert_called_once()

            # Слот Ranged помечается как использованный
            self.assertIn((u_ranged.name, 0), executed_slots)

            # [FIX] Убрана проверка (u_dummy.name, 0), так как при One-Sided
            # без ответного действия цель не помечается как executed.

        # 3. ВЫПОЛНЕНИЕ: Melee (Ход 2)
        # Melee атакует Ranged. Слот Ranged УЖЕ в executed_slots.
        # Это должен быть One-Sided Redirected (удар по занятому).
        with patch.object(MagicMock(), '_resolve_one_sided', return_value=[]) as mock_onesided_2:
            engine_mock = MagicMock()
            engine_mock._resolve_one_sided = mock_onesided_2

            execute_single_action(engine_mock, actions[1], executed_slots)

            mock_onesided_2.assert_called_once()
            _, kwargs = mock_onesided_2.call_args

            # Проверяем флаг редиректа
            self.assertTrue(kwargs.get('is_redirected', False), "Атака должна быть Redirected, т.к. цель уже сходила")

        print("✅ Тест подтвердил: Скорость Melee (20) не позволяет перехватить Ranged (1) из-за приоритета.")


if __name__ == '__main__':
    unittest.main()