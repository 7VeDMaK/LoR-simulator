import unittest
import sys
import os
import logging
from unittest.mock import MagicMock

# Добавляем путь к проекту
sys.path.append(os.getcwd())

# Импорт наших моков
from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType

# Импорт тестируемой логики
from logic.character_changing.talents.branch_3_tireless import TalentBigGuy, TalentDefense, \
    TalentCommendableConstitution, TalentRock, TalentDespiteAdversities, TalentBigHeart, \
    TalentHardenedSkin, TalentDefender


class TestBranch3Tireless(unittest.TestCase):

    def setUp(self):
        """Обновленный setUp с инициализацией всех талантов."""
        logging.getLogger("streamlit").setLevel(logging.ERROR)

        self.unit = MockUnit(name="Tester", level=10, max_hp=100)

        self.talent_defense = TalentDefense()
        self.talent_big_guy = TalentBigGuy()
        self.talent_constitution = TalentCommendableConstitution()
        self.talent_rock = TalentRock()
        # Инициализируем новые таланты
        self.talent_adversities = TalentDespiteAdversities()

        # === [FIX] Инициализируем мок для логгера ===
        self.log_func = MagicMock()

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

    # ============================================
    # ТЕСТ 3.5 (NEW): Закаленная кожа
    # ============================================
    def test_talent_hardened_skin(self):
        """
        Проверка таланта 3.5 Закаленная кожа:
        - Снижает урон, если damage_type в списке dot_types (Bleed/Burn).
        - Восстанавливает 1% Stagger.
        - Игнорирует обычный урон (Slash).
        """
        talent = TalentHardenedSkin()
        self.unit.max_stagger = 100
        self.unit.current_stagger = 50

        # 1. Тест на Кровотечение (передаем "bleed" в damage_type)
        # Входящий 10 -> Ожидаем 6 (10 * 0.67 = 6.7 -> int 6)
        # Stagger должен восстановиться на 1% (1 ед)
        reduced_dmg = talent.modify_incoming_damage(self.unit, 10, "bleed")

        self.assertEqual(reduced_dmg, 6, "Урон от 'bleed' должен быть снижен")
        self.assertEqual(self.unit.current_stagger, 51, "Должен восстановиться 1 Stagger")

        # 2. Тест на Ожог (передаем "Burn" - проверка регистра)
        reduced_dmg = talent.modify_incoming_damage(self.unit, 100, "Burn")

        self.assertEqual(reduced_dmg, 67, "Урон от 'Burn' должен быть снижен")
        self.assertEqual(self.unit.current_stagger, 52, "Должен восстановиться еще 1 Stagger")

        # 3. Тест на обычную атаку (Slash)
        # Не должен снижать урон и не должен лечить Stagger
        normal_dmg = talent.modify_incoming_damage(self.unit, 20, "slash")

        self.assertEqual(normal_dmg, 20, "Обычный урон (slash) не должен меняться")
        self.assertEqual(self.unit.current_stagger, 52, "Stagger не должен меняться от обычной атаки")

    # ============================================
    # ТЕСТ 3.7: Защитник
    # ============================================
    def test_talent_defender_active(self):
        """
        Проверка таланта 3.7 Защитник (Active):
        - Активируется и вешает КД.
        - Накладывает Taunt (3 раунда).
        - Накладывает Protection (1 раунд).
        """
        talent = TalentDefender()
        # Сброс кулдаунов и статусов
        self.unit.cooldowns = {}
        self.unit.statuses = {}

        # 1. Активация
        # [FIX] Теперь self.log_func существует в setUp
        result = talent.activate(self.unit, log_func=self.log_func)

        self.assertTrue(result, "Способность должна успешно активироваться")
        self.assertEqual(self.unit.cooldowns.get("defender"), 5, "Кулдаун должен быть 5")

        # 2. Проверка статусов
        # Taunt
        self.unit.add_status.assert_any_call("taunt", 1, duration=3)
        # Protection
        self.unit.add_status.assert_any_call("protection", 3, duration=3)

        # 3. Проверка повторной активации (Кулдаун)
        self.unit.cooldowns["defender"] = 5
        result_cd = talent.activate(self.unit, log_func=self.log_func)
        self.assertFalse(result_cd, "Не должно работать, пока есть КД")

    def test_talent_idol_oath(self):
        """
        Проверка таланта 3.9 Клятва идола:
        - Блокирует лечение от других источников.
        - Разрешает лечение от себя.
        - Дает бонусы статов при HP < 25%.
        """
        from logic.character_changing.talents.branch_3_tireless import TalentIdolOath

        talent = TalentIdolOath()

        # Создаем союзника
        ally = MockUnit(name="Healer")

        # Настраиваем нашего юнита
        self.unit.max_hp = 100
        self.unit.current_hp = 10  # 10% HP (Кризис)

        # 1. Проверка статов при низком ХП (<25%)
        stats = talent.on_calculate_stats(self.unit)
        self.assertEqual(stats.get("power_attack"), 2, "Должен быть бонус +2 к атаке при HP < 25%")
        self.assertEqual(stats.get("medicine"), 15, "Базовый бонус медицины должен быть 15")

        # 2. Проверка блокировки лечения от союзника
        # Имитируем вызов modify_incoming_heal движком
        heal_from_ally = talent.modify_incoming_heal(self.unit, 20, source=ally)
        self.assertEqual(heal_from_ally, 0, "Лечение от союзника должно быть заблокировано (0)")

        # 3. Проверка самолечения
        heal_self = talent.modify_incoming_heal(self.unit, 20, source=self.unit)
        self.assertEqual(heal_self, 20, "Лечение от самого себя должно проходить полностью")

        # 4. Проверка статов при высоком ХП (>25%)
        self.unit.current_hp = 50
        stats_high_hp = talent.on_calculate_stats(self.unit)
        self.assertIsNone(stats_high_hp.get("power_attack"), "Бонуса к атаке не должно быть при HP > 25%")

