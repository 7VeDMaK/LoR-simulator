"""
Модуль для превращения JSON-скриптов в читаемый HTML для UI.
Отвечает за генерацию красивых описаний карт и эффектов.
"""
from ui.icons import get_icon_html

def _translate_script_effect(script_obj):
    """
    Превращает словарь скрипта в понятную строку с HTML-подсветкой.
    Учитывает задержки, длительность и сложные условия.
    """
    s_id = script_obj.get("script_id", "")
    p = script_obj.get("params", {})

    # Хелпер для подсветки значений
    def _hl(text):
        return f"<span class='param-highlight'>{text}</span>"

    # --- 1. ОПРЕДЕЛЕНИЕ ЦЕЛИ ---
    tgt_map = {
        "target": "Цель",
        "self": "Себя",
        "all_allies": "Всех союзников",
        "all_enemies": "Всех врагов",
        "all": "Всех"
    }
    # Ищем цель в разных параметрах (target или apply_target)
    tgt_raw = p.get("target", p.get("apply_target", ""))
    tgt = tgt_map.get(tgt_raw, "")

    # Формируем строку цели (если она есть)
    tgt_str = f"&nbsp;на&nbsp;{tgt}" if tgt else ""

    # --- 2. ОПРЕДЕЛЕНИЕ ЗНАЧЕНИЯ (Amount/Stack/Base) ---
    val_str = ""
    # Приоритет полей: base -> amount -> stack -> 0
    raw_val = p.get("base", p.get("amount", p.get("stack", 0)))

    # Если значение 0, но есть factor (множитель)
    if "factor" in p and not raw_val:
        factor = p["factor"]
        stat = p.get("stat", "Stat")
        if factor < 1.0:
            val_str = f"{int(factor * 100)}%&nbsp;от&nbsp;{stat}"
        else:
            val_str = f"{factor}x&nbsp;{stat}"
    else:
        val_str = str(raw_val)

    # --- 3. ОБРАБОТКА СКРИПТОВ ---

    # === СТАТУСЫ ===
    if s_id == "apply_status":
        status_key = p.get("status", "Status").lower()
        status_label = status_key.replace("_", " ").title()

        # [NEW] Получаем иконку
        icon = get_icon_html(status_key)

        # Логика отображения времени
        dur = int(p.get("duration", 0))
        delay = int(p.get("delay", 0))

        time_parts = []
        if delay > 0:
            time_parts.append(f"через&nbsp;{delay}&nbsp;ход(а)")

        if dur >= 90:
            time_parts.append("Постоянно")
        elif dur > 1:
            time_parts.append(f"на&nbsp;{dur}&nbsp;ход(а)")
        elif dur == 1 and delay > 0:
             # Если длительность 1, но есть задержка, уточняем
             time_parts.append("на&nbsp;1&nbsp;ход")

        time_str = f"&nbsp;({', '.join(time_parts)})" if time_parts else ""

        return f"Наложить&nbsp;{icon}&nbsp;{_hl(val_str + '&nbsp;' + status_label)}{tgt_str}{time_str}"


    elif s_id == "consume_status_apply":
        # Логика Аксис: Снять X -> Наложить Y (поддержка списка статусов)
        con_key = p.get("consume_status", "").lower()
        con_label = con_key.replace("_", " ").title()
        con_icon = get_icon_html(con_key)

        raw_apply = p.get("apply_status", "")
        app_amt = p.get("apply_amount", 1)
        dur = int(p.get("duration", 0))
        dur_str = f"&nbsp;({dur}&nbsp;ход)" if dur > 1 else ""

        # Если передан список статусов, объединяем их через запятую с иконками
        if isinstance(raw_apply, list):
            app_parts = []
            for s in raw_apply:
                key = s.lower()
                label = key.replace("_", " ").title()
                ic = get_icon_html(key)
                app_parts.append(f"{ic}&nbsp;{label}")
            app_stat_str = ", ".join(app_parts)
        else:
            key = raw_apply.lower()
            label = key.replace("_", " ").title()
            ic = get_icon_html(key)
            app_stat_str = f"{ic}&nbsp;{label}"

        return f"Поглотить&nbsp;{con_icon}&nbsp;{con_label}&nbsp;➔&nbsp;Наложить&nbsp;{_hl(f'{app_amt} {app_stat_str}')}{tgt_str}{dur_str}"

    elif s_id == "remove_status":
        status_key = p.get("status", "Status").lower()
        status_label = status_key.replace("_", " ").title()
        icon = get_icon_html(status_key)
        val = p.get("amount", p.get("base"))
        amt_str = f"&nbsp;{val}" if val else "&nbsp;Все"
        return f"Снять&nbsp;{icon}&nbsp;{_hl(amt_str + '&nbsp;' + status_label)}{tgt_str}"

    elif s_id == "remove_all_positive":
        return f"Снять&nbsp;{_hl('ВСЕ&nbsp;положительные')}{tgt_str}"

    elif s_id == "remove_best_positive":
        return f"Снять&nbsp;{_hl('лучший&nbsp;положительный')}{tgt_str}"

    elif s_id == "remove_random_status":
        stype = p.get("type", "any")
        return f"Снять&nbsp;случайный&nbsp;{_hl(stype)}&nbsp;статус"

    elif s_id == "steal_status":
        status_key = p.get("status", "???").lower()
        status_label = status_key.replace("_", " ").title()
        icon = get_icon_html(status_key)
        return f"✋ Украсть&nbsp;{icon}&nbsp;{_hl(status_label)}"

    elif s_id == "multiply_status":
        mult = p.get("multiplier", 1)
        stat = p.get("status", "")
        return f"Умножить&nbsp;{_hl(stat)}&nbsp;на&nbsp;{_hl(mult)}"

    elif s_id == "apply_status_by_roll":
        status_key = p.get("status", "").lower()
        status_label = status_key.replace("_", " ").title()
        icon = get_icon_html(status_key)
        return f"🎲&nbsp;Наложить&nbsp;{icon}&nbsp;{_hl(status_label)}&nbsp;равное&nbsp;броску"

    # === РЕСУРСЫ И ЛЕЧЕНИЕ ===
    elif s_id == "restore_resource":
        rtype_key = p.get("type", "hp").lower()
        rtype_label = rtype_key.upper()
        icon = get_icon_html(rtype_key)
        return f"Восстановить&nbsp;{icon}&nbsp;{_hl(val_str + '&nbsp;' + rtype_label)}{tgt_str}"

    elif s_id == "restore_resource_by_roll":
        rtype_key = p.get("type", "hp").lower()
        rtype_label = rtype_key.upper()
        icon = get_icon_html(rtype_key)
        return f"Восст.&nbsp;{icon}&nbsp;{_hl(rtype_label)}&nbsp;равно&nbsp;значению&nbsp;броску"

    elif s_id == "heal_self_by_roll":
        icon = get_icon_html("hp")
        return f"Вампиризм:&nbsp;{icon}&nbsp;{_hl('Лечение&nbsp;от&nbsp;броска')}"

    # === УРОН ===
    elif s_id in ["deal_effect_damage", "deal_damage", "add_hp_damage"]:
        dmg_type = p.get("type", "hp").lower() # обычно это тип ресурса, по которому бьем
        dtype_label = dmg_type.replace("_", " ").title()
        icon = get_icon_html(dmg_type)
        return f"Нанести&nbsp;{icon}&nbsp;{_hl(val_str + '&nbsp;' + dtype_label + '&nbsp;урона')}{tgt_str}"

    elif s_id == "multiply_damage":
        mult = p.get("multiplier", 2.0)
        return f"Урон&nbsp;x{_hl(mult)}"

    elif s_id == "self_harm_percent":
        pct = int(p.get("percent", 0.0) * 100)
        icon = get_icon_html("hp")
        return f"Потерять&nbsp;{icon}&nbsp;{_hl(f'{pct}%&nbsp;HP')}"

    elif s_id == "nullify_hp_damage":
        icon = get_icon_html("hp")
        return f"{_hl('Игнорировать')}&nbsp;урон&nbsp;по&nbsp;{icon}&nbsp;HP"

    elif s_id == "damage_self_by_roll" or s_id == "deal_damage_by_roll":
        return f"Получить&nbsp;урон&nbsp;равный&nbsp;{_hl('Броску')}"

    elif s_id == "damage_self_clash_diff" or s_id == "deal_damage_by_clash_diff":
        return f"Получить&nbsp;урон&nbsp;равный&nbsp;{_hl('Разнице&nbsp;Клэша')}"

    elif s_id == "break_target_dice":
        icon = get_icon_html("dice_break")
        return f"{icon}&nbsp;{_hl('СЛОМАТЬ')}&nbsp;кубик&nbsp;противника"

    elif s_id == "adaptive_damage_type":
        icon = get_icon_html("adaptation")
        return f"{icon}&nbsp;{_hl('Адаптивный')}&nbsp;тип&nbsp;урона&nbsp;(по&nbsp;уязвимости)"

    elif s_id == "lima_ram_logic":
        icon = get_icon_html("speed")
        return f"🐑&nbsp;{_hl('Таран')}:&nbsp;Урон&nbsp;зависит&nbsp;от&nbsp;{icon}&nbsp;Скорости"

    # === КУБИКИ И СИЛА ===
    elif s_id == "add_preset_dice":
        dice_list = p.get("dice", [])
        # Для каждого кубика можно было бы иконку, но их много.
        # Просто перечислим типы.
        desc_parts = []
        for d in dice_list:
            dt = d.get('type', 'Die').lower()
            ic = get_icon_html(dt)
            desc_parts.append(f"{ic} {dt.title()}")
        desc = ", ".join(desc_parts)
        return f"Добавить&nbsp;кубики:&nbsp;{_hl(desc)}"

    elif s_id == "repeat_dice_by_luck":
        step = p.get("step", 10)
        limit = p.get("limit", 10)
        icon = get_icon_html("luck")
        return f"Повторы&nbsp;кубика&nbsp;по&nbsp;{icon}&nbsp;Удаче&nbsp;(шаг&nbsp;{_hl(step)},&nbsp;лимит&nbsp;{_hl(limit)})"

    elif s_id == "repeat_dice_by_status":
        status_key = p.get("status", "status").lower()
        status_label = status_key.replace("_", " ").title()
        icon = get_icon_html(status_key)
        limit = p.get("max", 4)
        die_index = p.get("die_index", 0)
        return f"Повторить&nbsp;кубик&nbsp;#{die_index + 1}&nbsp;по&nbsp;{icon}&nbsp;{_hl(status_label)}&nbsp;(лимит&nbsp;{_hl(limit)})"

    elif s_id == "share_dice_with_hand":
        flag = p.get("flag", "unity")
        return f"Раздать&nbsp;кубик&nbsp;картам&nbsp;в&nbsp;руке&nbsp;({flag})"

    elif s_id == "modify_roll_power":
        reason = p.get("reason", "Bonus")
        return f"Сила&nbsp;+{_hl(val_str)}&nbsp;({reason})"

    elif s_id == "multiply_roll_power":
        mult = p.get("multiplier", 2.0)
        reason = p.get("reason", "Power x2")
        return f"Сила&nbsp;x{_hl(mult)}&nbsp;({reason})"

    elif s_id == "set_card_power_multiplier" or s_id == "apply_card_power_multiplier":
        mult = p.get("multiplier", 2.0)
        condition = p.get("condition", "")
        cond_str = f"&nbsp;({condition})" if condition else ""
        return f"Множитель&nbsp;мощности&nbsp;x{_hl(mult)}{cond_str}"

    # === ПРИЗЫВ И ПРОЧЕЕ ===
    elif s_id == "summon_ally":
        u_name = p.get("unit_name", "Unknown")
        return f"Призвать:&nbsp;{_hl(u_name)}"

    elif s_id == "apply_axis_team_buff":
        status_key = p.get("status", "").lower()
        status_label = status_key.replace("_", " ").title()
        icon = get_icon_html(status_key)
        return f"Axis&nbsp;Buff:&nbsp;{_hl('+1&nbsp;' + icon + '&nbsp;' + status_label)}&nbsp;союзникам"

    elif s_id == "set_memory_flag":
        flag = p.get("flag", "")
        val = p.get("value", True)
        return f"Флаг:&nbsp;{flag}={val}"

    elif s_id == "unity_chain_reaction":
        return f"🔗&nbsp;{_hl('Unity&nbsp;Chain')}:&nbsp;Накопление&nbsp;и&nbsp;передача"

    elif s_id == "apply_marked_flesh":
        dur = int(p.get("duration", 0))
        dur_str = f"&nbsp;({dur}&nbsp;ход)" if dur > 1 else ""
        icon = get_icon_html("marked_flesh") # Убедитесь, что такая иконка есть в маппинге, иначе будет ?
        # В icons.py нет "marked_flesh", но может быть "fanat_mark" или "target".
        # Добавим фолбек на 'under_crosshairs' если нет
        if "marked_flesh" not in icon: icon = get_icon_html("under_crosshairs")
        return f"Наложить&nbsp;{icon}&nbsp;{_hl('Помеченную&nbsp;Плоть')}{tgt_str}{dur_str}"

    elif s_id == "apply_slot_debuff":
        debuff = p.get("debuff", "???")
        return f"Дебафф&nbsp;слота:&nbsp;{_hl(debuff)}"

    elif s_id == "consume_evade_for_haste":
        ev = get_icon_html("evade")
        hst = get_icon_html("haste")
        return f"{ev}&nbsp;{_hl('Уклонение')}&nbsp;➔&nbsp;{hst}&nbsp;{_hl('Скорость')}"

    # Fallback (для неизвестных скриптов)
    return f"<span style='color:#777; font-size:0.8em'>{s_id}: {val_str}</span>"


