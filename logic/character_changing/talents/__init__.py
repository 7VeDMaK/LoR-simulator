# logic/talents/__init__.py
from logic.character_changing.talents.branch_10_energy import (
    TalentElectrician, TalentPainPoints, TalentMechanicalEnergy, TalentPainShock,
    TalentEmergencyProtection, TalentStaticElectricity, TalentEnteringRhythm, TalentDirtyTricks,
    TalentPlayingOnNerves, TalentOvervoltage, TalentEMField, TalentWithCaution, TalentSharpEye,
    TalentTeamPlayer, TalentArrest, TalentBattery, TalentGrounding, TalentFeint, TalentWeakPointEnergy,
    TalentRuptureApplication, TalentRiftingSpace, TalentCapacitor, TalentAchillesHeel, TalentNoMistakes,
    TalentShortCircuit, TalentPrideOfSeven
)
from logic.character_changing.talents.branch_11_flame import (
    TalentStrikeWhileIronHot, TalentSpark, TalentCauterization, TalentHot,
    TalentBodyAdaptation, TalentHearthOfPower, TalentAshesToAshes,
    TalentHellfire, TalentWildfire, TalentFieryTemper,
    TalentIfrit, TalentPhoenix, TalentFirestorm, TalentBurnMeDown
)
from logic.character_changing.talents.branch_12_technologist import (
    TalentProjection, TalentHacker, TalentLittleHelper, TalentProgrammingLanguages,
    TalentPortableShield, TalentEnergyCycle, TalentModulation, TalentAccessPoint,
    TalentError404, TalentAssHack)
from logic.character_changing.talents.branch_13_roboticist import (
    TalentBestFriendsForever, TalentLittleBigTrouble, TalentCellExpander,
    TalentNoFirstLaw, TalentBrightTalent, TalentSmallerLighterFaster,
    TalentFrameUpgrade, TalentMadeToLast, TalentChimeraCore,
    TalentUpshotRobot, TalentQuantumHub, TalentJackOfAllTrades,
    TalentMachinaExDeo, TalentExogenesisProtocol, TalentMultiConnection
)
from logic.character_changing.talents.branch_14_tremor import (
    TalentFightToTheEnd, TalentShareWithFriend, TalentCarelessness,
    TalentPassTheFare, TalentOwnTremor, TalentReadinessForEverything,
    TalentKeepGoing, TalentResonance, TalentImmobile, TalentTremorToBone
)
from logic.character_changing.talents.branch_1_mindgames import TalentKeepItTogether, TalentCenterOfBalance, \
    TalentControlledDistortion, \
    TalentSafeEGO, TalentEmotionalStorm, TalentUnbearablePresence, TalentTeaMaster, TalentMindPower, TalentPeakSanity, \
    TalentPsychicStrain
from logic.character_changing.talents.branch_2_best import (
    # Новые таланты ветки 2
    TalentNaturalGenius, TalentCelestialEyes, TalentWatchAndLearn, TalentRightOfTheFirst,
    TalentBlackFlash, TalentBlueFlash, TalentRoleModel, TalentMockery, TalentPlotArmor,
    TalentMuted, TalentJustGettingStarted
)
from logic.character_changing.talents.branch_3_tireless import (
    TalentBigGuy, TalentDefense, TalentCommendableConstitution, TalentBigHeart,
    TalentRock, TalentDespiteAdversities, TalentHeatResistant,
    TalentAdaptationTireless, TalentToughAsSteel, TalentDefender,
    TalentSurvivor, TalentMuscleOverstrain, TalentIdolOath, TalentSurgeOfStrength
)
from logic.character_changing.talents.branch_4_medic import TalentNoHippocraticOath, TalentGoodAsNew, TalentRemedyGood, \
    TalentCheese, \
    TalentYouWontDieGood, TalentCarefulNeutralization, TalentDoingGoodWork, TalentNotToday, \
    TalentMadGoodDoctor, TalentToxicologyWeapon, TalentRemedyBad, TalentOrganStriking, TalentAdvancedToxicology, \
    TalentYouWontDieBad, TalentMedicalJargon, TalentChristmasTree, TalentInsaneZeal, TalentGeniusToxicologist, \
    TalentConfete
