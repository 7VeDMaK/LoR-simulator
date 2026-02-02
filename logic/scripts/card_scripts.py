# logic/card_scripts.py
from logic.scripts.axis_scripts import axis_radiance_clash_win, axis_plot_armor_clash, axis_ex_machina_clash, \
    axis_mcguffin_on_hit, axis_small_failures_use
from logic.scripts.card_damage import deal_effect_damage, self_harm_percent, add_hp_damage, nullify_hp_damage
from logic.scripts.card_dice import consume_evade_for_haste, repeat_dice_by_status, adaptive_damage_type
from logic.scripts.card_power import modify_roll_power, convert_status_to_power, lima_ram_logic
from logic.scripts.card_special import apply_axis_team_buff, summon_ally
from logic.scripts.luck import add_luck_bonus_roll, scale_roll_by_luck, add_power_by_luck, repeat_dice_by_luck
from logic.scripts.resources import restore_resource
from logic.scripts.statuses import (
    apply_status, steal_status, multiply_status, remove_status_script,
    remove_all_positive, apply_status_by_roll, remove_random_status, apply_slot_debuff
)

# === НОВЫЕ ИМПОРТЫ (АДАМ) ===
from logic.scripts.adam_card_scripts import (
    adam_t1_cost, adam_t1_punish,
    adam_t2_cost, adam_t2_punish, adam_t2_combo,
    adam_t3_cost, adam_t3_punish, adam_t3_execution,
    adam_t4_cost, adam_t4_wethermon_fail
)

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

    # === СКРИПТЫ АДАМА ===
    "adam_t1_cost": adam_t1_cost,
    "adam_t1_punish": adam_t1_punish,

    "adam_t2_cost": adam_t2_cost,
    "adam_t2_punish": adam_t2_punish,
    "adam_t2_combo": adam_t2_combo,

    "adam_t3_cost": adam_t3_cost,
    "adam_t3_punish": adam_t3_punish,
    "adam_t3_execution": adam_t3_execution,

    "adam_t4_cost": adam_t4_cost,
    "adam_t4_wethermon_fail": adam_t4_wethermon_fail,

    "axis_radiance_clash_win": axis_radiance_clash_win,
    "axis_mcguffin_on_hit": axis_mcguffin_on_hit,
    "axis_plot_armor_clash": axis_plot_armor_clash,
    "axis_ex_machina_clash": axis_ex_machina_clash,
    "axis_small_failures_use": axis_small_failures_use,
}