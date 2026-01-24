# Импортируем классы из новых модулей
from logic.statuses.common import (
    StrengthStatus, EnduranceStatus, BleedStatus, ParalysisStatus,
    ProtectionStatus, FragileStatus, VulnerabilityStatus, BarrierStatus, BindStatus, DeepWoundStatus, SlowStatus,
    HasteStatus, BurnStatus, WeaknessStatus, WeakStatus, StaggerResistStatus, DmgUpStatus, DmgDownStatus, RuptureStatus
)
from logic.statuses.custom import (
    SelfControlStatus, SmokeStatus, RedLycorisStatus, SinisterAuraStatus,
    AdaptationStatus, BulletTimeStatus, ClarityStatus,  InvisibilityStatus, EnrageTrackerStatus,
    SatietyStatus, MentalProtectionStatus, RegenGanacheStatus, BleedResistStatus,
    IgnoreSatietyStatus, RevengeDmgUpStatus, TauntStatus, FanatMarkStatus, ArrestedStatus,
    SlashResistDownStatus, PierceResistDownStatus, BluntResistDownStatus
)

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
    "burn": BurnStatus(),
    "rupture": RuptureStatus(),
    "self_control": SelfControlStatus(),
    "smoke": SmokeStatus(),
    "red_lycoris": RedLycorisStatus(),
    "sinister_aura": SinisterAuraStatus(),
    "adaptation": AdaptationStatus(),
    "bullet_time": BulletTimeStatus(),
    "clarity" :ClarityStatus(),

    "enrage_tracker": EnrageTrackerStatus(),
    "invisibility": InvisibilityStatus(),
    "weakness": WeaknessStatus()   ,

    "satiety": SatietyStatus(),
    "mental_protection": MentalProtectionStatus(),
    "ignore_satiety": IgnoreSatietyStatus(),
    "stagger_resist": StaggerResistStatus(),
    "bleed_resist": BleedResistStatus(),
    "regen_ganache": RegenGanacheStatus(),
    "revenge_dmg_up": RevengeDmgUpStatus(),
    "taunt": TauntStatus() ,

    "slash_resist_down": SlashResistDownStatus(),
    "pierce_resist_down": PierceResistDownStatus(),
    "blunt_resist_down": BluntResistDownStatus(),

    "arrested": ArrestedStatus(),

    "bind": BindStatus(),
    "deep_wound": DeepWoundStatus(),

    "haste": HasteStatus(),
    "slow": SlowStatus(),

    "fanat_mark":FanatMarkStatus(),
    "dmg_up":DmgUpStatus(),
    "dmg_down":DmgDownStatus(),
    "weak": WeakStatus()
}