import unittest
import os
import json
import shutil
from unittest.mock import MagicMock, patch

# Добавляем корень проекта
import sys

sys.path.append(os.getcwd())

from core.library import Library
from core.card import Card

TEST_DIR = "data/cards"  # Используем реальную папку, но временные файлы


class TestEditorFullCycle(unittest.TestCase):

    def setUp(self):
        # Временные имена файлов
        self.pack_a = "test_pack_A_temp.json"
        self.pack_b = "test_pack_B_temp.json"
        self.path_a = os.path.join(TEST_DIR, self.pack_a)
        self.path_b = os.path.join(TEST_DIR, self.pack_b)

        # Очистка перед тестом (на всякий случай)
        self._clean()

        # Патчим логгер, чтобы он не спамил и не падал
        self.logger_patcher = patch('core.library.logger')
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        self._clean()
        self.logger_patcher.stop()

    def _clean(self):
        if os.path.exists(self.path_a): os.remove(self.path_a)
        if os.path.exists(self.path_b): os.remove(self.path_b)

    def test_create_and_switch_pack(self):
        """Тест 1: Создание пака и проверка, что он появился."""
        # 1. Создаем пак
        res = Library.create_new_pack(self.pack_a)
        self.assertTrue(res)
        self.assertTrue(os.path.exists(self.path_a))

        # 2. Проверяем, что reload сработал и файл есть в списке
        files = Library.get_all_source_files()
        self.assertIn(self.pack_a, files)

    def test_save_and_move_card(self):
        """Тест 2: Создание карты в Паке А, затем сохранение (перенос) в Пак Б."""
        Library.create_new_pack(self.pack_a)
        Library.create_new_pack(self.pack_b)

        # 1. Создаем карту
        card = Card(id="test_mover", name="Mover", tier=1, card_type="Melee", description="I like to move it")

        # 2. Сохраняем в А
        Library.save_card(card, filename=self.pack_a)

        # Проверяем A
        cards_a = Library.load_cards_from_file(self.pack_a)
        self.assertEqual(len(cards_a), 1)
        self.assertEqual(cards_a[0].name, "Mover")

        # 3. "Редактор": меняем имя и сохраняем в B
        card.name = "Mover (Moved)"
        Library.save_card(card, filename=self.pack_b)

        # Проверяем B
        cards_b = Library.load_cards_from_file(self.pack_b)
        self.assertEqual(len(cards_b), 1)
        self.assertEqual(cards_b[0].name, "Mover (Moved)")

        # Проверяем, что в А осталась старая версия (так работает "Дублирование/Перенос" без явного удаления)
        cards_a_again = Library.load_cards_from_file(self.pack_a)
        self.assertEqual(cards_a_again[0].name, "Mover")

    def test_duplicate_card_logic(self):
        """Тест 3: Логика дублирования (создание копии с новым ID)."""
        Library.create_new_pack(self.pack_a)

        original_card = Card(id="orig_1", name="Original", tier=1, card_type="Melee")
        Library.save_card(original_card, filename=self.pack_a)

        # Эмуляция "Дублирования" в редакторе: стираем ID, меняем имя
        dupe_card = copy.deepcopy(original_card)
        dupe_card.id = "dupe_2"  # Новый ID генерируется при сохранении
        dupe_card.name = "Original (Copy)"

        Library.save_card(dupe_card, filename=self.pack_a)

        # Проверяем файл
        cards = Library.load_cards_from_file(self.pack_a)
        self.assertEqual(len(cards), 2)

        names = [c.name for c in cards]
        self.assertIn("Original", names)
        self.assertIn("Original (Copy)", names)


import copy  # Нужен для теста

if __name__ == '__main__':
    unittest.main()