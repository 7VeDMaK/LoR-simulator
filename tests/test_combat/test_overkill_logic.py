import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.getcwd())

from core.enums import DiceType
from logic.battle_flow.clash.clash import process_clash


# === CUSTOM MOCKS ===

class OverkillMockUnit:
    """Юнит, поддерживающий отрицательное HP для тестов."""

    def __init__(self, name, hp=10):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.stagger = 20
        self.active_slots = []
        self.current_card = None
        self.counter_dice = []
        self.passive_counter_queue = []
        self.stored_dice = []
        self.current_die = None  # Для трекинга

    def is_dead(self):
        # Юнит считается мертвым, но объект существует
        return self.hp <= 0

    def is_staggered(self):
        return False

    def take_damage(self, amount):
        # [ВАЖНО] Логика Overkill: HP уходит в минус, не клампится
        self.hp -= amount


class MockDice:
    def __init__(self, val, is_counter=False):
        self.dtype = DiceType.SLASH
        self.min_val = val
        self.max_val = val
        self.is_counter = is_counter


class TestOverkillLogic(unittest.TestCase):

    def setUp(self):
        self.engine = MagicMock()

        # Настраиваем роллы
        def mock_roll(u, t, die, **kwargs):
            ctx = MagicMock()
            ctx.source = u
            ctx.target = t
            ctx.final_value = die.min_val
            ctx.log = []
            return ctx

        self.engine._create_roll_context.side_effect = mock_roll

        # Настраиваем нанесение урона через движок
        # В clash_resolution вызывается _resolve_clash_interaction
        def mock_resolve_interaction(ctx_atk, ctx_def, diff):
            damage = diff  # Просто разница
            # Наносим урон цели (ctx_def - это проигравший защитник, или наоборот)
            # В коде resolution: if val_a > val_d -> resolve(ctx_a, ctx_d, ...)
            # Значит ctx_d - это тот, кто получает урон
            if ctx_def and hasattr(ctx_def.source, 'take_damage'):
                ctx_def.source.take_damage(damage)
            return damage

        self.engine._resolve_clash_interaction.side_effect = mock_resolve_interaction

        self.engine._handle_clash_win = MagicMock()
        self.engine._handle_clash_lose = MagicMock()
        self.engine._handle_clash_draw = MagicMock()

    def test_hp_goes_negative(self):
        """
        Проверка: Юнит (HP 5) получает 20 урона.
        Результат: HP должно стать -15.
        """
        u = OverkillMockUnit("Dummy", hp=5)
        u.take_damage(20)
        self.assertEqual(u.hp, -15, "HP должно уходить в минус для накопления Overkill.")

    def test_attack_continues_after_death_in_clash(self):
        """
        Сценарий:
        Attacker (3 кубика по 20) vs Defender (1 кубик по 5, HP=10).

        Ход боя:
        1. Clash 1: 20 vs 5 -> Defender получает 15 урона. HP: 10 -> -5 (Dead).
        2. Clash 2: 20 vs (Empty/One-Sided).
        3. Clash 3: 20 vs (Empty/One-Sided).

        Ожидание:
        Атака НЕ должна прерываться после смерти цели. Все 3 кубика должны отработать.
        Итоговый HP должен быть (10 - 15 - 20 - 20) = -45.
        """
        attacker = OverkillMockUnit("Attacker", hp=100)
        defender = OverkillMockUnit("Defender", hp=10)

        # Атакующий: 3 мощных удара
        attacker.current_card = MagicMock()
        attacker.current_card.dice_list = [MockDice(20), MockDice(20), MockDice(20)]

        # Защитник: 1 слабый блок/атака (потратится на первом)
        defender.current_card = MagicMock()
        defender.current_card.dice_list = [MockDice(5)]

        # Нам нужно, чтобы One-Sided тоже наносил урон
        # Мокаем handle_one_sided_exchange, так как после 1-го кубика у защитника кончатся карты
        def mock_onesided(eng, active_side, passive_side, detail_logs):
            # Эмуляция: активный кубик бьет пассивного юнита
            die = active_side.resolve_current_die()
            target = passive_side.unit
            if die and target:
                dmg = die.min_val  # Полный урон (20)
                target.take_damage(dmg)
                return "Hit (Overkill)"
            return "Skip"

        with patch('logic.battle_flow.clash.clash.handle_one_sided_exchange', side_effect=mock_onesided):
            # [ВАЖНО] Если в process_clash есть проверка "if defender.is_dead(): break",
            # то этот тест упадет (HP будет -5, а не -45).
            report = process_clash(self.engine, attacker, defender, "R1", True, 10, 5)

            print(f"Final Defender HP: {defender.hp}")

            # Проверяем, что было 3 раунда (3 удара)
            self.assertEqual(len(report), 3, "Должно быть 3 раунда (атака не должна останавливаться).")

            # Проверяем итоговый Overkill
            # -5 (после 1 удара) - 20 (2 удар) - 20 (3 удар) = -45
            self.assertEqual(defender.hp, -45, "Система должна накапливать оверкилл даже по трупу.")


if __name__ == '__main__':
    unittest.main()