from logic.character_changing.passives.asgick_passives import PassiveWitnessOfGroGoroth, PassivePovar, PassiveFoodLover, \
    PassiveDistortionGroGoroth
from logic.character_changing.passives.equipment_passives import PassiveAnnihilator, PassiveBanganrang, PassiveGanitar, \
    PassiveLimagun, PassivePhantomRazors, PassiveCoagulation
from logic.character_changing.passives.fanat_passives import PassiveFanatReflect, PassiveFanatMarkHunter, \
    PassiveFanatAntiDefense, PassiveFanatStaggerRecovery, PassiveFanatUnwavering
from logic.character_changing.passives.lilith_passives import PassiveHedonism, PassiveWagTail, PassiveBackstreetDemon, \
    PassiveDaughterOfBackstreets, PassiveLiveFastDieYoung
from logic.character_changing.passives.lima_passives import PassiveAcceleratedLearning, TalentArtOfSelfDefense, \
    PassiveLuckyStreak, \
    PassiveFourEyes, PassiveHuntersVedas, PassiveMindSuppression, PassiveShipOfTheseus, PassiveWildCityscape
from logic.character_changing.passives.rein_passives import PassiveSCells, PassiveNewDiscovery, TalentRedLycoris, TalentShadowOfMajesty
from logic.character_changing.passives.zafiel_passives import PassiveSevereTraining, PassiveAdaptation
from logic.character_changing.passives.leila_passives import PassiveStances, PassiveHardenedBySolitude
    
# === РЕГИСТРАЦИЯ ===
PASSIVE_REGISTRY = {
"hedonism": PassiveHedonism(),
"wag_tail": PassiveWagTail(),
"backstreet_demon": PassiveBackstreetDemon(),
"daughter_of_backstreets": PassiveDaughterOfBackstreets(),
"live_fast_die_young": PassiveLiveFastDieYoung(),
"s_cells": PassiveSCells(),
"new_discovery": PassiveNewDiscovery(),
"red_lycoris": TalentRedLycoris(),
"shadow_majesty":TalentShadowOfMajesty(),
"severe_training": PassiveSevereTraining(),
"adaptation": PassiveAdaptation(),
"accelerated_learning": PassiveAcceleratedLearning(),
"art_of_self_defense": TalentArtOfSelfDefense(),
"lucky_streak": PassiveLuckyStreak(),
"four_eyes": PassiveFourEyes(),
"hunters_vedas": PassiveHuntersVedas(),
"mind_suppression": PassiveMindSuppression(),
"witness_gro_goroth": PassiveWitnessOfGroGoroth(),

"mech_annihilator": PassiveAnnihilator(),
"mech_banganrang": PassiveBanganrang(),
"mech_ganitar": PassiveGanitar(),
"mech_limagun": PassiveLimagun(),
"povar":PassivePovar(),
"food_lover": PassiveFoodLover(),
"ship_of_theseus": PassiveShipOfTheseus(),
"wild_cityscape": PassiveWildCityscape(),
"distortionGroGoroth": PassiveDistortionGroGoroth(),
"mech_phantom_razors": PassivePhantomRazors(),
"coagulation": PassiveCoagulation(),

"fanat_stagger_recovery": PassiveFanatStaggerRecovery(),
    "fanat_anti_defense": PassiveFanatAntiDefense(),
    "fanat_mark_hunter": PassiveFanatMarkHunter(),
    "fanat_reflect": PassiveFanatReflect(),
"fanat_unwavering": PassiveFanatUnwavering(),
"stances": PassiveStances(),
"hardened_by_solitude": PassiveHardenedBySolitude(),
}