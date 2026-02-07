import threading
import unittest
import sys
import os
import logging
import random
from unittest.mock import MagicMock, patch

# Глушим логи Streamlit
os.environ["STREAMLIT_LOG_LEVEL"] = "error"
logging.getLogger("streamlit").setLevel(logging.ERROR)
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)

try:
    from streamlit.runtime.scriptrunner import add_script_run_context
    for thread in threading.enumerate():
        add_script_run_context(thread)
except ImportError:
    pass

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType

sys.path.append(os.getcwd())
# Импортируем все кастомные статусы
from logic.statuses.custom import (
    SelfControlStatus, SmokeStatus, RedLycorisStatus, SinisterAuraStatus,
    AdaptationStatus, BulletTimeStatus, EnrageTrackerStatus,
    InvisibilityStatus, SatietyStatus,
    ArrestedStatus, SlashResistDownStatus, PierceResistDownStatus, BluntResistDownStatus,
    RegenGanacheStatus, RevengeDmgUpStatus, MentalProtectionStatus,
    MainCharacterShellStatus, AzinoJackpotStatus, AzinoBeastStatus,
    LuckyCoinStatus, StatusAntiCharge, UnderCrosshairsStatus, AmmoStatus,
    StaggerImmuneStatus
)


class TestCustomStatuses(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnit(name="Tester", max_hp=100)
        self.target = MockUnit(name="Target", max_hp=100)

        # Добавляем поля, необходимые для тестов (Stagger, SP и т.д.)
        self.unit.current_stagger = 100
        self.unit.max_stagger = 100
        self.unit.current_sp = 100  # Нужно для SinisterAuraStatus
        self.target.current_sp = 100

    # ==========================================
    # 1. Self Control (Самообладание)
    # ==========================================
    def test_self_control_crit(self):
        """Self Control дает шанс крита (x2 урон)."""
        status = SelfControlStatus()
        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)
        ctx.damage_multiplier = 1.0

        # Гарантируем срабатывание random (1 <= chance)
        with patch('random.randint', return_value=1):
            status.on_hit(ctx, stack=20)

        self.assertTrue(ctx.is_critical, "Должен быть крит при 100% шансе")
        self.assertEqual(ctx.damage_multiplier, 2.0, "Множитель должен быть x2")

        # Проверяем снятие статуса
        self.unit.add_status("self_control", 20)
        status.on_hit(ctx, stack=20)
        self.assertEqual(self.unit.get_status("self_control"), 0)

    def test_self_control_decay(self):
        """В конце раунда Self Control спадает на 20."""
        status = SelfControlStatus()
        self.unit.add_status("self_control", 25)

        status.on_round_end(self.unit, log_func=None)

        self.assertEqual(self.unit.get_status("self_control"), 5)

    # ==========================================
    # 2. Smoke (Дым)
    # ==========================================
    def test_smoke_bonus_power(self):
        """Если дыма >= 9, +1 к мощи."""
        status = SmokeStatus()
        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)

        status.on_roll(ctx, stack=8)
        self.assertEqual(ctx.final_value, 0)

        status.on_roll(ctx, stack=9)
        self.assertEqual(ctx.final_value, 1)

    def test_smoke_damage_modifier(self):
        """Модификатор урона от дыма."""
        status = SmokeStatus()

        # Обычный режим (Атакующий): +5% за стак
        self.unit.memory["smoke_is_defensive"] = False
        mod = status.get_damage_modifier(self.unit, stack=10)
        self.assertAlmostEqual(mod, 0.5)

        # Защитный режим: -3% за стак
        self.unit.memory["smoke_is_defensive"] = True
        mod = status.get_damage_modifier(self.unit, stack=10)
        self.assertAlmostEqual(mod, -0.3)

    def test_smoke_cap_decay(self):
        """Спад дыма и лимит."""
        status = SmokeStatus()
        self.unit.add_status("smoke", 15)
        status.on_round_end(self.unit, log_func=None)
        self.assertEqual(self.unit.get_status("smoke"), 10)

    # ==========================================
    # 3. Red Lycoris (Ликорис)
    # ==========================================
    def test_red_lycoris_stats(self):
        """Ликорис дает безумную инициативу."""
        status = RedLycorisStatus()
        stats = status.on_calculate_stats(self.unit)
        self.assertEqual(stats["initiative"], 999)

    def test_red_lycoris_immunity(self):
        """Ликорис дает иммунитет к урону."""
        status = RedLycorisStatus()
        self.assertTrue(status.prevents_damage(self.unit, None))

    # ==========================================
    # 4. Sinister Aura (Зловещая Аура)
    # ==========================================
    def test_sinister_aura(self):
        """Аура наносит урон по SP владельца при его атаке."""
        status = SinisterAuraStatus()
        attacker = self.unit
        target = self.target
        target.current_sp = 50

        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(attacker, target=target, dice=dice)

        status.on_roll(ctx, stack=1)

        # Урон = 50 // 10 = 5. SP: 100 -> 95.
        self.assertEqual(attacker.current_sp, 95)

    # ==========================================
    # 5. Adaptation (Адаптация)
    # ==========================================
    def test_adaptation_resist(self):
        """Адаптация снижает урон от привычного типа."""
        status = AdaptationStatus()
        self.unit.memory["adaptation_active_type"] = DiceType.SLASH

        slash_dice = MockDice(DiceType.SLASH)
        res = status.modify_resistance(self.unit, 1.0, "hp", dice=slash_dice)
        self.assertEqual(res, 0.75)

        pierce_dice = MockDice(DiceType.PIERCE)
        res2 = status.modify_resistance(self.unit, 1.0, "hp", dice=pierce_dice)
        self.assertEqual(res2, 1.0)

    # ==========================================
    # 6. Bullet Time
    # ==========================================
    def test_bullet_time_evade(self):
        """Bullet Time делает уворот максимальным."""
        status = BulletTimeStatus()
        dice = MockDice(DiceType.EVADE, max_val=20)
        ctx = MockContext(self.unit, dice=dice)

        status.on_roll(ctx, stack=1)
        self.assertEqual(ctx.final_value, 20)

    def test_bullet_time_attack(self):
        """Bullet Time обнуляет атаку."""
        status = BulletTimeStatus()
        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)
        ctx.damage_multiplier = 1.0

        status.on_roll(ctx, stack=1)
        self.assertEqual(ctx.final_value, 0)
        self.assertEqual(ctx.damage_multiplier, 0.0)

    # ==========================================
    # 7. Enrage Tracker (Разозлить)
    # ==========================================
    def test_enrage_tracker(self):
        """Получение урона дает Силу."""
        status = EnrageTrackerStatus()
        status.on_take_damage(self.unit, amount=10, source=None)
        self.assertEqual(self.unit.get_status("attack_power_up"), 10)

    # ==========================================
    # 8. Invisibility (Невидимость)
    # ==========================================
    def test_invisibility_break(self):
        """Невидимость спадает при ударе или проигрыше клэша."""
        status = InvisibilityStatus()
        self.unit.add_status("invisibility", 1)

        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)

        status.on_hit(ctx)
        self.assertEqual(self.unit.get_status("invisibility"), 0)

        self.unit.add_status("invisibility", 1)
        status.on_clash_lose(ctx)
        self.assertEqual(self.unit.get_status("invisibility"), 0)

    # ==========================================
    # 9. Satiety (Сытость)
    # ==========================================
    def test_satiety_penalty(self):
        """Сытость >= 15 снижает инициативу."""
        status = SatietyStatus()
        stats = status.on_calculate_stats(self.unit, stack=14)
        self.assertEqual(stats, {})

        stats = status.on_calculate_stats(self.unit, stack=15)
        self.assertEqual(stats.get("initiative"), -3)

    def test_satiety_ignore(self):
        """ignore_satiety предотвращает штрафы."""
        status = SatietyStatus()
        self.unit.add_status("ignore_satiety", 1)
        stats = status.on_calculate_stats(self.unit, stack=20)
        self.assertEqual(stats, {})

    def test_satiety_damage(self):
        """Переедание наносит урон."""
        status = SatietyStatus()
        self.unit.current_hp = 100
        # Лимит 20, стаков 22 -> excess 2 -> dmg 20
        status.on_round_end(self.unit, log_func=None, stack=22)
        self.assertEqual(self.unit.current_hp, 80)

    # ==========================================
    # 10. Arrested (Арестован)
    # ==========================================
    def test_arrested_stats(self):
        """Arrested дает -20 ко всем характеристикам."""
        status = ArrestedStatus()
        stats = status.on_calculate_stats(self.unit)
        self.assertEqual(stats["strength"], -20)
        self.assertEqual(stats["speed"], -20)
        self.assertEqual(stats["wisdom"], -20)

    # ==========================================
    # 11. Resist Down (Ахиллесова пята и др.)
    # ==========================================
    def test_resist_down(self):
        """Проверка статусов снижения сопротивления."""
        # Slash
        s_status = SlashResistDownStatus()
        # stack 2 -> +0.5 к получаемому урону (резист растет)
        res = s_status.modify_resistance(self.unit, 1.0, "slash", stack=2)
        self.assertEqual(res, 1.5)

        # Pierce
        p_status = PierceResistDownStatus()
        res = p_status.modify_resistance(self.unit, 1.0, "pierce", stack=4)
        self.assertEqual(res, 2.0)

        # Blunt
        b_status = BluntResistDownStatus()
        res = b_status.modify_resistance(self.unit, 1.0, "blunt", stack=1)
        self.assertEqual(res, 1.25)

        # Проверка неверного типа урона
        res = s_status.modify_resistance(self.unit, 1.0, "blunt", stack=2)
        self.assertEqual(res, 1.0)

    # ==========================================
    # 12. Regen Ganache
    # ==========================================
    def test_regen_ganache(self):
        """Ганаш регенерирует 5% HP в начале раунда."""
        status = RegenGanacheStatus()
        self.unit.current_hp = 50
        self.unit.max_hp = 100

        status.on_round_start(self.unit, log_func=None)
        self.assertEqual(self.unit.current_hp, 55)  # 50 + 5

    # ==========================================
    # 13. Revenge Damage Up (Месть)
    # ==========================================
    def test_revenge_dmg_up(self):
        """Месть дает x1.5 урона при попадании и исчезает."""
        status = RevengeDmgUpStatus()
        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)
        ctx.damage_multiplier = 1.0

        self.unit.add_status("revenge_dmg_up", 1)
        status.on_hit(ctx, stack=1)

        self.assertEqual(ctx.damage_multiplier, 1.5)
        self.assertEqual(self.unit.get_status("revenge_dmg_up"), 0)

    # ==========================================
    # 14. Mental Protection (Сырная защита)
    # ==========================================
    def test_mental_protection(self):
        """Ментальная защита снижает урон по SP."""
        status = MentalProtectionStatus()

        # 2 стака -> 50% снижение (min(0.5, 2*0.25))
        # Урон 10 -> 5
        dmg = status.modify_incoming_damage(self.unit, 10, "sp", stack=2)
        self.assertEqual(dmg, 5)

        # Проверка капа (10 стаков все равно макс 50%)
        dmg = status.modify_incoming_damage(self.unit, 10, "sp", stack=10)
        self.assertEqual(dmg, 5)

        # Не SP урон не снижается
        dmg = status.modify_incoming_damage(self.unit, 10, "hp", stack=2)
        self.assertEqual(dmg, 10)

    # ==========================================
    # 15. Main Character Shell (Сюжетная броня)
    # ==========================================
    def test_main_character_shell_hp(self):
        """Броня не дает HP упасть ниже 1."""
        status = MainCharacterShellStatus()
        self.unit.current_hp = 10
        self.unit.add_status("main_character_shell", 1)

        # Урон 20 -> HP должно стать 1 (урон 9)
        taken = status.modify_incoming_damage(self.unit, 20, "hp")
        self.assertEqual(taken, 9)

        # Проверка удаления после срабатывания (в конце раунда)
        status.on_round_end(self.unit)
        self.assertEqual(self.unit.get_status("main_character_shell"), 0)

    def test_main_character_shell_stagger(self):
        """Броня не дает Stagger упасть ниже 1."""
        status = MainCharacterShellStatus()
        self.unit.current_stagger = 10
        self.unit.memory["main_character_shell_triggered"] = False

        taken = status.modify_incoming_damage(self.unit, 20, "stagger")
        self.assertEqual(taken, 9)

    # ==========================================
    # 16. Azino Jackpot
    # ==========================================
    def test_azino_jackpot_roll(self):
        """Джекпот максимизирует бросок и дает крит."""
        status = AzinoJackpotStatus()
        dice = MockDice(DiceType.SLASH, max_val=8)
        ctx = MockContext(self.unit, dice=dice)

        status.on_roll(ctx, stack=1)

        self.assertEqual(ctx.final_value, 8)
        self.assertTrue(ctx.is_critical)
        self.assertTrue(status.prevents_damage(self.unit, None))

    # ==========================================
    # 17. Azino Beast (666)
    # ==========================================
    def test_azino_beast_mechanics(self):
        """Число Зверя дает статы, урон, но бьет владельца."""
        status = AzinoBeastStatus()

        # Stats
        stats = status.on_calculate_stats(self.unit)
        self.assertEqual(stats["strength"], 6)

        # On Hit
        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)
        ctx.damage_multiplier = 1.0
        self.unit.current_hp = 100

        status.on_hit(ctx, stack=1)

        self.assertAlmostEqual(ctx.damage_multiplier, 1.66)
        self.assertEqual(self.unit.current_hp, 94)  # 100 - 6

    # ==========================================
    # 18. Lucky Coin (Монетка)
    # ==========================================
    def test_lucky_coin_heads(self):
        """Орел: Авто-победа (9999)."""
        status = LuckyCoinStatus()
        dice = MockDice(DiceType.SLASH, min_val=5, max_val=10)
        ctx = MockContext(self.unit, dice=dice)

        # Мокаем карту
        self.unit.current_card = MagicMock()
        self.unit.current_card.id = "card_heads"

        # Мокаем random.choice -> True (Орел)
        with patch('random.choice', return_value=True):
            status.on_roll(ctx, stack=1)

        self.assertEqual(ctx.final_value, 9999)
        self.assertTrue(ctx.is_critical)
        self.assertEqual(self.unit.memory[f"lucky_coin_result_card_heads"], "HEADS")

    def test_lucky_coin_tails(self):
        """Решка: Провал и урон по себе."""
        status = LuckyCoinStatus()
        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)

        self.unit.current_card = MagicMock()
        self.unit.current_card.id = "card_tails"
        self.unit.max_hp = 100
        self.unit.current_hp = 100

        # Мокаем random.choice -> False (Решка)
        with patch('random.choice', return_value=False):
            status.on_roll(ctx, stack=1)

        self.assertEqual(ctx.final_value, 0)
        self.assertTrue(ctx.dice.is_broken)
        # Урон 15% от 100 = 15
        self.assertEqual(self.unit.current_hp, 85)

    # ==========================================
    # 19. Anti-Charge (Анти-Заряд)
    # ==========================================
    def test_anti_charge(self):
        """Анти-Заряд снижает мощь и скорость."""
        status = StatusAntiCharge()

        # Power (-3 за стак)
        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)
        status.on_roll(ctx, stack=2)
        self.assertEqual(ctx.final_value, -6)

        # Speed
        speed_mod = status.get_speed_dice_value_modifier(self.unit, stack=3)
        self.assertEqual(speed_mod, -9)

    # ==========================================
    # 20. Under Crosshairs (Под Прицелом)
    # ==========================================
    def test_under_crosshairs(self):
        """Увеличивает входящий урон."""
        status = UnderCrosshairsStatus()

        # Stack 2 -> +50% урона (1.0 + 0.25*2)
        dmg = status.modify_incoming_damage(self.unit, 20, "hp", stack=2)
        self.assertEqual(dmg, 30)

    # ==========================================
    # 21. Stagger Immune
    # ==========================================
    def test_stagger_immune(self):
        """Полностью блокирует урон по Stagger."""
        status = StaggerImmuneStatus()
        dmg = status.modify_incoming_damage(self.unit, 50, "stagger")
        self.assertEqual(dmg, 0)

    # ==========================================
    # 22. Ammo (Боеприпасы)
    # ==========================================
    def test_ammo_gun(self):
        """Ammo усиливает оружие типа 'gun' и тратится."""
        status = AmmoStatus()
        self.unit.add_status("ammo", 5)
        self.unit.weapon_id = "test_gun"

        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)

        # Мокаем реестр оружия, который импортируется внутри метода on_roll.
        # Используем patch.dict для sys.modules, чтобы подменить модуль logic.weapon_definitions
        mock_registry = {
            "test_gun": MagicMock(weapon_type="gun")
        }

        with patch.dict("sys.modules", {"logic.weapon_definitions": MagicMock()}):
            sys.modules["logic.weapon_definitions"].WEAPON_REGISTRY = mock_registry

            status.on_roll(ctx)

            self.assertEqual(self.unit.get_status("ammo"), 4)  # Потратился 1
            self.assertEqual(ctx.final_value, 2)  # Бонус +2


if __name__ == '__main__':
    unittest.main()