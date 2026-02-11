# Импортируем классы из новых модулей
from logic.statuses.common import (
    AttackPowerUpStatus, EnduranceStatus, BleedStatus, ParalysisStatus,
    ProtectionStatus, FragileStatus, VulnerableStatus, BarrierStatus, BindStatus, DeepWoundStatus,
    HasteStatus, BurnStatus, WeaknessStatus, WeakStatus, StaggerResistStatus, DmgUpStatus, DmgDownStatus, RuptureStatus,
    AttackPowerDownStatus, ImmuneParalysisStatus
)
from logic.statuses.custom import (
    SelfControlStatus, SmokeStatus, RedLycorisStatus, SinisterAuraStatus,
    AdaptationStatus, BulletTimeStatus, ClarityStatus, InvisibilityStatus, EnrageTrackerStatus,
    SatietyStatus, MentalProtectionStatus, RegenGanacheStatus, BleedResistStatus,
    IgnoreSatietyStatus, RevengeDmgUpStatus, TauntStatus, FanatMarkStatus, ArrestedStatus,
    SlashResistDownStatus, PierceResistDownStatus, BluntResistDownStatus,
    MainCharacterShellStatus, AzinoBeastStatus, AzinoJackpotStatus, LuckyCoinStatus, StatusAntiCharge, UnderCrosshairsStatus,
    AmmoStatus, StaggerImmuneStatus, ExhaustionStatus, MarkedFleshStatus,  # НОВЫЕ ИМПОРТЫ
)

# === РЕГИСТРАЦИЯ ===
STATUS_REGISTRY = {
    # Common
    "attack_power_up": AttackPowerUpStatus(),
    "endurance": EnduranceStatus(),
    "bleed": BleedStatus(),
    "paralysis": ParalysisStatus(),
    "protection": ProtectionStatus(),
    "fragile": FragileStatus(),
    "vulnerable": VulnerableStatus(),
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

    "fanat_mark":FanatMarkStatus(),
    "dmg_up":DmgUpStatus(),
    "dmg_down":DmgDownStatus(),
    
    # Иммунитеты
    "immune_paralysis": ImmuneParalysisStatus(),
    "stagger_immune": StaggerImmuneStatus(),
    "exhaustion": ExhaustionStatus(),
    "marked_flesh": MarkedFleshStatus(),
    
    # Talent statuses
    "main_character_shell": MainCharacterShellStatus(),
    "weak": WeakStatus(),
    "attack_power_down": AttackPowerDownStatus(),
    "azino_jackpot": AzinoJackpotStatus(),
    "azino_beast": AzinoBeastStatus(),
    "lucky_coin_status": LuckyCoinStatus(),
    "under_crosshairs": UnderCrosshairsStatus(),
    
    # Новый статус Ammo
    "ammo": AmmoStatus(),
    
    # Алиасы для обратной совместимости
    "strength": AttackPowerUpStatus(),  # Старое название -> attack_power_up
    "anti_charge": StatusAntiCharge(),
}