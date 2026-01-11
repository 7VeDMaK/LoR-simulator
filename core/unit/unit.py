# core/unit.py
from dataclasses import dataclass
from core.unit.unit_data import UnitData
from core.unit.mixins.status import UnitStatusMixin
from core.unit.mixins.combat import UnitCombatMixin
from core.unit.mixins.lifecycle import UnitLifecycleMixin
# 1. ИМПОРТ МИКСИНА
from core.unit.mixins.mechanics import UnitMechanicsMixin


@dataclass
class Unit(UnitData, UnitStatusMixin, UnitCombatMixin, UnitLifecycleMixin, UnitMechanicsMixin):
    """
    Основной класс Юнита.
    Объединяет данные (UnitData) и логику (Mixins).
    """

    def recalculate_stats(self):
        """Пересчитывает характеристики на основе атрибутов, навыков и пассивок."""
        # Импорт здесь, чтобы избежать циклических ссылок
        from core.calculations import recalculate_unit_stats
        return recalculate_unit_stats(self)

    def get_total_money(self) -> int:
        """Считает текущий баланс."""
        return sum(item.get("amount", 0) for item in self.money_log)

    @classmethod
    def from_dict(cls, data: dict):
        unit = super().from_dict(data)
        unit.recalculate_stats()
        return unit