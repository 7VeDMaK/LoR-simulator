import unittest
from unittest.mock import MagicMock
import copy


# Эмуляция классов, если нет доступа к реальным
class MockDice:
    def __init__(self, type, min_val, max_val, scripts=None):
        self.type = type
        self.base_min = min_val
        self.base_max = max_val
        self.scripts = scripts or {}

    def __repr__(self):
        return f"Dice({self.type}, {self.base_min}-{self.base_max})"


class MockCard:
    def __init__(self, name, flags=None, dice=None):
        self.name = name
        self.flags = flags or []
        self.dice = dice or []


class TestAxisUnity(unittest.TestCase):
    def setUp(self):
        self.unit = MagicMock()
        self.unit.name = "Axis"
        self.unit.memory = {}  # Память для хранения Unity-кубиков
        self.unit.hand = []  # Рука с картами

    def _unity_share_logic(self, source_card):
        """
        Логика, которую мы хотим протестировать:
        Берем 1-й кубик из source_card и добавляем его в память unit'а,
        а затем раздаем всем Unity-картам в руке.
        """
        if not source_card.dice:
            return

        # 1. Берем первый кубик для копирования
        dice_to_share = copy.deepcopy(source_card.dice[0])

        # 2. Сохраняем в память (чтобы знать, что раздали в этом ходу)
        # В реальном движке это может быть список 'shared_dice'
        if "shared_dice" not in self.unit.memory:
            self.unit.memory["shared_dice"] = []
        self.unit.memory["shared_dice"].append(dice_to_share)

        # 3. Раздаем картам в руке
        count_affected = 0
        for card in self.unit.hand:
            # Не добавляем самому себе (обычно Unity баффает ДРУГИЕ карты, но если карта осталась в руке...)
            # В механике Ruina/Limbus обычно бафф идет на руку. Карта, которую мы сыграли, уже не в руке.
            if card == source_card:
                continue

            if "unity" in card.flags:
                # Добавляем копию кубика
                new_dice = copy.deepcopy(dice_to_share)
                card.dice.append(new_dice)
                count_affected += 1

        return count_affected

    def _end_turn_cleanup(self):
        """Очистка памяти в конце хода."""
        self.unit.memory["shared_dice"] = []
        # В реальной игре карты сбрасываются, но если бы они оставались,
        # нам нужно было бы удалять добавленные кубики?
        # Обычно в карточных играх добавленные кубики "сгорают" после использования карты или в конце хода.
        # Для теста предположим, что мы просто очищаем память источника.

    # =========================================================================
    # ТЕСТ 1: Передача кубика (Sword of Glory -> Spear of Determination)
    # =========================================================================
    def test_unity_share_basic(self):
        # Карта-источник: Меч Славы (Slash 1-2)
        sword_dice = MockDice("slash", 1, 2, {"on_hit": ["buff_str"]})
        sword_card = MockCard("Sword of Glory", flags=["unity"], dice=[sword_dice])

        # Карта-получатель: Копье Решимости (Pierce 1-2)
        spear_dice = MockDice("pierce", 1, 2)
        spear_card = MockCard("Spear of Determination", flags=["unity"], dice=[spear_dice])

        # Карта без Unity (не должна получить кубик)
        basic_card = MockCard("Basic Attack", flags=[], dice=[MockDice("blunt", 2, 2)])

        self.unit.hand = [sword_card, spear_card, basic_card]

        # === ИГРАЕМ КАРТУ SWORD OF GLORY ===
        affected = self._unity_share_logic(sword_card)

        # Проверки
        self.assertEqual(affected, 1, "Кубик должен получить только Spear (Unity)")

        # 1. Spear должен иметь 2 кубика: свой Pierce и полученный Slash
        self.assertEqual(len(spear_card.dice), 2)
        self.assertEqual(spear_card.dice[0].type, "pierce")  # Родной
        self.assertEqual(spear_card.dice[1].type, "slash")  # Полученный
        self.assertEqual(spear_card.dice[1].scripts["on_hit"], ["buff_str"])  # Эффекты скопированы

        # 2. Basic Card не изменилась
        self.assertEqual(len(basic_card.dice), 1)

    # =========================================================================
    # ТЕСТ 2: Накопление (Цепочка Unity)
    # Sword -> Spear (теперь у Spear 2 кубика). Затем играем Spear.
    # =========================================================================
    def test_unity_chain(self):
        # Sword (Slash)
        sword_card = MockCard("Sword", flags=["unity"], dice=[MockDice("slash", 4, 4)])
        # Spear (Pierce)
        spear_card = MockCard("Spear", flags=["unity"], dice=[MockDice("pierce", 5, 5)])
        # Fist (Blunt)
        fist_card = MockCard("Fist", flags=["unity"], dice=[MockDice("blunt", 6, 6)])

        self.unit.hand = [sword_card, spear_card, fist_card]

        # 1. Играем Sword. Spear и Fist получают Slash.
        self._unity_share_logic(sword_card)

        # Spear: [Pierce, Slash]
        # Fist: [Blunt, Slash]
        self.assertEqual(len(spear_card.dice), 2)
        self.assertEqual(len(fist_card.dice), 2)

        # 2. Теперь играем Spear.
        # ВАЖНО: Какой кубик шарится? Родной (первый) или добавленный?
        # По описанию "Unity берет ПЕРВЫЙ дайс карты".
        # У Spear первый дайс - Pierce.
        self._unity_share_logic(spear_card)

        # Fist должен получить Pierce.
        # Fist: [Blunt, Slash (от Sword), Pierce (от Spear)]
        self.assertEqual(len(fist_card.dice), 3)
        self.assertEqual(fist_card.dice[0].type, "blunt")
        self.assertEqual(fist_card.dice[1].type, "slash")
        self.assertEqual(fist_card.dice[2].type, "pierce")

    # =========================================================================
    # ТЕСТ 3: Мелкие неудачи (Minor Setbacks)
    # Эта карта создает кубики скриптом, а потом шарит.
    # Проверяем, что шарится именно первый (Блок).
    # =========================================================================
    def test_minor_setbacks_share(self):
        # Minor Setbacks: [Block 3-6]
        setbacks_dice = MockDice("block", 3, 6)
        setbacks_card = MockCard("Minor Setbacks", flags=["unity"], dice=[setbacks_dice])

        receiver = MockCard("Receiver", flags=["unity"], dice=[MockDice("evade", 1, 1)])
        self.unit.hand = [setbacks_card, receiver]

        # Эмуляция: Скрипт карты добавляет ей кубики (presets) ПЕРЕД шарингом?
        # Или шаринг берет базу?
        # В JSON скрипты идут списком: 1. add_preset_dice, 2. share_dice_with_hand.
        # Значит, карта сначала получает доп. кубики.

        # Добавляем пресеты (имитация add_preset_dice)
        setbacks_card.dice.append(MockDice("slash", 4, 8))
        setbacks_card.dice.append(MockDice("pierce", 4, 8))

        # Теперь у карты: [Block, Slash, Pierce]

        # Вызываем шаринг (должен взять 0-й индекс, т.е. Block)
        self._unity_share_logic(setbacks_card)

        # Проверка получателя
        self.assertEqual(len(receiver.dice), 2)
        self.assertEqual(receiver.dice[1].type, "block")  # Получил именно Блок
        self.assertEqual(receiver.dice[1].base_min, 3)


if __name__ == '__main__':
    unittest.main()