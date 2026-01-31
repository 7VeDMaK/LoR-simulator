from core.logging import logger, LogLevel


# === ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ (Не экспортируется в реестр) ===
def _pay_hp_cost(unit, percent, ctx=None, is_punishment=False):
    """
    Отнимает % от МАКС ХП.
    Если is_punishment=True, считается уроном от отдачи (наказание).
    """
    dmg = int(unit.max_hp * (percent / 100.0))
    if dmg > 0:
        # Важно: используем take_damage, чтобы это считалось уроном
        unit.take_damage(dmg)

        msg = f"💔 Отдача: -{dmg} HP" if is_punishment else f"🩸 Плата: -{dmg} HP"
        if ctx:
            ctx.log.append(msg)


# ==========================================
# TIER 1: 5% Cost / 5% Punishment
# ==========================================
def adam_t1_cost(ctx, params=None):
    """Скрипт On Play: Плата 5% HP"""
    _pay_hp_cost(ctx.source, 5.0, ctx)


def adam_t1_punish(ctx, params=None):
    """Скрипт On Clash Lose: Урон 5% HP"""
    _pay_hp_cost(ctx.source, 5.0, ctx, is_punishment=True)


# ==========================================
# TIER 2: 10% Cost / 10% Punishment
# ==========================================
def adam_t2_cost(ctx, params=None):
    _pay_hp_cost(ctx.source, 10.0, ctx)


def adam_t2_punish(ctx, params=None):
    _pay_hp_cost(ctx.source, 10.0, ctx, is_punishment=True)


def adam_t2_combo(ctx, params=None):
    """On Hit: Если ударил, следующий кубик сильнее"""
    ctx.modify_power(3, "Combo")


# ==========================================
# TIER 3: 20% Cost / 10% Punishment
# ==========================================
def adam_t3_cost(ctx, params=None):
    _pay_hp_cost(ctx.source, 20.0, ctx)


def adam_t3_punish(ctx, params=None):
    _pay_hp_cost(ctx.source, 10.0, ctx, is_punishment=True)


def adam_t3_execution(ctx, params=None):
    """On Clash Win: Уничтожение кубика врага"""
    if ctx.opponent_ctx and ctx.opponent_ctx.dice:
        ctx.opponent_ctx.dice.is_broken = True
        ctx.log.append("⚔️ Dice Destroyed!")


# ==========================================
# TIER 4: 40% Cost / WETHERMON MECHANIC
# ==========================================
def adam_t4_cost(ctx, params=None):
    _pay_hp_cost(ctx.source, 40.0, ctx)


def adam_t4_wethermon_fail(ctx, params=None):
    """
    Ставим метку, что Адам проиграл Масс-Атаку.
    Реальный урон нанесет пассивка.
    """
    ctx.log.append("⚠️ Wethermon Check Failed! (Flag Set)")
    # Ставим флаг в память. Memory обычно общая или мержится обратно.
    ctx.source.memory['wethermon_failed'] = True