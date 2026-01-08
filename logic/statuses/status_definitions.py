# Импортируем классы из новых модулей
from logic.statuses.common import (
    StrengthStatus, EnduranceStatus, BleedStatus, ParalysisStatus,
    ProtectionStatus, FragileStatus, VulnerabilityStatus, BarrierStatus, BindStatus, DeepWoundStatus, SlowStatus,
    HasteStatus
)
from logic.statuses.custom import (
    SelfControlStatus, SmokeStatus, RedLycorisStatus, SinisterAuraStatus,
    AdaptationStatus, BulletTimeStatus, ClarityStatus, WeaknessStatus, InvisibilityStatus, EnrageTrackerStatus,
    SatietyStatus, MentalProtectionStatus, RegenGanacheStatus, BleedResistStatus, StaggerResistStatus,
    IgnoreSatietyStatus, RevengeDmgUpStatus, TauntStatus
)

NEGATIVE_STATUSES = [
    "bleed", "paralysis", "fragile", "vulnerability", "burn",
    "bind", "slow", "weakness", "lethargy", "wither", "tremor"
]

# === РЕГИСТРАЦИЯ ===
STATUS_REGISTRY = {
    # Common
    "strength": StrengthStatus(),
    "endurance": EnduranceStatus(),
    "bleed": BleedStatus(),
    "paralysis": ParalysisStatus(),
    "protection": ProtectionStatus(),
    "fragile": FragileStatus(),
    "vulnerability": VulnerabilityStatus(),
    "barrier": BarrierStatus(),

    # Custom
    "self_control": SelfControlStatus(),
    "smoke": SmokeStatus(),
    "red_lycoris": RedLycorisStatus(),
    "sinister_aura": SinisterAuraStatus(),
    "adaptation": AdaptationStatus(),
    "bullet_time": BulletTimeStatus(),
    "clarity" :ClarityStatus(),

    "enrage_tracker": EnrageTrackerStatus(),
    "invisibility": InvisibilityStatus(),
    "weakness": WeaknessStatus(),

    "satiety": SatietyStatus(),
    "mental_protection": MentalProtectionStatus(),
    "ignore_satiety": IgnoreSatietyStatus(),
    "stagger_resist": StaggerResistStatus(),
    "bleed_resist": BleedResistStatus(),
    "regen_ganache": RegenGanacheStatus(),
    "revenge_dmg_up": RevengeDmgUpStatus(),
    "taunt": TauntStatus(),

    "bind": BindStatus(),
    "deep_wound": DeepWoundStatus(),

    "haste": HasteStatus(),
    "slow": SlowStatus(),
}