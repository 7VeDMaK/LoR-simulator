from logic.context import RollContext

class BasePassive:
    id = "base"
    name = "Base Passive"
    description = "No description"
    is_active_ability = False
    cooldown = 0
    duration = 0

    def on_combat_start(self, unit, log_func, **kwargs): pass

    def on_combat_end(self, unit, log_func, **kwargs): pass # На всякий случай и тут

    def on_round_start(self, unit, log_func, **kwargs): pass

    def on_round_end(self, unit, log_func, **kwargs): pass

    def on_roll(self, ctx: RollContext): pass

    def on_clash_win(self, ctx: RollContext): pass

    def on_clash_lose(self, ctx: RollContext): pass

    def on_hit(self, ctx: RollContext): pass

    def activate(self, unit, log_func): pass

    def modify_stats(self, unit, stats: dict, logs: list): pass

    def modify_clash_interaction(self, ctx, interaction, loser_ctx): pass

    def modify_clash_interaction_loser(self, ctx, interaction, winner_ctx): pass

    def get_virtual_defense_die(self, unit, incoming_die): return None

    def on_calculate_stats(self, unit) -> dict: return {}

    def on_take_damage(self, unit, amount, source, **kwargs): pass

    def get_speed_dice_bonus(self, unit) -> int: return 0

    # === [NEW] Хук для изменения множителя урона по Staggered цели ===
    def modify_stagger_damage_multiplier(self, unit, multiplier: float) -> float:
        return multiplier

    def calculate_level_growth(self, unit) -> dict:
        """
        Если возвращает dict (напр. {'hp': 100, 'sp': 50, 'logs': [...]}),
        то стандартная формула (5+roll) игнорируется.
        """
        return None

    # === [NEW] Хук для модификации штрафов Сытости ===
    def modify_satiety_penalties(self, unit, penalties: dict) -> dict:
        return penalties

    # === [NEW] Хук для изменения входящего урона (Pre-mitigation) ===
    def modify_incoming_damage(self, unit, amount: int, damage_type: str) -> int:
        return amount

# 1. Для "Атлетичный" (Targeting)
    def can_redirect_on_equal_speed(self, unit) -> bool:
        return False

    # 2. Для "Гедонизм" (Speed / Clash)
    def prevents_dice_destruction_by_speed(self, unit) -> bool:
        """Если True, этот юнит НЕ может ломать кубики врага скоростью (получает штраф вместо этого)."""
        return False

    # 3. Для "Кошачьи рефлексы" (Clash)
    def prevents_specific_die_destruction(self, unit, die) -> bool:
        """Спасает ли конкретный кубик от уничтожения?"""
        return False

    # 4. Для "Не взирая на невзгоды" (Clash / OneSided)
    def can_use_counter_die_while_staggered(self, unit) -> bool:
        return False