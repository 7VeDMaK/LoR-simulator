# ==========================================
# Махнуть хвостиком (Wag Tail)
# ==========================================
from core.dice import Dice
from core.enums import DiceType
from logic.context import RollContext
from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# Махнуть хвостиком (Wag Tail)
# ==========================================
class PassiveWagTail(BasePassive):
    id = "wag_tail"
    name = "Махнуть хвостиком"
    description = "🐈 (Пассивно) Каждый раунд добавляет 1 Counter Evade (5-7) в пул контр-атак."
    is_active_ability = False

    def on_round_start(self, unit, log_func, **kwargs):
        # Create the counter evade die
        # Note: 5-7 range as per description
        evade_die = Dice(5, 7, DiceType.EVADE, is_counter=True)

        # Add to the unit's counter dice pool
        # This list is cleared every round in roll_speed_dice
        if not hasattr(unit, 'counter_dice'):
            unit.counter_dice = []

        unit.counter_dice.append(evade_die)

        if log_func:
            log_func(f"🐈 **{self.name}**: +1 Counter Evade (5-7) added to pool.")


# ==========================================
# Демон переулка (Backstreet Demon)
# ==========================================
class PassiveBackstreetDemon(BasePassive):
    id = "backstreet_demon"
    name = "Демон переулка"
    description = "Сильная сторона: Уворот наносит урон. Слабая: Блок врага наносит вам урон."

    # --- СИЛЬНАЯ СТОРОНА (Победа Уворотом) ---
    def on_clash_win(self, ctx):
        # 1. Проверяем, что выиграли УВОРОТОМ
        if ctx.dice.dtype != DiceType.EVADE:
            return

        # 2. Получаем контекст проигравшего (Врага)
        loser = getattr(ctx, 'opponent_ctx', None)
        if not loser: return

        # 3. Считаем урон (Половина броска врага)
        counter_dmg = loser.final_value // 2
        if counter_dmg <= 0: return

        # 4. Наносим урон врагу (HP)
        # Так как это прямой урон от эффекта, используем current_hp
        loser.source.current_hp = max(0, loser.source.current_hp - counter_dmg)

        ctx.log.append(f"😈 **{self.name}**: Уворот! Враг получает {counter_dmg} урона (50% от {loser.final_value})")

    # --- СЛАБАЯ СТОРОНА (Проигрыш против Блока) ---
    def on_clash_lose(self, ctx):
        # ctx.source - это Лилит (Проигравшая)

        # 1. Получаем контекст победителя (Врага)
        winner = getattr(ctx, 'opponent_ctx', None)
        if not winner: return

        # 2. Проверяем, что враг выиграл БЛОКОМ
        if winner.dice.dtype == DiceType.BLOCK:
            # 3. Считаем урон (Половина броска Блока)
            recoil_dmg = winner.final_value // 2
            if recoil_dmg <= 0: return

            # 4. Лилит получает урон
            ctx.source.current_hp = max(0, ctx.source.current_hp - recoil_dmg)

            ctx.log.append(f"💔 **{self.name}**: Разбились о блок! Получено {recoil_dmg} урона.")


# ==========================================
# Дочь переулка (Daughter of Backstreets)
# ==========================================
class PassiveDaughterOfBackstreets(BasePassive):
    id = "daughter_of_backstreets"
    name = "Дочь переулка"
    description = "В конце хода +1 HP/SP/Stagger. Лечение от чужих источников снижено на 50%."

    def on_round_end(self, unit, log_func, **kwargs):
        # Самолечение не режется, так как source=None (или self, если передать)
        # Но в методе tick/round_end мы вызываем heal_hp(1)
        # heal_hp по умолчанию считает source_unit=None как self, так что резать не будет.
        unit.heal_hp(1)

        if unit.current_sp < unit.max_sp: unit.current_sp += 1
        if unit.current_stagger < unit.max_stagger: unit.current_stagger += 1

        if log_func:
            log_func(f"🏙️ **{self.name}**: Реген (+1 HP, +1 SP, +1 Stagger)")


# ==========================================
# Гедонизм (Hedonism)
# ==========================================
class PassiveHedonism(BasePassive):
    id = "hedonism"
    name = "Гедонизм"
    description = "Вы не можете уничтожать кубики врага за счет разницы в скорости. Вместо этого вы получаете Помеху (Disadvantage) на этот бросок."
    is_active_ability = False



# ==========================================
# Живи быстро, умирай молодым (Live Fast, Die Young)
# ==========================================
class PassiveLiveFastDieYoung(BasePassive):
    id = "live_fast_die_young"
    name = "Живи быстро, умирай молодым"
    description = "Каждый кубик скорости даёт +1 к Силе и Стойкости в начале сцены. +1 Дым за победу в столкновении атакой."

    # === [UPD] Используем on_round_start вместо on_combat_start ===
    def on_round_start(self, unit, log_func, **kwargs):
        # Если юнит в оглушении, бонусов за скорость нет
        if unit.is_staggered():
            return

        # Считаем реальные активные слоты (включая бонусы от Ярости и т.д.)
        slots_count = len(unit.active_slots) if unit.active_slots else 0

        if slots_count > 0:
            unit.add_status("strength", slots_count, duration=1)
            unit.add_status("endurance", slots_count, duration=1)

            if log_func:
                log_func(f"⚡ **{self.name}**: +{slots_count} Силы и Стойкости (за {slots_count} слота)")

    def on_clash_win(self, ctx: RollContext):
        # Если выиграли атакующим кубиком -> +1 Дым
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.source.add_status("smoke", 1, duration=99)
            ctx.log.append(f"⚡ **{self.name}**: +1 Дым за победу")