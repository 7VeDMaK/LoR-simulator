# core/unit.py
from dataclasses import dataclass
from core.unit.unit_data import UnitData
from core.unit.unit_mixins import UnitStatusMixin, UnitCombatMixin, UnitLifecycleMixin


@dataclass
class Unit(UnitData, UnitStatusMixin, UnitCombatMixin, UnitLifecycleMixin):
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

    # Можно переопределить from_dict, чтобы сразу вызывать recalculate_stats
    @classmethod
    def from_dict(cls, data: dict):
        # Вызываем родительский метод (из UnitData), который создаст экземпляр Unit
        unit = super().from_dict(data)
        # И сразу пересчитываем статы
        unit.recalculate_stats()
        return unit