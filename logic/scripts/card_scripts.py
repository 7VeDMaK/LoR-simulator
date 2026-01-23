# logic/card_scripts.py

from logic.scripts.combat import modify_roll_power, deal_effect_damage, self_harm_percent, add_hp_damage, \
    nullify_hp_damage, convert_status_to_power, repeat_dice_by_status, consume_evade_for_haste, lima_ram_logic, \
    apply_axis_team_buff, adaptive_damage_type, summon_ally
from logic.scripts.resources import restore_resource
from logic.scripts.statuses import (
    apply_status, steal_status, multiply_status, remove_status_script,
    remove_all_positive, apply_status_by_roll, remove_random_status, apply_slot_debuff
)
from logic.scripts.luck import add_luck_bonus_roll, scale_roll_by_luck, add_power_by_luck, repeat_dice_by_luck

# Реестр скриптов для использования в JSON карт
SCRIPTS_REGISTRY = {
    # Combat
    "modify_roll_power": modify_roll_power,
    "deal_effect_damage": deal_effect_damage,
    "self_harm_percent": self_harm_percent,
    "add_hp_damage": add_hp_damage,
    "nullify_hp_damage": nullify_hp_damage,

    # Resources
    "restore_resource": restore_resource,

    # Statuses
    "apply_status": apply_status,
    "steal_status": steal_status,
    "multiply_status": multiply_status,
    "remove_status": remove_status_script,
    "remove_all_positive": remove_all_positive,
    "apply_status_by_roll": apply_status_by_roll,

    # Luck
    "add_luck_bonus_roll": add_luck_bonus_roll,
    "scale_roll_by_luck": scale_roll_by_luck,
    "add_power_by_luck": add_power_by_luck,
    "convert_status_to_power": convert_status_to_power,
    "repeat_dice_by_luck": repeat_dice_by_luck,
    "consume_evade_for_haste": consume_evade_for_haste,
    "repeat_dice_by_status": repeat_dice_by_status,
    "lima_ram_logic": lima_ram_logic,
    "remove_random_status": remove_random_status,
    "apply_slot_debuff": apply_slot_debuff,

    "apply_axis_team_buff": apply_axis_team_buff,
    "adaptive_damage_type": adaptive_damage_type,
    "summon_ally": summon_ally,
}