def _get_trigger_badge(trigger_key):
    """Возвращает HTML бейджик для триггера (On Use, On Hit и т.д.)."""
    t_map = {
        "on_use": ("ON USE", "tr-use"),
        "on_play": ("ON PLAY", "tr-use"),
        "on_hit": ("ON HIT", "tr-hit"),
        "on_clash": ("ON CLASH", "tr-clash"),
        "on_clash_win": ("CLASH WIN", "tr-win"),
        "on_clash_lose": ("CLASH LOSE", "tr-lose"),
        "on_roll": ("ON ROLL", "tr-roll"),
        "on_combat_start": ("START", "tr-start"),
        "on_round_start": ("ROUND", "tr-start"),
    }
    label, css = t_map.get(trigger_key, (trigger_key.replace("on_", "").upper(), "tr-passive"))
    return f"<span class='trigger-tag {css}'>{label}</span>"


def render_scripts_block(scripts_dict):
    """Рендерит блок всех скриптов карты в HTML."""
    if not scripts_dict: return ""
    html_lines = []

    # Порядок сортировки триггеров (чтобы On Use был первым)
    priority = ["on_use", "on_play", "on_roll", "on_clash", "on_clash_win", "on_clash_lose", "on_hit"]
    sorted_keys = sorted(scripts_dict.keys(), key=lambda k: priority.index(k) if k in priority else 99)

    for trigger in sorted_keys:
        effects_list = scripts_dict[trigger]
        if not isinstance(effects_list, list): continue

        trigger_badge = _get_trigger_badge(trigger)

        for effect in effects_list:
            effect_text = _translate_script_effect(effect)
            html_lines.append(f"<div class='script-line'>{trigger_badge}{effect_text}</div>")

    return f"<div class='script-container'>{''.join(html_lines)}</div>"


