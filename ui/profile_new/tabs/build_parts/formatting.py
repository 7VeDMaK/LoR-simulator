def _translate_script_effect(script_obj):
    s_id = script_obj.get("script_id", "")
    p = script_obj.get("params", {})

    tgt_map = {"target": "Цель", "self": "Себя", "all_allies": "Всех союзников", "all_enemies": "Всех врагов"}
    tgt = tgt_map.get(p.get("target", ""), p.get("target", ""))
    tgt_str = f"&nbsp;на&nbsp;{tgt}" if tgt else ""

    val_str = ""
    if "base" in p:
        val_str = str(p["base"])
    elif "factor" in p:
        factor = p["factor"]
        stat = p.get("stat", "Stat")
        if factor < 1.0:
            val_str = f"{int(factor * 100)}%&nbsp;от&nbsp;{stat}"
        else:
            val_str = f"{factor}x&nbsp;{stat}"

    def _hl(text):
        return f"<span class='param-highlight'>{text}</span>"

    if s_id == "apply_status":
        status = p.get("status", "Status").capitalize()
        dur = p.get("duration", 0)
        dur_str = f"&nbsp;({dur}&nbsp;ход)" if dur > 0 else ""
        return f"Наложить&nbsp;{_hl(status + '&nbsp;' + val_str)}{tgt_str}{dur_str}"
    elif s_id == "restore_resource":
        rtype = p.get("type", "Resource").capitalize()
        return f"Восстановить&nbsp;{_hl(val_str + '&nbsp;' + rtype)}{tgt_str}"
    elif s_id == "modify_roll_power":
        stat = p.get("stat", "Stat").upper()
        diff = "&nbsp;(Разница)" if p.get("diff") else ""
        factor = p.get("factor", 1.0)
        return f"Сила&nbsp;+{factor}x&nbsp;{_hl(stat + diff)}"
    elif s_id == "deal_damage":
        dmg_type = p.get("damage_type", "True").capitalize()
        return f"Нанести&nbsp;{_hl(val_str + '&nbsp;' + dmg_type + '&nbsp;урона')}{tgt_str}"
    elif s_id == "draw_cards":
        count = p.get("count", 1)
        return f"Взять&nbsp;{_hl(str(count) + '&nbsp;карт')}"
    elif s_id == "remove_status":
        status = p.get("status", "Status").capitalize()
        return f"Снять&nbsp;{_hl(val_str + '&nbsp;' + status)}{tgt_str}"
    elif s_id == "remove_all_positive":
        return f"Снять&nbsp;{_hl('ВСЕ&nbsp;положительные&nbsp;эффекты')}{tgt_str}"

    return f"{s_id}: {val_str if val_str else str(p)}"


def _get_trigger_badge(trigger_key):
    t_map = {
        "on_use": ("ON USE", "tr-use"),
        "on_play": ("ON PLAY", "tr-use"),
        "on_hit": ("ON HIT", "tr-hit"),
        "on_clash_win": ("CLASH WIN", "tr-win"),
        "on_clash_lose": ("CLASH LOSE", "tr-lose"),
        "on_roll": ("ON ROLL", "tr-roll"),
        "on_combat_start": ("START", "tr-start"),
    }
    label, css = t_map.get(trigger_key, (trigger_key.replace("on_", "").upper(), "tr-passive"))
    return f"<span class='trigger-tag {css}'>{label}</span>"


def render_scripts_block(scripts_dict):
    if not scripts_dict: return ""
    html_lines = []
    priority = ["on_use", "on_roll", "on_clash_win", "on_hit"]
    sorted_keys = sorted(scripts_dict.keys(), key=lambda k: priority.index(k) if k in priority else 99)

    for trigger in sorted_keys:
        effects_list = scripts_dict[trigger]
        if not isinstance(effects_list, list): continue
        trigger_badge = _get_trigger_badge(trigger)
        for effect in effects_list:
            effect_text = _translate_script_effect(effect)
            # ВАЖНО: Никаких переносов строк внутри тегов div
            html_lines.append(f"<div class='script-line'>{trigger_badge}{effect_text}</div>")
    return f"<div class='script-container'>{''.join(html_lines)}</div>"


def _get_dice_css(dtype):
    dtype = dtype.lower()
    if "slash" in dtype: return "dice-slash", "🗡️"
    if "pierce" in dtype: return "dice-pierce", "🏹"
    if "blunt" in dtype: return "dice-blunt", "🔨"
    if "block" in dtype: return "dice-block-def", "🛡️"
    if "evade" in dtype: return "dice-evade", "💨"
    return "dice-normal", "🎲"


def render_dice_full(dice_list):
    """Рендерит кубики (без расчета бонусов пока что, чтобы не ломать верстку)."""
    if not dice_list: return ""
    html = []

    for die in dice_list:
        d_type = getattr(die, 'type', None) or getattr(die, 'dtype', 'blunt')
        if hasattr(d_type, 'name'): d_type = d_type.name

        d_min = getattr(die, 'base_min', None)
        if d_min is None: d_min = getattr(die, 'min_val', 0)
        d_max = getattr(die, 'base_max', None)
        if d_max is None: d_max = getattr(die, 'max_val', 0)
        d_scripts = getattr(die, 'scripts', {}) or getattr(die, 'script', {})

        # Пока бонус отключен (заглушка)
        bonus_html = ""
        # Если нужно будет вернуть:
        # bonus_html = f" <span style='color:#4ade80; font-size:12px; margin-left:4px;'>+{bonus}</span>"

        css, icon = _get_dice_css(str(d_type))
        script_html = render_scripts_block(d_scripts)

        # ВАЖНО: Все в одну строку, никаких переносов \n
        block = f"<div class='dice-block {css}'><div class='dice-header'><span style='margin-right:6px;'>{icon}</span><span>{d_min}-{d_max}{bonus_html}</span></div>{script_html}</div>"
        html.append(block)
    return "".join(html)


def generate_card_html(card, border_cls, type_badge_cls):
    """Собирает полный HTML блок карты в одну строку."""
    c_name = getattr(card, 'name', 'Unknown')
    c_tier = getattr(card, 'tier', 0)
    c_type = getattr(card, 'type', getattr(card, 'card_type', 'melee'))
    c_flags = getattr(card, 'flags', [])
    c_desc = getattr(card, 'description', '')
    c_dice = getattr(card, 'dice', []) or getattr(card, 'dice_list', [])
    c_scripts = getattr(card, 'scripts', {}) or getattr(card, 'script', {})

    # Header
    header_html = f"<div class='card-header-row'><div style='display:flex; align-items:center;'><div class='card-cost-badge'>{c_tier}</div><div class='card-name' title='{c_name}'>{c_name}</div></div><div class='card-type-badge {type_badge_cls}'>{str(c_type).upper()}</div></div>"

    # Body Parts
    scripts_html = render_scripts_block(c_scripts)
    dice_html = render_dice_full(c_dice)  # Убрал unit из аргументов

    desc_html = ""
    if c_desc:
        desc_html = f"<div class='card-desc-text'>{c_desc}</div>"

    tags_html = ""
    if c_flags:
        tags = "".join([f"<span class='card-flag'>{f}</span>" for f in c_flags])
        tags_html = f"<div class='tags-row'>{tags}</div>"

    # Final Assembly (One Line)
    return f"<div class='card-wrapper {border_cls}'>{header_html}{scripts_html}{dice_html}{desc_html}{tags_html}</div>"