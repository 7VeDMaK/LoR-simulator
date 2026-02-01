import unittest
import sys
import os
import logging
import random

# Глушим логи Streamlit
logging.getLogger("streamlit").setLevel(logging.ERROR)

sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType

# Импортируем кастомные статусы (предполагаем, что они в logic/statuses/custom.py)
# Если они в common.py, поправьте импорт.
from logic.statuses.custom import (
    SelfControlStatus, SmokeStatus, RedLycorisStatus, SinisterAuraStatus,
    AdaptationStatus, BulletTimeStatus, EnrageTrackerStatus,
    InvisibilityStatus, SatietyStatus
)


class TestCustomStatuses(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnit(name="Tester", max_hp=100)
        self.target = MockUnit(name="Target", max_hp=100)

    # ==========================================
    # 1. Self Control (Самообладание)
    # ==========================================
    def test_self_control_crit(self):
        """Self Control дает шанс крита (x2 урон)."""
        status = SelfControlStatus()
        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)
        ctx.damage_multiplier = 1.0

        # Чтобы тест был детерминированным, хакнем random
        # random.randint(1, 100) <= chance
        # При 20 стаках шанс = 20 * 5 = 100%. Гарантированный крит.

        status.on_hit(ctx, stack=20)

        self.assertTrue(ctx.is_critical, "Должен быть крит при 100% шансе")
        self.assertEqual(ctx.damage_multiplier, 2.0, "Множитель должен быть x2")
        # Статус должен сняться (-20)
        # В моке remove_status просто вычитает из словаря.
        # Но у нас stack передается аргументом, а не берется из юнита в on_hit.
        # В коде on_hit: ctx.source.remove_status("self_control", 20)
        # Проверим вызов:
        self.unit.add_status("self_control", 20)  # Начальное состояние
        status.on_hit(ctx, stack=20)
        self.assertEqual(self.unit.get_status("self_control"), 0)

    def test_self_control_decay(self):
        """В конце раунда Self Control спадает на 20."""
        status = SelfControlStatus()
        self.unit.add_status("self_control", 25)

        status.on_round_end(self.unit, log_func=None)

        self.assertEqual(self.unit.get_status("self_control"), 5)  # 25 - 20 = 5

    # ==========================================
    # 2. Smoke (Дым)
    # ==========================================
    def test_smoke_bonus_power(self):
        """Если дыма >= 9, +1 к мощи."""
        status = SmokeStatus()
        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)

        # 8 стаков -> +0
        status.on_roll(ctx, stack=8)
        self.assertEqual(ctx.final_value, 0)

        # 9 стаков -> +1
        status.on_roll(ctx, stack=9)
        self.assertEqual(ctx.final_value, 1)  # Накопилось 0 + 1

    def test_smoke_damage_modifier(self):
        """Модификатор урона от дыма."""
        status = SmokeStatus()

        # Обычный режим (Атакующий): +5% за стак
        self.unit.memory["smoke_is_defensive"] = False
        mod = status.get_damage_modifier(self.unit, stack=10)
        self.assertAlmostEqual(mod, 0.5)  # 10 * 0.05 = 0.5 (+50%)

        # Защитный режим: -3% за стак (снижение урона)
        self.unit.memory["smoke_is_defensive"] = True
        mod = status.get_damage_modifier(self.unit, stack=10)
        self.assertAlmostEqual(mod, -0.3)  # 10 * -0.03 = -0.3 (-30%)

    def test_smoke_cap_decay(self):
        """Спад дыма и лимит."""
        status = SmokeStatus()
        # Лимит по дефолту 10. Ставим 15.
        self.unit.add_status("smoke", 15)

        status.on_round_end(self.unit, log_func=None)

        # 1. Decay -1 -> 14
        # 2. Check Limit (10). 14 > 10. Excess 4 removed.
        # Итог: 10.
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
        # Метод prevents_damage возвращает True
        self.assertTrue(status.prevents_damage(self.unit, None))

    # ==========================================
    # 4. Sinister Aura (Зловещая Аура)
    # ==========================================
    def test_sinister_aura(self):
        """Аура наносит урон по SP врага при его атаке."""
        # Ситуация: Враг (ctx.source) атакует Нас (ctx.target, у кого аура).
        # Но wait, код статуса:
        # def on_roll(self, ctx, stack):
        #    if ... target = ctx.target ...
        #    ctx.source.take_sanity_damage(...)
        # Логика: Тот, у кого статус (source), бьет target.
        # И от величия target (target.current_sp), source получает урон?
        # "от величия {target.name}" -> Похоже, что Аура висит на АТАКУЮЩЕМ,
        # и он получает урон от СП цели? Или наоборот?

        # Исходя из кода:
        # ctx.source (Атакующий с Аурой)
        # ctx.target (Жертва)
        # ctx.source.take_sanity_damage(target.sp // 10)
        # Значит: Атакующий с Аурой получает урон рассудку, зависящий от СП цели.

        status = SinisterAuraStatus()
        attacker = self.unit  # С аурой
        target = self.target  # Цель
        target.current_sp = 50  # 50 SP

        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(attacker, target=target, dice=dice)

        status.on_roll(ctx, stack=1)

        # Урон = 50 // 10 = 5.
        # Attacker (100) -> 95.
        self.assertEqual(attacker.current_sp, 95)

    # ==========================================
    # 5. Adaptation (Адаптация)
    # ==========================================
    def test_adaptation_resist(self):
        """Адаптация снижает урон от типа, к которому привыкла."""
        status = AdaptationStatus()
        # Запоминаем тип SLASH
        self.unit.memory["adaptation_active_type"] = DiceType.SLASH

        # Атака SLASH (совпадает)
        slash_dice = MockDice(DiceType.SLASH)
        res = status.modify_resistance(self.unit, 1.0, "hp", dice=slash_dice)
        self.assertEqual(res, 0.75)  # 1.0 * 0.75

        # Атака PIERCE (не совпадает)
        pierce_dice = MockDice(DiceType.PIERCE)
        res2 = status.modify_resistance(self.unit, 1.0, "hp", dice=pierce_dice)
        self.assertEqual(res2, 1.0)  # Без изменений

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

        # Получаем 10 урона
        status.on_take_damage(self.unit, amount=10, source=None)

        # Должно добавиться 10 силы
        self.assertEqual(self.unit.get_status("strength"), 10)

    # ==========================================
    # 8. Invisibility (Невидимость)
    # ==========================================
    def test_invisibility_break(self):
        """Невидимость спадает при ударе или проигрыше клэша."""
        status = InvisibilityStatus()
        self.unit.add_status("invisibility", 1)

        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)

        # Сценарий 1: On Hit
        status.on_hit(ctx)
        self.assertEqual(self.unit.get_status("invisibility"), 0)

        # Восстановим
        self.unit.add_status("invisibility", 1)

        # Сценарий 2: On Clash Lose
        status.on_clash_lose(ctx)
        self.assertEqual(self.unit.get_status("invisibility"), 0)

    # ==========================================
    # 9. Satiety (Сытость)
    # ==========================================
    def test_satiety_penalty(self):
        """Сытость >= 15 снижает инициативу."""
        status = SatietyStatus()

        # 14 стаков -> 0 штрафа
        stats = status.on_calculate_stats(self.unit, stack=14)
        self.assertEqual(stats, {})

        # 15 стаков -> -3 Init
        stats = status.on_calculate_stats(self.unit, stack=15)
        self.assertEqual(stats.get("initiative"), -3)

    def test_satiety_ignore(self):
        """Если есть статус ignore_satiety, штрафов нет."""
        status = SatietyStatus()
        self.unit.add_status("ignore_satiety", 1)

        stats = status.on_calculate_stats(self.unit, stack=20)
        self.assertEqual(stats, {})

    def test_satiety_damage(self):
        """Переедание наносит урон."""
        status = SatietyStatus()
        # Лимит 20. Ставим 22.
        self.unit.current_hp = 100

        # Передаем stack через kwargs, как в коде on_round_end
        status.on_round_end(self.unit, log_func=None, stack=22)

        # Excess = 2. Dmg = 2 * 10 = 20. HP = 80.
        self.assertEqual(self.unit.current_hp, 80)


if __name__ == '__main__':
    unittest.main()