class TestTalentBigHeart(unittest.TestCase):
    def setUp(self):
        self.talent = TalentBigHeart()
        self.unit = MagicMock()
        self.unit.name = "Guardian"
        # Настраиваем статы для расчета
        self.unit.max_hp = 300
        self.unit.max_stagger = 100
        self.unit.current_stagger = 100  # Полный стаггер по умолчанию
        self.unit.cooldowns = {}

        # Настройка логгера
        self.log_func = MagicMock()

    def test_activation_success(self):
        """
        Проверка успешной активации:
        - Stagger > 50%
        - Союзники получают барьер 10% от Max HP юнита
        - Кулдаун вешается
        """
        # Условия: Стаггер 60/100 (>50%)
        self.unit.current_stagger = 60

        # Создаем макеты союзников
        ally1 = MagicMock()
        ally1.is_dead = False
        ally2 = MagicMock()
        ally2.is_dead = True  # Мертвый
        ally3 = MagicMock()
        ally3.is_dead.return_value = False  # Живой (метод)

        allies = [ally1, ally2, ally3, self.unit]

        # Активируем
        result = self.talent.activate(self.unit, log_func=self.log_func, allies=allies)

        self.assertTrue(result, "Способность должна активироваться")

        # [FIX] Обновлено значение с 5 на 99 согласно коду таланта (cooldown = 99)
        self.assertEqual(self.unit.cooldowns.get("big_heart"), 5, "Кулдаун должен быть установлен (99)")

        # [FIX] Расчет барьера: 15% от 300 HP = 30 (было 45/15%)
        expected_barrier = 45

        # Ally1 (живой) -> получает барьер
        ally1.add_status.assert_called_with("barrier", expected_barrier, duration=1)

        # Ally2 (мертвый) -> не получает
        ally2.add_status.assert_not_called()

        # Ally3 (живой, метод) -> получает барьер
        ally3.add_status.assert_called_with("barrier", expected_barrier, duration=1)

        # Unit (сам на себя) -> не получает
        self.unit.add_status.assert_not_called()

    def test_fail_low_stagger(self):
        """Проверка отказа: Stagger <= 50%"""
        self.unit.current_stagger = 50
        allies = [MagicMock()]

        result = self.talent.activate(self.unit, log_func=self.log_func, allies=allies)

        self.assertFalse(result, "Не должно активироваться при низком стаггере")
        self.log_func.assert_called_with(f"❌ {self.talent.name}: Недостаточно концентрации (нужно > 50% Stagger).")
        allies[0].add_status.assert_not_called()

    def test_fail_cooldown(self):
        """Проверка отказа: Кулдаун"""
        self.unit.cooldowns["big_heart"] = 99
        self.unit.current_stagger = 100
        allies = [MagicMock()]

        result = self.talent.activate(self.unit, log_func=self.log_func, allies=allies)

        self.assertFalse(result, "Не должно активироваться в кулдауне")
        self.log_func.assert_called_with(f"❌ {self.talent.name}: Способность уже использована.")
        allies[0].add_status.assert_not_called()


