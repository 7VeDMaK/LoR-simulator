from logic.character_changing.augmentations.augmentations import AUGMENTATION_REGISTRY
from logic.character_changing.passives import PASSIVE_REGISTRY
from logic.character_changing.talents import TALENT_REGISTRY

# Импорт наших новых модулей
from logic.calculations.modifiers import init_modifiers, init_bonuses
from logic.calculations.collectors import (
    collect_ability_bonuses, collect_status_bonuses, collect_weapon_bonuses
)
from logic.calculations.formulas import (
    calculate_totals, apply_attribute_effects, apply_skill_effects,
    calculate_speed_dice, calculate_pools, finalize_state
)
    
# [LOG] Импорт логгера
from core.logging import logger, LogLevel


def recalculate_unit_stats(unit):
    """
    Полный пересчет всех характеристик персонажа.
    """
    # [LOG] Начало пересчета (Verbose, так как это частое событие)
    logger.log(f"🔄 Recalculating stats for {unit.name}", LogLevel.VERBOSE, "Stats")

    # 1. Инициализация
    mods = init_modifiers()
    bonuses = init_bonuses(unit)

    # 2. Сбор бонусов
    # Мы убрали аргумент logs, подразумевая, что collectors.py теперь пишут в logger сами
    collect_ability_bonuses(unit, unit.passives, PASSIVE_REGISTRY, "🛡️", mods, bonuses)
    collect_ability_bonuses(unit, unit.talents, TALENT_REGISTRY, "🌟", mods, bonuses)
    collect_ability_bonuses(unit, unit.augmentations, AUGMENTATION_REGISTRY, "🧬", mods, bonuses)
    collect_weapon_bonuses(unit, mods, bonuses)
    collect_status_bonuses(unit, mods, bonuses)

    # 3. Расчет атрибутов
    attrs, skills = calculate_totals(unit, bonuses, mods)

    # 4. Эффекты статов
    apply_attribute_effects(attrs, mods)
    apply_skill_effects(skills, mods)

    # 5. Производные (Скорость, Пулы)
    calculate_speed_dice(unit, skills["speed"], mods)
    calculate_pools(unit, attrs, skills, mods)

    # 6. Финализация
    finalize_state(unit, mods)

    unit.modifiers = mods

    # [LOG] Завершение
    logger.log(
        f"✅ Stats updated for {unit.name}. HP: {unit.max_hp}, SP: {unit.max_sp}, Speed: {unit.computed_speed_dice}",
        LogLevel.VERBOSE, "Stats")

    # Больше не возвращаем список logs, так как всё уходит в BattleLogger
    return []