from logic.character_changing.talents.branch_5_berseker import (
    TalentNakedDefense, TalentVengefulPayback, TalentBerserkerRage, TalentCalmMind,
    TalentFrenzy, TalentCatchBreath, TalentRagingFury, TalentFullConcentration,
    TalentNakedDefense2, TalentNakedDefense3, TalentDescendingIntoMadness,
    TalentSteadyHand, TalentKeyMoment, TalentSecondWindBerserk, TalentDieHard
)
from logic.character_changing.talents.branch_6_smoker import (
    TalentHidingInSmoke, TalentSmokeUniversality, TalentAerialFoot, TalentSmokeScreen,
    TalentRecycling, TalentSelfPreservation, TalentCleansing, TalentExperiencedSmoker,
    TalentLungProcessing, TalentToNarnia, TalentSmokeAdvantage, TalentVulnerabilitySmoke,
    TalentThickSmoke, TalentSmokeAndMirrors
)
from logic.character_changing.talents.branch_7_luck import (
    TalentDealWithFortune, TalentSecondChance, TalentSequentialLuck,
    TalentLuckyBastard, TalentJustSkill, TalentRaiseStakes,
    TalentAzino777, TalentBlessedByFate, TalentAceSleeve,
    TalentImpossiblePossible
)
from logic.character_changing.talents.branch_8_military import (
    TalentAthletic, TalentFastHands, TalentLeader, TalentAddiction,
    TalentRapidRetreat, TalentCombatReload, TalentFindVulnerability,
    TalentBorrowedTime, TalentIronFormation, TalentLastHope
)
from logic.character_changing.talents.branch_9_shadow import (
    TalentAthleticismShadow, TalentRevenge, TalentNotGreatAttention, TalentFormidablePerson,
    TalentSmashingBlade, TalentSlaughter, TalentTrapmaster, TalentFastAndSilent,
    TalentAggressiveParry, TalentStepIntoShadow, TalentTasteOfVictory, TalentSleightOfHand,
    TalentCatReflexes, TalentEnduranceLessons, TalentEyeForDanger, TalentColdBlooded,
    TalentIdentityThief, TalentCoveringTracks, TalentCompetentAdrenaline, TalentKnifeInBack,
    TalentOppression, TalentVulnerabilityPoint, TalentExtremeMeasures, TalentButcher
)
from logic.character_changing.talents.link_talents import (
    TalentCenser, TalentArdentDefense, TalentHitmanAssortment,
    TalentThermalEnergy, TalentScorchingMastery
)