def _get_dice_css(dtype):
    """Возвращает CSS класс и иконку для типа кубика."""
    dtype = str(dtype).lower()
    if "slash" in dtype: return "dice-slash", get_icon_html("slash")
    if "pierce" in dtype: return "dice-pierce", get_icon_html("pierce")
    if "blunt" in dtype: return "dice-blunt", get_icon_html("blunt")
    if "block" in dtype: return "dice-block-def", get_icon_html("block")
    if "evade" in dtype: return "dice-evade", get_icon_html("evade")
    return "dice-normal", "🎲"


def render_dice_full(dice_list):
    """Рендерит визуальные блоки кубиков."""
    if not dice_list: return ""
    html = []

    for die in dice_list:
        # Безопасное получение типа кубика
        d_type = getattr(die, 'type', None) or getattr(die, 'dtype', 'blunt')
        if hasattr(d_type, 'name'): d_type = d_type.name
        elif isinstance(die, dict): d_type = die.get('type', 'blunt')

        # Безопасное получение мин/макс
        def _get_val(obj, key1, key2, default=0):
            val = getattr(obj, key1, None)
            if val is None: val = getattr(obj, key2, None)
            if val is None and isinstance(obj, dict): val = obj.get(key1, obj.get(key2))
            return val if val is not None else default

        d_min = _get_val(die, 'base_min', 'min_val')
        d_max = _get_val(die, 'base_max', 'max_val')

        # Скрипты на самом кубике
        d_scripts = getattr(die, 'scripts', {}) or getattr(die, 'script', {})
        if not d_scripts and isinstance(die, dict):
            d_scripts = die.get('scripts', {})

        # [UPDATE] Теперь _get_dice_css возвращает HTML-иконку
        css, icon_html = _get_dice_css(d_type)
        script_html = render_scripts_block(d_scripts)

        # Вставляем icon_html вместо жестко заданных эмодзи
        block = f"<div class='dice-block {css}'><div class='dice-header'><span style='margin-right:6px;'>{icon_html}</span><span>{d_min}-{d_max}</span></div>{script_html}</div>"
        html.append(block)

    return "".join(html)


