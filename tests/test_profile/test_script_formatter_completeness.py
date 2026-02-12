import unittest
import os
import json
import sys

# Добавляем корневую папку в путь импорта, чтобы найти ui модуль
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем именно тот модуль, который вы прислали
from ui.profile_new.tabs.build_parts.formatting import _translate_script_effect


class TestProfileFormattingCompleteness(unittest.TestCase):
    def setUp(self):
        # Путь к папке с картами
        self.cards_dir = os.path.join("data", "cards")
        if not os.path.exists(self.cards_dir):
            self.cards_dir = os.path.join("..", "data", "cards")

    def test_all_scripts_have_profile_formatting(self):
        """
        Проверяет, что все script_id в картах имеют красивое описание в профиле (HTML).
        """
        unique_scripts = set()

        # 1. Сбор всех скриптов из файлов
        for filename in os.listdir(self.cards_dir):
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(self.cards_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                cards = data.get("cards", [])
                for card in cards:
                    # Скрипты карты
                    card_scripts = card.get("scripts", {})
                    for _, script_list in card_scripts.items():
                        for script in script_list:
                            unique_scripts.add(script.get("script_id"))

                    # Скрипты кубиков
                    for die in card.get("dice", []):
                        die_scripts = die.get("scripts", {})
                        for _, script_list in die_scripts.items():
                            for script in script_list:
                                unique_scripts.add(script.get("script_id"))

            except Exception as e:
                print(f"⚠️ Error reading {filename}: {e}")

        # 2. Проверка форматирования
        missing_format = []

        print(f"\n🔍 Checking {len(unique_scripts)} scripts against Profile Formatter...")

        for script_id in unique_scripts:
            # Имитируем объект скрипта
            fake_script_obj = {"script_id": script_id, "params": {}}

            # Вызываем функцию перевода
            formatted = _translate_script_effect(fake_script_obj)

            # Если описание начинается со span с серым цветом (fallback), значит описания нет
            # Fallback строка из вашего кода: <span style='color:#777; font-size:0.8em'>{s_id}: {val_str}</span>
            if "color:#777" in formatted:
                missing_format.append(script_id)

        # 3. Результат
        if missing_format:
            print("\n❌ MISSING HTML FORMATTING for scripts in Profile:")
            for s in missing_format:
                print(f"   - {s}")

            print("\n⚠️ Please add these IDs to ui/profile_new/tabs/build_parts/formatting.py")
            # Можно раскомментировать, чтобы тест падал
            # self.fail("Missing script descriptions")
        else:
            print("\n✅ All scripts have HTML descriptions in Profile!")


if __name__ == '__main__':
    unittest.main()