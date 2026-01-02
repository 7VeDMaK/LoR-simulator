from logic.mechanics import scripts, rolling, damage

class ClashMechanicsMixin:
    """
    Уровень 1: Связующее звено механик.
    Делегирует выполнение специализированным модулям.
    """

    def _process_card_scripts(self, trigger: str, ctx):
        return scripts.process_card_scripts(trigger, ctx)

    def _process_card_self_scripts(self, trigger: str, source, target, custom_log_list=None):
        return scripts.process_card_self_scripts(trigger, source, target, self.logs, custom_log_list)

    def _create_roll_context(self, source, target, die, is_disadvantage=False):
        return rolling.create_roll_context(source, target, die, is_disadvantage)

    def _handle_clash_win(self, ctx):
        return scripts.handle_clash_outcome("on_clash_win", ctx)

    def _handle_clash_lose(self, ctx):
        return scripts.handle_clash_outcome("on_clash_lose", ctx)

    def _trigger_unit_event(self, event_name, unit, *args, **kwargs):
        return scripts.trigger_unit_event(event_name, unit, *args, **kwargs)

    def _deal_direct_damage(self, source_ctx, target, amount, dmg_type):
        return damage.deal_direct_damage(source_ctx, target, amount, dmg_type, self._trigger_unit_event)

    def _apply_damage(self, attacker_ctx, defender_ctx, dmg_type="hp"):
        return damage.apply_damage(
            attacker_ctx, 
            defender_ctx, 
            dmg_type, 
            trigger_event_func=self._trigger_unit_event,
            script_runner_func=self._process_card_scripts
        )