def generate_card_html(card, border_cls="border-gray", type_badge_cls="badge-gray"):
    """
    Генерирует полный HTML виджет карты.
    Используется и в профиле, и в симуляторе.
    """
    def _get(obj, key, default):
        return getattr(obj, key, default) if not isinstance(obj, dict) else obj.get(key, default)

    c_name = _get(card, 'name', 'Unknown')
    c_tier = _get(card, 'tier', 0)
    if not c_tier: c_tier = _get(card, 'cost', 0)

    c_type = _get(card, 'type', _get(card, 'card_type', 'melee'))
    c_flags = _get(card, 'flags', [])
    c_desc = _get(card, 'description', '')

    c_dice = _get(card, 'dice', []) or _get(card, 'dice_list', [])
    c_scripts = _get(card, 'scripts', {}) or _get(card, 'script', {})

    # Шапка карты
    header_html = f"""
    <div class='card-header-row'>
        <div style='display:flex; align-items:center;'>
            <div class='card-cost-badge'>{c_tier}</div>
            <div class='card-name' title='{c_name}'>{c_name}</div>
        </div>
        <div class='card-type-badge {type_badge_cls}'>{str(c_type).upper()}</div>
    </div>
    """

    # Тело карты
    scripts_html = render_scripts_block(c_scripts)
    dice_html = render_dice_full(c_dice)

    desc_html = f"<div class='card-desc-text'>{c_desc}</div>" if c_desc else ""

    tags_html = ""
    if c_flags:
        tags = "".join([f"<span class='card-flag'>{f}</span>" for f in c_flags])
        tags_html = f"<div class='tags-row'>{tags}</div>"

    return f"<div class='card-wrapper {border_cls}'>{header_html}{scripts_html}{dice_html}{desc_html}{tags_html}</div>"