# logic/base_effect.py
from logic.context import RollContext


class BaseEffect:
    """
    Единый базовый класс для всех игровых механик (Пассивки, Таланты, Статусы, Аугментации).
    Содержит заглушки для всех возможных событий и хуков.
    """
    id = "base"
    name = "Base Effect"
    description = ""

    # === БАЗОВЫЕ СОБЫТИЯ (Lifecycle) ===
    # Combat: 1 раз за весь бой
    def on_combat_start(self, unit, log_func, **kwargs): pass

    def on_combat_end(self, unit, log_func, **kwargs): pass

    # Round: 1 раз за каждый раунд (ход)
    def on_round_start(self, unit, log_func, **kwargs): pass

    def on_speed_rolled(self, unit, log_func, **kwargs): pass

    def on_round_end(self, unit, log_func, **kwargs): pass

    # === БОЕВЫЕ ТРИГГЕРЫ ===
    def on_roll(self, ctx: RollContext, **kwargs): pass

    def on_clash_win(self, ctx: RollContext, **kwargs): pass

    def on_clash_lose(self, ctx: RollContext, **kwargs): pass

    def on_clash_draw(self, ctx: RollContext, **kwargs): pass

    def on_hit(self, ctx: RollContext, **kwargs): pass

    def on_take_damage(self, unit, amount, source, **kwargs): pass

    # === АКТИВНЫЕ СПОСОБНОСТИ ===
    def activate(self, unit, log_func, **kwargs): return False

    # === МОДИФИКАТОРЫ И ХУКИ ===
    def modify_stats(self, unit, stats: dict, logs: list): pass

    def modify_clash_interaction(self, ctx, interaction, loser_ctx): pass

    def modify_clash_interaction_loser(self, ctx, interaction, winner_ctx): pass

    def on_calculate_stats(self, unit, stack=0) -> dict: return {}

    def get_speed_dice_bonus(self, unit, stack=0) -> int: return 0

    def modify_active_slot(self, unit, slot, stack=0): pass

    def modify_stagger_damage_multiplier(self, unit, multiplier: float) -> float:
        return multiplier

    def calculate_level_growth(self, unit, stack=0) -> dict:
        return None

    def modify_satiety_penalties(self, unit, penalties: dict, stack=0) -> dict:
        return penalties

    def modify_incoming_damage(self, unit, amount: int, damage_type: str, stack=0) -> int:
        return amount

    def on_before_status_add(self, unit, status_id, amount, stack=0):
        return True, None

    def on_status_applied(self, unit, status_id, amount, duration=1, stack=0, **kwargs): pass

    def get_damage_modifier(self, unit, stack=0) -> float: return 0.0

    def apply_heal_reduction(self, unit, amount: int) -> int: return amount

    def can_redirect_on_equal_speed(self, unit) -> bool: return False

    def prevents_dice_destruction_by_speed(self, unit) -> bool: return False

    def prevents_specific_die_destruction(self, unit, die) -> bool: return False

    def can_use_counter_die_while_staggered(self, unit) -> bool: return False

    def can_break_empty_slot(self, unit) -> bool: return False

    def prevents_death(self, unit, stack=0) -> bool: return False

    def prevents_stagger(self, unit, stack=0) -> bool: return False