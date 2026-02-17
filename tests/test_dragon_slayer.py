# tests/test_items/test_dragon_slayer.py
import unittest
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType
from tests.mocks import MockUnit, MockDice, MockContext
from logic.character_changing.passives.equipment_passives import PassiveDragonSlab


# Расширяем MockUnit, чтобы он соответствовал ожиданиям кода пассивки
class DragonSlayerMockUnit(MockUnit):
    @property
    def hp(self):
        return self.current_hp

    @hp.setter
    def hp(self, value):
        self.current_hp = value


class TestDragonSlayer(unittest.TestCase):
    def setUp(self):
        self.passive = PassiveDragonSlab()
        # Используем расширенный мок
        self.unit = DragonSlayerMockUnit(name="Guts", max_hp=100)

        # Явная инициализация всех полей, которые ищет код пассивки
        self.unit.stats = {"strength": 0, "endurance": 0}
        self.unit.attributes = {"strength": 0, "endurance": 0}

        self.target = MockUnit(name="Eclipse Demon")
        self.target.resistances = {"slash": 0.5, "blunt": 1.5}

    def test_weight_mechanic_combined_stats(self):
        """Проверка суммирования Силы и Стойкости (strength + endurance)."""
        self.passive.on_round_start(self.unit)

        # 10 Силы + 10 Стойкости = 20 (лимит 1 удар)
        self.unit.stats["strength"] = 10
        self.unit.stats["endurance"] = 10

        ctx1 = MockContext(self.unit, self.target, MockDice(dtype=DiceType.SLASH))
        self.passive.on_roll(ctx1)
        # Проверяем, что удар не провалился (не -9999)
        self.assertGreater(ctx1.final_value, -100)

        ctx2 = MockContext(self.unit, self.target, MockDice(dtype=DiceType.SLASH))
        self.passive.on_roll(ctx2)
        # Второй удар должен получить штраф
        self.assertLess(ctx2.final_value, -1000)

    def test_berserk_mechanic(self):
        """Проверка работы бонусов при низком HP (использование unit.hp)."""
        self.passive.on_round_start(self.unit)
        self.unit.stats["strength"] = 100  # Убираем ограничение веса

        # Устанавливаем 10% здоровья
        self.unit.hp = 10
        ctx = MockContext(self.unit, self.target, MockDice(dtype=DiceType.SLASH))

        self.passive.on_roll(ctx)

        # Проверяем наличие бонусов в логах или итоговом значении
        self.assertGreaterEqual(ctx.damage_multiplier, 1.4, "Множитель урона не вырос")
        # База +3 и бонус от потери 90% HP
        self.assertGreaterEqual(ctx.final_value, 6)

    def test_adaptation(self):
        """Проверка автоматической смены типа урона."""
        dice = MockDice(dtype=DiceType.SLASH)
        ctx = MockContext(self.unit, self.target, dice)

        self.passive.on_hit(ctx)

        # У цели резист к slash (0.5), но слабость к blunt (1.5). Должно смениться.
        self.assertEqual(dice.dtype, DiceType.BLUNT)


if __name__ == '__main__':
    unittest.main()