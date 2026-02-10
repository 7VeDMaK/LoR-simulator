from core.logging import logger, LogLevel
from logic.mechanics import scripts
from logic.mechanics.damage.damage import apply_damage, deal_direct_damage
from logic.mechanics.rolling.rolling import create_roll_context


class ClashMechanicsMixin:
    """
    Уровень 1: Связующее звено механик.
    Делегирует выполнение специализированным модулям.
    """

    def _process_card_scripts(self, trigger: str, ctx):
        # Делегируем выполнение скриптов
        return scripts.process_card_scripts(trigger, ctx)

    def _process_card_self_scripts(self, trigger: str, source, target, custom_log_list=None, card_override=None):
        # Делегируем выполнение скриптов "на себя"
        # card_override добавлен для поддержки предметов
        return scripts.process_card_self_scripts(trigger, source, target, custom_log_list, card_override)

    def _create_roll_context(self, source, target, die, is_disadvantage=False):
        # Создаем контекст броска
        return create_roll_context(source, target, die, is_disadvantage)

    def _handle_clash_win(self, ctx):
        logger.log(f"🏆 Clash Win Hook: {ctx.source.name}", LogLevel.VERBOSE, "Mechanics")
        if ctx and ctx.source:
            ctx.source.memory["last_clash_win"] = True
        return scripts.handle_clash_outcome("on_clash_win", ctx)

    def _handle_clash_lose(self, ctx):
        logger.log(f"🏳️ Clash Lose Hook: {ctx.source.name}", LogLevel.VERBOSE, "Mechanics")
        if ctx and ctx.source:
            ctx.source.memory["last_clash_lose"] = True
        return scripts.handle_clash_outcome("on_clash_lose", ctx)

    def _handle_clash_draw(self, ctx):
        logger.log(f"🤝 Clash Draw Hook: {ctx.source.name}", LogLevel.VERBOSE, "Mechanics")
        if ctx and ctx.source:
            ctx.source.memory["last_clash_draw"] = True
        return scripts.handle_clash_outcome("on_clash_draw", ctx)

    def _trigger_unit_event(self, event_name, unit, *args, **kwargs):
        # Триггер событий юнита (on_hit, on_take_damage и т.д.)
        return scripts.trigger_unit_event(event_name, unit, *args, **kwargs)

    def _deal_direct_damage(self, source_ctx, target, amount, dmg_type):
        logger.log(f"Direct Damage Call: {amount} {dmg_type} -> {target.name}", LogLevel.VERBOSE, "Mechanics")
        return deal_direct_damage(source_ctx, target, amount, dmg_type, self._trigger_unit_event)

    def _apply_damage(self, attacker_ctx, defender_ctx, dmg_type="hp"):
        # [FIX] Безопасное получение имени защитника
        def_name = "Unknown"
        if defender_ctx:
            def_name = defender_ctx.source.name
        elif attacker_ctx.target:
            def_name = attacker_ctx.target.name

        logger.log(f"Apply Damage Flow: {attacker_ctx.source.name} -> {def_name}", LogLevel.VERBOSE, "Mechanics")

        return apply_damage(
            attacker_ctx,
            defender_ctx,
            dmg_type,
            trigger_event_func=self._trigger_unit_event,
            script_runner_func=self._process_card_scripts
        )