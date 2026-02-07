import unittest
import sys
import os
import logging

# Убираем шум
logging.getLogger("streamlit").setLevel(logging.ERROR)

sys.path.append(os.getcwd())

from tests.mocks import MockUnit, MockContext, MockDice
from core.enums import DiceType

# Импортируем классы статусов (предполагаем, что они в logic/statuses/common.py или custom.py)
# Если вы еще не разнесли их по файлам, сохраните код статусов в logic/statuses/common.py
from logic.statuses.common import (
    AttackPowerUpStatus, EnduranceStatus, AttackPowerDownStatus, ParalysisStatus,
    HasteStatus, BindStatus,
    DmgUpStatus, DmgDownStatus,
    ProtectionStatus, FragileStatus, VulnerableStatus, WeaknessStatus, WeakStatus, StaggerResistStatus,
    BleedStatus, BurnStatus, DeepWoundStatus, RuptureStatus,
    BarrierStatus
)


class TestStatuses(unittest.TestCase):

    def setUp(self):
        self.unit = MockUnit(name="Tester", max_hp=100)
        self.target = MockUnit(name="Target", max_hp=100)

    # ==========================================
    # 1. МОДИФИКАТОРЫ СИЛЫ КУБИКОВ
    # ==========================================

    def test_attack_power_up(self):
        """Сила должна увеличивать атакующие броски."""
        status = AttackPowerUpStatus()
        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)

        # 3 стака Силы
        status.on_roll(ctx, stack=3)
        self.assertEqual(ctx.final_value, 3)

    def test_endurance(self):
        """Стойкость должна увеличивать защитные броски."""
        status = EnduranceStatus()
        dice = MockDice(DiceType.BLOCK)  # Блок
        ctx = MockContext(self.unit, dice=dice)

        status.on_roll(ctx, stack=2)
        self.assertEqual(ctx.final_value, 2)

    def test_attack_power_down(self):
        """Снижение силы атаки."""
        status = AttackPowerDownStatus()
        dice = MockDice(DiceType.PIERCE)
        ctx = MockContext(self.unit, dice=dice)

        status.on_roll(ctx, stack=2)
        self.assertEqual(ctx.final_value, -2)

    def test_paralysis(self):
        """Паралич снижает бросок на разницу (min - roll), если roll < min."""
        status = ParalysisStatus()
        self.unit.add_status("paralysis", 3)

        dice = MockDice(DiceType.SLASH, min_val=5, max_val=10)
        ctx = MockContext(self.unit, dice=dice)

        # --- СЦЕНАРИЙ 1: Низкий ролл (2) ---
        # 2 < 5. Разница положительная (3), но условие diff < 0.
        # min(5) - base(2) = 3. 3 !< 0. Модификации нет.
        ctx.base_value = 2
        status.on_roll(ctx)
        # Стаков стало: 3 - 1 = 2

        # --- СЦЕНАРИЙ 2: Высокий ролл (8) ---
        # 8 > 5.
        # min(5) - base(8) = -3. -3 < 0. Модификация -3.
        ctx.base_value = 8
        status.on_roll(ctx)
        # Стаков стало: 2 - 1 = 1

        # Проверяем снижение силы
        # Примечание: final_value в моке накопительный, если первый вызов ничего не дал (0),
        # то после второго там будет -3.
        self.assertEqual(ctx.final_value, -3)

        # [FIX] Проверяем стаки: 2 раза вызвался on_roll -> снялось 2 стака. Остался 1.
        self.assertEqual(self.unit.get_status("paralysis"), 1)

    def test_vulnerable(self):
        """Рассредоточенность снижает защиту."""
        status = VulnerableStatus()
        dice = MockDice(DiceType.EVADE)
        ctx = MockContext(self.unit, dice=dice)

        status.on_roll(ctx, stack=4)
        self.assertEqual(ctx.final_value, -4)

    # ==========================================
    # 2. СКОРОСТЬ
    # ==========================================

    def test_haste_bind(self):
        """Спешка и Замедление."""
        haste = HasteStatus()
        bind = BindStatus()

        mod_h = haste.get_speed_dice_value_modifier(self.unit, stack=3)
        self.assertEqual(mod_h, 3)

        mod_b = bind.get_speed_dice_value_modifier(self.unit, stack=2)
        self.assertEqual(mod_b, -2)

    # ==========================================
    # 3. МОДИФИКАТОРЫ УРОНА (ВХОД/ВЫХОД)
    # ==========================================

    def test_dmg_up_down(self):
        """Усиление и ослабление исходящего урона."""
        up = DmgUpStatus()
        down = DmgDownStatus()

        val = up.modify_outgoing_damage(self.unit, 10, "hp", stack=5)
        self.assertEqual(val, 15)

        val = down.modify_outgoing_damage(self.unit, 10, "hp", stack=3)
        self.assertEqual(val, 7)

    def test_protection_fragile(self):
        """Защита и Хрупкость (Входящий урон)."""
        prot = ProtectionStatus()
        frag = FragileStatus()
        weak = WeaknessStatus()

        # Protection: 10 урона - 4 защиты = 6
        res = prot.modify_incoming_damage(self.unit, 10, "hp", stack=4)
        self.assertEqual(res, 6)

        # Fragile: 10 урона + 3 хрупкости = 13
        res = frag.modify_incoming_damage(self.unit, 10, "hp", stack=3)
        self.assertEqual(res, 13)

        # Weakness (то же самое, что Fragile в базовом классе)
        res = weak.modify_incoming_damage(self.unit, 10, "hp", stack=2)
        self.assertEqual(res, 12)

    def test_weak_percent(self):
        """Слабость (Weak): +25% урона."""
        status = WeakStatus()
        # 20 урона * 1.25 = 25
        res = status.modify_incoming_damage(self.unit, 20, "hp", stack=1)
        self.assertEqual(res, 25)

    def test_stagger_resist(self):
        """Stagger Resist снижает урон по стаггеру."""
        status = StaggerResistStatus()
        # 100 Stagger Dmg * 0.67 = 67
        res = status.modify_incoming_damage(self.unit, 100, "stagger", stack=1)
        self.assertEqual(res, 67)

    # ==========================================
    # 4. DOT ЭФФЕКТЫ
    # ==========================================

    def test_bleed(self):
        """Кровотечение при атаке."""
        status = BleedStatus()
        dice = MockDice(DiceType.SLASH)
        ctx = MockContext(self.unit, dice=dice)  # self.unit атакует

        # 10 стаков кровотечения
        self.unit.current_hp = 100

        status.on_hit(ctx, stack=10)

        # Урон = стаки = 10. HP = 90.
        self.assertEqual(self.unit.current_hp, 90)
        # Стаки должны уменьшиться на половину (10 // 2 = 5 снимаем)
        # В моке remove_status просто вызывается, проверим лог или состояние
        # (MockUnit.remove_status нужно, чтобы bleed был в словаре)
        # В тесте status.on_hit вызывает remove_status.
        # Для проверки нам нужно, чтобы стаки были в юните.
        self.unit.statuses["bleed"] = 10
        status.on_hit(ctx, stack=10)  # Второй вызов, но логика та же
        self.assertEqual(self.unit.get_status("bleed"), 5)  # 10 - 5 = 5

    def test_burn(self):
        """Ожог в конце раунда."""
        status = BurnStatus()
        self.unit.statuses["burn"] = 8
        self.unit.current_hp = 100

        # Конец раунда
        msgs = status.on_round_end(self.unit, stack=8)

        # Урон = 8. HP = 92.
        self.assertEqual(self.unit.current_hp, 92)
        # Стаки делятся на 2: 8 -> 4.
        self.assertEqual(self.unit.get_status("burn"), 4)
        self.assertIn("🔥 Burn: -8 HP", msgs)

    def test_rupture(self):
        """Разрыв: доп урон при получении урона."""
        status = RuptureStatus()
        self.unit.statuses["rupture"] = 10
        self.unit.current_hp = 100

        # Триггерим получение урона (например, 5 от удара)
        status.on_take_damage(self.unit, amount=5, source=self.target)

        # Доп урон = 10. Итого HP = 100 - 10 = 90 (amount 5 вычитается движком отдельно)
        # В тесте мы проверяем только эффект статуса (он вычитает extra_dmg)
        self.assertEqual(self.unit.current_hp, 90)

        # Стаки уменьшаются: 10 // 2 = 5.
        self.assertEqual(self.unit.get_status("rupture"), 5)

    def test_deep_wound(self):
        """Глубокая рана: урон при защите."""
        status = DeepWoundStatus()
        self.unit.statuses["deep_wound"] = 4
        self.unit.current_hp = 100

        dice = MockDice(DiceType.BLOCK)
        ctx = MockContext(self.unit, dice=dice)

        status.on_roll(ctx, stack=4)

        # Урон = 4. HP = 96.
        self.assertEqual(self.unit.current_hp, 96)
        # Накладывается Bleed = 4
        self.assertEqual(self.unit.get_status("bleed"), 4)

    # ==========================================
    # 5. БАРЬЕРЫ
    # ==========================================

    def test_barrier(self):
        """Барьер поглощает урон."""
        status = BarrierStatus()
        self.unit.statuses["barrier"] = 10

        # Входящий урон 15
        remaining = status.absorb_damage(self.unit, 15, "hp", stack=10)

        # Поглощено 10, осталось 5
        self.assertEqual(remaining, 5)
        # Барьер должен исчезнуть
        self.assertEqual(self.unit.get_status("barrier"), 0)

    def test_barrier_partial(self):
        """Барьер больше урона."""
        status = BarrierStatus()
        self.unit.statuses["barrier"] = 20

        # Входящий урон 5
        remaining = status.absorb_damage(self.unit, 5, "hp", stack=20)

        # Весь урон поглощен
        self.assertEqual(remaining, 0)
        # Барьер уменьшился: 20 - 5 = 15
        self.assertEqual(self.unit.get_status("barrier"), 15)


if __name__ == '__main__':
    unittest.main()