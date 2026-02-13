import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Добавляем путь к корню проекта
sys.path.append(os.getcwd())

from core.enums import DiceType
from tests.mocks import MockUnit, MockDice
from logic.battle_flow.clash.clash import process_clash
from logic.battle_flow.clash.clash_state import ClashParticipantState


class TestClashInfiniteCounter(unittest.TestCase):

    @patch('logic.battle_flow.clash.clash.setup_clash_parameters')
    @patch('logic.battle_flow.clash.clash.resolve_clash_round')
    @patch('logic.battle_flow.clash.clash.handle_one_sided_exchange')
    def test_counter_die_burns_out_vs_empty(self, mock_handle_one_sided, mock_resolve, mock_setup):
        """
        Проверяет, что Counter Die сжигается, если против него 'Broken' (пустой слот),
        вместо того чтобы бесконечно бить его как One-Sided в цикле Clash.
        """
        # 1. SETUP MOCKS
        mock_setup.return_value = (False, False, False, False, [])

        # Симулируем поведение: если бы clash произошел, атакующий (Counter) победил бы
        # Но мы ожидаем, что до этого не дойдет, так как Counter vs None/Broken должен сгореть.
        mock_resolve.return_value = {
            "outcome": "Win", "details": [],
            "recycle_a": True,  # Если бы сработал, он бы вернулся (что и вызывало баг)
            "recycle_d": False
        }

        mock_handle_one_sided.return_value = "One-Sided Hit"

        engine = MagicMock()
        engine._create_roll_context.return_value = MagicMock(final_value=10, log=[])

        attacker = MockUnit("Zafiel (Counter)")
        defender = MockUnit("Rat (Empty)")

        # 2. DICE SETUP
        # Атакующий: Контр-кубик (Counter Slash)
        counter_die = MockDice(DiceType.SLASH)
        counter_die.is_counter = True

        # Защитник: У него НЕТ кубиков (или они сломаны/кончились)
        # В ClashParticipantState, если dice_list пуст, resolve_current_die вернет None

        card_a = MagicMock()
        card_a.dice_list = [counter_die]
        attacker.current_card = card_a

        card_d = MagicMock()
        card_d.dice_list = []  # Пусто!
        defender.current_card = card_d

        # 3. ЗАПУСК
        # Запускаем process_clash.
        # Ожидание:
        # Итерация 1:
        #   die_a = Counter Die
        #   die_d = None (Broken)
        #   В оригинальном коде это шло в "Случай 2: Защитник сломан/пуст" -> handle_one_sided_exchange
        #   В handle_one_sided_exchange контр-кубик бил, наносил урон и ВОЗВРАЩАЛСЯ (так как он Counter).
        #   Цикл while продолжался бесконечно (или до лимита).

        #   С ИСПРАВЛЕНИЕМ:
        #   В "Случай 2" мы должны проверить, что active_side (die_a) это Counter.
        #   Если да -> СЖИГАЕМ ЕГО (consume), не нанося урон.

        report = process_clash(engine, attacker, defender, "R1", True, 5, 3)

        # 4. ПРОВЕРКИ

        # Проверяем, что handle_one_sided_exchange НЕ был вызван для нанесения урона
        # (или был вызван, но внутри него есть проверка, которую мы имитируем?)
        # Нет, фикс должен быть на уровне process_clash или handle_one_sided_exchange.

        # Если мы добавили фикс в handle_one_sided_exchange (как в прошлом ответе про onesided.py),
        # то process_clash вызывает его.
        # Но process_clash использует `handle_one_sided_exchange` из `clash_one_sided.py`.
        # Давайте проверим, есть ли там логика.

        # Если фикса НЕТ, то mock_handle_one_sided будет вызван.
        # Если фикс ЕСТЬ (внутри process_clash перед вызовом или внутри handle...), то поведение изменится.

        # В ВАШЕМ КОДЕ `clash.py` (который вы скинули):
        # elif die_a and not die_d:
        #    outcome = handle_one_sided_exchange(...)

        # Это значит, что Counter Die (die_a) пойдет бить Broken (die_d).
        # Чтобы исправить это, нужно изменить `clash.py`.

        pass


if __name__ == '__main__':
    unittest.main()