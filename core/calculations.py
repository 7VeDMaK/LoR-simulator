from logic.augmentations import AUGMENTATION_REGISTRY
from logic.passives import PASSIVE_REGISTRY
from logic.talents import TALENT_REGISTRY

# Импорт наших новых модулей
from logic.calculations.modifiers import init_modifiers, init_bonuses
from logic.calculations.collectors import (
    collect_ability_bonuses, collect_status_bonuses, collect_weapon_bonuses
)
from logic.calculations.formulas import (
    calculate_totals, apply_attribute_effects, apply_skill_effects,
    calculate_speed_dice, calculate_pools, finalize_state
)


def recalculate_unit_stats(unit):
    """
    Полный пересчет всех характеристик персонажа.
    """
    logs = []

    # 1. Инициализация
    mods = init_modifiers()
    bonuses = init_bonuses(unit)

    # 2. Сбор бонусов
    collect_ability_bonuses(unit, unit.passives, PASSIVE_REGISTRY, "🛡️", mods, bonuses, logs)
    collect_ability_bonuses(unit, unit.talents, TALENT_REGISTRY, "🌟", mods, bonuses, logs)
    collect_ability_bonuses(unit, unit.augmentations, AUGMENTATION_REGISTRY, "🧬", mods, bonuses, logs)
    collect_weapon_bonuses(unit, mods, bonuses, logs)
    collect_status_bonuses(unit, mods, bonuses, logs)

    # 3. Расчет атрибутов
    attrs, skills = calculate_totals(unit, bonuses, mods)

    # 4. Эффекты статов
    apply_attribute_effects(attrs, mods, logs)
    apply_skill_effects(skills, mods, logs)

    # 5. Производные (Скорость, Пулы)
    calculate_speed_dice(unit, skills["speed"], mods)
    calculate_pools(unit, attrs, skills, mods, logs)

    # 6. Финализация
    finalize_state(unit, mods, logs)

    unit.modifiers = mods
    return logs