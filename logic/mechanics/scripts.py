from logic.card_scripts import SCRIPTS_REGISTRY
from logic.statuses.status_manager import STATUS_REGISTRY
from logic.passives import PASSIVE_REGISTRY
from logic.talents import TALENT_REGISTRY
from logic.context import RollContext
from logic.weapon_definitions import WEAPON_REGISTRY


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

    # Если передали конкретную карту (предмет), берем её. Иначе берем текущую карту юнита.
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
    """Универсальный триггер для пассивок, талантов и статусов."""
    # 1. Статусы
    for status_id, stack in list(unit.statuses.items()):
        if status_id in STATUS_REGISTRY:
            handler = getattr(STATUS_REGISTRY[status_id], event_name, None)
            if handler: handler(unit, *args, **kwargs)

    if unit.get_status("passive_lock") > 0:
        # Если заблокировано, пропускаем пассивки
        pass
    # 2. Пассивки
    for pid in unit.passives:
        if pid in PASSIVE_REGISTRY:
            handler = getattr(PASSIVE_REGISTRY[pid], event_name, None)
            if handler: handler(unit, *args, **kwargs)
    if unit.weapon_id in WEAPON_REGISTRY:
        wep = WEAPON_REGISTRY[unit.weapon_id]
        if wep.passive_id and wep.passive_id in PASSIVE_REGISTRY:
            handler = getattr(PASSIVE_REGISTRY[wep.passive_id], event_name, None)
            if handler: handler(unit, *args, **kwargs)
    # 3. Таланты
    for pid in unit.talents:
        if pid in TALENT_REGISTRY:
            handler = getattr(TALENT_REGISTRY[pid], event_name, None)
            if handler: handler(unit, *args, **kwargs)


def handle_clash_outcome(trigger, ctx: RollContext):
    """Обрабатывает on_clash_win / on_clash_lose."""
    # Статусы
    for status_id, stack in list(ctx.source.statuses.items()):
        handler = getattr(STATUS_REGISTRY[status_id], trigger, None)
        if handler: handler(ctx, stack)

    # Пассивки
    for pid in ctx.source.passives:
        handler = getattr(PASSIVE_REGISTRY[pid], trigger, None)
        if handler: handler(ctx)

    w_id = ctx.source.weapon_id
    if w_id in WEAPON_REGISTRY:
        wep = WEAPON_REGISTRY[w_id]
        if wep.passive_id and wep.passive_id in PASSIVE_REGISTRY:
            handler = getattr(PASSIVE_REGISTRY[wep.passive_id], trigger, None)
            if handler: handler(ctx)

    # Таланты
    for pid in ctx.source.talents:
        handler = getattr(TALENT_REGISTRY[pid], trigger, None)
        if handler: handler(ctx)

    # Скрипты на кубике
    process_card_scripts(trigger, ctx)