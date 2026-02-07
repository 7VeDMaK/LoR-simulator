import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Добавляем корень проекта
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType

# Импортируем универсальные скрипты, которые теперь использует Вивьен
from logic.scripts.card_damage import deal_damage_by_roll, deal_damage_by_clash_diff
from logic.scripts.resources import restore_resource, restore_resource_by_roll
from logic.scripts.statuses import apply_status


class TestVivianCards(unittest.TestCase):

    def setUp(self):
        self.vivian = MockUnit(name="Vivian", max_hp=100)
        self.vivian.current_hp = 50  # Половина ХП для тестов лечения
        self.enemy = MockUnit(name="Enemy", max_hp=100)

        self.ctx = MockContext(self.vivian, target=self.enemy)
        self.ctx.log = []

    # ==========================================
    # 1. Тест карты "Удар головой" (Headbutt)
    # ==========================================
    def test_card_headbutt_self_damage(self):
        """
        Проверяем: [On Hit] Вивьен получает урон, равный броску.
        JSON Params: { "target": "self" } для deal_damage_by_roll
        """
        self.vivian.current_hp = 100
        self.ctx.final_value = 6  # Значение броска

        params = {"target": "self"}

        # Запускаем скрипт
        deal_damage_by_roll(self.ctx, params)

        # 100 - 6 = 94
        self.assertEqual(self.vivian.current_hp, 94)
        self.assertTrue(any("Roll Dmg" in msg for msg in self.ctx.log))

    # ==========================================
    # 2. Тест карты "Мазохизм" (Masochism)
    # ==========================================
    def test_card_masochism_heal(self):
        """
        Проверяем: [On Clash Lose] Восстанавливает 5 HP.
        JSON Params: { "type": "hp", "base": 5, "target": "self" } для restore_resource
        """
        self.vivian.current_hp = 50

        params = {"type": "hp", "base": 5, "target": "self"}

        # Патчим утилиты, так как restore_resource использует их для проверки условий
        with patch('logic.scripts.resources._check_conditions', return_value=True), \
                patch('logic.scripts.resources._get_targets', return_value=[self.vivian]), \
                patch('logic.scripts.resources._resolve_value', return_value=5):
            restore_resource(self.ctx, params)

            # 50 + 5 = 55
            self.assertEqual(self.vivian.current_hp, 55)
            self.assertTrue(any("💚" in msg for msg in self.ctx.log))

    # ==========================================
    # 3. Тест карты "Откусила!" (Bite)
    # ==========================================
    def test_card_bite_heal_by_roll(self):
        """
        Проверяем: [On Hit] Лечит на значение броска.
        JSON Params: { "type": "hp", "target": "self" } для restore_resource_by_roll
        """
        self.vivian.current_hp = 40
        self.ctx.final_value = 10  # Бросок

        params = {"type": "hp", "target": "self"}

        restore_resource_by_roll(self.ctx, params)

        # 40 + 10 = 50
        self.assertEqual(self.vivian.current_hp, 50)
        self.assertTrue(any("Roll Heal" in msg for msg in self.ctx.log))

    # ==========================================
    # 4. Тест карты "Кровопускание" (Bloodletting)
    # ==========================================
    def test_card_bloodletting_self_bleed(self):
        """
        Проверяем: [On Hit] Накладывает Bleed на себя.
        JSON Params: { "status": "bleed", "base": 1, "duration": 1, "delay": 1, "target": "self" }
        """
        params = {
            "status": "bleed",
            "base": 1,
            "duration": 1,
            "delay": 1,
            "target": "self"
        }

        with patch('logic.scripts.statuses._get_targets', return_value=[self.vivian]), \
                patch('logic.scripts.statuses._resolve_value', return_value=1):  # stack=1

            apply_status(self.ctx, params)

            # Проверяем, что вызвался add_status с delay=1
            # MockUnit в tests/mocks.py должен возвращать "Delayed", если delay > 0
            # Если логика mock отличается, проверяем лог
            self.assertTrue(
                any("Delayed" in msg for msg in self.ctx.log) or any("bleed" in str(self.vivian.statuses).lower()))

    # ==========================================
    # 5. Тест карты "Коллекция шрамов" (Scar Collection)
    # ==========================================
    def test_card_scar_collection_diff_damage(self):
        """
        Проверяем: [On Clash Win] Урон себе равен разнице бросков.
        JSON Params: { "target": "self" } для deal_damage_by_clash_diff
        """
        self.vivian.current_hp = 80

        # Сценарий: Вивьен выкинула 15, Враг 10. Разница 5.
        self.ctx.final_value = 15
        self.ctx.target_die_result = 10
        self.ctx.clash_diff = 5

        params = {"target": "self"}

        deal_damage_by_clash_diff(self.ctx, params)

        # 80 - 5 = 75
        self.assertEqual(self.vivian.current_hp, 75)
        self.assertTrue(any("Clash Diff" in msg for msg in self.ctx.log))


if __name__ == '__main__':
    unittest.main()