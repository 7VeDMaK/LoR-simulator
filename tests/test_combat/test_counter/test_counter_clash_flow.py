import unittest
import sys
import os
from unittest.mock import MagicMock

sys.path.append(os.getcwd())

from core.enums import DiceType
from tests.mocks import MockUnit, MockDice
from logic.battle_flow.clash.clash import process_clash


class TestCounterConsistency(unittest.TestCase):
    def test_three_counters_vs_two_attacks_logic(self):
        engine = MagicMock()

        # Фиксированные броски: Афелия всегда 10, Враг всегда 5
        def mock_roll_ctx(unit, target, die, **kwargs):
            ctx = MagicMock()
            ctx.final_value = 10 if "Afelia" in unit.name else 5
            ctx.log = []
            return ctx

        engine._create_roll_context.side_effect = mock_roll_ctx

        # Афелия: Карта с 3 Counter Slash
        afelia = MockUnit(name="Afelia")
        c1 = MockDice(DiceType.SLASH);
        c1.is_counter = True
        c2 = MockDice(DiceType.SLASH);
        c2.is_counter = True
        c3 = MockDice(DiceType.SLASH);
        c3.is_counter = True

        card_a = MagicMock()
        card_a.dice_list = [c1, c2, c3]
        card_a.name = "3 Counters"
        afelia.current_card = card_a
        afelia.counter_dice = []
        afelia.stored_dice = []

        # Враг: Карта с 2 обычными атаками
        enemy = MockUnit(name="Enemy")
        e1 = MockDice(DiceType.SLASH)
        e2 = MockDice(DiceType.SLASH)
        card_e = MagicMock()
        card_e.dice_list = [e1, e2]
        card_e.name = "2 Attacks"
        enemy.current_card = card_e

        # ЗАПУСК БОЯ
        process_clash(engine, afelia, enemy, "Test", True, 5, 5)

        # ОЖИДАЕМАЯ ЛОГИКА (Burnout):
        # Раунд 1: c1 vs e1 -> Afelia Win, c1 recycled (idx в ClashState становится 1).
        # Раунд 2: c1 vs e2 -> Afelia Win, c1 recycled (idx остается 1, так как c1 уже в active_counter).
        # Раунд 3: c1 vs None -> Break.
        # Сохранение (Cleanup):
        # - c1 (активный) — СГОРАЕТ (не сохраняется в stored_dice).
        # - c2 и c3 (остаток очереди с индекса 1) — СОХРАНЯЮТСЯ.

        total_saved = len(afelia.stored_dice)

        # 1. Проверяем общее количество: должны остаться только нетронутые c2 и c3
        self.assertEqual(total_saved, 2, f"Should save 2 dice (c2, c3), but found {total_saved}")

        # 2. Убеждаемся, что c1 сгорел и его нет в хранилище
        for die in afelia.stored_dice:
            self.assertIsNot(die, c1, "Active counter die c1 should have burned out!")

        # 3. Проверяем, что сохранены именно c2 и c3
        self.assertIs(afelia.stored_dice[0], c2, "First stored die should be c2")
        self.assertIs(afelia.stored_dice[1], c3, "Second stored die should be c3")

        print(f"✅ Success: 1 used counter burned out, 2 unused counters preserved.")


if __name__ == '__main__':
    unittest.main()