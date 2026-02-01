import unittest
import sys
import os
import logging

# Добавляем путь к проекту
sys.path.append(os.getcwd())

# Импорт наших моков
from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType

# Импорт тестируемой логики (Убедись, что файл существует!)
from logic.character_changing.talents.branch_3_tireless import TalentBigGuy, TalentDefense, \
    TalentCommendableConstitution, TalentRock, TalentDespiteAdversities


class TestBranch3Tireless(unittest.TestCase):

    def setUp(self):
        """Обновленный setUp с инициализацией всех талантов."""
        logging.getLogger("streamlit").setLevel(logging.ERROR)

        self.unit = MockUnit(name="Tester", level=10, max_hp=100)

        self.talent_defense = TalentDefense()
        self.talent_big_guy = TalentBigGuy()
        self.talent_constitution = TalentCommendableConstitution()
        self.talent_rock = TalentRock()
        # Инициализируем новый талант
        self.talent_adversities = TalentDespiteAdversities()

    # ============================================
    # ТЕСТ 3.1: ЗДОРОВЯК
    # ============================================
    def test_big_guy_stats(self):
        """Проверка бонуса к HP от таланта Здоровяк."""
        stats = self.talent_big_guy.on_calculate_stats(self.unit)

        # Ожидаем, что вернется словарь с ключом max_hp_pct = 15
        self.assertIn("max_hp_pct", stats)
        self.assertEqual(stats["max_hp_pct"], 15, "Бонус HP должен быть 15%")

    # ============================================
    # ТЕСТ 3.2: ОБОРОНА (Генерация кубиков)
    # ============================================
    def test_defense_basic_generation(self):
        """Базовая защита должна давать 1 кубик."""
        self.unit.talents = []  # Нет апгрейдов

        self.talent_defense.on_speed_rolled(self.unit, log_func=None)

        # Проверяем кол-во кубиков
        self.assertEqual(len(self.unit.counter_dice), 1)
        # Проверяем тип кубика
        self.assertEqual(self.unit.counter_dice[0].dtype, DiceType.BLOCK)
        # Проверяем флаг
        self.assertIn("talent_defense_die", self.unit.counter_dice[0].flags)

    def test_defense_full_upgrade(self):
        """Полная прокачка должна давать 4 кубика."""
        self.unit.talents = ["despite_adversities", "survivor", "surge_of_strength"]

        self.talent_defense.on_speed_rolled(self.unit, log_func=None)

        self.assertEqual(len(self.unit.counter_dice), 4, "Должно быть 4 кубика при полной прокачке")

    # ============================================
    # ТЕСТ 3.5: Вопреки всему (Победа в блоке)
    # ============================================
    def test_clash_win_effect(self):
        """Победа защитным кубиком должна давать Protection."""
        self.unit.talents = ["despite_adversities"]

        # Создаем кубик с нужным флагом
        dice = MockDice(flags=["talent_defense_die"])
        ctx = MockContext(self.unit, dice=dice)

        # Эмулируем победу
        self.talent_defense.on_clash_win(ctx)

        # Проверяем статус
        current_prot = self.unit.statuses.get("protection", 0)
        self.assertEqual(current_prot, 1, "Должен быть наложен 1 стак Protection")

    def test_clash_win_no_talent(self):
        """Если таланта нет, бонус не дается."""
        self.unit.talents = []  # Пусто

        dice = MockDice(flags=["talent_defense_die"])
        ctx = MockContext(self.unit, dice=dice)

        self.talent_defense.on_clash_win(ctx)

        self.assertIsNone(self.unit.statuses.get("protection"), "Без таланта бонус не положен")

    # ============================================
    # ТЕСТ 3.3: Похвальное телосложение
    # ============================================

    def test_constitution_passive_stats(self):
        """Проверка: +3 к Endurance."""
        stats = self.talent_constitution.on_calculate_stats(self.unit)
        self.assertEqual(stats.get("endurance"), 3, "Должно давать +3 Endurance")

    def test_constitution_round_start_basic(self):
        """Начало раунда: +1 Protection (без синергий)."""
        self.unit.talents = []
        self.talent_constitution.on_round_start(self.unit, log_func=None)

        val = self.unit.statuses.get("protection", 0)
        self.assertEqual(val, 1, "Базовый эффект должен давать 1 Protection")

    def test_constitution_round_start_synergy(self):
        """Начало раунда: +2 Protection (если есть Survivor)."""
        self.unit.talents = ["survivor"]  # Синергия 3.8
        self.talent_constitution.on_round_start(self.unit, log_func=None)

        val = self.unit.statuses.get("protection", 0)
        self.assertEqual(val, 2, "С талантом Survivor должно быть 2 Protection")

    def test_constitution_active_heal(self):
        """Активка: Лечение 20%."""
        # 1. Раним юнита
        self.unit.current_hp = 50

        # 2. Активируем
        self.talent_constitution.activate(self.unit, log_func=None)

        # 3. Проверяем
        # 20% от 100 = 20. Было 50, стало 70.
        self.assertEqual(self.unit.current_hp, 70, "Должно восстановить 20% HP")

        # 4. Проверяем КД
        cd = self.unit.cooldowns.get("commendable_constitution")
        self.assertEqual(cd, 99, "Способность должна уйти в вечный КД (99)")

    def test_constitution_active_synergy(self):
        """Активка: Лечение 30% (если есть Tough as Steel)."""
        self.unit.talents = ["tough_as_steel"]  # Синергия 3.7
        self.unit.current_hp = 50

        self.talent_constitution.activate(self.unit, log_func=None)

        # 30% от 100 = 30. Было 50, стало 80.
        self.assertEqual(self.unit.current_hp, 80, "С синергией должно восстановить 30% HP")

    def test_constitution_cooldown_lock(self):
        """Нельзя использовать, если на КД."""
        self.unit.current_hp = 50
        # Ставим КД вручную
        self.unit.cooldowns["commendable_constitution"] = 99

        result = self.talent_constitution.activate(self.unit, log_func=None)

        self.assertFalse(result, "Функция должна вернуть False, если на КД")
        self.assertEqual(self.unit.current_hp, 50, "ХП не должно измениться")

    # ============================================
    # ТЕСТ 3.4: Скала (Rock)
    # ============================================

    def test_rock_reflection_success(self):
        """Успешное отражение: Урон 0, Кубик НЕ Блок."""
        attacker = MockUnit(name="Attacker", max_hp=100)
        talent_rock = TalentRock()

        # 1. Мы атакуем НЕ блоком (например, парируем атакой или уклоняемся, или просто стоим)
        self.unit.current_die = MockDice(DiceType.SLASH)

        # 2. Вызываем триггер:
        # amount=0 (урон поглощен броней), raw_amount=20 (исходный удар)
        talent_rock.on_take_damage(
            self.unit,
            amount=0,
            source=attacker,
            raw_amount=20,
            log_func=None
        )

        # 3. Проверяем: Атакующий должен получить 20 урона (100 - 20 = 80)
        self.assertEqual(attacker.current_hp, 80, "Весь raw_amount должен отразиться")

    def test_rock_no_reflect_on_block(self):
        """Нет отражения, если урон сдержан Блоком."""
        attacker = MockUnit(name="Attacker", max_hp=100)
        talent_rock = TalentRock()

        # 1. Мы защищаемся БЛОКОМ
        self.unit.current_die = MockDice(DiceType.BLOCK)

        # 2. Урон 0 (блок сработал)
        talent_rock.on_take_damage(
            self.unit,
            amount=0,
            source=attacker,
            raw_amount=20
        )

        # 3. Проверяем: Атакующий цел
        self.assertEqual(attacker.current_hp, 100, "Урон не должен отражаться при активном Блоке")

    def test_rock_no_reflect_on_damage(self):
        """Нет отражения, если хоть 1 ед. урона прошла."""
        attacker = MockUnit(name="Attacker", max_hp=100)
        talent_rock = TalentRock()

        self.unit.current_die = MockDice(DiceType.SLASH)

        # 2. Прошел 1 урон (броня не справилась полностью)
        talent_rock.on_take_damage(
            self.unit,
            amount=1,
            source=attacker,
            raw_amount=20
        )

        # 3. Проверяем: Атакующий цел
        self.assertEqual(attacker.current_hp, 100, "Урон не должен отражаться, если защита пробита")

    # ============================================
    # ТЕСТ 3.5: Не взирая на невзгоды
    # ============================================

    def test_adversities_multiplier_basic(self):
        """Проверка: Снижение множителя Stagger до 1.5 (база)."""
        self.unit.talents = []  # Нет синергии

        # Симулируем запрос от движка. Базовый множитель обычно 2.0
        new_mult = self.talent_adversities.modify_stagger_damage_multiplier(self.unit, 2.0)

        self.assertEqual(new_mult, 1.5, "Без синергии множитель должен стать 1.5")

    def test_adversities_multiplier_synergy(self):
        """Проверка: Снижение множителя Stagger до 1.25 (с синергией)."""
        # Добавляем талант 3.10 "Прилив сил" (surge_of_strength)
        self.unit.talents = ["surge_of_strength"]

        new_mult = self.talent_adversities.modify_stagger_damage_multiplier(self.unit, 2.0)

        self.assertEqual(new_mult, 1.25, "С талантом Surge of Strength множитель должен быть 1.25")

    # def test_adversities_counter_in_stagger(self):
    #     """Проверка: Разрешено ли использовать контр-кубики в оглушении."""
    #
    #     # 1. Функция проверки (копия вашей логики для теста)
    #     def _can_use_while_staggered(unit):
    #         if hasattr(unit, "iter_mechanics"):
    #             for mech in unit.iter_mechanics():
    #                 # Проверяем, есть ли у механики нужный метод и возвращает ли он True
    #                 if hasattr(mech, "can_use_counter_die_while_staggered") and \
    #                         mech.can_use_counter_die_while_staggered(unit):
    #                     return True
    #         return False
    #
    #     # СЦЕНАРИЙ А: Обычный юнит (Без таланта)
    #     self.unit.passives = []  # Очищаем пассивки
    #     result_basic = _can_use_while_staggered(self.unit)
    #     self.assertFalse(result_basic, "Обычный юнит НЕ должен бить в стаггере")
    #
    #     # СЦЕНАРИЙ Б: Юнит с талантом 'Не взирая на невзгоды'
    #     # Добавляем объект таланта в список пассивок (чтобы iter_mechanics его нашел)
    #     self.unit.passives.append(self.talent_adversities)
    #
    #     result_talent = _can_use_while_staggered(self.unit)
    #     self.assertTrue(result_talent, "С талантом Adversities юнит ДОЛЖЕН бить в стаггере")
# Эта часть позволяет запускать файл напрямую
if __name__ == '__main__':
    unittest.main()