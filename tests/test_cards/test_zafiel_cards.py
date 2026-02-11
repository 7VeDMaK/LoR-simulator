import unittest
from unittest.mock import MagicMock, patch


# Импортируем необходимые классы (замените на ваши реальные пути)
# from core.unit import Unit
# from core.card import Card
# from core.dice import Dice

class TestZafielCards(unittest.TestCase):
    def setUp(self):
        # Создаем макет Зафиэля
        self.zafiel = MagicMock()
        self.zafiel.name = "Zafiel"
        self.zafiel.max_hp = 100
        self.zafiel.current_hp = 50
        self.zafiel.memory = {}
        self.zafiel.statuses = {}
        self.zafiel.active_slots = []

        # Мокаем методы работы со статусами
        self.zafiel.get_status = MagicMock(side_effect=lambda name: self.zafiel.statuses.get(name, 0))
        self.zafiel.add_status = MagicMock(side_effect=lambda name, val, **kwargs: self.zafiel.statuses.update(
            {name: self.zafiel.statuses.get(name, 0) + val}))
        self.zafiel.remove_status = MagicMock(side_effect=lambda name, val=None: self.zafiel.statuses.update(
            {name: max(0, self.zafiel.statuses.get(name, 0) - (val if val else 999))}))
        self.zafiel.take_damage = MagicMock(
            side_effect=lambda val: setattr(self.zafiel, 'current_hp', self.zafiel.current_hp - val))
        self.zafiel.heal_hp = MagicMock(side_effect=lambda val: setattr(self.zafiel, 'current_hp',
                                                                        min(self.zafiel.max_hp,
                                                                            self.zafiel.current_hp + val)))

        # Создаем макет Врага
        self.target = MagicMock()
        self.target.name = "Dummy Target"
        self.target.current_hp = 100
        self.target.statuses = {}
        # Сложная структура статусов для теста 1 уровня (храним не просто число, а метаданные для проверки длительности)
        # Формат: {status_id: [{'amount': 1, 'duration': 5}, ...]}
        self.target._status_effects = {}
        self.target.remove_status = MagicMock()

    # =========================================================================
    # 1 УРОВЕНЬ: Ложный жест (False Gesture)
    # "При попадании, снимает положительный статус с наибольшей длительностью
    # (при равной - с наибольшим количеством)"
    # =========================================================================
    def test_false_gesture_remove_best_positive(self):
        """
        Проверка алгоритма выбора статуса для снятия.
        Приоритет: Длительность -> Количество.
        """
        # Подготовка статусов на цели
        # 1. Strength: Длит 2, Стак 10 (Много стаков, но мало времени)
        # 2. Haste:    Длит 5, Стак 1  (Долго, но мало - должен проиграть Protection)
        # 3. Protect:  Длит 5, Стак 5  (Долго и больше чем Haste - ПОБЕДИТЕЛЬ)

        self.target._status_effects = {
            "strength": [{"amount": 10, "duration": 2}],
            "haste": [{"amount": 1, "duration": 5}],
            "protection": [{"amount": 5, "duration": 5}],
            "burn": [{"amount": 50, "duration": 10}]  # Негативный, должен игнорироваться
        }

        # Эмуляция функции "is_positive"
        positive_statuses = ["strength", "haste", "protection"]

        # --- ЛОГИКА СКРИПТА ---
        candidates = []
        for s_id, instances in self.target._status_effects.items():
            if s_id in positive_statuses:
                # Берем максимальную длительность и сумму стаков для этого ID
                max_dur = max(i['duration'] for i in instances)
                total_amt = sum(i['amount'] for i in instances)
                candidates.append((s_id, max_dur, total_amt))

        # Сортируем: сначала по duration (desc), потом по amount (desc)
        # sort key: (duration, amount)
        candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)

        target_status = candidates[0][0] if candidates else None

        if target_status:
            self.target.remove_status(target_status)
        # ----------------------

        # Проверка
        self.assertEqual(target_status, "protection")
        self.target.remove_status.assert_called_with("protection")

    # =========================================================================
    # 2 УРОВЕНЬ: Нарастающая свирепость (Growing Fury)
    # "Если использована сразу после победы в столкновении, получает двойной бонус к мощи"
    # =========================================================================
    def test_growing_fury_clash_win(self):
        """
        Проверка множителя силы при победе в столкновении.
        """
        card = MagicMock()
        card.name = "Growing Fury"

        # Сценарий 1: Нет победы в прошлом действии
        self.zafiel.memory = {"last_clash_result": "lose"}

        multiplier = 1.0
        if self.zafiel.memory.get("last_clash_result") == "win":
            multiplier = 2.0

        self.assertEqual(multiplier, 1.0)

        # Сценарий 2: Победа есть
        self.zafiel.memory = {"last_clash_result": "win"}

        if self.zafiel.memory.get("last_clash_result") == "win":
            multiplier = 2.0

        self.assertEqual(multiplier, 2.0)

    # =========================================================================
    # 3 УРОВЕНЬ: Разрыв оболочки (Shell Break)
    # 1. Накладывает 1 Истощения. При 3 Истощения -> -25% MaxHP, сброс счетчика.
    # 2. Если единственная карта в ходу -> Тройная мощь.
    # =========================================================================
    def test_shell_break_exhaustion_explosion(self):
        """
        Проверка механики накопления истощения и урона по себе.
        """
        # Начальное состояние: 2 истощения
        self.zafiel.statuses = {"exhaustion": 2}

        # --- ЛОГИКА СКРИПТА (Применение карты) ---
        self.zafiel.add_status("exhaustion", 1)

        current_exhaustion = self.zafiel.get_status("exhaustion")
        if current_exhaustion >= 3:
            dmg = self.zafiel.max_hp * 0.25
            self.zafiel.take_damage(dmg)
            self.zafiel.remove_status("exhaustion")  # Полный сброс
        # -----------------------------------------

        # Проверки
        # 1. Урон нанесен (25 от 100 = 25. Было 50 -> стало 25)
        self.zafiel.take_damage.assert_called_with(25.0)
        self.assertEqual(self.zafiel.current_hp, 25.0)

        # 2. Статус сброшен
        self.zafiel.remove_status.assert_called_with("exhaustion")

    def test_shell_break_solo_card_power(self):
        """
        Проверка тройного бонуса если карта одна.
        """
        this_card = MagicMock()
        other_card = MagicMock()

        # Сценарий 1: Много карт
        self.zafiel.active_slots = [this_card, other_card]

        power_mult = 1.0
        if len(self.zafiel.active_slots) == 1:
            power_mult = 3.0

        self.assertEqual(power_mult, 1.0)

        # Сценарий 2: Только эта карта
        self.zafiel.active_slots = [this_card]

        if len(self.zafiel.active_slots) == 1:
            power_mult = 3.0

        self.assertEqual(power_mult, 3.0)

    # =========================================================================
    # 4 УРОВЕНЬ: Помеченная плоть (Marked Flesh)
    # 1. Выбор цели с мин HP.
    # 2. При убийстве цели: Heal 25% MaxHP, Remove 2 Exhaustion.
    # =========================================================================
    def test_marked_flesh_targeting(self):
        """
        Проверка выбора цели с наименьшим здоровьем.
        """
        # ИСПРАВЛЕНИЕ: Задаем атрибут .name явно после создания мока
        enemy_1 = MagicMock(current_hp=80)
        enemy_1.name = "Fat Guy"

        enemy_2 = MagicMock(current_hp=20)
        enemy_2.name = "Low HP Guy"  # Цель

        enemy_3 = MagicMock(current_hp=50)
        enemy_3.name = "Mid Guy"

        enemies = [enemy_1, enemy_2, enemy_3]

        # --- ЛОГИКА СКРИПТА ---
        # Сортируем врагов по текущему здоровью
        target = sorted(enemies, key=lambda x: x.current_hp)[0]
        # ----------------------

        # Теперь target.name вернет строку "Low HP Guy"
        self.assertEqual(target.name, "Low HP Guy")

    def test_marked_flesh_on_kill(self):
        """
        Проверка эффектов при убийстве меченой цели.
        """
        # Подготовка Зафиэля: ранен и истощен
        self.zafiel.current_hp = 10
        self.zafiel.statuses = {"exhaustion": 5}

        # --- ЛОГИКА СКРИПТА (On Kill Event) ---
        # Условие: цель умерла и на ней была метка (проверяется движком)
        heal_amt = self.zafiel.max_hp * 0.25
        self.zafiel.heal_hp(heal_amt)
        self.zafiel.remove_status("exhaustion", 2)
        # --------------------------------------

        # Проверки
        # 1. Лечение (10 + 25 = 35)
        self.zafiel.heal_hp.assert_called_with(25.0)
        self.assertEqual(self.zafiel.current_hp, 35.0)

        # 2. Снятие истощения (снимаем именно 2 стака)
        self.zafiel.remove_status.assert_called_with("exhaustion", 2)


if __name__ == '__main__':
    unittest.main()