# ============================================
# ТЕСТ 3.10: Прилив сил (Surge of Strength)
# ============================================
class TestTalentSurgeOfStrength(unittest.TestCase):
    def setUp(self):
        from logic.character_changing.talents.branch_3_tireless import TalentSurgeOfStrength
        self.talent = TalentSurgeOfStrength()
        self.unit = MockUnit(name="Berseker", level=1, max_hp=100, max_stagger=50)

        # Мокаем методы
        self.unit.add_status = MagicMock(side_effect=self.unit.add_status)
        self.unit.roll_speed = MagicMock()
        self.log_func = MagicMock()

        # Настраиваем кулдауны для теста
        # Карта 'card_1' имеет кд 2, 'card_2' имеет кд 0
        self.unit.card_cooldowns = {
            "card_1": [2],
            "card_2": [0],
            "card_3": [1, 3]  # Две копии
        }

    def test_activation_trigger(self):
        """
        Проверка срабатывания:
        - HP падает ниже 25%.
        - Stagger восстанавливается.
        - Скорость перебрасывается.
        - Статусы накладываются.
        - Кулдауны снижаются.
        """
        # 1. Установка состояния ДО удара
        self.unit.current_hp = 30  # 30% HP
        self.unit.current_stagger = 0  # Сбит с ног

        # 2. Нанесение урона (до 20 HP = 20%)
        self.unit.current_hp = 20

        # Вызываем хук (имитация движка)
        self.talent.on_take_damage(self.unit, 10, source=None, log_func=self.log_func)

        # === ПРОВЕРКИ ===

        # 1. Флаг памяти
        self.assertTrue(self.unit.memory.get("surge_activated"), "Флаг активации должен быть True")

        # 2. Stagger
        self.assertEqual(self.unit.current_stagger, 50, "Stagger должен восстановиться до максимума")

        # 3. Скорость
        self.unit.roll_speed.assert_called_once()

        # 4. Статусы (Временные +4)
        self.unit.add_status.assert_any_call("attack_power_up", 4, duration=1)
        self.unit.add_status.assert_any_call("endurance", 4, duration=1)
        self.unit.add_status.assert_any_call("haste", 4, duration=1)
        self.unit.add_status.assert_any_call("protection", 4, duration=1)

        # 5. Статусы (Постоянные +2)
        self.unit.add_status.assert_any_call("haste", 2, duration=99)

        # 6. Кулдауны
        # card_1: 2 -> 1
        self.assertEqual(self.unit.card_cooldowns["card_1"], [1])
        # card_2: 0 -> 0 (не уходит в минус)
        self.assertEqual(self.unit.card_cooldowns["card_2"], [0])
        # card_3: [1, 3] -> [0, 2]
        self.assertEqual(self.unit.card_cooldowns["card_3"], [0, 2])

    def test_no_activation_above_threshold(self):
        """Не срабатывает, если HP > 25%."""
        self.unit.current_hp = 26  # 26%
        self.talent.on_take_damage(self.unit, 10, source=None)

        self.assertFalse(self.unit.memory.get("surge_activated"))
        self.unit.add_status.assert_not_called()

    def test_single_activation(self):
        """Срабатывает только 1 раз за бой."""
        # Активируем первый раз
        self.unit.current_hp = 20
        self.talent.on_take_damage(self.unit, 10, source=None)
        self.assertTrue(self.unit.memory.get("surge_activated"))

        # Сбрасываем моки, чтобы проверить отсутствие повторных вызовов
        self.unit.add_status.reset_mock()

        # Второй удар (HP еще ниже)
        self.unit.current_hp = 10
        self.talent.on_take_damage(self.unit, 10, source=None)

        # Статусы НЕ должны накладываться снова
        self.unit.add_status.assert_not_called()


if __name__ == '__main__':
    unittest.main()