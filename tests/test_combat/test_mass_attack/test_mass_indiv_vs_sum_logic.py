import unittest
from unittest.mock import MagicMock
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType, CardType
from logic.battle_flow.executor import execute_single_action
from logic.battle_flow.priorities import get_action_priority
from tests.mocks import MockUnit, MockDice


class TestMassIndivVsSumLogic(unittest.TestCase):

    def create_unit(self, name):
        u = MockUnit(name)
        u.is_dead = MagicMock(return_value=False)
        u.is_staggered = MagicMock(return_value=False)
        u.card_cooldowns = {}
        u.deck = []
        u.active_slots = []
        u.current_card = None
        return u

    def create_mass_action(self, source, targets, card_type_enum, speed, dice_vals):
        card = MagicMock()
        is_sum = (card_type_enum == CardType.MASS_SUMMATION)
        type_str = "Sum" if is_sum else "Ind"
        card.name = f"Mass_{type_str}_{speed}"

        card.card_type = card_type_enum.value
        card.tier = 3
        card.id = f"id_{card.name}"

        card.dice_list = []
        for val in dice_vals:
            # Для Масс Атак кубики обычно Slash (Атакующие)
            d = MockDice(DiceType.SLASH)
            d.min_val = val
            d.max_val = val
            card.dice_list.append(d)

        slot = {'card': card, 'speed': speed, 'destroy_on_speed': False, 'mass_defenses': {}}
        source.active_slots = [slot]
        source.current_card = card

        return {
            'label': card.name,
            'source': source,
            'source_idx': 0,
            'target_unit': targets[0],
            'target_slot_idx': 0,
            # [ВАЖНО] Приводим к нижнему регистру для executor.py
            'card_type': str(card.card_type).lower(),
            'slot_data': slot,
            'is_left': True,
            'opposing_team': targets
        }

    def sort_actions(self, actions):
        return sorted(
            actions,
            key=lambda x: (get_action_priority(x['slot_data']['card']), x['slot_data']['speed']),
            reverse=True
        )

    def test_individual_attacker_does_not_trigger_defense_summation(self):
        """
        Проверка: Individual (Атака) vs Summation (Защита).

        Атака (Individual): [10, 10]
        Защита (Summation): [15, 2]

        Ожидание:
        1. Clash 1: 10 vs 15 -> Blocked
        2. Clash 2: 10 vs 2  -> Hit

        Это докажет, что кубики защиты (Summation) НЕ складываются (15+2=17),
        а работают индивидуально.
        """
        unit_indiv = self.create_unit("Unit_Individual")
        unit_sum = self.create_unit("Unit_Summation")

        # 1. Individual (Быстрее - Spd 20). Dice: [10, 10]
        act_indiv = self.create_mass_action(unit_indiv, [unit_sum], CardType.MASS_INDIVIDUAL, 20, [10, 10])

        # 2. Summation (Медленнее - Spd 1). Dice: [15, 2]
        act_sum = self.create_mass_action(unit_sum, [unit_indiv], CardType.MASS_SUMMATION, 1, [15, 2])

        actions = self.sort_actions([act_indiv, act_sum])
        self.assertEqual(actions[0]['label'], act_indiv['label'])

        executed_slots = set()
        engine = MagicMock()
        engine._process_card_self_scripts = MagicMock()
        # Мокаем роллы: просто возвращаем значение кубика
        engine._create_roll_context.side_effect = lambda u, t, d, **k: MagicMock(final_value=d.min_val if d else 0,
                                                                                 log=[])

        # ВЫПОЛНЕНИЕ (Individual атакует)
        report = execute_single_action(engine, actions[0], executed_slots)

        self.assertEqual(len(report), 2, "Должно быть 2 отдельных столкновения (Individual Logic)")

        # --- ПРОВЕРКА 1-го КУБИКА ---
        # 10 vs 15
        clash1 = report[0]
        self.assertEqual(clash1['left']['val'], 10)
        self.assertEqual(clash1['right']['val'], 15)
        self.assertIn("Blocked", clash1['outcome'])  # 10 < 15

        # --- ПРОВЕРКА 2-го КУБИКА ---
        # 10 vs 2
        clash2 = report[1]
        self.assertEqual(clash2['left']['val'], 10)
        self.assertEqual(clash2['right']['val'], 2)
        self.assertIn("Hit", clash2['outcome'])  # 10 > 2

        # --- ПРОВЕРКА КАРТЫ ЗАЩИТНИКА ---
        # Слот должен быть помечен как "использованный" (executed)
        self.assertIn((unit_sum.name, 0), executed_slots)

        # Но сама карта (Summation) обычно не уничтожается при попадании Individual атаки,
        # она просто ломает свои кубики (dice broken) или остается использованной.
        # В нашей реализации mass_attack.py (строка 222) нет удаления карты целиком,
        # только сообщение "Die broken".
        self.assertIsNotNone(unit_sum.active_slots[0]['card'])

        print("✅ Тест пройден: Mass Individual разбила Mass Summation по частям (1 Block, 1 Hit).")
        print("   Это доказывает, что защитная Summation карта НЕ суммировала свои значения.")


if __name__ == '__main__':
    unittest.main()