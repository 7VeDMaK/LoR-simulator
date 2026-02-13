from core.enums import DiceType
from core.logging import logger, LogLevel

def resolve_clash_round(engine, ctx_a, ctx_d, die_a, die_d):
    """
    Решает исход одного раунда стычки (сравнение значений).
    Возвращает словарь с результатами: outcome_text, recycle_a, recycle_d, detail_logs.
    """
    attacker = ctx_a.source
    defender = ctx_d.source
    val_a = ctx_a.final_value
    val_d = ctx_d.final_value

    type_a = die_a.dtype
    type_d = die_d.dtype

    is_atk_a = type_a in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]
    is_evade_a = type_a == DiceType.EVADE
    is_block_a = type_a == DiceType.BLOCK

    is_atk_d = type_d in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]
    is_evade_d = type_d == DiceType.EVADE
    is_block_d = type_d == DiceType.BLOCK

    result = {
        "outcome": "",
        "recycle_a": False,
        "recycle_d": False,
        "details": []
    }

    # === ATTACKER WINS ===
    if val_a > val_d:
        engine._handle_clash_win(ctx_a)
        engine._handle_clash_lose(ctx_d)
        logger.log(f"{attacker.name} wins clash ({val_a} vs {val_d})", LogLevel.NORMAL, "Clash")

        if is_atk_a and is_atk_d:
            dmg = engine._resolve_clash_interaction(ctx_a, ctx_d, val_a - val_d)
            dmg_str = f" 💥 **-{dmg} HP**" if dmg else ""
            result["outcome"] = f"🏆 {attacker.name} Win (Hit){dmg_str}"

        elif is_atk_a and is_evade_d:
            dmg = engine._resolve_clash_interaction(ctx_a, ctx_d, val_a)
            dmg_str = f" 💥 **-{dmg} HP**" if dmg else ""
            result["outcome"] = f"💥 Evade Failed{dmg_str}"

        elif is_evade_a and is_atk_d:
            result["outcome"] = f"🏃 {attacker.name} Evades! (Recycle)"
            rec = attacker.restore_stagger(val_a)
            result["details"].append(f"🛡️ +{rec} Stagger")
            result["recycle_a"] = True

        elif is_atk_a and is_block_d:
            dmg = engine._resolve_clash_interaction(ctx_a, ctx_d, val_a - val_d)
            dmg_str = f" 💥 **-{dmg} HP**" if dmg else ""
            result["outcome"] = f"🏆 {attacker.name} Win (Hit){dmg_str}"

        elif is_block_a and is_atk_d:
            stg = engine._resolve_clash_interaction(ctx_a, ctx_d, val_a - val_d)
            result["outcome"] = f"🛡️ Blocked"
            if stg:
                result["details"].append(f"😵 {defender.name} took {stg} Stagger")

        # [NEW] ВАЖНО: Если победил контр-кубик (и это не уворот, который уже обработан), он возвращается
        if not result["recycle_a"] and getattr(die_a, "is_counter", False):
            result["recycle_a"] = True
            result["details"].append("🔄 Counter Recycled")


    # === DEFENDER WINS ===
    elif val_d > val_a:
        engine._handle_clash_win(ctx_d)
        engine._handle_clash_lose(ctx_a)
        logger.log(f"{defender.name} wins clash ({val_d} vs {val_a})", LogLevel.NORMAL, "Clash")

        if is_atk_d and is_atk_a:
            dmg = engine._resolve_clash_interaction(ctx_d, ctx_a, val_d - val_a)
            dmg_str = f" 💥 **-{dmg} HP**" if dmg else ""
            result["outcome"] = f"🏆 {defender.name} Win (Hit){dmg_str}"

        elif is_atk_d and is_evade_a:
            dmg = engine._resolve_clash_interaction(ctx_d, ctx_a, val_d)
            dmg_str = f" 💥 **-{dmg} HP**" if dmg else ""
            result["outcome"] = f"💥 Evade Failed{dmg_str}"

        elif is_evade_d and is_atk_a:
            result["outcome"] = f"🏃 {defender.name} Evades! (Recycle)"
            rec = defender.restore_stagger(val_d)
            result["details"].append(f"🛡️ +{rec} Stagger")
            result["recycle_d"] = True

        elif is_atk_d and is_block_a:
            dmg = engine._resolve_clash_interaction(ctx_d, ctx_a, val_d - val_a)
            dmg_str = f" 💥 **-{dmg} HP**" if dmg else ""
            result["outcome"] = f"🏆 {defender.name} Win (Hit){dmg_str}"

        elif is_block_d and is_atk_a:
            stg = engine._resolve_clash_interaction(ctx_d, ctx_a, val_d - val_a)
            result["outcome"] = f"🛡️ Blocked"
            if stg:
                result["details"].append(f"😵 {attacker.name} took {stg} Stagger")

        # [NEW] ВАЖНО: Если победил контр-кубик защитника, он возвращается
        if not result["recycle_d"] and getattr(die_d, "is_counter", False):
            result["recycle_d"] = True
            result["details"].append("🔄 Counter Recycled")

    # === DRAW ===
    else:
        result["outcome"] = "🤝 Draw"
        logger.log(f"Clash Draw ({val_a})", LogLevel.NORMAL, "Clash")
        engine._handle_clash_draw(ctx_a)
        engine._handle_clash_draw(ctx_d)

    return result