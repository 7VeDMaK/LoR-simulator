from logic.calculations.formulas import get_modded_value

class UnitLifecycleMixin:
    def heal_hp(self, amount: int):
        # === [NEW] ЛОГИКА ГЛУБОКОЙ РАНЫ ===
        if self.get_status("deep_wound") > 0:
            from logic.statuses.status_definitions import STATUS_REGISTRY
            if "deep_wound" in STATUS_REGISTRY:
                amount = STATUS_REGISTRY["deep_wound"].apply_heal_reduction(self, amount)

        # Дальше ваш стандартный код лечения...
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return amount

    def restore_sp(self, amount: int) -> int:
        if amount <= 0: return 0
        final_sp = min(self.max_sp, self.current_sp + amount)
        recovered = final_sp - self.current_sp
        self.current_sp = final_sp
        return recovered

    def take_sanity_damage(self, amount: int):
        # Паника начинается с 0, но значение может уходить в минус
        self.current_sp = max(-45, self.current_sp - amount)