from logic.statuses.status_definitions import STATUS_REGISTRY

# Списки опций
STATUS_LIST = sorted(list(STATUS_REGISTRY.keys()))
TARGET_OPTS = ["self", "target", "all"]
STAT_OPTS = ["None", "attack_power_up", "endurance", "agility", "intellect", "eloquence", "luck", "max_hp", "current_hp",
             "max_sp", "current_sp", "charge", "smoke"]

# Схемы скриптов
SCRIPT_SCHEMAS = {
    # --- БОЕВЫЕ МОДИФИКАТОРЫ ---
    "Modify Roll Power": {
        "id": "modify_roll_power",
        "params": [
            {"key": "base", "label": "База (Flat)", "type": "int", "default": 0},
            {"key": "stat", "label": "Скалирование от...", "type": "select", "opts": STAT_OPTS, "default": "None"},
            {"key": "scale_from_target", "label": "Брать стат у Цели?", "type": "bool", "default": False},
            {"key": "factor", "label": "Множитель стата (x)", "type": "float", "default": 1.0},
            {"key": "diff", "label": "Разница с врагом?", "type": "bool", "default": False,
             "help": "(Мой стат - Стат врага)"},
            {"key": "reason", "label": "Название в логе", "type": "text", "default": "Bonus"}
        ]
    },

    # --- ЛЕЧЕНИЕ / РЕСУРСЫ ---
    "Restore Resource": {
        "id": "restore_resource",
        "params": [
            {"key": "type", "label": "Ресурс", "type": "select", "opts": ["hp", "sp", "stagger"], "default": "hp"},
            {"key": "base", "label": "База", "type": "int", "default": 5},
            {"key": "stat", "label": "Скалирование от...", "type": "select", "opts": STAT_OPTS, "default": "None"},
            {"key": "scale_from_target", "label": "Брать стат у Цели?", "type": "bool", "default": False},
            {"key": "factor", "label": "Множитель стата", "type": "float", "default": 0.5},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target", "all_allies"],
             "default": "self"}
        ]
    },

    # --- УРОН ЭФФЕКТОМ ---
    "Deal Effect Damage": {
        "id": "deal_effect_damage",
        "params": [
            {"key": "type", "label": "Тип урона", "type": "select", "opts": ["hp", "stagger", "sp"], "default": "hp"},
            {"key": "base", "label": "База", "type": "int", "default": 0},
            {"key": "stat", "label": "Скалирование от...", "type": "select", "opts": STAT_OPTS,
             "default": "current_hp"},
            {"key": "scale_from_target", "label": "Брать стат у Цели?", "type": "bool", "default": False},
            {"key": "factor", "label": "Множитель (для %)", "type": "float", "default": 0.05},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target", "all"], "default": "self"}
        ]
    },

    # --- СТАТУСЫ ---
    "Apply Status": {
        "id": "apply_status",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "bleed"},
            {"key": "base", "label": "Базовое кол-во", "type": "int", "default": 1},
            {"key": "stat", "label": "Скейл от (опц.)", "type": "select", "opts": STAT_OPTS, "default": "None"},
            {"key": "scale_from_target", "label": "Брать стат у Цели?", "type": "bool", "default": False},
            {"key": "factor", "label": "Множитель скейла", "type": "float", "default": 1.0},
            {"key": "duration", "label": "Длительность", "type": "int", "default": 1},
            {"key": "delay", "label": "Задержка (Delay)", "type": "int", "default": 0},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["target", "self", "all_allies"],
             "default": "target"}
        ]
    },

    "Steal Status": {
        "id": "steal_status",
        "params": [{"key": "status", "label": "Статус", "type": "status_select", "default": "smoke"}]
    },
    "Multiply Status": {
        "id": "multiply_status",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "smoke"},
            {"key": "multiplier", "label": "Множитель", "type": "float", "default": 2.0}
        ]
    },
    "Remove Status": {
        "id": "remove_status",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "bleed"},
            {"key": "base", "label": "Сколько снять", "type": "int", "default": 999},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"], "default": "self"}
        ]
    },
    "Remove All Positive": {
        "id": "remove_all_positive",
        "params": [
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"], "default": "self"}
        ]
    },
    "Self Harm Percent": {
        "id": "self_harm_percent",
        "params": [
            {"key": "percent", "label": "Процент (0.1 = 10%)", "type": "float", "default": 0.1}
        ]
    },
    "Add HP Damage": {
        "id": "add_hp_damage",
        "params": [
            {"key": "percent", "label": "Процент от Макс HP цели", "type": "float", "default": 0.05}
        ]
    },
    "Apply Status By Roll": {
        "id": "apply_status_by_roll",
        "params": [
            {"key": "status", "label": "Статус", "type": "status_select", "default": "protection"},
            {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"], "default": "self"}
        ]
    },
    "Add Luck Bonus": {
        "id": "add_luck_bonus_roll",
        "params": [
            {"key": "step", "label": "Шаг удачи", "type": "int", "default": 10},
            {"key": "limit", "label": "Лимит бонуса", "type": "int", "default": 999}
        ]
    },
    "Scale Roll By Luck": {
        "id": "scale_roll_by_luck",
        "params": [
            {"key": "step", "label": "Шаг удачи", "type": "int", "default": 10},
            {"key": "limit", "label": "Лимит повторов", "type": "int", "default": 7}
        ]
    },
    "Add Power By Luck": {
        "id": "add_power_by_luck",
        "params": [
            {"key": "step", "label": "Шаг удачи", "type": "int", "default": 5},
            {"key": "limit", "label": "Лимит силы", "type": "int", "default": 15}
        ]
    }
}