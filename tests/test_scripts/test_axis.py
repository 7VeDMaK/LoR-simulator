import unittest
import sys
import os
from copy import deepcopy
from unittest.mock import MagicMock

# Добавляем корень в путь
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType
from core.dice import Dice

# Импортируем скрипты Аксис
from logic.scripts.axis_scripts import (
    axis_radiance_clash_win, axis_mcguffin_on_hit,
    axis_plot_armor_clash, axis_ex_machina_clash,
    axis_small_failures_use, axis_apply_unity
)


class MockCard:
    def __init__(self, name="Test Card", cid="test_id"):
        self.name = name
        self.id = cid
        self.dice_list = []
        self.flags = []


class TestAxisScripts(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnit(name="Axis", max_hp=100)
        self.target = MockUnit(name="Target", max_hp=100)
        self.dice = MockDice(DiceType.SLASH)
        self.ctx = MockContext(self.unit, target=self.target, dice=self.dice)

        # Для скриптов Юнити
        self.card = MockCard("Axis Card", "axis_card")
        self.ctx.card = self.card
        self.unit.hand = []

    # ==========================================
    # 1. Win Condition (Радианс и МакГаффин)
    # ==========================================
    def test_axis_radiance_wincon(self):
        """Сияние: Накладывает WinCon на 1 ход."""
        axis_radiance_clash_win(self.ctx)
        self.assertEqual(self.target.get_status("win_condition"), 1)
        self.assertIn("✨ **Сияние**", self.ctx.log[0])

    def test_axis_mcguffin_wincon(self):
        """МакГаффин: Накладывает WinCon навсегда (duration 99)."""
        axis_mcguffin_on_hit(self.ctx)
        self.assertEqual(self.target.get_status("win_condition"), 1)
        self.assertIn("📦 **МакГаффин**", self.ctx.log[0])

    # ==========================================
    # 2. Потребление WinCon (Сюжетная Броня)
    # ==========================================
    def test_axis_plot_armor_consumption(self):
        """Сюжетная Броня: Тратит WinCon и дебаффает врага."""
        self.target.add_status("win_condition", 1)

        axis_plot_armor_clash(self.ctx)

        # Должен быть 0, так как потратили
        self.assertEqual(self.target.get_status("win_condition"), 0)
        # Должны появиться дебаффы
        self.assertEqual(self.target.get_status("fragile"), 2)
        self.assertEqual(self.target.get_status("bind"), 2)
        self.assertIn("🛡️ **Сюжетная Броня**", self.ctx.log[0])

    # ==========================================
    # 3. Командная работа (Экс Махина)
    # ==========================================
    def test_axis_ex_machina_ally_buff(self):
        """Экс Махина: Баффает союзника при трате WinCon."""
        self.target.add_status("win_condition", 1)

        # Настраиваем "сцену" и "команду"
        ally = MockUnit(name="Summon")
        self.unit.team_id = 0
        self.unit.scene = MagicMock()
        # scene.teams[0] вернет список юнитов
        self.unit.scene.teams = {0: [self.unit, ally]}

        axis_ex_machina_clash(self.ctx)

        # Проверяем баффы на союзнике
        self.assertEqual(ally.get_status("strength"), 3)
        self.assertEqual(ally.get_status("haste"), 3)
        self.assertEqual(self.target.get_status("win_condition"), 0)

    # ==========================================
    # 4. Юнити и Синергия
    # ==========================================
    def test_axis_small_failures_adds_dice(self):
        """Мелкие неудачи: Добавляют 3 кубика к карте."""
        initial_count = len(self.card.dice_list)
        axis_small_failures_use(self.ctx)

        self.assertEqual(len(self.card.dice_list), initial_count + 3)
        self.assertEqual(self.card.dice_list[-3].dtype, DiceType.SLASH)  # Меч
        self.assertEqual(self.card.dice_list[-1].dtype, DiceType.BLUNT)  # Кулак

    def test_axis_apply_unity_mechanic(self):
        """Юнити: Раздает кубик другим картам 'unity' в руке."""
        # Настраиваем руку: одна карта с Юнити, одна без
        unity_card = MockCard("Unity Ally", "ally_1")
        unity_card.flags = ["unity"]
        normal_card = MockCard("Normal Card", "norm_1")

        self.unit.hand = [self.ctx.card, unity_card, normal_card]

        # Аксис играет "Мелкие неудачи"
        self.ctx.card.id = "axis_minor_setbacks"

        axis_apply_unity(self.ctx)

        # Карта Юнити должна получить кубик Блока (от Неудач)
        self.assertEqual(len(unity_card.dice_list), 1)
        self.assertEqual(unity_card.dice_list[0].dtype, DiceType.BLOCK)

        # Обычная карта ничего не должна получить
        self.assertEqual(len(normal_card.dice_list), 0)


if __name__ == '__main__':
    unittest.main()