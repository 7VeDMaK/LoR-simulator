import copy
import glob
import json
import os

from core.card import Card
from core.logging import logger, LogLevel  # [LOG]


class Library:
    _cards = {}  # Тут хранятся ВСЕ карты (из всех файлов) для игры
    _sources = {}  # Словарь: card_id -> filename

    @classmethod
    def register(cls, card: Card):
        """Просто добавляет карту в оперативную память"""
        key = card.id if card.id and card.id != "unknown" else card.name
        cls._cards[key] = card

    @classmethod
    def register_temp_card(cls, new_id, card_obj):
        """
        [NEW] Регистрирует модифицированную временную карту под новым ID.
        Используется для талантов типа Copycat.
        """
        card_obj.id = new_id
        cls._cards[new_id] = card_obj

    @classmethod
    def get_card(cls, key: str) -> Card:
        if key in cls._cards:
            return copy.deepcopy(cls._cards[key])
        for card in cls._cards.values():
            if card.name == key:
                return copy.deepcopy(card)

        try:
            name = str(key)
        except Exception:
            name = "Unknown"
        return Card(name=name, dice_list=[], description="", id="unknown")

    @classmethod
    def get_all_cards(cls):
        return list(cls._cards.values())

    @classmethod
    def get_source(cls, card_id: str) -> str:
        """Возвращает имя файла, откуда карта была загружена."""
        return cls._sources.get(card_id)

    @classmethod
    def load_all(cls, path="data/cards"):
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            logger.log(f"Created directory: {path}", LogLevel.VERBOSE, "System")
            return

        if os.path.isdir(path):
            files = glob.glob(os.path.join(path, "*.json"))
            logger.log(f"--- Loading cards from {path} ---", LogLevel.VERBOSE, "System")
            for filepath in files:
                cls._load_single_file(filepath)
        else:
            cls._load_single_file(path)

    @classmethod
    def _load_single_file(cls, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cards_list = data.get("cards", []) if isinstance(data, dict) else data

            count = 0
            filename = os.path.basename(filepath)

            for card_data in cards_list:
                card = Card.from_dict(card_data)
                cls.register(card)

                if card.id:
                    cls._sources[card.id] = filename

                count += 1

            logger.log(f"✔ Loaded {count} cards from {filename}", LogLevel.NORMAL, "System")
        except Exception as e:
            logger.log(f"Error loading {filepath}: {e}", LogLevel.NORMAL, "System")

    @classmethod
    def save_card(cls, card: Card, filename="custom_cards.json"):
        """
        Сохраняет конкретную карту в конкретный файл.
        """
        folder = "data/cards"
        filepath = os.path.join(folder, filename)
        os.makedirs(folder, exist_ok=True)

        current_data = {"cards": []}
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

            cls.register(card)
            cls._sources[card.id] = filename
        except Exception as e:
            logger.log(f"Error saving card to disk: {e}", LogLevel.NORMAL, "System")

    @classmethod
    def delete_card(cls, card_id):
        """Удаляет карту из памяти и из файла."""
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

                    original_len = len(cards_list)
                    new_list = [c for c in cards_list if c.get("id") != card_id]

                    if len(new_list) != original_len:
                        if isinstance(data, dict):
                            data["cards"] = new_list
                        else:
                            data = new_list

                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)

                        logger.log(f"🗑️ Card {card_id} deleted from {filepath}", LogLevel.NORMAL, "System")
                        return True
                except Exception as e:
                    logger.log(f"Error deleting from {filepath}: {e}", LogLevel.NORMAL, "System")

        return False


# Инициализация
Library.load_all("data/cards")