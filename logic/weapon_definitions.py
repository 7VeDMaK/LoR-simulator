class Weapon:
    # === ИЗМЕНЕНИЕ: Добавили weapon_type="light" ===
    def __init__(self, id, name, rank, description, stats, passive_id=None, weapon_type="light"):
        self.id = id
        self.name = name
        self.rank = rank
        self.description = description
        self.stats = stats
        self.passive_id = passive_id
        self.weapon_type = weapon_type  # "light", "medium", "heavy", "ranged"


# === РЕЕСТР ОРУЖИЯ ===
WEAPON_REGISTRY = {
    # Кулаки обычно считаются Легким оружием (или можно сделать отдельный тип "hand", который скалируется от Легкого)
    "none": Weapon("none", "Без оружия", 9, "Кулаки (Легкое).", {}, weapon_type="light"),

    "cleaver_7": Weapon(
        "cleaver_7", "Тесак (7 ранг)", 7, "Легкое оружие +1, +1 к Рубящему",
        {"light_weapon": 1, "power_slash": 1},
        weapon_type="light"  # <---
    ),
    "police_baton": Weapon(
        "police_baton", "Дубинка", 8, "Среднее +2, +1 Дробящий",
        {"medium_weapon": 2, "power_blunt": 1},
        weapon_type="medium" # <---
    ),
    "workshop_pistol": Weapon(
        "workshop_pistol", "Пистолет Мастерской", 6, "Огнестрел +3, +1 Колющий",
        {"firearms": 3, "power_pierce": 1},
        weapon_type="ranged" # <---
    ),

    # === НОВЫЕ ПРЕДМЕТЫ ===
    "annihilator": Weapon(
        id="annihilator",
        name="Аннигиляторная пушка",
        rank=4,
        description="Одноразовая (1 патрон). +100 Мощи. Не пробивает стены.",
        stats={},
        passive_id="mech_annihilator",
        weapon_type="ranged" # Пушка
    ),
    "dual_blades": Weapon(
        id="dual_blades",
        name="Двойные клинки",
        rank=7,
        description="+5 к Атаке.",
        stats={"power_attack": 5},
        weapon_type="medium" # Обычно парные клинки - это среднее или легкое
    ),
    "banganrang": Weapon(
        id="banganrang [WIP]",
        name="Банганранг",
        rank=8,
        description="+5 к Атаке. Наносит Белый урон (SP) вместо Красного.",
        stats={"power_attack": 5},
        passive_id="mech_banganrang",
        weapon_type="ranged" # Гармошка/Инструмент
    ),
    "ganitar": Weapon(
        id="ganitar",
        name="Дуэльный Ганитар",
        rank=4,
        description="Активно: Отключает пассивки врагов.",
        stats={},
        passive_id="mech_ganitar",
        weapon_type="light" # Ожерелье/Клинок
    ),
    "limagun": Weapon(
        id="limagun",
        name="ЛИМАГАН",
        rank=6,
        description="+666% урона по Лиме.",
        stats={},
        passive_id="mech_limagun",
        weapon_type="ranged"
    ),
    "skalalaz_iceaxe": Weapon(
        id="skalalaz_iceaxe",
        name="Ледоруб 'Скала Лаз'",
        rank=7,
        description="Позволяет карабкаться по стенам, отвесным скалам. Иногда требуется проверка Ловкости / Акробатики для совершения действия. +3 к кубам Атаке.",
        stats={"power_attack": 3},
        weapon_type="medium"
    ),
    "lilith_scythe": Weapon(
        id="lilith_scythe",
        name="Коса 'Sinfoil'",
        rank=8,
        description="Легкое. Фирменное оружие Лилит. Длинное лезвие позволяет контролировать дистанцию.",
        stats={},
        weapon_type="medium"
    ),

    "phantom_razors": Weapon(
        id="phantom_razors",
        name="Фантомные Бритвы",
        rank=5,
        description="Нейротоксин. +2 к Рубящему, +2 ко всем броскам (включая уворот).\nПассивно: Паралич при ударе.\nАктивно: Уход в тень.",
        # power_all дает +2 ко всему, power_slash добавляет еще +2 к рубящему (итого +4 к рубящему)
        stats={"power_slash": 2, "power_all": 2},
        weapon_type="light"
    ),

    "mace": Weapon(
        id="mace",
        name="Булава",
        rank=8,  # Ранг можете изменить по желанию
        description="Тяжелое оружие. +3 к Тяжелому, +2 к Дробящему.",
        stats={"heavy_weapon": 3, "power_blunt": 2},
        weapon_type="heavy"
    ),
}