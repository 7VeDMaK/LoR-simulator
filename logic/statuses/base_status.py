from logic.context import RollContext

class StatusEffect:
    id = "base"

    # Базовые методы-заглушки
    def on_use(self, unit, card, log_func): pass

    def on_combat_start(self, unit, log_func, **kwargs): pass

    def on_combat_end(self, unit, log_func): pass

    def on_roll(self, ctx: RollContext, stack: int): pass

    def on_clash_win(self, ctx: RollContext, stack: int): pass

    def on_clash_lose(self, ctx: RollContext, stack: int): pass

    def on_hit(self, ctx: RollContext, stack: int): pass

    def on_turn_end(self, unit, stack) -> list[str]: return []

    def get_damage_modifier(self, unit, stack) -> float:
        """Возвращает % изменения урона (0.1 = +10%, -0.2 = -20%)"""
        return 0.0

    def on_calculate_stats(self, unit, stack=0) -> dict:
        """Возвращает бонусы к статам (если статус их дает)."""
        return {}