import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType
from logic.battle_flow.executor import execute_single_action


# === MOCKS ===

class MockDice:
    def __init__(self, val, dtype=DiceType.BLOCK, is_counter=False):
        self.dtype = dtype
        self.min_val = val
        self.max_val = val
        self.is_counter = is_counter
        self.id = f"dice_{val}_{id(self)}"


class MockCard:
    def __init__(self, name="Test Card"):
        self.name = name
        self.dice_list = [MockDice(5, DiceType.SLASH)]
        self.id = f"card_{id(self)}"
        self.tier = 1
        self.card_type = "melee"
        self.flags = []


class MockUnit:
    def __init__(self, name):
        self.name = name
        self.active_slots = []
        self.current_card = None
        self.counter_dice = []  # Очередь контр-кубиков
        self.card_cooldowns = {}
        self.deck = []

    def is_dead(self): return False

    def is_staggered(self): return False


# === СИМУЛЯТОР ТАЛАНТА ===

def trigger_talent_3_2_full_upgrade(unit):
    """
    Симулирует работу таланта 3.2 (Full Upgrade) в начале хода.
    Выдает 4 Контр-кубика Блока.
    """
    print(f"\n[Talent] ✨ Talent 3.2 Triggered for {unit.name}!")

    # База + Апгрейды = 4 кубика
    new_dice = [
        MockDice(8, DiceType.BLOCK, is_counter=True),
        MockDice(9, DiceType.BLOCK, is_counter=True),
        MockDice(10, DiceType.BLOCK, is_counter=True),
        MockDice(11, DiceType.BLOCK, is_counter=True)
    ]

    unit.counter_dice.extend(new_dice)
    print(f"[Talent] 🛡️ Added {len(new_dice)} Counter Block Dice. Total: {len(unit.counter_dice)}")


# === ТЕСТ ===

class TestFullCounterLogic(unittest.TestCase):

    def setUp(self):
        self.engine = MagicMock()
        self.engine.logs = []

        # Моки для движка, чтобы не зависеть от рандома
        self.engine._create_roll_context.side_effect = lambda u, t, d, **k: MagicMock(final_value=d.min_val, log=[])
        self.engine._resolve_clash_interaction.return_value = 0
        self.engine._resolve_one_sided.return_value = [{"outcome": "One-Sided Hit"}]

    def create_attack_action(self, source, target, enemy_idx):
        card = MockCard(f"Enemy Attack {enemy_idx}")
        source.current_card = card
        slot = {'card': card, 'speed': 5, 'destroy_on_speed': False}
        source.active_slots = [slot]

        return {
            'label': f"Atk_{enemy_idx}",
            'source': source,
            'source_idx': 0,
            'target_unit': target,
            'target_slot_idx': 0,
            'card_type': "melee",
            'slot_data': slot,
            'is_left': True,
            'opposing_team': [target]
        }

    def test_zafiel_vs_horde(self):
        """
        Полная проверка сценария: Зафиэль с талантом против 5 врагов.
        """
        zafiel = MockUnit("Zafiel")
        # У Зафиэля нет активной карты (он в стойке)
        zafiel.active_slots = [{'card': None, 'speed': 1}]

        enemies = [MockUnit(f"Enemy_{i + 1}") for i in range(5)]

        # 1. ФАЗА НАЧАЛА ХОДА
        # Талант выдает кубы
        trigger_talent_3_2_full_upgrade(zafiel)

        self.assertEqual(len(zafiel.counter_dice), 4, "Талант должен был выдать 4 кубика.")

        # 2. ФАЗА БОЯ
        executed_slots = set()

        # Патчим executor, чтобы видеть, когда запускается Clash (перехват)
        with patch('logic.battle_flow.executor.process_clash') as mock_clash, \
                patch('logic.battle_flow.executor.process_mass_attack'):

            # Настраиваем mock_clash, чтобы он возвращал лог (для executor)
            mock_clash.return_value = [{"outcome": "Counter Clash Win"}]

            print("\n=== ⚔️ BATTLE START ⚔️ ===")

            # --- Враги 1-4 (Должны быть перехвачены) ---
            for i in range(4):
                attacker = enemies[i]
                action = self.create_attack_action(attacker, zafiel, i + 1)

                print(f"\n🔻 {attacker.name} attacks!")
                execute_single_action(self.engine, action, executed_slots)

                if mock_clash.called:
                    print(f"   ✅ INTERCEPTED! Zafiel uses Counter Die (Remaining: {len(zafiel.counter_dice)})")
                else:
                    print("   ❌ FAILED! One-Sided Hit.")
                    self.fail(f"Attack {i + 1} was not intercepted!")

                mock_clash.reset_mock()

            # Проверяем, что кубики кончились
            self.assertEqual(len(zafiel.counter_dice), 0, "Все контр-кубики должны быть потрачены.")

            # --- Враг 5 (Должен пробить One-Sided) ---
            attacker = enemies[4]
            action = self.create_attack_action(attacker, zafiel, 5)

            print(f"\n🔻 {attacker.name} attacks! (No counters left)")
            logs = execute_single_action(self.engine, action, executed_slots)

            # Проверяем, что clash НЕ вызывался
            if not mock_clash.called:
                print("   ⚠️ One-Sided Hit (Expected). Zafiel takes damage.")
            else:
                self.fail("Attack 5 should NOT be intercepted (no dice left)!")

        print("\n=== ✅ Test Complete: Talent worked perfectly. ===")


if __name__ == '__main__':
    unittest.main()