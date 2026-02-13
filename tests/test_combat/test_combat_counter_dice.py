import unittest
import sys
import os

# Путь к корню проекта
sys.path.append(os.getcwd())

from core.enums import DiceType
from core.logging import logger, LogLevel
from tests.mocks import MockUnit, MockDice, MockContext

# Импортируем реальную логику
from logic.battle_flow.clash.clash_resolution import resolve_clash_round
from logic.battle_flow.interactions import resolve_interaction


class MockEngine:
    def __init__(self):
        self.logs = []

    def log(self, text, level=LogLevel.NORMAL, category="Test"):
        self.logs.append(text)

    def _handle_clash_win(self, ctx):
        pass

    def _handle_clash_lose(self, ctx):
        pass

    def _handle_clash_draw(self, ctx):
        pass

    def _resolve_clash_interaction(self, winner_ctx, loser_ctx, diff):
        return resolve_interaction(self, winner_ctx, loser_ctx, diff)

    def _apply_damage(self, source_ctx, target_ctx, resource_type):
        amount = source_ctx.final_value
        target = target_ctx.source
        if resource_type == "hp":
            target.take_damage(amount)
        elif resource_type == "stagger":
            target.take_stagger_damage(amount)
        return amount

    def _deal_direct_damage(self, source_ctx, target_unit, amount, resource_type):
        if resource_type == "stagger":
            target_unit.take_stagger_damage(amount)
        return amount


class TestCounterDice(unittest.TestCase):
    def setUp(self):
        self.engine = MockEngine()
        self.attacker = MockUnit(name="Zafiel", max_hp=100, max_stagger=50)
        self.defender = MockUnit(name="Roland", max_hp=100, max_stagger=50)

    def _create_contexts(self, atk_val, def_val, atk_type, def_type,
                         atk_is_counter=False, def_is_counter=False):
        die_a = MockDice(dtype=atk_type)
        die_a.is_counter = atk_is_counter  # Устанавливаем флаг контр-кубика

        die_d = MockDice(dtype=def_type)
        die_d.is_counter = def_is_counter

        ctx_a = MockContext(self.attacker, self.defender, die_a)
        ctx_a.final_value = atk_val

        ctx_d = MockContext(self.defender, self.attacker, die_d)
        ctx_d.final_value = def_val

        return ctx_a, ctx_d, die_a, die_d

    # =========================================================================
    # ТЕСТ 1: Контр-Атака (Победа)
    # Обычная атака исчезает после победы. Контр-атака должна вернуться (Recycle).
    # =========================================================================
    def test_counter_attack_win(self):
        # Zafiel бьет контр-атакой (10) против обычной атаки Roland (5)
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(
            10, 5,
            DiceType.SLASH, DiceType.BLUNT,
            atk_is_counter=True, def_is_counter=False
        )

        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        self.assertIn("Win (Hit)", result["outcome"])
        self.assertEqual(self.defender.current_hp, 90)  # Урон 10 прошел

        # ГЛАВНАЯ ПРОВЕРКА: Кубик должен вернуться!
        self.assertTrue(result["recycle_a"], "Counter Attack die should recycle on win!")

    # =========================================================================
    # ТЕСТ 2: Контр-Атака (Поражение)
    # Если контр-кубик проигрывает, он ломается как обычный.
    # =========================================================================
    def test_counter_attack_lose(self):
        # Zafiel (Counter 5) vs Roland (Attack 10)
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(
            5, 10,
            DiceType.SLASH, DiceType.BLUNT,
            atk_is_counter=True, def_is_counter=False
        )

        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        # Roland wins
        self.assertIn("Win (Hit)", result["outcome"])
        self.assertEqual(self.attacker.current_hp, 90)

        # Zafiel проиграл -> кубик НЕ возвращается
        self.assertFalse(result["recycle_a"], "Losing counter die should NOT recycle.")

    # =========================================================================
    # ТЕСТ 3: Контр-Блок (Победа)
    # Обычный блок исчезает после победы (или остается как "защитный" до конца сцены в некоторых играх,
    # но в LoR в клэше он тратится). Контр-блок должен вернуться.
    # =========================================================================
    def test_counter_block_win(self):
        # Zafiel (Atk 5) vs Roland (Counter Block 10)
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(
            5, 10,
            DiceType.SLASH, DiceType.BLOCK,
            atk_is_counter=False, def_is_counter=True
        )

        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        self.assertIn("Blocked", result["outcome"])
        # Zafiel получает Stagger (10-5=5)
        self.assertEqual(self.attacker.current_stagger, 45)

        # Roland выиграл контр-блоком -> Recycle
        self.assertTrue(result["recycle_d"], "Counter Block should recycle on win!")

    # =========================================================================
    # ТЕСТ 4: Контр vs Контр (Победа)
    # Оба кубика контр. Победитель рециклится, проигравший ломается.
    # =========================================================================
    def test_counter_vs_counter(self):
        # Zafiel (Counter Slash 15) vs Roland (Counter Pierce 10)
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(
            15, 10,
            DiceType.SLASH, DiceType.PIERCE,
            atk_is_counter=True, def_is_counter=True
        )

        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        self.assertIn("Zafiel Win", result["outcome"])

        self.assertTrue(result["recycle_a"], "Winner Counter should recycle")
        self.assertFalse(result["recycle_d"], "Loser Counter should NOT recycle")


if __name__ == '__main__':
    unittest.main()