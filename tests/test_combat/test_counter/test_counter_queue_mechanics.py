import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType
from logic.battle_flow.executor import execute_single_action


# === MOCKS ===
class MockDice:
    def __init__(self, val, is_counter=False):
        self.dtype = DiceType.BLOCK
        self.min_val = val
        self.max_val = val
        self.is_counter = is_counter
        self.id = f"dice_{val}_{id(self)}"


class MockCard:
    def __init__(self, dice_list):
        self.name = "Test Card"
        self.dice_list = dice_list
        self.id = "card_id"
        self.tier = 1
        self.card_type = "melee"


class MockUnit:
    def __init__(self, name):
        self.name = name
        self.active_slots = []
        self.current_card = None
        self.counter_dice = []  # Единая очередь контр-кубиков
        self.stored_dice = []
        self.current_die = None

        # [FIX] Добавлены атрибуты для поддержки кулдаунов и колоды (используются в executor)
        self.card_cooldowns = {}
        self.deck = []

    def is_dead(self): return False

    def is_staggered(self): return False

    def restore_stagger(self, val): return val


class TestCounterQueueMechanics(unittest.TestCase):

    def setUp(self):
        self.engine = MagicMock()
        self.engine.logs = []

        # Настраиваем роллы и урон
        self.engine._create_roll_context.side_effect = lambda u, t, d, **k: MagicMock(final_value=d.min_val, log=[])
        self.engine._resolve_clash_interaction.return_value = 0
        self.engine._resolve_one_sided.return_value = [{"outcome": "One-Sided Hit"}]
        # _resolve_card_clash нам не нужен, если мы перехватываем через process_clash

    def create_action(self, source, target, dice_val):
        card = MockCard([MockDice(dice_val)])
        source.current_card = card
        slot = {'card': card, 'speed': 5, 'destroy_on_speed': False}
        source.active_slots = [slot]

        return {
            'label': "Attack",
            'source': source,
            'source_idx': 0,
            'target_unit': target,
            'target_slot_idx': 0,
            'card_type': "melee",
            'slot_data': slot,
            'is_left': True,
            'opposing_team': [target]
        }

    def test_multiple_counters_vs_multiple_attackers(self):
        """
        Сценарий:
        Зафиэль имеет 4 Контр-кубика (Блок 10).
        Враг 1 атакует -> Clash (Counter #1).
        Враг 2 атакует -> Clash (Counter #2).
        """
        zafiel = MockUnit("Zafiel")
        enemy1 = MockUnit("Enemy1")
        enemy2 = MockUnit("Enemy2")

        # Даем Зафиэлю 4 контр-кубика в единую очередь
        zafiel.counter_dice = [
            MockDice(10, is_counter=True),
            MockDice(10, is_counter=True),
            MockDice(10, is_counter=True),
            MockDice(10, is_counter=True)
        ]

        # У Зафиэля нет активной карты в слоте
        zafiel.active_slots = [{'card': None, 'speed': 1}]

        act1 = self.create_action(enemy1, zafiel, 5)
        act2 = self.create_action(enemy2, zafiel, 5)

        executed_slots = set()

        # Патчим process_clash, который теперь импортирован в executor.
        # [ВАЖНО] Если executor.py лежит в logic/battle_flow/executor.py, то путь для патча должен быть таким:
        with patch('logic.battle_flow.executor.process_clash') as mock_clash, \
                patch('logic.battle_flow.executor.process_mass_attack') as mock_mass:

            # --- ВЫПОЛНЕНИЕ 1 (Enemy 1) ---
            execute_single_action(self.engine, act1, executed_slots)

            # Проверка 1
            if mock_clash.called:
                print("✅ Enemy 1 перехвачен Контр-кубиком №1.")
                # Executor должен был сделать pop(0)
                self.assertEqual(len(zafiel.counter_dice), 3, "Кубик №1 должен быть извлечен из очереди.")
            else:
                self.fail("Counter Die #1 failed to intercept Attack 1")

            mock_clash.reset_mock()

            # --- ВЫПОЛНЕНИЕ 2 (Enemy 2) ---
            execute_single_action(self.engine, act2, executed_slots)

            # Проверка 2
            if mock_clash.called:
                print("✅ Enemy 2 перехвачен Контр-кубиком №2.")
                self.assertEqual(len(zafiel.counter_dice), 2, "Кубик №2 должен быть извлечен из очереди.")
            else:
                self.fail("Counter Die #2 failed to intercept Attack 2. Queue logic is broken.")


if __name__ == '__main__':
    unittest.main()