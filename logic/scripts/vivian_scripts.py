from core.logging import logger, LogLevel


# === СКРИПТЫ ВИВЬЕН (МАЗОХИЗМ) ===

def damage_self_by_roll(ctx, params=None):
    """
    Наносит владельцу урон, равный выпавшему значению кубика (final_value).
    """
    amount = ctx.final_value
    if amount > 0:
        ctx.source.take_damage(amount)
        if hasattr(ctx, "log"):
            ctx.log.append(f"🩸 **Мазохизм**: {ctx.source.name} наносит себе {amount} урона!")
        logger.log(f"🩸 Self-Damage (Roll): {ctx.source.name} took {amount}", LogLevel.VERBOSE, "Script")


def heal_self_by_roll(ctx, params=None):
    """
    Лечит владельца на количество ХП, равное значению кубика.
    """
    amount = ctx.final_value
    if amount > 0:
        heal_val = ctx.source.heal_hp(amount)
        if hasattr(ctx, "log"):
            ctx.log.append(f"🧛 **Вампиризм**: Восстановлено {heal_val} HP (от броска {amount})")


def damage_self_clash_diff(ctx, params=None):
    """
    При победе в столкновении наносит себе урон = (Мой бросок - Бросок врага).
    Движок должен передавать 'clash_diff' в контекст или мы вычисляем его.
    """
    # Пытаемся найти разницу в контексте (если движок её сохраняет)
    # Если нет, пытаемся вычислить, если есть target_roll
    diff = getattr(ctx, "clash_diff", 0)

    # Если движок не передал diff напрямую, пробуем эвристику
    if diff == 0 and hasattr(ctx, "target_die_result"):
        diff = max(0, ctx.final_value - ctx.target_die_result)

    if diff > 0:
        ctx.source.take_damage(diff)
        if hasattr(ctx, "log"):
            ctx.log.append(f"⛓️ **Коллекция шрамов**: Получено {diff} урона от разницы в силе!")