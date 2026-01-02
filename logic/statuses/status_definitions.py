# Импортируем классы из новых модулей
from logic.statuses.common import (
    StrengthStatus, EnduranceStatus, BleedStatus, ParalysisStatus,
    ProtectionStatus, FragileStatus, VulnerabilityStatus, BarrierStatus
)
from logic.statuses.custom import (
    SelfControlStatus, SmokeStatus, RedLycorisStatus, SinisterAuraStatus,
    AdaptationStatus, BulletTimeStatus, ClarityStatus
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
    "clarity" :ClarityStatus()
}