# logic/card_scripts.py

# === УДАЛЕНЫ ИМПОРТЫ AXIS_SCRIPTS ===

from logic.scripts.card_damage import deal_effect_damage, self_harm_percent, add_hp_damage, nullify_hp_damage, \
    deal_damage_by_roll, deal_damage_by_clash_diff
from logic.scripts.card_damage import multiply_damage
from logic.scripts.card_dice import (
    consume_evade_for_haste, repeat_dice_by_status, adaptive_damage_type,
    break_target_dice, add_preset_dice, share_dice_with_hand # <--- НОВЫЕ ИМПОРТЫ
)
from logic.scripts.card_power import modify_roll_power, convert_status_to_power, lima_ram_logic, apply_card_power_bonus, \
    multiply_roll_power, set_card_power_multiplier, apply_card_power_multiplier
from logic.scripts.card_special import apply_axis_team_buff, summon_ally, set_memory_flag, apply_marked_flesh, \
    set_card_power_bonus
from logic.scripts.luck import add_luck_bonus_roll, scale_roll_by_luck, add_power_by_luck, repeat_dice_by_luck
from logic.scripts.resources import restore_resource, restore_resource_by_roll
from logic.scripts.statuses import (
    apply_status, steal_status, multiply_status, remove_status_script,
    remove_all_positive, apply_status_by_roll, remove_random_status, remove_best_positive,
    apply_slot_debuff, consume_status_apply # <--- НОВЫЙ ИМПОРТ
)

from logic.scripts.utils import _resolve_value, _get_targets, _check_conditions

# Реестр скриптов для использования в JSON карт
SCRIPTS_REGISTRY = {
    # Combat
    "modify_roll_power": modify_roll_power,
    "multiply_roll_power": multiply_roll_power,
    "set_card_power_multiplier": set_card_power_multiplier,
    "apply_card_power_multiplier": apply_card_power_multiplier,
    "deal_effect_damage": deal_effect_damage,
    "self_harm_percent": self_harm_percent,
    "add_hp_damage": add_hp_damage,
    "nullify_hp_damage": nullify_hp_damage,
    "multiply_damage": multiply_damage,

    # Resources
    "restore_resource": restore_resource,

    # Statuses
    "apply_status": apply_status,
    "steal_status": steal_status,
    "multiply_status": multiply_status,
    "remove_status": remove_status_script,
    "remove_all_positive": remove_all_positive,
    "apply_status_by_roll": apply_status_by_roll,
    "consume_status_apply": consume_status_apply, # <--- НОВОЕ

    # Luck & Dice Manipulation
    "add_luck_bonus_roll": add_luck_bonus_roll,
    "scale_roll_by_luck": scale_roll_by_luck,
    "add_power_by_luck": add_power_by_luck,
    "convert_status_to_power": convert_status_to_power,
    "apply_card_power_bonus": apply_card_power_bonus,
    "repeat_dice_by_luck": repeat_dice_by_luck,
    "consume_evade_for_haste": consume_evade_for_haste,
    "repeat_dice_by_status": repeat_dice_by_status,
    "lima_ram_logic": lima_ram_logic,
    "remove_random_status": remove_random_status,
    "remove_best_positive": remove_best_positive,
    "apply_slot_debuff": apply_slot_debuff,
    "adaptive_damage_type": adaptive_damage_type,
    "break_target_dice": break_target_dice,
    "add_preset_dice": add_preset_dice,       # <--- НОВОЕ
    "share_dice_with_hand": share_dice_with_hand, # <--- НОВОЕ

    # Special & Summons
    "apply_axis_team_buff": apply_axis_team_buff,
    "summon_ally": summon_ally,
    "set_memory_flag": set_memory_flag,
    "apply_marked_flesh": apply_marked_flesh,
    "set_card_power_bonus": set_card_power_bonus,

    # Utils (редко вызываются напрямую из JSON, но оставим)
    "_resolve_value": _resolve_value,
    "_get_targets": _get_targets,
    "_check_conditions": _check_conditions,

    "deal_damage_by_roll": deal_damage_by_roll,
    "deal_damage_by_clash_diff": deal_damage_by_clash_diff,
    "restore_resource_by_roll": restore_resource_by_roll,
}