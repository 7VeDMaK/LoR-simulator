import unittest
from unittest.mock import MagicMock
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType


# === MOCKS (Ваши реальные классы) ===

class MockDice:
    def __init__(self, val, dtype, is_counter=False):
        self.val = val
        self.dtype = dtype
        self.is_counter = is_counter
        self.min_val = val
        self.max_val = val


class MockUnit:
    def __init__(self, name):
        self.name = name
        self.counter_dice = []
        self.talents = set()  # Множество ID изученных талантов
        self.level = 1  # Уровень для скейлинга силы кубика


# === РЕАЛЬНАЯ ЛОГИКА ТАЛАНТА (Вставьте это в logic/mechanics/talents.py) ===

def apply_counter_logic_talent(unit):
    """
    Реализация Таланта 3.2 'Контр-логика'.
    Проверяет наличие базы и апгрейдов в unit.talents.
    Генерирует кубики и кладет их в unit.counter_dice.
    """
    # ID талантов
    TALENT_BASE = "3.2"
    UPGRADE_1 = "3.5"  # Вопреки всему
    UPGRADE_2 = "3.8"  # Выживший
    UPGRADE_3 = "3.10"  # Прилив сил

    if TALENT_BASE not in unit.talents:
        return  # Талант не изучен

    # 1. Считаем количество кубиков
    dice_count = 1  # База

    if UPGRADE_1 in unit.talents: dice_count += 1
    if UPGRADE_2 in unit.talents: dice_count += 1
    if UPGRADE_3 in unit.talents: dice_count += 1

    # 2. Расчет силы кубика (скейлинг от уровня, например)
    # Формула: 4 + (Уровень // 2). Примерно 5-10.
    base_power = 4 + (unit.level // 2)

    print(f"[Talent] 🛡️ Applying 'Counter Logic' for {unit.name}. Count: {dice_count}, Power: {base_power}")

    # 3. Генерация и выдача
    new_dice = []
    for _ in range(dice_count):
        d = MockDice(base_power, DiceType.BLOCK, is_counter=True)
        new_dice.append(d)

    # Добавляем в общую очередь
    unit.counter_dice.extend(new_dice)


# === ТЕСТЫ ===

class TestRealTalentLogic(unittest.TestCase):

    def test_base_talent_only(self):
        """Проверка: Только базовый талант (3.2) -> 1 кубик."""
        u = MockUnit("Novice Zafiel")
        u.talents.add("3.2")

        apply_counter_logic_talent(u)

        self.assertEqual(len(u.counter_dice), 1)
        print("✅ Base Talent: 1 Die received.")

    def test_partial_upgrade(self):
        """Проверка: База + 1 апгрейд (3.2 + 3.5) -> 2 кубика."""
        u = MockUnit("Trained Zafiel")
        u.talents.add("3.2")
        u.talents.add("3.5")  # +1 кубик

        apply_counter_logic_talent(u)

        self.assertEqual(len(u.counter_dice), 2)
        print("✅ Partial Upgrade: 2 Dice received.")

    def test_full_upgrade_max_power(self):
        """Проверка: Фулл прокачка (3.2, 3.5, 3.8, 3.10) -> 4 кубика."""
        u = MockUnit("Master Zafiel")
        u.level = 10  # Проверим скейлинг силы

        # Добавляем все таланты ветки
        u.talents.update(["3.2", "3.5", "3.8", "3.10"])

        apply_counter_logic_talent(u)

        # Проверка количества
        self.assertEqual(len(u.counter_dice), 4, "Должно быть 4 кубика (1 база + 3 апгрейда)")

        # Проверка силы (4 + 10//2 = 9)
        first_die = u.counter_dice[0]
        self.assertEqual(first_die.min_val, 9, "Сила кубика должна быть 9 на 10 уровне.")
        self.assertTrue(first_die.is_counter, "Кубик должен быть помечен как Counter.")

        print(f"✅ Full Upgrade: 4 Dice received with Power {first_die.min_val}.")

    def test_no_talent(self):
        """Проверка: Талант не изучен -> 0 кубиков."""
        u = MockUnit("Civilian")
        # u.talents пусто

        apply_counter_logic_talent(u)

        self.assertEqual(len(u.counter_dice), 0)
        print("✅ No Talent: 0 Dice.")


if __name__ == '__main__':
    unittest.main()