import unittest
from unittest.mock import MagicMock
import sys
import os

# Добавляем путь к корню проекта
sys.path.append(os.getcwd())

from core.enums import CardType
from logic.battle_flow.priorities import get_action_priority


class TestRealPriorities(unittest.TestCase):
    def create_mock_action(self, name, card_type, speed):
        """Хелпер для создания структуры действия, которую использует ваш движок."""
        card = MagicMock()
        # Имитируем поведение card_type. В priorities.py вы делаете str(card.card_type).lower()
        # Поэтому передаем строку или объект, который при приведении к строке даст нужный тип.
        card.card_type = card_type
        card.name = name

        return {
            'label': name,
            'source': MagicMock(current_card=card),
            'spd_atk': speed,
            'card_type': str(card_type).lower()
        }

    def test_full_priority_sort(self):
        """
        Проверяет полную цепочку приоритетов:
        On Play > Mass > Ranged > Offensive > Melee
        А внутри одного типа — по скорости (от большей к меньшей).
        """

        # Создаем список действий в хаотичном порядке
        actions = [
            # Melee со скоростью 10 (самый быстрый, но низкий приоритет типа)
            self.create_mock_action("Fast Melee", "melee", 10),

            # Массовая атака со скоростью 1 (медленная, но высокий приоритет)
            self.create_mock_action("Slow Mass", "mass_summation", 1),

            # Дальняя атака (скорость 5)
            self.create_mock_action("Mid Ranged", "ranged", 5),

            # Мгновенная карта (On Play)
            self.create_mock_action("Instant Buff", "on_play", 3),

            # Новая категория Offensive (скорость 7)
            self.create_mock_action("Fast Offensive", "offensive", 7),

            # Еще одна массовая, но быстрее первой
            self.create_mock_action("Fast Mass", "mass_individual", 8),
        ]

        # Функция сортировки, использующая вашу логику из priorities.py
        # Сортируем:
        # 1. По весу типа (get_action_priority) - от большего к меньшему
        # 2. По скорости (spd_atk) - от большего к меньшему
        sorted_actions = sorted(
            actions,
            key=lambda x: (get_action_priority(x['source'].current_card), x['spd_atk']),
            reverse=True
        )

        # Ожидаемый порядок имен
        expected_order = [
            "Instant Buff",  # 5000 (On Play)
            "Fast Mass",  # 4000 (Mass) + Spd 8
            "Slow Mass",  # 4000 (Mass) + Spd 1
            "Mid Ranged",  # 3000 (Ranged)
            "Fast Offensive",  # 2000 (Offensive)
            "Fast Melee"  # 1000 (Melee)
        ]

        actual_order = [a['label'] for a in sorted_actions]

        self.assertEqual(actual_order, expected_order)
        print("✅ Порядок приоритетов подтвержден:")
        for i, name in enumerate(actual_order, 1):
            print(f"{i}. {name}")

    def test_item_priority(self):
        """
        Проверка типа ITEM.
        В priorities.py он сейчас не прописан явно, поэтому должен получить 0.
        """
        item_card = MagicMock(card_type="item", name="Health Potion")
        prio = get_action_priority(item_card)

        # Если в priorities.py нет "item", вернется 0.
        # Если вы хотите, чтобы предметы были как On Play, их надо туда добавить.
        print(f"ℹ️ Приоритет ITEM сейчас: {prio}")
        self.assertEqual(prio, 0, "Item should have 0 priority unless added to priorities.py")


if __name__ == '__main__':
    unittest.main()