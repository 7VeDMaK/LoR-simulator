import copy
import glob
import json
import os
from typing import List, Dict

from core.card import Card
from core.logging import logger, LogLevel

CARDS_DIR = "data/cards"


class Library:
    _cards = {}  # {id: Card}
    _sources = {}  # {id: filename}

    @classmethod
    def register(cls, card: Card):
        key = card.id if card.id and card.id != "unknown" else card.name
        cls._cards[key] = card

    @classmethod
    def get_cards_dict(cls) -> Dict[str, Card]:
        return cls._cards

    @classmethod
    def get_source(cls, card_id: str) -> str:
        return cls._sources.get(card_id)

    @classmethod
    def load_cards_from_file(cls, filename: str) -> List[Card]:
        """Возвращает список карт, привязанных к конкретному файлу."""
        # Убедимся, что filename это только имя файла, а не путь
        filename = os.path.basename(filename)
        return [c for c in cls._cards.values() if cls._sources.get(c.id) == filename]

    @classmethod
    def load_all(cls, path="data/cards"):
        """Полная перезагрузка всех карт."""
        # Очищаем старое, чтобы не дублировать при перезагрузке
        cls._cards.clear()
        cls._sources.clear()

        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            return

        if os.path.isdir(path):
            files = glob.glob(os.path.join(path, "*.json"))
            for filepath in files:
                cls._load_single_file(filepath)
        else:
            cls._load_single_file(path)

    @classmethod
    def reload(cls):
        """Принудительно перечитывает папку карт."""
        cls.load_all(CARDS_DIR)

    @classmethod
    def _load_single_file(cls, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cards_list = data.get("cards", []) if isinstance(data, dict) else data
            filename = os.path.basename(filepath)

            for card_data in cards_list:
                card = Card.from_dict(card_data)
                cls.register(card)
                if card.id:
                    cls._sources[card.id] = filename

        except Exception as e:
            logger.log(f"Error loading {filepath}: {e}", LogLevel.NORMAL, "System")

    @classmethod
    def save_card(cls, card: Card, filename="custom_cards.json"):
        folder = "data/cards"
        filepath = os.path.join(folder, filename)
        os.makedirs(folder, exist_ok=True)

        current_data = {"cards": []}

        # Читаем текущий файл, если есть
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        current_data["cards"] = content
                    else:
                        current_data = content
            except Exception as e:
                logger.log(f"Error reading save file: {e}", LogLevel.NORMAL, "System")

        card_dict = card.to_dict()
        found = False

        # Обновляем или добавляем
        for i, existing in enumerate(current_data["cards"]):
            if existing.get("id") == card.id:
                current_data["cards"][i] = card_dict
                found = True
                break

        if not found:
            current_data["cards"].append(card_dict)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)

            logger.log(f"💾 Card '{card.name}' saved to {filename}", LogLevel.NORMAL, "System")

            # Обновляем память
            cls.register(card)
            cls._sources[card.id] = filename
        except Exception as e:
            logger.log(f"Error saving card: {e}", LogLevel.NORMAL, "System")

    @classmethod
    def delete_card(cls, card_id):
        # ... (код удаления оставляем как был, он вроде корректный) ...
        # Для краткости не дублирую, если он у вас работает
        if card_id in cls._cards:
            del cls._cards[card_id]
        if card_id in cls._sources:
            del cls._sources[card_id]

        path = "data/cards"
        if os.path.exists(path) and os.path.isdir(path):
            files = glob.glob(os.path.join(path, "*.json"))
            for filepath in files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    cards_list = data.get("cards", []) if isinstance(data, dict) else data
                    if not isinstance(cards_list, list): continue

                    new_list = [c for c in cards_list if c.get("id") != card_id]

                    if len(new_list) != len(cards_list):
                        if isinstance(data, dict):
                            data["cards"] = new_list
                        else:
                            data = new_list

                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        return True
                except:
                    pass
        return False

    @staticmethod
    def get_all_source_files() -> List[str]:
        if not os.path.exists(CARDS_DIR):
            return []
        return [f for f in os.listdir(CARDS_DIR) if f.endswith(".json")]

    @classmethod
    def create_new_pack(cls, filename: str) -> bool:
        if not filename.endswith(".json"):
            filename += ".json"

        path = os.path.join(CARDS_DIR, filename)
        if os.path.exists(path):
            # [FIX] Используем log вместо warning
            logger.log(f"Файл {filename} уже существует.", LogLevel.NORMAL, "System")
            return False

        try:
            empty_data = {"cards": []}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(empty_data, f, ensure_ascii=False, indent=2)

            logger.log(f"Создан новый пак: {filename}", LogLevel.NORMAL, "System")
            # [FIX] Перечитываем библиотеку, чтобы новый файл появился в списках
            cls.reload()
            return True
        except Exception as e:
            logger.log(f"Ошибка при создании пака: {e}", LogLevel.NORMAL, "System")
            return False