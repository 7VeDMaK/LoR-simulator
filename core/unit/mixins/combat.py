from core.unit.mixins.checks import StatusCheckMixin
from core.unit.mixins.cooldowns import CooldownsMixin
from core.unit.mixins.mechanics import UnitMechanicsMixin
from core.unit.mixins.speed import SpeedRollMixin


class UnitCombatMixin(UnitMechanicsMixin, SpeedRollMixin, StatusCheckMixin, CooldownsMixin):
    """
    Сборный класс для боевой логики.
    Наследует функционал из специализированных миксинов.
    """
    pass