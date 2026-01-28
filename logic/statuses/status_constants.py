# logic/statuses/status_constants.py

# Список положительных эффектов (Баффы)
POSITIVE_BUFFS = [
    "strength", "endurance", "haste", "protection", "barrier",
    "regen_hp", "regen_ganache", "mental_protection", "clarity",
    "dmg_up", "power_up", "clash_power_up", "stagger_resist",
    "bleed_resist", "ignore_satiety"
]

# Список негативных эффектов (Дебаффы)
NEGATIVE_STATUSES = [
    "bleed", "paralysis", "fragile", "vulnerability", "burn",
    "bind", "weakness", "lethargy", "wither", "tremor", "rupture",
    "poison",       # Яд
    "deep_wound",   # Глубокая рана
    "slot_lock",    # Блокировка слота
    "passive_lock"  # Блокировка пассивок (от Ганитара)
]

# Список статусов, которые нельзя снимать случайной очисткой (Purge)
IGNORED_STATUSES = [
    "slot_lock",        # Механика карты
    "adaptation",       # Уникальный статус (Хаски/Рейн)
    "red_lycoris",      # Уникальный статус
    "ammo",             # Ресурс
    "charge",           # Ресурс
    "bullet_time",      # Спец. эффект (Лима)
    "no_glasses",       # Спец. эффект (Лима)
    "mental_protection" # Защита Эдама
]