# core/unit.py
from dataclasses import dataclass

# 2. ИМПОРТ ЛОГГЕРА
from core.logging import logger, LogLevel
from core.unit.mixins.combat import UnitCombatMixin
from core.unit.mixins.lifecycle import UnitLifecycleMixin
from core.unit.mixins.mechanics import MechanicsIteratorMixin
# 1. ИМПОРТ МИКСИНА
from core.unit.mixins.status import UnitStatusMixin
from core.unit.unit_data import UnitData


@dataclass
class Unit(UnitData, UnitStatusMixin, UnitCombatMixin, UnitLifecycleMixin, MechanicsIteratorMixin):
    """
    Основной класс Юнита.
    Объединяет данные (UnitData) и логику (Mixins).
    """

    def recalculate_stats(self):
        """Пересчитывает характеристики на основе атрибутов, навыков и пассивок."""
        # Импорт здесь, чтобы избежать циклических ссылок
        from core.calculations import recalculate_unit_stats

        logger.log(f"Recalculating stats for {self.name}", LogLevel.VERBOSE, "Stats")

        return recalculate_unit_stats(self)

    def get_total_money(self) -> int:
        """Считает текущий баланс."""
        return sum(item.get("amount", 0) for item in self.money_log)

    @classmethod
    def from_dict(cls, data: dict):
        unit = super().from_dict(data)

        # Логируем загрузку юнита
        logger.log(f"Unit loaded/created: {unit.name} (Lvl {unit.level})", LogLevel.VERBOSE, "System")

        unit.recalculate_stats()
        return unit