# logic/mechanics/scripts.py
from logic.scripts.card_scripts import SCRIPTS_REGISTRY
from logic.context import RollContext


def process_card_scripts(trigger: str, ctx: RollContext):
    """Запускает скрипты, привязанные к конкретному кубику."""
    die = ctx.dice
    if not die or not die.scripts or trigger not in die.scripts: return

    for script_data in die.scripts[trigger]:
        script_id = script_data.get("script_id")
        params = script_data.get("params", {})
        if script_id in SCRIPTS_REGISTRY:
            SCRIPTS_REGISTRY[script_id](ctx, params)


def process_card_self_scripts(trigger: str, source, target, logs, custom_log_list=None, card_override=None):
    """Запускает скрипты самой карты (например, On Use)."""
    card = card_override if card_override else source.current_card

    if not card or not card.scripts or trigger not in card.scripts: return

    target_log = custom_log_list if custom_log_list is not None else logs
    # Создаем фиктивный контекст для скрипта карты
    ctx = RollContext(source=source, target=target, dice=None, final_value=0, log=target_log)

    for script_data in card.scripts[trigger]:
        script_id = script_data.get("script_id")
        params = script_data.get("params", {})
        if script_id in SCRIPTS_REGISTRY:
            SCRIPTS_REGISTRY[script_id](ctx, params)


def trigger_unit_event(event_name, unit, *args, **kwargs):
    """
    Универсальный триггер для пассивок, талантов и статусов.
    Делегирует выполнение методу unit.trigger_mechanics, который уже умеет
    правильно работать со стеками статусов и kwargs.
    """
    if hasattr(unit, "trigger_mechanics"):
        unit.trigger_mechanics(event_name, unit, *args, **kwargs)


def handle_clash_outcome(trigger, ctx: RollContext):
    """
    Обрабатывает on_clash_win / on_clash_lose.
    Делегирует выполнение unit.trigger_mechanics для всех эффектов персонажа
    и запускает скрипты карты.
    """
    if hasattr(ctx.source, "trigger_mechanics"):
        ctx.source.trigger_mechanics(trigger, ctx)
    process_card_scripts(trigger, ctx)