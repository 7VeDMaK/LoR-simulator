from logic.context import RollContext
from logic.character_changing.passives.base_passive import BasePassive

class IWin(BasePassive):
    id = "i_win"
    name = "I WIN"
    description = (
        "NAH I'D WIN"
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        if unit.get_status("test_power") > 0:
            unit.remove_status("test_power", 999)
        else:
            unit.add_status("test_power", 1, duration=99)
        return True

    def on_roll(self, ctx: RollContext):
        if ctx.source.get_status("test_power") <= 0:
            return
            
        ctx.modify_power(99, "Test Power")
        
class ILose(BasePassive):
    id = "i_lose"
    name = "I LOSE"
    description = (
        "NAH I'D LOSE"
    )
    is_active_ability = True

    def activate(self, unit, log_func, **kwargs):
        if unit.get_status("test_weakness") > 0:
            unit.remove_status("test_weakness", 999)
        else:
            unit.add_status("test_weakness", 1, duration=99)
        return True

    def on_roll(self, ctx: RollContext):
        if ctx.source.get_status("test_weakness") <= 0:
            return
            
        ctx.modify_power(-99, "Test Weakness")