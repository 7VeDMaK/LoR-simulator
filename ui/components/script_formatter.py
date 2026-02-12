from ui.icons import get_icon_html


def _format_script_text(script_id: str, params: dict) -> str:
    """
    Форматирует технические ID скриптов в читаемый текст с иконками.
    Используется в логах боя и всплывающих подсказках.
    """

    # Хелперы для извлечения параметров
    def get_val(p):
        # Приоритет: base -> amount -> stack -> 0
        return p.get("base", p.get("amount", p.get("stack", 0)))

    def get_scale_text(p):
        stat = p.get("stat")
        if stat and stat != "None":
            factor = p.get("factor", 1.0)
            diff = p.get("diff", False)
            sign = "+" if factor >= 0 else ""
            diff_txt = " (Diff)" if diff else ""
            return f" [{sign}{factor}x {stat}{diff_txt}]"
        return ""

    def get_time_text(p):
        dur = int(p.get("duration", 0))
        dly = int(p.get("delay", 0))
        parts = []
        if dur >= 90:
            parts.append("Постоянно")
        elif dur > 1:
            parts.append(f"⏳{dur}")

        if dly > 0:
            parts.append(f"⏰{dly}")

        return f" ({', '.join(parts)})" if parts else ""

    # === СТАТУСЫ ===
    if script_id == "apply_status":
        status_key = params.get("status", "???").lower()
        status_label = status_key.replace("_", " ").title()
        icon = get_icon_html(status_key)
        val = get_val(params)
        scale = get_scale_text(params)
        time_info = get_time_text(params)

        target = params.get("target", "target")
        tgt_map = {
            "self": "себя",
            "target": "цель",
            "all": "всех",
            "all_allies": "союзников",
            "all_enemies": "врагов"
        }
        tgt_str = f" ({tgt_map.get(target, target)})" if target != "target" else ""

        return f"{icon} {status_label}: {val}{scale}{time_info}{tgt_str}"

    elif script_id == "consume_status_apply":
        con_stat = params.get("consume_status", "").replace("_", " ").title()
        raw_apply = params.get("apply_status", "")
        app_amt = params.get("apply_amount", 1)

        if isinstance(raw_apply, list):
            app_stat_str = ", ".join([s.replace("_", " ").title() for s in raw_apply])
        else:
            app_stat_str = raw_apply.replace("_", " ").title()

        return f"♻️ Поглотить {con_stat} ➔ Наложить {app_amt} {app_stat_str}"

    elif script_id == "remove_status":
        status = params.get("status", "Status").replace("_", " ").title()
        val = get_val(params)
        val_str = str(val) if val else "Все"
        return f"🗑️ Снять {status}: {val_str}"

    elif script_id == "remove_all_positive":
        return "🗑️ Снять ВСЕ положительные эффекты"

    elif script_id == "remove_best_positive":
        return "🗑️ Снять лучший положительный эффект"

    elif script_id == "remove_random_status":
        type_s = params.get("type", "any")
        return f"🗑️ Снять случайный {type_s} статус"

    elif script_id == "steal_status":
        status = params.get("status", "???")
        return f"✋ Украсть {status}"

    elif script_id == "multiply_status":
        mult = params.get("multiplier", 1)
        stat = params.get("status", "")
        return f"✖️ Умножить {stat} на {mult}"

    elif script_id == "apply_status_by_roll":
        status = params.get("status", "")
        return f"🎲 Наложить {status} равное броску"

    # === РЕСУРСЫ И ЛЕЧЕНИЕ ===
    elif script_id in ["restore_hp", "restore_resource"]:
        res_type = params.get("type", "hp").lower()
        if script_id == "restore_hp": res_type = "hp"
        icon = get_icon_html(res_type)
        val = get_val(params)
        scale = get_scale_text(params)
        return f"{icon} {res_type.upper()}: {val}{scale}"

    elif script_id in ["restore_sp", "restore_sp_percent"]:
        val = get_val(params)
        icon = get_icon_html("sp")
        return f"{icon} SP: {val}"

    elif script_id == "restore_resource_by_roll":
        res_type = params.get("type", "hp").upper()
        return f"➕ Восст. {res_type} равное броску"

    elif script_id == "heal_self_by_roll":
        return "🧛 Вампиризм (Лечение от броска)"

    # === УРОН И САМОУРОН ===
    elif script_id in ["deal_effect_damage", "add_hp_damage", "deal_damage"]:
        dtype = params.get("type", "hp").lower()
        icon = get_icon_html(dtype)
        val = get_val(params)
        scale = get_scale_text(params)
        return f"💔 Урон ({icon}): {val}{scale}"

    elif script_id == "multiply_damage":
        mult = params.get("multiplier", 2.0)
        return f"💥 Урон x{mult}"

    elif script_id == "adaptive_damage_type":
        return "🦎 Адаптивный тип урона (по уязвимости)"

    elif script_id == "self_harm_percent":
        pct = int(params.get("percent", 0.0) * 100)
        return f"🩸 Потерять {pct}% HP"

    elif script_id == "nullify_hp_damage":
        return "🛡️ Игнорировать урон по HP"

    elif script_id in ["damage_self_by_roll", "deal_damage_by_roll"]:
        return "🩸 Получить урон равный Броску"

    elif script_id in ["damage_self_clash_diff", "deal_damage_by_clash_diff"]:
        return "🩸 Получить урон равный Разнице Клэша"

    # === МОЩЬ И КУБИКИ ===
    elif script_id == "modify_roll_power":
        val = get_val(params)
        scale = get_scale_text(params)
        reason = params.get("reason", "")
        reason_str = f" ({reason})" if reason else ""
        return f"🎲 Power: {val}{scale}{reason_str}"

    elif script_id == "multiply_roll_power":
        mult = params.get("multiplier", 1)
        return f"🎲 Power x{mult}"

    elif script_id in ["set_card_power_multiplier", "apply_card_power_multiplier"]:
        mult = params.get("multiplier", 1)
        cond = params.get("condition", "")
        return f"⚔️ Card Power x{mult} ({cond})"

    elif script_id == "add_preset_dice":
        dice_list = params.get("dice", [])
        desc = ", ".join([d.get('type', 'Die').title() for d in dice_list])
        return f"➕ Добавить кубики: {desc}"

    elif script_id in ["repeat_dice_by_status", "repeat_dice_by_luck"]:
        limit = params.get("limit", params.get("max", 3))
        type_s = "Удаче" if "luck" in script_id else "Статусу"
        return f"🔁 Повтор кубика по {type_s} (до {limit} раз)"

    elif script_id == "break_target_dice":
        return "🔨 СЛОМАТЬ кубик противника"

    elif script_id == "share_dice_with_hand":
        flag = params.get("flag", "unity")
        return f"🤝 Раздать кубик картам ({flag})"

    # === МЕХАНИКИ (Unity, Lima, Memory, Summon) ===
    elif script_id == "unity_chain_reaction":
        return "🔗 Unity Chain: Накопление и передача кубиков"

    elif script_id == "apply_axis_team_buff":
        status = params.get("status", "").title()
        return f"🙌 Axis Buff: +1 {status} союзникам (или +2 себе)"

    elif script_id == "summon_ally":
        unit = params.get("unit_name", "???")
        return f"🤖 Призвать: {unit}"

    elif script_id == "lima_ram_logic":
        return "🐑 Лима: Таран (Урон от скорости)"

    elif script_id == "apply_marked_flesh":
        dur = int(params.get("duration", 0))
        return f"🩸 Наложить 'Помеченную Плоть' ({dur} ход)"

    elif script_id == "apply_slot_debuff":
        debuff = params.get("debuff", "???")
        return f"🚫 Дебафф слота: {debuff}"

    elif script_id == "set_memory_flag":
        flag = params.get("flag", "")
        val = params.get("value", True)
        return f"🚩 Флаг {flag}={val}"

    elif script_id == "consume_evade_for_haste":
        return "💨 Уклонение -> Скорость"

    # Fallback
    return f"🔧 {script_id} {params}"