import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Добавляем корень проекта
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext
from logic.scripts.card_special import apply_axis_team_buff, summon_ally


# Специальный класс мока, так как скрипт призыва требует специфичных полей
class MockUnitWithStats(MockUnit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_sp = 100
        self.max_stagger = 50

    def recalculate_stats(self):
        pass


class TestCardSpecial(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnitWithStats(name="Caster", max_hp=100)
        self.ctx = MockContext(self.unit)
        self.ctx.log = []  # Инициализируем лог

    # ==========================================
    # 1. apply_axis_team_buff
    # ==========================================
    def test_apply_axis_team_buff_solo(self):
        """Тест: Если союзников нет, бафф накладывается на себя (x2)."""
        # Имитируем состояние, где юнит один в команде
        mock_state = {
            'team_left': [self.unit],
            'team_right': []
        }

        # Подменяем session_state
        with patch('streamlit.session_state', mock_state):
            params = {"status": "strength", "duration": 2}
            apply_axis_team_buff(self.ctx, params)

            # Должно быть 2 стака на себе
            self.assertEqual(self.unit.get_status("strength"), 2)
            self.assertIn("Axis Solo", self.ctx.log[0])

    def test_apply_axis_team_buff_with_allies(self):
        """Тест: Если есть союзники, бафф накладывается на них (x1), а не на себя."""
        ally = MockUnitWithStats(name="Ally")

        mock_state = {
            'team_left': [self.unit, ally],
            'team_right': []
        }

        with patch('streamlit.session_state', mock_state):
            params = {"status": "endurance"}
            apply_axis_team_buff(self.ctx, params)

            # Союзник получает 1
            self.assertEqual(ally.get_status("endurance"), 1)
            # Кастер получает 0
            self.assertEqual(self.unit.get_status("endurance"), 0)
            self.assertIn("Axis Team", self.ctx.log[0])

    def test_apply_axis_team_buff_dead_ally(self):
        """Тест: Мертвые союзники не считаются (должен сработать Solo бафф)."""
        dead_ally = MockUnitWithStats(name="Corpse")
        dead_ally.current_hp = 0  # Мертв

        mock_state = {
            'team_left': [self.unit, dead_ally],
            'team_right': []
        }

        with patch('streamlit.session_state', mock_state):
            apply_axis_team_buff(self.ctx, {"status": "haste"})

            self.assertEqual(self.unit.get_status("haste"), 2)
            self.assertEqual(dead_ally.get_status("haste"), 0)

    # ==========================================
    # 2. summon_ally
    # ==========================================
    def test_summon_ally_success(self):
        """Тест: Успешный призыв юнита из ростера."""
        # Подготавливаем шаблон в ростере
        template = MockUnitWithStats(name="Minion", max_hp=50)
        roster = {"Minion": template}

        team = [self.unit]

        mock_state = {
            'team_left': team,
            'roster': roster
        }

        with patch('streamlit.session_state', mock_state):
            params = {"unit_name": "Minion"}
            summon_ally(self.ctx, params)

            # Размер команды должен увеличиться
            self.assertEqual(len(team), 2)
            new_unit = team[1]

            # Проверяем свойства призванного
            self.assertTrue(new_unit.name.startswith("Minion"))
            self.assertNotEqual(new_unit, template)  # Это должна быть копия, а не ссылка
            self.assertEqual(new_unit.current_hp, 50)
            self.assertIn("Summon", self.ctx.log[0])

    def test_summon_ally_full_team(self):
        """Тест: Призыв не срабатывает, если в команде уже 5 юнитов."""
        roster = {"Minion": MockUnitWithStats(name="Minion")}
        # Создаем полную команду (5 чел)
        team = [self.unit] + [MockUnitWithStats(name=f"Ally_{i}") for i in range(4)]

        mock_state = {
            'team_left': team,
            'roster': roster
        }

        with patch('streamlit.session_state', mock_state):
            summon_ally(self.ctx, {"unit_name": "Minion"})

            self.assertEqual(len(team), 5)  # Размер не изменился
            self.assertTrue(any("Team Full" in msg for msg in self.ctx.log))

    def test_summon_ally_not_found(self):
        """Тест: Призыв несуществующего юнита."""
        mock_state = {
            'team_left': [self.unit],
            'roster': {}
        }

        with patch('streamlit.session_state', mock_state):
            summon_ally(self.ctx, {"unit_name": "Ghost"})

            self.assertEqual(len(mock_state['team_left']), 1)
            self.assertTrue(any("not found" in msg for msg in self.ctx.log))


if __name__ == '__main__':
    unittest.main()