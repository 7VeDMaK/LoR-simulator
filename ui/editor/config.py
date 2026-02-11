from logic.statuses.status_definitions import STATUS_REGISTRY

# === СПИСКИ ОПЦИЙ ===
STATUS_LIST = sorted(list(STATUS_REGISTRY.keys()))
TARGET_OPTS = ["self", "target", "all_allies", "all_enemies", "all"]
STAT_OPTS = ["None", "attack_power_up", "endurance", "agility", "intellect",
             "eloquence", "luck", "max_hp", "current_hp",
             "max_sp", "current_sp", "max_stagger", "current_stagger", "charge", "smoke"]

# === ОБЩИЕ УСЛОВИЯ (Добавляются ко всем скриптам) ===
COMMON_CONDITIONS = [
    {"key": "probability", "label": "🎲 Шанс (1.0 = 100%)", "type": "float", "default": 1.0,
     "help": "Вероятность срабатывания скрипта."},
    {"key": "req_stat", "label": "🔒 Треб. Стат (опц.)", "type": "select", "opts": STAT_OPTS, "default": "None",
     "help": "Скрипт сработает, только если этот стат выше значения."},
    {"key": "req_val", "label": "🔒 Значение стата", "type": "int", "default": 0}
]

# === СХЕМЫ СКРИПТОВ ДЛЯ РЕДАКТОРА ===
SCRIPT_SCHEMAS = {

    # =========================================
    # 1. БОЕВЫЕ МОДИФИКАТОРЫ (POWER / DAMAGE)
    # =========================================
    "Modify Roll Power": {
        "id": "modify_roll_power",
        "description": "Изменяет итоговое значение броска кубика. Можно добавить фиксированное число или бонус от статов.",
        "params": [
                      {"key": "base", "label": "База (Flat)", "type": "int", "default": 0},
                      {"key": "stat", "label": "Скалирование от...", "type": "select", "opts": STAT_OPTS,
                       "default": "None"},
                      {"key": "factor", "label": "Множитель стата (x)", "type": "float", "default": 1.0},
                      {"key": "scale_from_target", "label": "Брать стат у Цели?", "type": "bool", "default": False},
                      {"key": "diff", "label": "Разница с врагом?", "type": "bool", "default": False,
                       "help": "(Мой - Врага)"},
                      {"key": "reason", "label": "Название в логе", "type": "text", "default": "Bonus"}
                  ] + COMMON_CONDITIONS
    },
    "Multiply Roll Power": {
        "id": "multiply_roll_power",
        "description": "Умножает итоговое значение броска кубика (мощность) на коэффициент.",
        "params": [
                      {"key": "multiplier", "label": "Множитель", "type": "float", "default": 2.0},
                      {"key": "reason", "label": "Название в логе", "type": "text", "default": "Power x2"}
                  ] + COMMON_CONDITIONS
    },
    "Set Card Power Multiplier": {
        "id": "set_card_power_multiplier",
        "description": "Ставит множитель мощности для этой карты (через память, on_use).",
        "params": [
                      {"key": "multiplier", "label": "Множитель", "type": "float", "default": 2.0},
                      {"key": "condition", "label": "Условие", "type": "select",
                       "opts": ["", "last_clash_win", "last_clash_lose", "last_clash_draw"], "default": ""},
                      {"key": "reason", "label": "Название в логе", "type": "text", "default": "Power Mult"}
                  ] + COMMON_CONDITIONS
    },
    "Apply Card Power Multiplier": {
        "id": "apply_card_power_multiplier",
        "description": "Применяет множитель мощности, установленный для этой карты (on_roll).",
        "params": [
                      {"key": "reason", "label": "Название в логе", "type": "text", "default": "Power Mult"}
                  ] + COMMON_CONDITIONS
    },
    "Deal Effect Damage": {
        "id": "deal_effect_damage",
        "description": "Наносит прямой урон (HP/SP/Stagger) эффектом (игнорирует резисты, если не указано иное в движке).",
        "params": [
                      {"key": "type", "label": "Тип урона", "type": "select", "opts": ["hp", "stagger", "sp"],
                       "default": "hp"},
                      {"key": "base", "label": "База", "type": "int", "default": 0},
                      {"key": "stat", "label": "Скалирование от...", "type": "select", "opts": STAT_OPTS,
                       "default": "None"},
                      {"key": "factor", "label": "Множитель (для %)", "type": "float", "default": 1.0},
                      {"key": "target", "label": "Цель", "type": "select", "opts": TARGET_OPTS, "default": "target"}
                  ] + COMMON_CONDITIONS
    },
    "Add HP Damage (%)": {
        "id": "add_hp_damage",
        "description": "Добавляет бонусный урон к атаке в процентах от Максимального HP цели.",
        "params": [
                      {"key": "percent", "label": "Процент от Макс HP цели (0.05 = 5%)", "type": "float",
                       "default": 0.05}
                  ] + COMMON_CONDITIONS
    },
    "Nullify Damage": {
        "id": "nullify_hp_damage",
        "description": "Полностью обнуляет весь HP урон, который должен был нанести этот кубик (или по этому кубику).",
        "params": [] + COMMON_CONDITIONS
    },
    "Multiply Damage": {
        "id": "multiply_damage",
        "description": "Умножает итоговый урон (HP) без изменения броска.",
        "params": [
                      {"key": "multiplier", "label": "Множитель урона", "type": "float", "default": 2.0}
                  ] + COMMON_CONDITIONS
    },

    # =========================================
    # 2. СТАТУСЫ (STATUSES)
    # =========================================
    "Apply Status": {
        "id": "apply_status",
        "description": "Накладывает бафф или дебафф на цель.",
        "params": [
                      {"key": "status", "label": "Статус", "type": "status_select", "default": "bleed"},
                      {"key": "base", "label": "Количество", "type": "int", "default": 1},
                      {"key": "duration", "label": "Длительность (ходов)", "type": "int", "default": 1},
                      {"key": "delay", "label": "Задержка (Delay)", "type": "int", "default": 0},
                      {"key": "target", "label": "Цель", "type": "select", "opts": TARGET_OPTS, "default": "target"},
                      {"key": "min_roll", "label": "Мин. бросок (усл.)", "type": "int", "default": 0}
                  ] + COMMON_CONDITIONS
    },
    "Apply Status (Roll Based)": {
        "id": "apply_status_by_roll",
        "description": "Накладывает статус в количестве, равном значению, выпавшему на кубике.",
        "params": [
                      {"key": "status", "label": "Статус", "type": "status_select", "default": "protection"},
                      {"key": "target", "label": "Цель", "type": "select", "opts": TARGET_OPTS, "default": "self"}
                  ] + COMMON_CONDITIONS
    },
    "Remove Status": {
        "id": "remove_status",
        "description": "Снимает указанное количество стаков статуса с цели.",
        "params": [
                      {"key": "status", "label": "Статус", "type": "status_select", "default": "bleed"},
                      {"key": "base", "label": "Сколько снять", "type": "int", "default": 999},
                      {"key": "target", "label": "Цель", "type": "select", "opts": TARGET_OPTS, "default": "self"}
                  ] + COMMON_CONDITIONS
    },
    "Remove All Positive": {
        "id": "remove_all_positive",
        "description": "Очищает цель от всех положительных эффектов (Strength, Haste и т.д.).",
        "params": [
                      {"key": "target", "label": "Цель", "type": "select", "opts": TARGET_OPTS, "default": "target"}
                  ] + COMMON_CONDITIONS
    },
    "Remove Best Positive": {
        "id": "remove_best_positive",
        "description": "Снимает один положительный эффект с наибольшей длительностью (tie: большее количество).",
        "params": [
                      {"key": "target", "label": "Цель", "type": "select", "opts": TARGET_OPTS, "default": "target"}
                  ] + COMMON_CONDITIONS
    },
    "Steal Status": {
        "id": "steal_status",
        "description": "Забирает 1 стак статуса у врага и передает его себе.",
        "params": [
                      {"key": "status", "label": "Статус", "type": "status_select", "default": "power_up"}
                  ] + COMMON_CONDITIONS
    },
    "Multiply Status": {
        "id": "multiply_status",
        "description": "Умножает текущее количество стаков статуса на цели (например, удвоить Ожог).",
        "params": [
                      {"key": "status", "label": "Статус", "type": "status_select", "default": "burn"},
                      {"key": "multiplier", "label": "Множитель", "type": "float", "default": 2.0}
                  ] + COMMON_CONDITIONS
    },

    # =========================================
    # 3. ЛЕЧЕНИЕ И РЕСУРСЫ
    # =========================================
    "Restore Resource": {
        "id": "restore_resource",
        "description": "Восстанавливает HP, SP или Stagger. Можно скалировать от статов.",
        "params": [
                      {"key": "type", "label": "Ресурс", "type": "select", "opts": ["hp", "sp", "stagger"],
                       "default": "hp"},
                      {"key": "base", "label": "База", "type": "int", "default": 5},
                      {"key": "factor", "label": "Множитель скейла", "type": "float", "default": 0.0},
                      {"key": "stat", "label": "Скалирование от...", "type": "select", "opts": STAT_OPTS,
                       "default": "None"},
                      {"key": "target", "label": "Цель", "type": "select", "opts": TARGET_OPTS, "default": "self"}
                  ] + COMMON_CONDITIONS
    },
    "Restore Resource (Roll Based)": {
        "id": "restore_resource_by_roll",
        "description": "Восстанавливает ресурс в размере значения броска (Вампиризм).",
        "params": [
                      {"key": "type", "label": "Ресурс", "type": "select", "opts": ["hp", "sp"], "default": "hp"},
                      {"key": "factor", "label": "Множитель от броска", "type": "float", "default": 1.0},
                      {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "all_allies"],
                       "default": "self"}
                  ] + COMMON_CONDITIONS
    },

    # =========================================
    # 4. СПЕЦИФИЧНЫЕ МЕХАНИКИ (AXIS / VIVIAN)
    # =========================================
    "Consume Status -> Apply Effect": {
        "id": "consume_status_apply",
        "description": "Если у цели есть статус X, снимает его и накладывает статус Y. Используется для комбо.",
        "params": [
                      {"key": "consume_status", "label": "Снять статус (Условие)", "type": "status_select"},
                      {"key": "consume_amount", "label": "Сколько снять", "type": "int", "default": 1},
                      {"key": "apply_status", "label": "Наложить статус", "type": "status_select"},
                      {"key": "apply_amount", "label": "Сколько наложить", "type": "int", "default": 1},
                      {"key": "apply_target", "label": "На кого наложить", "type": "select", "opts": TARGET_OPTS,
                       "default": "target"},
                      {"key": "duration", "label": "Длительность", "type": "int", "default": 1}
                  ] + COMMON_CONDITIONS
    },
    "Damage by Roll (Masochism)": {
        "id": "deal_damage_by_roll",
        "description": "Цель получает урон, равный значению броска этого кубика. (Для Вивьен: target=self).",
        "params": [
                      {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"],
                       "default": "self"},
                      {"key": "type", "label": "Тип (hp/stagger)", "type": "select", "opts": ["hp", "stagger"],
                       "default": "hp"}
                  ] + COMMON_CONDITIONS
    },
    "Damage by Clash Diff": {
        "id": "deal_damage_by_clash_diff",
        "description": "Наносит урон, равный разнице между вашим броском и броском врага в столкновении.",
        "params": [
                      {"key": "target", "label": "Цель", "type": "select", "opts": ["self", "target"],
                       "default": "self"}
                  ] + COMMON_CONDITIONS
    },
    "Self Harm (%)": {
        "id": "self_harm_percent",
        "description": "Отнимает процент от ТЕКУЩЕГО здоровья владельца.",
        "params": [
                      {"key": "percent", "label": "Процент (0.1 = 10%)", "type": "float", "default": 0.1}
                  ] + COMMON_CONDITIONS
    },

    # =========================================
    # 5. МАНИПУЛЯЦИИ С КУБИКАМИ
    # =========================================
    "Break Target Dice": {
        "id": "break_target_dice",
        "description": "Уничтожает текущий кубик противника (обычно при победе в столкновении).",
        "params": [] + COMMON_CONDITIONS
    },
    "Share Dice (Unity)": {
        "id": "share_dice_with_hand",
        "description": "Копирует первый кубик этой карты и добавляет его всем картам в руке с указанным флагом.",
        "params": [
                      {"key": "flag", "label": "Флаг карты (unity)", "type": "text", "default": "unity"}
                  ] + COMMON_CONDITIONS
    },
    "Adaptive Damage Type": {
        "id": "adaptive_damage_type",
        "description": "Меняет тип урона кубика на тот, к которому у врага наименьшее сопротивление (Fatal/Weak).",
        "params": [] + COMMON_CONDITIONS
    },
    "Consume Evade -> Haste": {
        "id": "consume_evade_for_haste",
        "description": "Если это кубик уклонения и он не был использован, превращает его в Ускорение на след. ход.",
        "params": [] + COMMON_CONDITIONS
    },
    "Repeat Dice by Luck": {
        "id": "repeat_dice_by_luck",
        "description": "Добавляет копии первого кубика в карту в зависимости от Удачи.",
        "params": [
                      {"key": "step", "label": "Шаг удачи", "type": "int", "default": 10},
                      {"key": "limit", "label": "Лимит копий", "type": "int", "default": 10}
                  ] + COMMON_CONDITIONS
    },
    "Repeat Dice by Status": {
        "id": "repeat_dice_by_status",
        "description": "Добавляет копии кубика в карту в зависимости от стаков статуса.",
        "params": [
                      {"key": "status", "label": "Статус", "type": "status_select", "default": "haste"},
                      {"key": "max", "label": "Лимит копий", "type": "int", "default": 4},
                      {"key": "die_index", "label": "Индекс кубика", "type": "int", "default": 0}
                  ] + COMMON_CONDITIONS
    },

    # =========================================
    # 6. УДАЧА И ПРОЧЕЕ
    # =========================================
    "Add Luck Bonus": {
        "id": "add_luck_bonus_roll",
        "description": "Добавляет бонус к значению кубика на основе показателя Удачи.",
        "params": [
                      {"key": "step", "label": "Шаг удачи", "type": "int", "default": 10},
                      {"key": "limit", "label": "Лимит бонуса", "type": "int", "default": 999}
                  ] + COMMON_CONDITIONS
    },
    "Summon Ally": {
        "id": "summon_ally",
        "description": "Призывает нового персонажа в команду из библиотеки.",
        "params": [
                      {"key": "unit_name", "label": "Имя (из Roster)", "type": "text", "default": "Minion"}
                  ] + COMMON_CONDITIONS
    },
    "Apply Marked Flesh": {
        "id": "apply_marked_flesh",
        "description": "Помечает врага с наименьшим HP как единственную цель.",
        "params": [
                      {"key": "duration", "label": "Длительность", "type": "int", "default": 99}
                  ] + COMMON_CONDITIONS
    },
    "Set Memory Flag": {
        "id": "set_memory_flag",
        "description": "Устанавливает скрытый флаг в памяти юнита. Используется для сложных пассивок.",
        "params": [
                      {"key": "flag", "label": "Название флага", "type": "text", "default": "default"},
                      {"key": "value", "label": "Значение (True)", "type": "bool", "default": True}
                  ] + COMMON_CONDITIONS
    }
}