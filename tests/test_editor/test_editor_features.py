import unittest
import os
import json
import shutil
from core.library import Library
from core.card import Card

TEST_DIR = "tests_temp_data"


class TestEditorFeatures(unittest.TestCase):

    def setUp(self):
        # Подменяем директорию карт на тестовую
        self.original_dir = Library.CARDS_DIR if hasattr(Library, 'CARDS_DIR') else "data/cards"

        # Создаем временную папку
        if not os.path.exists(TEST_DIR):
            os.makedirs(TEST_DIR)

        # Патчим путь в классе (в Python это работает, если CARDS_DIR не заимпорчена отдельно как константа)
        # Если Library использует глобальную переменную модуля, нужно патчить её там.
        # Предположим для теста, что мы можем переопределить путь или используем мок.
        # Для простоты теста будем писать прямо в data/cards, но с уникальным именем, и удалять потом.
        self.test_pack_name = "test_pack_unique_123.json"
        self.full_path = os.path.join("data/cards", self.test_pack_name)

    def tearDown(self):
        # Удаляем созданный тестовый файл
        if os.path.exists(self.full_path):
            os.remove(self.full_path)

    def test_create_pack(self):
        """Тест создания нового пака через Library."""
        # 1. Создаем
        result = Library.create_new_pack(self.test_pack_name)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.full_path))

        # 2. Проверяем структуру
        with open(self.full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data, {"cards": []})

        # 3. Пытаемся создать дубликат
        result_dup = Library.create_new_pack(self.test_pack_name)
        self.assertFalse(result_dup)  # Должен вернуть False

    def test_save_card_to_specific_pack(self):
        """Тест сохранения карты в конкретный пак."""
        Library.create_new_pack(self.test_pack_name)

        card = Card(id="test_c1", name="Test Card", tier=1, card_type="Melee", description="Desc")

        # Сохраняем
        Library.save_card(card, filename=self.test_pack_name)

        # Проверяем, что она там
        with open(self.full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(len(data['cards']), 1)
        self.assertEqual(data['cards'][0]['id'], "test_c1")

    def test_move_card_simulation(self):
        """Симуляция переноса: сохранение в новый файл."""
        # Создаем два пака
        pack1 = "test_pack_A.json"
        pack2 = "test_pack_B.json"
        path1 = os.path.join("data/cards", pack1)
        path2 = os.path.join("data/cards", pack2)

        try:
            Library.create_new_pack(pack1)
            Library.create_new_pack(pack2)

            card = Card(id="moving_card", name="Mover", tier=1, card_type="Melee")

            # 1. Сохраняем в А
            Library.save_card(card, filename=pack1)

            # 2. Сохраняем в B (как дубликат/перенос)
            Library.save_card(card, filename=pack2)

            # Проверяем B
            with open(path2, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.assertEqual(data['cards'][0]['id'], "moving_card")

        finally:
            if os.path.exists(path1): os.remove(path1)
            if os.path.exists(path2): os.remove(path2)


if __name__ == '__main__':
    unittest.main()