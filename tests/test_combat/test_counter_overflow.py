import unittest
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType
from core.logging import logger, LogLevel
from tests.mocks import MockUnit, MockDice, MockContext
from logic.battle_flow.clash.clash_resolution import resolve_clash_round


# Имитация функции One-Sided атаки (как она должна выглядеть с фиксом)
def resolve_one_sided_fake(engine, ctx, die):
    """
    Симуляция логики односторонней атаки.
    """
    # [FIX LOGIC HERE]
    # Если это контр-кубик, он не должен бить в одностороннем порядке
    if getattr(die, "is_counter", False):
        engine.log(f"🚫 Counter Die '{die.dtype}' discarded (No target)")
        return 0  # Урона нет

    # Обычная логика
    dmg = die.roll()
    engine.log(f"⚔️ One-Sided Hit: {dmg}")
    return dmg


class MockEngine:
    def __init__(self):
        self.logs = []

    def log(self, text, level=LogLevel.NORMAL, category="Test"):
        self.logs.append(text)

    def _handle_clash_win(self, ctx): pass

    def _handle_clash_lose(self, ctx): pass

    def _handle_clash_draw(self, ctx): pass

    def _resolve_clash_interaction(self, w, l, d): return d


class TestCounterOverflow(unittest.TestCase):
    def setUp(self):
        self.engine = MockEngine()
        self.attacker = MockUnit(name="Zafiel", max_hp=100)  # С контрой
        self.defender = MockUnit(name="Rat", max_hp=100)  # С 2 атаками

    def test_counter_expires_after_clash(self):
        """
        Проверка: Контр-кубик побеждает 2 атаки, остается активным,
        но НЕ должен совершать одностороннюю атаку в пустоту.
        """
        # 1. Настройка: 1 мощный Контр-кубик vs 2 Слабых атаки
        counter_die = MockDice(DiceType.SLASH, min_val=10, max_val=10)
        counter_die.is_counter = True

        enemy_die_1 = MockDice(DiceType.BLUNT, min_val=5, max_val=5)
        enemy_die_2 = MockDice(DiceType.BLUNT, min_val=5, max_val=5)

        # Очереди кубиков
        zaf_queue = [counter_die]
        rat_queue = [enemy_die_1, enemy_die_2]

        print("\n=== Start Clash Simulation ===")

        # 2. Симуляция цикла клэшей (Clash Loop)
        while zaf_queue and rat_queue:
            d_a = zaf_queue[0]  # Контра
            d_b = rat_queue.pop(0)  # Враг

            ctx_a = MockContext(self.attacker, self.defender, d_a)
            ctx_a.final_value = d_a.roll()

            ctx_b = MockContext(self.defender, self.attacker, d_b)
            ctx_b.final_value = d_b.roll()

            # Резолв раунда
            res = resolve_clash_round(self.engine, ctx_a, ctx_b, d_a, d_b)

            # Логика очереди: если ресайкл, оставляем в zaf_queue, иначе удаляем
            if not res["recycle_a"]:
                zaf_queue.pop(0)

            print(f"Round Result: {res['outcome']}")

        # 3. Проверка состояния после клэша
        self.assertEqual(len(rat_queue), 0, "У врага кончились кубики")
        self.assertEqual(len(zaf_queue), 1, "Контр-кубик все еще в очереди (так как побеждал)")

        # 4. ФАЗА ONE-SIDED (Где сейчас баг)
        # Мы берем оставшийся кубик и пытаемся нанести им удар
        leftover_die = zaf_queue[0]

        damage = resolve_one_sided_fake(self.engine, MockContext(self.attacker, self.defender, leftover_die),
                                        leftover_die)

        # ОЖИДАНИЕ: Урон должен быть 0, так как Контр-кубик сгорает без цели
        self.assertEqual(damage, 0, "Counter die should NOT deal one-sided damage!")
        self.assertIn("discarded", self.engine.logs[-1], "Log should mention discard")


if __name__ == '__main__':
    unittest.main()