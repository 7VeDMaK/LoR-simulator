import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType, CardType
from logic.battle_flow.executor import execute_single_action
from logic.battle_flow.priorities import get_action_priority
from tests.mocks import MockUnit, MockDice


class TestMassAttackLogic(unittest.TestCase):

    def create_unit(self, name):
        u = MockUnit(name)
        u.is_dead = MagicMock(return_value=False)
        u.is_staggered = MagicMock(return_value=False)
        u.card_cooldowns = {}
        u.deck = []
        u.active_slots = []
        return u

    def create_action(self, source, target, card_type_str, speed, label=""):
        card = MagicMock()
        card.name = label or f"{card_type_str}_Card"
        card.card_type = card_type_str.lower()
        card.id = f"{card.name}_id"
        card.tier = 3 if "mass" in card_type_str else 1

        card.dice_list = [MockDice(DiceType.SLASH)]
        source.current_card = card

        # ВНИМАНИЕ: Этот метод перезаписывает слоты источника!
        # Если нужно много слотов, настраивайте их вручную после вызова.
        source.active_slots = [{'card': card, 'speed': speed, 'destroy_on_speed': False}]

        return {
            'label': card.name,
            'source': source,
            'source_idx': 0,
            'target_unit': target,
            'target_slot_idx': 0,
            'card_type': card_type_str.lower(),
            'slot_data': {'card': card, 'speed': speed, 'destroy_on_speed': False},
            'is_left': True,
            'opposing_team': [target]
        }

    def sort_actions(self, actions):
        return sorted(
            actions,
            key=lambda x: (get_action_priority(x['slot_data']['card']), x['slot_data']['speed']),
            reverse=True
        )

    # === ТЕСТЫ ПРИОРИТЕТОВ ===

    def test_mass_attack_priority_absolute(self):
        """Mass Attack (Summation) перебивает всё, даже быстрых."""
        u_boss = self.create_unit("Boss")
        u_ranged = self.create_unit("Sniper")
        u_melee = self.create_unit("Fighter")

        act_mass = self.create_action(u_boss, u_melee, "mass_summation", 1, "The_Apocalypse")
        act_ranged = self.create_action(u_ranged, u_boss, "ranged", 10, "Headshot")
        act_melee = self.create_action(u_melee, u_boss, "melee", 20, "Punch")

        actions = self.sort_actions([act_ranged, act_melee, act_mass])

        self.assertEqual(actions[0]['label'], "The_Apocalypse")
        self.assertEqual(actions[1]['label'], "Headshot")
        self.assertEqual(actions[2]['label'], "Punch")
        print("✅ Mass Attack (Spd 1) успешно обогнал Ranged (Spd 10) и Melee (Spd 20).")

    def test_mass_individual_vs_summation(self):
        """Между двумя масс атаками решает скорость."""
        u_boss1 = self.create_unit("Boss1")
        u_boss2 = self.create_unit("Boss2")

        act_sum = self.create_action(u_boss1, u_boss2, "mass_summation", 5, "Summation")
        act_ind = self.create_action(u_boss2, u_boss1, "mass_individual", 8, "Individual")

        actions = self.sort_actions([act_sum, act_ind])

        self.assertEqual(actions[0]['label'], "Individual")
        self.assertEqual(actions[1]['label'], "Summation")
        print("✅ Битва Mass Attack разрешена по Скорости.")

    # === ТЕСТЫ ПОСЛЕДСТВИЙ (FLOW) ===

    def test_mass_summation_destroys_defender_card(self):
        """Если Mass Attack побеждает, карта защитника уничтожается (пропуск хода)."""
        u_boss = self.create_unit("Boss")
        u_hero = self.create_unit("Hero")

        act_mass = self.create_action(u_boss, u_hero, "mass_summation", 10, "Giant_Laser")
        act_hero = self.create_action(u_hero, u_boss, "melee", 5, "Hero_Slash")

        executed_slots = set()

        # Мокаем process_mass_attack
        with patch('logic.battle_flow.executor.process_mass_attack') as mock_proc:
            def side_effect(engine, action, team, label, slots):
                # Эмуляция: Герой проиграл, его карта уничтожается
                slots.add((u_hero.name, 0))
                u_hero.current_card = None
                return ["Mass Attack Hit!"]

            mock_proc.side_effect = side_effect

            # 1. Ход Босса
            execute_single_action(MagicMock(), act_mass, executed_slots)
            self.assertIn((u_hero.name, 0), executed_slots)

        # 2. Ход Героя (должен быть пропущен)
        res = execute_single_action(MagicMock(), act_hero, executed_slots)
        self.assertEqual(res, [], "Герой не должен атаковать.")
        print("✅ Mass Attack подавила атаку Героя.")

    def test_mass_attack_survival(self):
        """
        Проверка: Mass Attack блокирует только защищающийся слот.
        Второй слот героя должен атаковать нормально.
        """
        u_boss = self.create_unit("Boss")
        u_hero = self.create_unit("Hero")

        # 1. Создаем действия
        act_mass = self.create_action(u_boss, u_hero, "mass_individual", 10, "Rain_of_Arrows")

        act_hero_slot0 = self.create_action(u_hero, u_boss, "melee", 5, "Defend_This")
        act_hero_slot0['source_idx'] = 0

        act_hero_slot1 = self.create_action(u_hero, u_boss, "melee", 4, "Attack_Next")
        act_hero_slot1['source_idx'] = 1  # Второй слот

        # [FIX] Вручную настраиваем слоты героя, чтобы их было два
        # Берем карты из созданных действий
        card0 = act_hero_slot0['slot_data']['card']
        card1 = act_hero_slot1['slot_data']['card']

        u_hero.active_slots = [
            {'card': card0, 'speed': 5, 'destroy_on_speed': False},
            {'card': card1, 'speed': 4, 'destroy_on_speed': False}
        ]

        # Обновляем slot_data в действиях, чтобы они ссылались на правильный список
        act_hero_slot0['slot_data'] = u_hero.active_slots[0]
        act_hero_slot1['slot_data'] = u_hero.active_slots[1]

        executed_slots = set()

        # 1. Mass Attack Босса
        with patch('logic.battle_flow.executor.process_mass_attack') as mock_proc:
            def side_effect(engine, action, team, label, slots):
                # Масс атака заставляет Героя защищаться ТОЛЬКО слотом 0
                slots.add((u_hero.name, 0))
                return ["Clash occurred"]

            mock_proc.side_effect = side_effect

            execute_single_action(MagicMock(), act_mass, executed_slots)

        # 2. Ход Героя (Слот 0) -> Должен быть пропущен (защищался)
        res0 = execute_single_action(MagicMock(), act_hero_slot0, executed_slots)
        self.assertEqual(res0, [], "Слот 0 должен быть занят.")

        # 3. Ход Героя (Слот 1) -> Должен сработать!
        with patch.object(MagicMock(), '_resolve_one_sided', return_value=["Hit"]) as mock_onesided:
            eng = MagicMock()
            eng._resolve_one_sided = mock_onesided
            eng._resolve_card_clash = MagicMock()

            # Убеждаемся, что executor сможет найти карту по индексу 1
            res1 = execute_single_action(eng, act_hero_slot1, executed_slots)

            self.assertNotEqual(res1, [], "Слот 1 должен быть свободен для атаки.")
            self.assertIn((u_hero.name, 1), executed_slots, "Теперь и слот 1 использован.")

        print("✅ Mass Attack заблокировала только слот 0. Слот 1 успешно атаковал.")


if __name__ == '__main__':
    unittest.main()