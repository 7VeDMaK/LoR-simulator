class Armor:
    def __init__(self, id, name, rank, description, hp_resists=None, stagger_resists=None, stats=None, passive_id=None):
        self.id = id
        self.name = name
        self.rank = rank
        self.description = description
        # Резисты HP (slash, pierce, blunt)
        self.hp_resists = hp_resists if hp_resists else {"slash": 1.0, "pierce": 1.0, "blunt": 1.0}
        # Резисты Stagger (slash, pierce, blunt)
        self.stagger_resists = stagger_resists if stagger_resists else {"slash": 1.0, "pierce": 1.0, "blunt": 1.0}
        # Дополнительные статы (endurance, tough_skin и т.д.)
        self.stats = stats if stats else {}
        # Пассивная способность брони
        self.passive_id = passive_id


# === РЕЕСТР БРОНИ ===
ARMOR_REGISTRY = {
    "none": Armor(
        id="none",
        name="Без брони",
        rank=9,
        description="Нет защиты.",
        hp_resists={"slash": 1.0, "pierce": 1.0, "blunt": 1.0},
        stagger_resists={"slash": 1.0, "pierce": 1.0, "blunt": 1.0}
    ),
    
    "standard_fixer_suit": Armor(
        id="standard_fixer_suit",
        name="Standard Fixer Suit",
        rank=8,
        description="Стандартная броня фиксера. Базовая защита от всех типов урона.",
        hp_resists={"slash": 1.0, "pierce": 1.0, "blunt": 1.0},
        stagger_resists={"slash": 1.0, "pierce": 1.0, "blunt": 1.0}
    ),
    
    "light_jacket": Armor(
        id="light_jacket",
        name="Средняя Броня",
        rank=9,
        description="Средняя Броня. Средняя защита от всех типов урона.",
        hp_resists={"slash": 0.9, "pierce": 0.9, "blunt": 0.9},
        stagger_resists={"slash": 1.0, "pierce": 1.0, "blunt": 1.0}
    ),
    
    "heavy_armor": Armor(
        id="heavy_armor",
        name="Тяжелая броня",
        rank=6,
        description="Тяжелая защита. Хорошая защита от всех физических атак, но снижает скорость.",
        hp_resists={"slash": 0.7, "pierce": 0.7, "blunt": 0.8},
        stagger_resists={"slash": 0.9, "pierce": 0.9, "blunt": 0.9},
        stats={"speed": -2, "tough_skin": 3}
    ),
    
    "reinforced_coat": Armor(
        id="reinforced_coat",
        name="Усиленный плащ",
        rank=7,
        description="Усиленный плащ с металлическими вставками. Защита от колющего урона.",
        hp_resists={"slash": 0.9, "pierce": 0.75, "blunt": 0.95},
        stagger_resists={"slash": 1.0, "pierce": 0.9, "blunt": 1.0}
    ),
    
    "padded_vest": Armor(
        id="padded_vest",
        name="Стеганый жилет",
        rank=8,
        description="Мягкая защита от дробящего урона.",
        hp_resists={"slash": 1.0, "pierce": 1.0, "blunt": 0.8},
        stagger_resists={"slash": 1.0, "pierce": 1.0, "blunt": 0.85}
    ),

    "armor_leila": Armor(
        id="armor_leila",
        name="Броня Лайлы",
        rank=9,
        description="Старая броня Лайлы... что получила от кого-то, всё ещё может держать удар.",
        hp_resists={"slash": 0.8, "pierce": 1.0, "blunt": 1.2},
        stagger_resists={"slash": 1.0, "pierce": 1.0, "blunt": 1.0}
    ),

    "armor_leila2": Armor(
        id="armor_leila",
        name="FURR SUT",
        rank=9,
        description="Старая броня fursut... что получила от кого-то, всё ещё может держать удар.",
        hp_resists={"slash": 0.7, "pierce": 0.7, "blunt": 0.7},
        stagger_resists={"slash": 1.0, "pierce": 1.0, "blunt": 1.0}
    ),

    "ghost_exoskeleton": Armor(
        id="ghost_exoskeleton",
        name="Экзо-костюм 'Призрак'",
        rank=4,
        description=(
            "Высокотехнологичная броня Синдиката.\n"
            "• Оптический камуфляж (-20% урона при высокой скорости).\n"
            "• Нано-ремонт (реген HP/Stagger).\n"
            "• Перегрузка (защита от первого ошеломления)."
        ),
        # Физика держит хорошо (0.3-0.7), но уязвим к менталу (1.5)
        hp_resists={
            "slash": 0.5,
            "pierce": 0.5,
            "blunt": 0.7,
        },
        # Стаггер резисты (заглушка 1.0)
        stagger_resists={
            "slash": 1.0,
            "pierce": 1.0,
            "blunt": 1.0
        },
        stats={"speed": 3, "agility": 5},
        passive_id="armor_ghost_exo",
    ),
}
