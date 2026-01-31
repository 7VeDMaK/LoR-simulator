from core.logging import logger, LogLevel


class UnitLifecycleMixin:
    def heal_hp(self, amount: int):
        if self.get_status("deep_wound") > 0:
            from logic.statuses.status_definitions import STATUS_REGISTRY
            if "deep_wound" in STATUS_REGISTRY:
                original_amount = amount
                amount = STATUS_REGISTRY["deep_wound"].apply_heal_reduction(self, amount)

                # Логируем работу механики (NORMAL)
                if amount != original_amount:
                    logger.log(
                        f"{self.name}: Healing reduced by Deep Wound ({original_amount} -> {amount})",
                        LogLevel.NORMAL,
                        "Status"
                    )

        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        actual_healed = self.current_hp - old_hp

        # Логируем факт лечения (MINIMAL)
        if actual_healed > 0:
            logger.log(f"💚 {self.name} healed +{actual_healed} HP", LogLevel.MINIMAL, "Resource")

        return amount

    def take_damage(self, amount: int):
        self.heal_hp(-amount)


    def restore_sp(self, amount: int) -> int:
        if amount <= 0: return 0

        final_sp = min(self.max_sp, self.current_sp + amount)
        recovered = final_sp - self.current_sp
        self.current_sp = final_sp

        # Логируем восстановление SP (MINIMAL)
        if recovered > 0:
            logger.log(f"🧠 {self.name} restored +{recovered} SP", LogLevel.MINIMAL, "Resource")

        return recovered

    def take_sanity_damage(self, amount: int):
        old_sp = self.current_sp
        self.current_sp = max(-45, self.current_sp - amount)
        lost = old_sp - self.current_sp

        # Логируем урон по SP (MINIMAL)
        if lost > 0:
            logger.log(f"🤯 {self.name} took {lost} SP damage", LogLevel.MINIMAL, "Damage")

    def restore_stagger(self, amount: int):
        """Восстанавливает выдержку (Stagger Resist)."""
        if amount <= 0: return

        old_stg = self.current_stagger
        self.current_stagger = min(self.max_stagger, self.current_stagger + amount)
        recovered = self.current_stagger - old_stg

        # Логируем восстановление (MINIMAL)
        if recovered > 0:
            logger.log(f"🛡️ {self.name} restored +{recovered} Stagger", LogLevel.MINIMAL, "Resource")

        return amount

    def take_stagger_damage(self, amount: int):
        """Наносит урон по выдержке."""
        if amount <= 0: return

        old_stg = self.current_stagger
        self.current_stagger = max(0, self.current_stagger - amount)
        lost = old_stg - self.current_stagger

        # Логируем урон по Stagger (MINIMAL)
        if lost > 0:
            logger.log(f"😵 {self.name} took {lost} Stagger damage", LogLevel.MINIMAL, "Damage")