TALENT_REGISTRY = {
# === ВЕТКА 1: ИСКАЖЕНИЕ (MINDGAMES) ===
    "keep_it_together": TalentKeepItTogether(),
    "center_of_balance": TalentCenterOfBalance(),
    "tea_master": TalentTeaMaster(),
    "mind_power": TalentMindPower(),
    "peak_sanity": TalentPeakSanity(),
    "psychic_strain": TalentPsychicStrain(),
    "unbearable_presence": TalentUnbearablePresence(),
    "emotional_storm": TalentEmotionalStorm(),
    "safe_ego": TalentSafeEGO(),
    "controlled_distortion": TalentControlledDistortion(),

# === ВЕТКА 2: ЛУЧШИЙ ИЗ ЛУЧШИХ ===  
    # Новые основные таланты ветки 2
    "natural_genius": TalentNaturalGenius(),
    "celestial_eyes": TalentCelestialEyes(),
    "watch_and_learn": TalentWatchAndLearn(),
    "right_of_the_first": TalentRightOfTheFirst(),
    "black_flash": TalentBlackFlash(),
    "blue_flash": TalentBlueFlash(),
    "role_model": TalentRoleModel(),
    "mockery": TalentMockery(),
    "plot_armor_v2": TalentPlotArmor(),
    "muted": TalentMuted(),
    "just_getting_started": TalentJustGettingStarted(),


# === ВЕТКА 3: НЕУТОМИМЫЙ ===
    "big_guy": TalentBigGuy(),
    "defense": TalentDefense(), # Перезаписали старую версию
    "commendable_constitution": TalentCommendableConstitution(),
    "big_heart": TalentBigHeart(),
    "rock": TalentRock(),
    "despiteAdversities": TalentDespiteAdversities(), # ID должен совпадать с тем, что в unit_mixins
    "heat_resistant": TalentHeatResistant(),
    "adaptation_tireless": TalentAdaptationTireless(),
    "tough_as_steel": TalentToughAsSteel(),
    "defender": TalentDefender(),
    "survivor": TalentSurvivor(),
    "muscle_overstrain": TalentMuscleOverstrain(),
    "idol_oath": TalentIdolOath(),
    "surgeOfStrength": TalentSurgeOfStrength(),

    # === ВЕТКА 4: ПОЛЕВОЙ МЕДИК ===
    "no_hippocratic_oath": TalentNoHippocraticOath(),

    # Хороший Врач
    "good_as_new": TalentGoodAsNew(),
    "remedy_good": TalentRemedyGood(),
    "cheese": TalentCheese(),
    "confete": TalentConfete(),
    "you_wont_die_good": TalentYouWontDieGood(),
    "careful_neutralization": TalentCarefulNeutralization(),
    "doing_good_work": TalentDoingGoodWork(),
    "not_today": TalentNotToday(),
    "mad_good_doctor": TalentMadGoodDoctor(),

    # Плохой Врач
    "toxicology_weapon": TalentToxicologyWeapon(),
    "remedy_bad": TalentRemedyBad(),
    "organ_striking": TalentOrganStriking(),
    "advanced_toxicology": TalentAdvancedToxicology(),
    "you_wont_die_bad": TalentYouWontDieBad(),
    "medical_jargon": TalentMedicalJargon(),
    "christmas_tree": TalentChristmasTree(),
    "insane_zeal": TalentInsaneZeal(),
    "genius_toxicologist": TalentGeniusToxicologist(),

# === ВЕТКА 5: БЕРСЕРК ===
    "naked_defense": TalentNakedDefense(),
    "vengeful_payback": TalentVengefulPayback(),
    "berserker_rage": TalentBerserkerRage(),
    "naked_defense_2": TalentNakedDefense2(),
    "calm_mind": TalentCalmMind(),
    "frenzy": TalentFrenzy(),
    "catch_breath": TalentCatchBreath(),
    "raging_fury": TalentRagingFury(),
    "full_concentration": TalentFullConcentration(),
    "naked_defense_3": TalentNakedDefense3(),
    "descending_into_madness": TalentDescendingIntoMadness(),
    "steady_hand": TalentSteadyHand(),
    "key_moment": TalentKeyMoment(),
    "second_wind_berserk": TalentSecondWindBerserk(),
    "die_hard": TalentDieHard(),

# === ВЕТКА 6: ДЫМОВОЙ ЭКСПЕРТ ===
    "hiding_in_smoke": TalentHidingInSmoke(),
    "smoke_universality": TalentSmokeUniversality(),
    "aerial_foot": TalentAerialFoot(),
    "smoke_screen": TalentSmokeScreen(),
    "recycling": TalentRecycling(),
    "self_preservation": TalentSelfPreservation(),
    "cleansing": TalentCleansing(),
    "experienced_smoker": TalentExperiencedSmoker(),
    "lung_processing": TalentLungProcessing(),
    "to_narnia": TalentToNarnia(),
    "smoke_advantage": TalentSmokeAdvantage(),
    "vulnerability_smoke": TalentVulnerabilitySmoke(),
    "thick_smoke": TalentThickSmoke(),
    "smoke_and_mirrors": TalentSmokeAndMirrors(),

# === ВЕТКА 7: ПОКРОВИТЕЛЬ УДАЧИ ===
    "deal_with_fortune": TalentDealWithFortune(),
    "second_chance": TalentSecondChance(),
    "sequential_luck": TalentSequentialLuck(),
    "lucky_bastard": TalentLuckyBastard(),
    "not_luck_just_skill": TalentJustSkill(),
    "raise_stakes": TalentRaiseStakes(),
    "azino_777": TalentAzino777(),
    "blessed_by_fate": TalentBlessedByFate(),
    "ace_sleeve": TalentAceSleeve(),
    "impossible_possible": TalentImpossiblePossible(),

# === ВЕТКА 8: ВОЕННЫЙ ===
    "athletic": TalentAthletic(), # Обновили класс
    "fast_hands": TalentFastHands(),
    "leader": TalentLeader(),
    "addiction_is_a_bitch": TalentAddiction(),
    "rapid_retreat": TalentRapidRetreat(),
    "combat_reload": TalentCombatReload(),
    "find_vulnerability": TalentFindVulnerability(),
    "borrowed_time": TalentBorrowedTime(),
    "iron_formation": TalentIronFormation(),
    "last_hope": TalentLastHope(),

    # === ВЕТКА 9: СКИТАЛЕЦ ТЕНЕЙ / КРОВОЖАДНЫЙ ===
    "athleticism_shadow": TalentAthleticismShadow(),
    "revenge": TalentRevenge(),
    "not_great_attention": TalentNotGreatAttention(),
    "formidable_person": TalentFormidablePerson(),
    "smashing_blade": TalentSmashingBlade(),
    "slaughter": TalentSlaughter(),
    "trapmaster": TalentTrapmaster(),
    "fast_and_silent": TalentFastAndSilent(),
    "aggressive_parry": TalentAggressiveParry(),
    "step_into_shadow": TalentStepIntoShadow(),
    "taste_of_victory": TalentTasteOfVictory(),
    "sleight_of_hand": TalentSleightOfHand(),
    "cat_reflexes": TalentCatReflexes(),
    "endurance_lessons": TalentEnduranceLessons(),
    "eye_for_danger": TalentEyeForDanger(),
    "cold_blooded": TalentColdBlooded(),
    "identity_thief": TalentIdentityThief(),
    "covering_tracks": TalentCoveringTracks(),
    "competent_adrenaline": TalentCompetentAdrenaline(),
    "knife_in_back": TalentKnifeInBack(),
    "oppression": TalentOppression(),
    "vulnerability_point": TalentVulnerabilityPoint(),
    "extreme_measures": TalentExtremeMeasures(),
    "butcher": TalentButcher(),

# === ВЕТКА 10: ЭНЕРГЕТИЧЕСКИЙ ВОИН ===
    "electrician": TalentElectrician(),
    "pain_points": TalentPainPoints(),
    "mechanical_energy": TalentMechanicalEnergy(),
    "pain_shock": TalentPainShock(),
    "emergency_protection": TalentEmergencyProtection(),
    "static_electricity": TalentStaticElectricity(),
    "entering_rhythm": TalentEnteringRhythm(),
    "dirty_tricks": TalentDirtyTricks(),
    "playing_on_nerves": TalentPlayingOnNerves(),
    "overvoltage": TalentOvervoltage(),
    "em_field": TalentEMField(),
    "with_caution": TalentWithCaution(),
    "sharp_eye": TalentSharpEye(),
    "team_player": TalentTeamPlayer(),
    "arrest": TalentArrest(),
    "battery": TalentBattery(),
    "grounding": TalentGrounding(),
    "feint": TalentFeint(),
    "weak_point_energy": TalentWeakPointEnergy(),
    "rupture_application": TalentRuptureApplication(),
    "rifting_space": TalentRiftingSpace(),
    "capacitor": TalentCapacitor(),
    "achilles_heel": TalentAchillesHeel(),
    "no_mistakes": TalentNoMistakes(),
    "short_circuit": TalentShortCircuit(),
    "pride_of_seven": TalentPrideOfSeven(),

# === ВЕТКА 11: НЕУГАСИМОЕ ПЛАМЯ ===
    "strike_iron_hot": TalentStrikeWhileIronHot(),
    "spark": TalentSpark(),
    "cauterization": TalentCauterization(),
    "hot_talent": TalentHot(),
    "body_adaptation": TalentBodyAdaptation(),
    "hearth_of_power": TalentHearthOfPower(),
    "ashes_to_ashes": TalentAshesToAshes(),
    "hellfire": TalentHellfire(),
    "wildfire": TalentWildfire(),
    "fiery_temper": TalentFieryTemper(),
    "ifrit": TalentIfrit(),
    "phoenix": TalentPhoenix(),
    "firestorm": TalentFirestorm(),
    "burn_me_down": TalentBurnMeDown(),

# === ВЕТКА 12: ТЕХНОЛОГ ===
    "projection": TalentProjection(),
    "hacker": TalentHacker(),
    "little_helper": TalentLittleHelper(),
    "programming_languages": TalentProgrammingLanguages(),
    "portable_shield": TalentPortableShield(),
    "energy_cycle": TalentEnergyCycle(),
    "modulation": TalentModulation(),
    "access_point": TalentAccessPoint(),
    "error_404": TalentError404(),
    "ass_hack": TalentAssHack(),

# === ВЕТКА 13: РОБОТОТЕХНИК ===
    "best_friends_forever": TalentBestFriendsForever(),
    "little_big_trouble": TalentLittleBigTrouble(),
    "cell_expander": TalentCellExpander(),
    "no_first_law": TalentNoFirstLaw(),
    "bright_talent": TalentBrightTalent(),
    "smaller_lighter_faster": TalentSmallerLighterFaster(),
    "frame_upgrade": TalentFrameUpgrade(),
    "made_to_last": TalentMadeToLast(),
    "chimera_core": TalentChimeraCore(),
    "upshot_robot": TalentUpshotRobot(),
    "quantum_hub": TalentQuantumHub(),
    "jack_of_all_trades": TalentJackOfAllTrades(),
    "machina_ex_deo": TalentMachinaExDeo(),
    "exogenesis_protocol": TalentExogenesisProtocol(),
    "multi_connection": TalentMultiConnection(),

# === ВЕТКА 14: ОШЕЛОМЛЯЮЩАЯ ТРЯСКА ===
    "fight_to_the_end": TalentFightToTheEnd(),
    "share_with_friend": TalentShareWithFriend(),
    "carelessness": TalentCarelessness(),
    "pass_the_fare": TalentPassTheFare(),
    "own_tremor": TalentOwnTremor(),
    "readiness_for_everything": TalentReadinessForEverything(),
    "keep_going": TalentKeepGoing(),
    "resonance": TalentResonance(),
    "immobile": TalentImmobile(),
    "tremor_to_bone": TalentTremorToBone(),

# === СВЯЗИ (LINK TALENTS) ===
    "censer": TalentCenser(),
    "ardent_defense": TalentArdentDefense(),
    "hitman_assortment": TalentHitmanAssortment(),
    "thermal_energy": TalentThermalEnergy(),
    "scorching_mastery": TalentScorchingMastery(),
}
