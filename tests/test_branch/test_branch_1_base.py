import unittest
from unittest.mock import MagicMock, patch

# Импортируйте ваши классы (пути могут отличаться в зависимости от структуры проекта)
from logic.character_changing.talents.branch_1_mindgames import *
from core.logging import LogLevel


class TestBranch1Talents(unittest.TestCase):
    def setUp(self):
        # Создаем мок-юнита
        self.unit = MagicMock()
        self.unit.name = "TestUnit"
        self.unit.max_sp = 100
        self.unit.current_sp = 100
        self.unit.statuses = {}
        self.unit.memory = {}

        # Мокаем методы работы со статусами
        self.unit.get_status = MagicMock(side_effect=lambda name: self.unit.statuses.get(name, 0))
        self.unit.add_status = MagicMock(side_effect=lambda name, amt, **kwargs: self.unit.statuses.update({name: amt}))
        self.unit.remove_status = MagicMock(side_effect=lambda name: self.unit.statuses.pop(name, None))
        self.unit.take_sanity_damage = MagicMock(
            side_effect=lambda amt: setattr(self.unit, 'current_sp', self.unit.current_sp - amt))

        self.log_func = MagicMock()

    # ==========================================
    # ТЕСТ 1.9 А: Безопасное Э.Г.О
    # ==========================================
    def test_safe_ego_mechanics(self):
        """
        Проверка:
        1. Активация при SP > 25.
        2. Срез урона -20% и Бонус урона +20%.
        3. Трата SP каждый ход.
        4. Деактивация при SP <= 25.
        """
        talent = TalentSafeEGO()

        # --- 1. АКТИВАЦИЯ ---
        self.unit.current_sp = 100  # > 25 (Порог)
        self.unit.statuses = {}  # Чисто

        talent.on_round_start(self.unit, self.log_func)

        # Проверяем, что статус появился
        self.assertIn("ego_manifested", self.unit.statuses)
        self.log_func.assert_called()

        # --- 2. МОДИФИКАТОРЫ ---
        # Входящий урон (100 -> 80)
        inc_dmg = talent.modify_incoming_damage(self.unit, 100, "slash")
        self.assertEqual(inc_dmg, 80)

        # Исходящий урон (100 -> 120)
        out_dmg = talent.modify_outgoing_damage(self.unit, 100, "slash")
        self.assertEqual(out_dmg, 120)

        # --- 3. ТРАТА SP ---
        # Эмулируем конец раунда
        talent.on_round_end(self.unit, self.log_func)

        # Было 50, цена 15 -> Стало 35
        self.assertEqual(self.unit.current_sp, 50)
        # Статус все еще должен висеть, т.к. 35 > 25
        self.assertIn("ego_manifested", self.unit.statuses)

        # --- 4. ДЕАКТИВАЦИЯ (СРЫВ) ---
        # Опускаем SP ниже порога (например, получили урон или просто кончилось)
        self.unit.current_sp = 20  # <= 25

        # Вызываем round_start (где проверяется выход)
        talent.on_round_start(self.unit, self.log_func)

        # Статус должен исчезнуть
        self.assertNotIn("ego_manifested", self.unit.statuses)

        # Проверяем, что модификаторы отключились
        inc_dmg_off = talent.modify_incoming_damage(self.unit, 100, "slash")
        self.assertEqual(inc_dmg_off, 100)

    # ==========================================
    # ТЕСТ 1.9 Б: Не теряя себя (Искажение)
    # ==========================================
    def test_controlled_distortion_mechanics(self):
        """
        Проверка:
        1. Вход при SP < 25 (Кризис).
        2. Умножение статов на 1.5.
        3. Регенерация SP каждый ход.
        4. Выход при SP > 75 (Покой).
        """
        talent = TalentControlledDistortion()

        # --- 1. ВХОД В ИСКАЖЕНИЕ ---
        self.unit.current_sp = 10  # < 25 (Кризис)
        self.unit.statuses = {}

        talent.on_round_start(self.unit, self.log_func)

        self.assertIn("distortion_form", self.unit.statuses)
        self.log_func.assert_called()

        # --- 2. УМНОЖЕНИЕ СТАТОВ ---
        # Базовые статы
        base_stats = {
            "strength": 10,
            "agility": 20,
            "endurance": 4
        }

        # Проверяем хук on_calculate_stats
        # (Передаем копию, чтобы не менять оригинал в тесте)
        modified_stats = talent.on_calculate_stats(self.unit, base_stats.copy())

        # Ожидание: x1.5 (округление вниз int)
        self.assertEqual(modified_stats["strength"], 15)  # 10 * 1.5
        self.assertEqual(modified_stats["agility"], 30)  # 20 * 1.5
        self.assertEqual(modified_stats["endurance"], 6)  # 4 * 1.5

        # --- 3. РЕГЕНЕРАЦИЯ SP ---
        # Конец раунда: зверь успокаивается
        self.unit.restore_sp = MagicMock(
            side_effect=lambda amt: setattr(self.unit, 'current_sp', self.unit.current_sp + amt))

        talent.on_round_end(self.unit, self.log_func)

        # Было 10, реген +15 -> Стало 25
        self.assertEqual(self.unit.current_sp, 60)
        self.unit.restore_sp.assert_called_with(50)

        # --- 4. ВЫХОД ИЗ ИСКАЖЕНИЯ ---
        # Поднимаем SP выше 75
        self.unit.current_sp = 80

        talent.on_round_start(self.unit, self.log_func)

        # Статус должен пропасть
        self.assertNotIn("distortion_form", self.unit.statuses)

        # Статы должны вернуться в норму (хук не сработает без статуса)
        normal_stats = talent.on_calculate_stats(self.unit, base_stats.copy())
        self.assertEqual(normal_stats["strength"], 10)