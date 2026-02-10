import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Добавляем путь к проекту
sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockDice, MockContext
from core.enums import DiceType

# Импортируем тестируемые классы
# (Предполагается, что вы сохранили код талантов в этот файл)
from logic.character_changing.talents.branch_6_smoker import (
    TalentHidingInSmoke,
    TalentSmokeUniversality,
    TalentAerialFoot, TalentSmokeScreen, TalentRecycling
)


class TestBranch6Smoker(unittest.TestCase):

    def setUp(self):
        """Настройка перед каждым тестом."""
        # Создаем мок-юнита 10 уровня
        self.unit = MockUnit(name="SmokerAgent", level=10, max_hp=100)

        # Настраиваем методы add/remove status, чтобы они работали как Spy
        # (выполняли реальную логику MockUnit и позволяли делать assert_called)
        self.unit.add_status = MagicMock(side_effect=self.unit.add_status)
        self.unit.remove_status = MagicMock(side_effect=self.unit.remove_status)

        # Мок для логгера
        self.log_func = MagicMock()

    # ==========================================
    # ТЕСТ 6.1: Скрываюсь в дыму
    # ==========================================
    def test_hiding_in_smoke_flag(self):
        """Проверка: В начале боя ставится флаг smoke_is_defensive."""
        talent = TalentHidingInSmoke()

        talent.on_combat_start(self.unit, log_func=self.log_func)

        # Проверяем память юнита
        self.assertTrue(
            self.unit.memory.get("smoke_is_defensive"),
            "Флаг smoke_is_defensive должен быть True"
        )
        # Проверяем лог
        self.log_func.assert_called()

    # ==========================================
    # ТЕСТ 6.2: Универсальность дыма
    # ==========================================
    def test_smoke_universality_no_choice(self):
        """Ошибка: Не выбран тип конвертации."""
        talent = TalentSmokeUniversality()

        result = talent.activate(self.unit, self.log_func, choice_key=None)

        self.assertFalse(result, "Должно вернуть False без выбора")
        self.unit.remove_status.assert_not_called()

    def test_smoke_universality_insufficient_smoke(self):
        """Ошибка: Не хватает дыма."""
        talent = TalentSmokeUniversality()
        # Даем 2 дыма (нужно 4 для Силы)
        self.unit.add_status("smoke", 2)

        result = talent.activate(self.unit, self.log_func, choice_key="str")

        self.assertFalse(result, "Не должно активироваться при нехватке ресурсов")
        self.unit.remove_status.assert_not_called()  # Дым не должен списаться

    def test_smoke_universality_success_str(self):
        """Успех: 4 Дыма -> 1 Сила."""
        talent = TalentSmokeUniversality()
        # Даем 10 дыма
        self.unit.add_status("smoke", 10)

        result = talent.activate(self.unit, self.log_func, choice_key="str")

        self.assertTrue(result, "Активация должна пройти успешно")

        # 1. Списание 4 дыма
        self.unit.remove_status.assert_called_with("smoke", 4)
        self.assertEqual(self.unit.get_status("smoke"), 6, "Остаток дыма должен быть 6")

        # 2. Начисление Силы (attack_power_up) на 3 раунда
        self.unit.add_status.assert_called_with("attack_power_up", 1, duration=3)

    def test_smoke_universality_success_self_control(self):
        """Успех: 3 Дыма -> 5 Самообладания."""
        talent = TalentSmokeUniversality()
        self.unit.add_status("smoke", 5)

        result = talent.activate(self.unit, self.log_func, choice_key="self")

        self.assertTrue(result)

        # Списание 3 дыма
        self.unit.remove_status.assert_called_with("smoke", 3)
        # Начисление Самообладания (99 раундов)
        self.unit.add_status.assert_called_with("self_control", 5, duration=99)

    # ==========================================
    # ТЕСТ 6.3: Воздушная стопа
    # ==========================================
    # Патчим функцию get_base_roll_by_level там, где она ИМПОРТИРУЕТСЯ в файле талантов
    @patch("logic.character_changing.talents.branch_6_smoker.get_base_roll_by_level")
    def test_aerial_foot_dice_generation(self, mock_get_roll):
        """Проверка генерации кубиков уклонения от стаков дыма."""
        # Настраиваем мок: уровень вернет диапазон 4-8
        mock_get_roll.return_value = (4, 8)

        talent = TalentAerialFoot()

        # --- Сценарий 1: 0 Дыма (База) ---
        self.unit.statuses["smoke"] = 0
        self.unit.counter_dice = []  # Сброс

        talent.on_speed_rolled(self.unit, self.log_func)

        self.assertEqual(len(self.unit.counter_dice), 1, "Должен быть 1 базовый кубик")
        self.assertEqual(self.unit.counter_dice[0].dtype, DiceType.EVADE)
        self.assertEqual(self.unit.counter_dice[0].min_val, 4)

        # --- Сценарий 2: 5 Дыма (+1 бонус) ---
        self.unit.statuses["smoke"] = 5
        self.unit.counter_dice = []

        talent.on_speed_rolled(self.unit, self.log_func)

        self.assertEqual(len(self.unit.counter_dice), 2, "1 база + 1 бонус (5 дыма) = 2 кубика")

        # --- Сценарий 3: 10 Дыма (+2 бонуса) ---
        self.unit.statuses["smoke"] = 10
        self.unit.counter_dice = []

        talent.on_speed_rolled(self.unit, self.log_func)

        self.assertEqual(len(self.unit.counter_dice), 3, "1 база + 2 бонуса (10 дыма) = 3 кубика")

        # --- Сценарий 4: 20 Дыма (Кап бонуса +2) ---
        self.unit.statuses["smoke"] = 20
        self.unit.counter_dice = []

        talent.on_speed_rolled(self.unit, self.log_func)

        # Максимум бонусов = 2 (min(2, smoke // 5)), итого 3 кубика
        self.assertEqual(len(self.unit.counter_dice), 3, "Бонус не должен превышать +2 кубика")

    # ==========================================
    # ТЕСТ 6.3 (Опц): Дымовая завеса
    # ==========================================
    def test_smoke_screen_passive(self):
        """Проверка пассивного бонуса к акробатике."""
        talent = TalentSmokeScreen()

        # Сценарий 1: База
        self.unit.talents = []
        stats = talent.on_calculate_stats(self.unit)
        self.assertEqual(stats["acrobatics"], 5, "Базовая акробатика должна быть +5")

        # Сценарий 2: С апгрейдом 6.5 (self_preservation)
        self.unit.talents = ["self_preservation"]
        stats_upg = talent.on_calculate_stats(self.unit)
        self.assertEqual(stats_upg["acrobatics"], 7, "С апгрейдом 6.5 акробатика должна быть +7")

    def test_smoke_screen_active_basic(self):
        """Активка: Базовое наложение дыма и КД."""
        talent = TalentSmokeScreen()
        self.unit.talents = []
        self.unit.cooldowns = {}

        # Создаем врагов
        enemy1 = MockUnit(name="Enemy1")
        enemy2 = MockUnit(name="Enemy2")
        # Мокаем add_status для врагов (так как MockUnit по умолчанию Spy, можно и не мокать, если используем MockUnit из mocks.py)
        enemy1.add_status = MagicMock()
        enemy2.add_status = MagicMock()

        # Активируем
        result = talent.activate(self.unit, self.log_func, enemies=[enemy1, enemy2])

        self.assertTrue(result)

        # Проверка КД (база 4)
        self.assertEqual(self.unit.cooldowns.get("smoke_screen"), 3)

        # Проверка наложения (3 дыма)
        enemy1.add_status.assert_called_with("smoke", 3, duration=99)
        enemy2.add_status.assert_called_with("smoke", 3, duration=99)

    def test_smoke_screen_active_upgrades(self):
        """Активка: Усиленное наложение (6.5) и сниженный КД (6.7)."""
        talent = TalentSmokeScreen()
        # Добавляем оба апгрейда
        self.unit.talents = ["cleansing", "lung_processing"]
        self.unit.cooldowns = {}

        enemy = MockUnit(name="Enemy")
        enemy.add_status = MagicMock()

        result = talent.activate(self.unit, self.log_func, enemies=[enemy])

        self.assertTrue(result)

        # Проверка КД (4 - 1 = 3)
        self.assertEqual(self.unit.cooldowns.get("smoke_screen"), 2,
                         "КД должен быть снижен на 1 при наличии таланта 6.7")

        # Проверка наложения (5 дыма)
        enemy.add_status.assert_called_with("smoke", 5, duration=99)

    # ==========================================
    # ТЕСТ 6.4: Переработка
    # ==========================================
    def test_recycling_logic(self):
        """
        Проверка таланта 6.4 Переработка:
        - Неиспользованные кубики в конце раунда конвертируются в Дым (1 к 1).
        - Если кубиков нет, дым не начисляется.
        """
        talent = TalentRecycling()

        # Сценарий 1: Кубики потрачены (пустой список)
        self.unit.counter_dice = []
        talent.on_round_end(self.unit, self.log_func)

        self.unit.add_status.assert_not_called()

        # Сценарий 2: Осталось 3 кубика (например, враг не атаковал или мы уклонились)
        # Наполняем список мок-дайсами
        self.unit.counter_dice = [MockDice(), MockDice(), MockDice()]

        # Вызываем хук конца раунда
        talent.on_round_end(self.unit, self.log_func)

        # Проверки
        # 1. Должно добавиться 3 дыма
        self.unit.add_status.assert_called_with("smoke", 3, duration=99)

        # 2. Проверяем сообщение в логе
        self.log_func.assert_called_with(f"♻️ **{talent.name}**: Сохранено движений: 3. Превращены в +3 Дыма.")

    # ==========================================
    # ТЕСТ 6.5 (Опц): Очищение
    # ==========================================
    class TestTalentCleansing(unittest.TestCase):
        def setUp(self):
            """Настройка перед каждым тестом."""
            from logic.character_changing.talents.branch_6_smoker import TalentCleansing

            self.talent = TalentCleansing()

            # Создаем юнита с удобными для расчетов статами
            # Max HP = 500 -> 2% = 10 HP за 1 стак
            # Max Stagger = 100 -> 2% = 2 Stagger за 1 стак
            self.unit = MockUnit(name="Smoker", level=1, max_hp=500, max_stagger=100)

            # Устанавливаем текущие значения (пораненный юнит)
            self.unit.current_hp = 100
            self.unit.current_stagger = 20
            self.unit.current_sp = 50
            self.unit.max_sp = 100

            # Мокаем методы восстановления, чтобы проверить вызовы с правильными аргументами
            # side_effect позволяет методам реально менять значения, если нужно,
            # но для assert_called достаточно просто Mock
            self.unit.heal_hp = MagicMock(side_effect=self.unit.heal_hp)
            self.unit.restore_sp = MagicMock(side_effect=self.unit.restore_sp)
            self.log_func = MagicMock()

        def test_cleansing_trigger_success(self):
            """
            Проверка срабатывания при удалении Дыма.
            Условия: Удаляется 5 стаков Дыма.
            Ожидание:
            - HP: 5 * (2% от 500) = 5 * 10 = +50 HP.
            - Stagger: 5 * (2% от 100) = 5 * 2 = +10 Stagger.
            - SP: 5 * 2 = +10 SP.
            """
            smoke_removed = 5

            # Эмулируем вызов события (как будто remove_status сработал)
            self.talent.on_status_removed(self.unit, "smoke", smoke_removed, log_func=self.log_func)

            # 1. Проверка HP
            # Ожидаем вызов heal_hp(50, source=unit)
            self.unit.heal_hp.assert_called_with(50, source=self.unit)
            self.assertEqual(self.unit.current_hp, 150, "HP должно увеличиться на 50")

            # 2. Проверка Stagger
            # Было 20, +10 = 30
            self.assertEqual(self.unit.current_stagger, 30, "Stagger должен увеличиться на 10")

            # 3. Проверка SP
            # Ожидаем вызов restore_sp(10)
            self.unit.restore_sp.assert_called_with(10)
            self.assertEqual(self.unit.current_sp, 60, "SP должно увеличиться на 10")

            # 4. Проверка лога
            self.log_func.assert_called()

        def test_cleansing_ignore_other_status(self):
            """Проверка: Талант игнорирует удаление других статусов."""
            # Удаляем "burn" (Ожог)
            self.talent.on_status_removed(self.unit, "burn", 10, log_func=self.log_func)

            self.unit.heal_hp.assert_not_called()
            self.unit.restore_sp.assert_not_called()
            # Значения не изменились
            self.assertEqual(self.unit.current_hp, 100)

        def test_cleansing_minimum_values(self):
            """Проверка: Минимальное исцеление (если 2% < 1)."""
            # Юнит с маленьким ХП (например, 10 HP -> 2% = 0.2 -> должно быть 1)
            self.unit.max_hp = 10
            self.unit.max_stagger = 10

            smoke_removed = 1

            self.talent.on_status_removed(self.unit, "smoke", smoke_removed)

            # Должно восстановить минимум 1 HP и 1 Stagger
            self.unit.heal_hp.assert_called_with(1, source=self.unit)
            # 20 + 1 = 21
            self.assertEqual(self.unit.current_stagger, 21)

        # ==========================================
        # ТЕСТ 6.6: Опытный курильщик
        # ==========================================
        def test_experienced_smoker_logic(self):
            """
            Проверка таланта 6.6 Опытный курильщик:
            - Старт боя: +5 Дыма (или +8 с апгрейдом).
            - Лимит дыма: Увеличивается на 5.
            - Снижение урона: -20% (или -25% с апгрейдом).
            """
            from logic.character_changing.talents.branch_6_smoker import TalentExperiencedSmoker
            talent = TalentExperiencedSmoker()

            # --- Сценарий 1: Базовая версия ---
            self.unit.talents = []
            self.unit.memory = {}  # Чистая память

            # 1. Combat Start
            talent.on_combat_start(self.unit, self.log_func)

            # Проверка дыма
            self.unit.add_status.assert_called_with("smoke", 5, duration=99)
            # Проверка лимита в памяти
            self.assertEqual(self.unit.memory.get("smoke_limit_bonus"), 5)

            # 2. Incoming Damage (-20%)
            # 100 урона -> 80
            dmg = talent.modify_incoming_damage(self.unit, 100, "slash")
            self.assertEqual(dmg, 80)

            # --- Сценарий 2: С апгрейдом (6.10) ---
            self.unit.talents = ["smoke_and_mirrors"]
            self.unit.memory = {}  # Сброс
            self.unit.add_status.reset_mock()

            # 1. Combat Start
            talent.on_combat_start(self.unit, self.log_func)

            # Проверка дыма (+8)
            self.unit.add_status.assert_called_with("smoke", 8, duration=99)
            # Лимит все еще +5 (апгрейд влияет только на старт и резист)
            self.assertEqual(self.unit.memory.get("smoke_limit_bonus"), 5)

            # 2. Incoming Damage (-25%)
            # 100 урона -> 75
            dmg = talent.modify_incoming_damage(self.unit, 100, "slash")
            self.assertEqual(dmg, 75)

    # ==========================================
    # ТЕСТ 6.7: Обработка лёгких
    # ==========================================
    def test_lung_processing_mechanics(self):
        """
        Проверка таланта 6.7 Обработка лёгких:
        - Увеличивает лимит дыма на 5.
        - При 15+ дыма дает +2 Power и +30% урона.
        - При <15 дыма бонусов нет.
        """
        from logic.character_changing.talents.branch_6_smoker import TalentLungProcessing
        talent = TalentLungProcessing()
        self.unit.memory = {}

        # 1. Проверка лимита
        talent.on_combat_start(self.unit, self.log_func)
        self.assertEqual(self.unit.memory.get("smoke_limit_bonus"), 5)

        # --- Сценарий: Мало дыма (10) ---
        self.unit.statuses["smoke"] = 10

        # Power
        ctx_low = MockContext(self.unit, dice=MockDice())
        talent.on_roll(ctx_low)
        self.assertEqual(ctx_low.final_value, 0, "Не должно быть бонуса силы при <15 дыма")

        # Damage
        dmg_low = talent.modify_outgoing_damage(self.unit, 100, "slash")
        self.assertEqual(dmg_low, 100, "Не должно быть бонуса урона при <15 дыма")

        # --- Сценарий: Много дыма (15) ---
        self.unit.statuses["smoke"] = 15

        # Power
        ctx_high = MockContext(self.unit, dice=MockDice())
        talent.on_roll(ctx_high)
        self.assertEqual(ctx_high.final_value, 2, "Должен быть бонус +2 силы при 15+ дыма")
        self.assertIn("Lung Processing", ctx_high.log[0])

        # Damage (+30%)
        dmg_high = talent.modify_outgoing_damage(self.unit, 100, "slash")
        self.assertEqual(dmg_high, 130, "Урон должен быть увеличен на 30% (130)")

        # # ==========================================
        # # ТЕСТ 6.7 (Опц): В Нарнию и обратно
        # # ==========================================
        # def test_to_narnia_logic(self):
        #     from logic.character_changing.talents.branch_6_smoker import TalentToNarnia
        #
        #     talent = TalentToNarnia()
        #     self.unit.memory = {}
        #
        #     enemy = MockUnit(name="Enemy")
        #     enemy.add_status = MagicMock()
        #
        #     ally = MockUnit(name="Ally")
        #     ally.add_status = MagicMock()
        #
        #     # === ВАЖНО: Мокаем метод is_enemy ===
        #     # Мы говорим тесту: "Когда талант спросит is_enemy(unit, enemy), верни True"
        #     # "А когда спросит is_enemy(unit, ally), верни False"
        #     talent.is_enemy = MagicMock(side_effect=lambda u, t: t == enemy)
        #
        #     # 1. Наложение на ВРАГА (должно сработать)
        #     talent.on_status_applied(
        #         self.unit, "smoke", 3, target=enemy, log_func=self.log_func
        #     )
        #
        #     enemy.add_status.assert_any_call("bind", 5, duration=1)
        #     self.assertIn(id(enemy), self.unit.memory["narnia_victims"])
        #
        #     # 2. Наложение на СОЮЗНИКА (не должно сработать)
        #     talent.on_status_applied(
        #         self.unit, "smoke", 3, target=ally, log_func=self.log_func
        #     )
        #
        #     ally.add_status.assert_not_called()
        #
        #     # 3. Повтор на врага (не должно сработать)
        #     enemy.add_status.reset_mock()
        #     talent.on_status_applied(
        #         self.unit, "smoke", 3, target=enemy, log_func=self.log_func
        #     )
        #     enemy.add_status.assert_not_called()

if __name__ == '__main__':
    unittest.main()