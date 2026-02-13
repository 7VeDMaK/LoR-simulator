import unittest
import sys
import os

# Путь к корню проекта
sys.path.append(os.getcwd())

from core.enums import DiceType
from core.logging import logger, LogLevel
from tests.mocks import MockUnit, MockDice, MockContext

# ИМПОРТИРУЕМ РЕАЛЬНУЮ ЛОГИКУ
from logic.battle_flow.clash.clash_resolution import resolve_clash_round
from logic.battle_flow.interactions import resolve_interaction


class MockEngine:
    """
    Имитация движка (BattleManager/ClashSystem), которая реализует методы,
    вызываемые из clash_resolution и interactions.
    """

    def __init__(self):
        self.logs = []

    def log(self, text, level=LogLevel.NORMAL, category="Test"):
        self.logs.append(text)
        # Можно раскомментировать для отладки
        # print(f"[{category}] {text}")

    # === Методы обработки побед/поражений ===
    def _handle_clash_win(self, ctx):
        self.log(f"Win Hook: {ctx.source.name}")

    def _handle_clash_lose(self, ctx):
        self.log(f"Lose Hook: {ctx.source.name}")

    def _handle_clash_draw(self, ctx):
        self.log(f"Draw Hook: {ctx.source.name}")

    # === Главный метод резолва (из clash_resolution -> engine -> interactions) ===
    def _resolve_clash_interaction(self, winner_ctx, loser_ctx, diff):
        """
        Прокси-метод, который вызывает РЕАЛЬНУЮ функцию resolve_interaction.
        """
        self.log(f"Resolving Interaction diff={diff}")
        return resolve_interaction(self, winner_ctx, loser_ctx, diff)

    # === Методы нанесения урона (вызываются из resolve_interaction) ===
    def _apply_damage(self, source_ctx, target_ctx, resource_type):
        """
        Упрощенная логика нанесения урона. В реальности тут сложные резисты.
        Мы берем final_value из контекста победителя как урон.
        """
        amount = source_ctx.final_value
        target = target_ctx.source

        self.log(f"Apply Damage: {amount} to {target.name} ({resource_type})")

        if resource_type == "hp":
            target.take_damage(amount)
        elif resource_type == "stagger":
            target.take_stagger_damage(amount)

        return amount

    def _deal_direct_damage(self, source_ctx, target_unit, amount, resource_type):
        """
        Нанесение фиксированного урона (например, Stagger при проигрыше атаки об блок).
        """
        self.log(f"Direct Damage: {amount} to {target_unit.name} ({resource_type})")

        if resource_type == "stagger":
            target_unit.take_stagger_damage(amount)

        return amount


class TestRealClashLogic(unittest.TestCase):
    def setUp(self):
        self.engine = MockEngine()
        self.attacker = MockUnit(name="Attacker", max_hp=50, max_stagger=30)
        self.defender = MockUnit(name="Defender", max_hp=50, max_stagger=30)

    def _create_contexts(self, atk_val, def_val, atk_type, def_type):
        """Хелпер для быстрой настройки раунда."""
        die_a = MockDice(dtype=atk_type)
        die_d = MockDice(dtype=def_type)

        ctx_a = MockContext(self.attacker, self.defender, die_a)
        ctx_a.final_value = atk_val

        ctx_d = MockContext(self.defender, self.attacker, die_d)
        ctx_d.final_value = def_val

        return ctx_a, ctx_d, die_a, die_d

    # =========================================================================
    # СЦЕНАРИЙ 1: Атака (10) vs Атака (5)
    # Ожидание: Победа атакующего, нанесение полного урона (10).
    # =========================================================================
    def test_attack_vs_attack_win(self):
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(
            10, 5, DiceType.SLASH, DiceType.BLUNT
        )

        # ЗАПУСК РЕАЛЬНОЙ ЛОГИКИ
        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        # Проверки
        self.assertIn("🏆 Attacker Win (Hit)", result["outcome"])
        self.assertEqual(self.defender.current_hp, 40)  # 50 - 10
        # Проверяем, что interaction вызвался
        self.assertIn("Resolving Interaction diff=5", self.engine.logs)

        # =========================================================================

    # СЦЕНАРИЙ 2: Атака (10) vs Блок (5)
    # Ожидание: Победа атакующего, но урон снижен на значение блока (10 - 5 = 5).
    # =========================================================================
    def test_attack_vs_block_win(self):
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(
            10, 5, DiceType.PIERCE, DiceType.BLOCK
        )

        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        # Логика в interactions.py:
        # Атака > Блок -> winner_ctx.final_value временно становится равна diff (5)
        # _apply_damage наносит 5 урона.

        self.assertIn("🏆 Attacker Win (Hit)", result["outcome"])
        self.assertEqual(self.defender.current_hp, 45)  # 50 - (10 - 5) = 45
        self.assertIn("Apply Damage: 5 to Defender (hp)", self.engine.logs)

    # =========================================================================
    # СЦЕНАРИЙ 3: Атака (5) vs Блок (10)
    # Ожидание: Победа защитника. Атакующий получает Stagger урон = разнице (5).
    # =========================================================================
    def test_block_vs_attack_win(self):
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(
            5, 10, DiceType.SLASH, DiceType.BLOCK
        )

        # Defender wins (10 > 5)
        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        # resolve_clash_round вызывает _resolve_clash_interaction(ctx_d, ctx_a, 5)
        # interactions.py (Block vs Atk) -> _deal_direct_damage(stagger)

        self.assertIn("🛡️ Blocked", result["outcome"])  # Текст из resolve_clash_round

        # Атакующий получил 5 урона по стаггеру
        self.assertEqual(self.attacker.current_stagger, 25)  # 30 - 5
        self.assertEqual(self.attacker.current_hp, 50)  # HP не задето

    # =========================================================================
    # СЦЕНАРИЙ 4: Уворот (12) vs Атака (8)
    # Ожидание: Победа уворота. Урон 0. Восстановление Stagger (логика clash_resolution).
    # Флаг recycle_a/d = True.
    # =========================================================================
    def test_evade_vs_attack_win(self):
        # Defender evades
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(
            8, 12, DiceType.SLASH, DiceType.EVADE
        )

        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        self.assertIn("🏃 Defender Evades!", result["outcome"])
        self.assertTrue(result["recycle_d"])  # Кубик должен вернуться

        # Логика восстановления стаггера при увороте прописана прямо в clash_resolution
        # rec = defender.restore_stagger(val_d) -> +12 stagger
        # MockUnit.restore_stagger просто возвращает разницу
        # У нас стаггер был фулл (30), значит восстановлено 0, но вызов был.
        # В деталях лога должно быть записано.
        self.assertTrue(any("Stagger" in s for s in result["details"]))

    # =========================================================================
    # СЦЕНАРИЙ 5: Атака (15) vs Уворот (5)
    # Ожидание: Уворот провален. Полный урон.
    # =========================================================================
    def test_attack_catches_evade(self):
        ctx_a, ctx_d, die_a, die_d = self._create_contexts(
            15, 5, DiceType.BLUNT, DiceType.EVADE
        )

        result = resolve_clash_round(self.engine, ctx_a, ctx_d, die_a, die_d)

        self.assertIn("💥 Evade Failed", result["outcome"])
        # Полный урон 15
        self.assertEqual(self.defender.current_hp, 35)  # 50 - 15


if __name__ == '__main__':
    unittest.main()