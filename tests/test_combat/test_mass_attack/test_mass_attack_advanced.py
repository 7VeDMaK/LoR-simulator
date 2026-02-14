import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import random

sys.path.append(os.getcwd())

from core.enums import DiceType, CardType
from logic.battle_flow.executor import execute_single_action
from logic.battle_flow.mass_attack import process_mass_attack
from tests.mocks import MockUnit, MockDice


class TestMassAttackAdvanced(unittest.TestCase):

    def create_unit(self, name, speed=5):
        u = MockUnit(name)
        u.is_dead = MagicMock(return_value=False)
        u.is_staggered = MagicMock(return_value=False)
        u.card_cooldowns = {}
        u.deck = []
        u.active_slots = []
        # [FIX] Обязательно инициализируем current_card, так как process_mass_attack пытается его прочитать
        u.current_card = None
        return u

    def create_mass_action(self, source, targets, is_summation=True, dice_vals=None):
        card = MagicMock()
        card.name = "Mass_Apocalypse"
        card.card_type = CardType.MASS_SUMMATION.value if is_summation else CardType.MASS_INDIVIDUAL.value
        card.tier = 3

        # Создаем кубики для карты
        dice_vals = dice_vals or [10]
        card.dice_list = []
        for val in dice_vals:
            d = MockDice(DiceType.SLASH)
            d.min_val = val
            d.max_val = val
            card.dice_list.append(d)

        source.current_card = card
        source.active_slots = [{'card': card, 'speed': 10, 'destroy_on_speed': False}]

        return {
            'label': card.name,
            'source': source,
            'source_idx': 0,
            'target_unit': targets[0],
            'target_slot_idx': 0,
            'card_type': card.card_type,
            'slot_data': {'card': card, 'speed': 10, 'destroy_on_speed': False, 'mass_defenses': {}},
            'is_left': True,
            'opposing_team': targets
        }

    def prepare_defender(self, unit, card_dice_vals=None):
        """Дает защитнику карту в слот 0."""
        card = MagicMock()
        card.name = "Def_Card"
        card.dice_list = []
        vals = card_dice_vals or [5]
        for v in vals:
            d = MockDice(DiceType.BLOCK)
            d.min_val = v
            d.max_val = v
            card.dice_list.append(d)

        slot = {'card': card, 'speed': 5, 'destroy_on_speed': False}
        unit.active_slots = [slot]
        unit.current_card = card

        # === ТЕСТЫ ===

    def test_staggered_source_skips_mass_attack(self):
        """1. Если источник Mass Attack оглушен (Staggered), атака не проходит."""
        u_boss = self.create_unit("Staggered_Boss")
        u_boss.is_staggered.return_value = True

        u_hero = self.create_unit("Hero")
        act = self.create_mass_action(u_boss, [u_hero])

        res = execute_single_action(MagicMock(), act, set())

        self.assertEqual(res, [], "Оглушенный юнит не должен выполнять действие.")
        print("✅ Mass Attack отменена из-за оглушения (Stagger).")

    def test_auto_targeting_priority(self):
        """
        2. Выбор целей (Auto):
        Mass Attack должна выбрать НЕИСПОЛЬЗОВАННЫЙ слот, если он есть.
        """
        u_boss = self.create_unit("Boss")
        u_hero = self.create_unit("Hero")

        s0 = {'card': MagicMock(name="Used"), 'speed': 5}
        s1 = {'card': MagicMock(name="Fresh"), 'speed': 4}
        u_hero.active_slots = [s0, s1]

        act = self.create_mass_action(u_boss, [u_hero])
        executed_slots = {(u_hero.name, 0)}

        engine = MagicMock()
        engine._create_roll_context.return_value = MagicMock(final_value=10, log=[])
        engine._process_card_self_scripts = MagicMock()  # Мокаем скрипты

        with patch('logic.battle_flow.mass_attack.random.choice') as mock_rand:
            def side_effect(seq):
                return seq[0]

            mock_rand.side_effect = side_effect

            process_mass_attack(engine, act, [u_hero], "Test", executed_slots)

            self.assertIn((u_hero.name, 1), executed_slots)
            self.assertIn((u_hero.name, 0), executed_slots)

        print("✅ Mass Attack автоматически выбрала свободный слот (S2) вместо занятого (S1).")

    def test_summation_clash_win(self):
        """
        3. Mass Summation (Победа):
        Сумма Атаки (10+10=20) > Сумма Защиты (5+5=10).
        Карта защитника уничтожается.
        """
        u_boss = self.create_unit("Boss")
        u_hero = self.create_unit("Hero")

        act = self.create_mass_action(u_boss, [u_hero], is_summation=True, dice_vals=[10, 10])
        self.prepare_defender(u_hero, card_dice_vals=[5, 5])

        engine = MagicMock()
        engine._process_card_self_scripts = MagicMock()

        def mock_roll(u, t, die, **kwargs):
            return MagicMock(final_value=die.min_val, log=[])

        engine._create_roll_context.side_effect = mock_roll

        executed_slots = set()

        process_mass_attack(engine, act, [u_hero], "R1", executed_slots)

        self.assertIn((u_hero.name, 0), executed_slots)
        self.assertIsNone(u_hero.active_slots[0]['card'], "Карта защитника должна быть уничтожена.")
        self.assertEqual(engine._apply_damage.call_count, 2)

        print("✅ Mass Summation Win: карта уничтожена, урон нанесен.")

    def test_individual_clash_mixed(self):
        """
        4. Mass Individual (Смешанный результат):
        Атака: [10, 2] vs Защита: [5, 5]
        """
        u_boss = self.create_unit("Boss")
        u_hero = self.create_unit("Hero")

        act = self.create_mass_action(u_boss, [u_hero], is_summation=False, dice_vals=[10, 2])
        self.prepare_defender(u_hero, card_dice_vals=[5, 5])

        engine = MagicMock()
        engine._process_card_self_scripts = MagicMock()

        def mock_roll(u, t, die, **kwargs):
            return MagicMock(final_value=die.min_val, log=[])

        engine._create_roll_context.side_effect = mock_roll

        executed_slots = set()
        report = process_mass_attack(engine, act, [u_hero], "R1", executed_slots)

        self.assertEqual(len(report), 2)
        self.assertIn("Hit", report[0]['outcome'])
        self.assertIn("Blocked", report[1]['outcome'])

        self.assertIsNotNone(u_hero.active_slots[0]['card'])
        self.assertIn((u_hero.name, 0), executed_slots)

        print("✅ Mass Individual Mixed: 1 пробитие, 1 блок.")

    def test_manual_targeting_undefended(self):
        """
        5. Ручной выбор цели (Manual Targeting):
        Атака в пустой слот -> One-Sided Attack.
        """
        u_boss = self.create_unit("Boss")
        u_hero = self.create_unit("Hero")

        u_hero.active_slots = [
            {'card': MagicMock(), 'speed': 5},
            {'card': None, 'speed': 3}
        ]

        act = self.create_mass_action(u_boss, [u_hero], is_summation=True)
        act['slot_data']['mass_defenses'] = {'0': "S2"}

        engine = MagicMock()
        engine._process_card_self_scripts = MagicMock()
        engine._create_roll_context.return_value = MagicMock(final_value=10, log=[])

        executed_slots = set()
        report = process_mass_attack(engine, act, [u_hero], "R1", executed_slots)

        # [FIX] Проверяем гибко, так как в отчете может быть эмодзи "💥 One-Sided Hit"
        details_str = " ".join(report[0]['details'])
        self.assertIn("One-Sided Hit", details_str)

        self.assertNotIn((u_hero.name, 1), executed_slots)

        print("✅ Manual Targeting в пустой слот -> One-Sided Hit.")


if __name__ == '__main__':
    unittest.main()