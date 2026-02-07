import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Добавляем корень проекта
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType

# Импортируем скрипты, которые используются в картах
from logic.scripts.statuses import apply_status, consume_status_apply
from logic.scripts.card_dice import add_preset_dice, share_dice_with_hand


class MockCard:
    def __init__(self, name="Test Card", flags=None):
        self.name = name
        self.dice_list = []
        self.flags = flags if flags else []


class TestAxisCards(unittest.TestCase):

    def setUp(self):
        self.axis = MockUnit(name="Axis", max_hp=100)
        self.enemy = MockUnit(name="Enemy", max_hp=100)
        self.ctx = MockContext(self.axis, target=self.enemy)
        self.ctx.log = []

    # ==========================================
    # 1. Тест карты "Сияние" (Radiance)
    # ==========================================
    def test_card_radiance_win_con(self):
        """
        Проверяем: [On Clash Win] Накладывает 1 'Win Condition' на врага.
        JSON Params: { "status": "win_condition", "base": 1, "duration": 1, "target": "target" }
        """
        # Параметры из JSON
        params = {"status": "win_condition", "base": 1, "duration": 1, "target": "target"}

        # Эмулируем вызов скрипта
        # В реальном движке это делает executor, здесь мы вызываем функцию напрямую
        apply_status(self.ctx, params)

        # Проверка
        self.assertEqual(self.enemy.get_status("win_condition"), 1)
        # Или если очень хочется проверить лог:
        self.assertTrue(any("Win_condition" in msg for msg in self.ctx.log))

    # ==========================================
    # 2. Тест карты "Сюжетная Броня" (Plot Armor)
    # ==========================================
    def test_card_plot_armor_debuff(self):
        """
        Проверяем: [On Clash] Снимает 1 WinCon -> Враг получает дебаффы.
        JSON Params: { "consume_status": "win_condition", "apply_status": "fragile", ... }
        """
        # Подготовка: даем врагу WinCon
        self.enemy.add_status("win_condition", 1)

        # Параметры из JSON (для Fragile)
        params_fragile = {
            "consume_status": "win_condition",
            "apply_status": "fragile",
            "apply_amount": 2,
            "apply_target": "target"
        }

        # Параметры из JSON (для Bind) - вызовется вторым, но статус уже снят?
        # ВАЖНО: В вашем JSON два скрипта consume_status.
        # Если первый снимет статус, второй не сработает, если у врага всего 1 WinCon!
        # Это может быть баг в дизайне карты, тест это покажет.

        # Сценарий А: У врага 1 WinCon. Сработает только первый эффект.
        with patch('logic.scripts.statuses._get_targets', return_value=[self.enemy]):
            consume_status_apply(self.ctx, params_fragile)

            self.assertEqual(self.enemy.get_status("win_condition"), 0)  # Снято
            self.assertEqual(self.enemy.get_status("fragile"), 2)  # Наложено

            # Попробуем второй скрипт (Bind)
            params_bind = {
                "consume_status": "win_condition",
                "apply_status": "bind",
                "apply_amount": 2,
                "apply_target": "target"
            }
            consume_status_apply(self.ctx, params_bind)

            # Bind НЕ должен наложиться, т.к. WinCon уже 0
            self.assertEqual(self.enemy.get_status("bind"), 0)

    def test_card_plot_armor_enough_stacks(self):
        """
        Проверяем: Если WinCon достаточно (2), сработают оба эффекта.
        """
        self.enemy.add_status("win_condition", 2)

        with patch('logic.scripts.statuses._get_targets', return_value=[self.enemy]):
            # 1. Fragile
            consume_status_apply(self.ctx, {
                "consume_status": "win_condition", "apply_status": "fragile",
                "apply_amount": 2, "apply_target": "target"
            })
            # 2. Bind
            consume_status_apply(self.ctx, {
                "consume_status": "win_condition", "apply_status": "bind",
                "apply_amount": 2, "apply_target": "target"
            })

            self.assertEqual(self.enemy.get_status("win_condition"), 0)  # 2 - 1 - 1
            self.assertEqual(self.enemy.get_status("fragile"), 2)
            self.assertEqual(self.enemy.get_status("bind"), 2)

    # ==========================================
    # 3. Тест карты "Мелкие неудачи" (Minor Setbacks)
    # ==========================================
    def test_card_minor_setbacks_dice_spawn(self):
        """
        Проверяем: [On Use] Создает 3 доп. кубика (Slash, Pierce, Blunt).
        """
        card = MockCard("Minor Setbacks")
        # Исходно 1 кубик (Block 3-6 из JSON)
        card.dice_list = [MockDice(DiceType.BLOCK, 3, 6)]
        self.axis.current_card = card

        # Параметры из JSON
        params = {
            "dice": [
                {"min": 4, "max": 8, "type": "Slash"},
                {"min": 4, "max": 8, "type": "Pierce"},
                {"min": 4, "max": 8, "type": "Blunt"}
            ]
        }

        add_preset_dice(self.ctx, params)

        # Было 1, добавили 3 -> Стало 4
        self.assertEqual(len(card.dice_list), 4)

        # Проверяем типы добавленных кубиков
        self.assertEqual(card.dice_list[1].dtype, DiceType.SLASH)
        self.assertEqual(card.dice_list[2].dtype, DiceType.PIERCE)
        self.assertEqual(card.dice_list[3].dtype, DiceType.BLUNT)

    def test_card_minor_setbacks_unity(self):
        """
        Проверяем: [On Use] Раздает Блок (первый кубик) картам Unity в руке.
        """
        # Карта, которую играем (Minor Setbacks)
        played_card = MockCard("Minor Setbacks", flags=["unity"])
        block_die = MockDice(DiceType.BLOCK, 3, 6)
        played_card.dice_list = [block_die]

        self.axis.current_card = played_card

        # Другая карта в руке с Unity
        ally_card = MockCard("Ally Card", flags=["unity"])

        # Карта без Unity
        other_card = MockCard("Other Card", flags=[])

        self.axis.hand = [played_card, ally_card, other_card]

        # Вызов скрипта (параметры из JSON)
        share_dice_with_hand(self.ctx, {"flag": "unity"})

        # Ally card должна получить кубик
        self.assertEqual(len(ally_card.dice_list), 1)
        self.assertEqual(ally_card.dice_list[0].dtype, DiceType.BLOCK)

        # Other card не должна
        self.assertEqual(len(other_card.dice_list), 0)


if __name__ == '__main__':
    unittest.main()