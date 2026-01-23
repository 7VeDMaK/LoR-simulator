from logic.context import RollContext
from logic.statuses.status_definitions import STATUS_REGISTRY


class ModifierSystem:
    @staticmethod
    def apply_modifiers(context: RollContext):
        unit = context.source

        # logger.log(f"Applying modifiers for {unit.name}...", LogLevel.VERBOSE, "Modifiers")

        # Перебираем все статусы юнита
        # Мы делаем list(items), чтобы можно было безопасно менять словарь, если вдруг понадобится
        for status_id, stack in list(unit.statuses.items()):
            if status_id in STATUS_REGISTRY:
                handler = STATUS_REGISTRY[status_id]

                # [FIX] Используем стандартный метод on_roll вместо modify_roll
                if hasattr(handler, "on_roll"):
                    # logger.log(f"Applying status {status_id} (stack {stack})", LogLevel.VERBOSE, "Modifiers")
                    handler.on_roll(context, stack=stack)

        return context