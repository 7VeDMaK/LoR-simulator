# logic/character_changing/passives/equipment_passives.py
from core.enums import DiceType
from core.logging import logger, LogLevel  # [NEW] Import
from logic.character_changing.passives.base_passive import BasePassive
from logic.context import RollContext


# === АННИГИЛЯТОРНАЯ ПУШКА ===
class PassiveAnnihilator(BasePassive):
    id = "mech_annihilator"
    name = "Мех: Аннигилятор"
    description = "Дает +100 к атаке на 1 удар. После использования отключается до конца боя."

    def on_combat_start(self, unit, log_func, **kwargs):
        if not unit.memory.get("annihilator_ammo_gift"):
            unit.memory["annihilator_ammo"] = 1
            unit.memory["annihilator_ammo_gift"] = True

        if log_func: log_func("🐭 **Аннигилятор**: Заводная мышь готова (1 патрон).")

    def on_roll(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        # Проверяем, что это атака
        if ctx.dice.dtype not in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            return

        ammo = ctx.source.memory.get("annihilator_ammo", 0)

        if ammo > 0:
            ctx.modify_power(100, "Annihilator")
            ctx.source.memory["annihilator_ammo"] = 0
            ctx.log.append("💥 **BOOM**: Патрон истрачен!")
            logger.log(f"💥 Annihilator used by {ctx.source.name} (+100 Pwr)", LogLevel.NORMAL, "Passive")
        else:
            ctx.log.append("🔇 **Click**: Пусто...")
            # logger.log(f"🔇 Annihilator click (empty) for {ctx.source.name}", LogLevel.VERBOSE, "Passive")


# === БАНГАНРАНГ ===
class PassiveBanganrang(BasePassive):
    id = "mech_banganrang"
    name = "Мех: Банганранг"
    description = "+5 к роллам. Весь наносимый красный урон (HP) становится белым (SP)."

    def on_hit(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        # Ставим флаг конвертации урона в контекст броска
        # Логика обработки будет в damage.py
        ctx.convert_hp_to_sp = True
        ctx.log.append("🎵 **Банганранг**: Тип урона изменен на Белый (SP).")
        logger.log(f"🎵 Banganrang: Converted HP dmg to SP dmg for {ctx.source.name}", LogLevel.VERBOSE, "Passive")


# === ОБНОВЛЕННЫЙ ГАНИТАР ===
class PassiveGanitar(BasePassive):
    id = "mech_ganitar"
    name = "Мех: Дуэльный Ганитар [WIP]"
    description = "Активно (1 раз в бой): Отключает пассивные способности ВСЕХ врагов."
    is_active_ability = True
    cooldown = 99

    def on_combat_start(self, unit, log_func, **kwargs):
        enemies = kwargs.get("enemies", [])
        if not enemies:
            op = kwargs.get("opponent")
            if op: enemies = [op]

        # Сохраняем ИМЕНА
        unit.memory['cached_enemies_names'] = [e.name for e in enemies]

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        enemy_names = unit.memory.get('cached_enemies_names', [])
        if not enemy_names:
            if log_func: log_func("❌ Ганитар: Цели не найдены в памяти.")
            return False

        import streamlit as st
        all_units = st.session_state.get('team_left', []) + st.session_state.get('team_right', [])

        count = 0
        names = []
        for u in all_units:
            if u.name in enemy_names and not u.is_dead():
                u.add_status("passive_lock", 1, duration=99)
                count += 1
                names.append(u.name)

        unit.cooldowns[self.id] = self.cooldown

        if log_func:
            log_func(f"📿 **Ганитар**: Активирован! Пассивки отключены у {count} врагов.")

        from core.logging import logger, LogLevel
        logger.log(f"📿 Ganitar activated by {unit.name}. Targets: {', '.join(names)}", LogLevel.NORMAL, "Passive")
        return True


# === ЛИМАГАН ===
class PassiveLimagun(BasePassive):
    id = "mech_limagun"
    name = "Мех: ЛИМАГАН"
    description = "+666% урона по целям с именем 'Лима'."

    def on_hit(self, ctx, **kwargs):
        if not ctx.target: return

        name = ctx.target.name.lower()
        if "лима" in name or "lima" in name:
            ctx.damage_multiplier += 6.66
            ctx.log.append("🚪 **ЛИМАГАН**: x6.66 Урона по Лиме!")
            logger.log(f"🚪 Limagun triggered: {ctx.source.name} vs {ctx.target.name}", LogLevel.NORMAL, "Passive")


# === ФАНТОМНЫЕ БРИТВЫ ===
class PassivePhantomRazors(BasePassive):
    id = "mech_phantom_razors"
    name = "Мех: Нейротоксин"
    description = (
        "Пассивно: При попадании накладывает 1 Паралич (3 хода).\n"
        "Активно (КД 3): Следующий удар считается Внезапным (получение Невидимости)."
    )
    is_active_ability = True
    cooldown = 3

    def on_hit(self, ctx, **kwargs):
        # Накладываем паралич при попадании любой атакой
        if ctx.target and ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            # Паралич: 1 стак, длительность 3 раунда
            ctx.target.add_status("paralysis", 1, duration=3)
            ctx.log.append("🧪 **Нейротоксин**: Паралич наложен (3 хода).")
            # Логгер для системы
            if hasattr(logger, 'log'):
                logger.log(f"🧪 Neurotoxin applied to {ctx.target.name}", LogLevel.VERBOSE, "Passive")

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0:
            return False

        # Даем невидимость. В системе (branch_9_shadow.py) Невидимость = Внезапная атака.
        unit.add_status("invisibility", 1, duration=1)

        unit.cooldowns[self.id] = self.cooldown

        if log_func:
            log_func(f"👻 **Фантомный удар**: Активирована маскировка! Следующая атака будет Внезапной.")

        if hasattr(logger, 'log'):
            logger.log(f"👻 Phantom Razors activated by {unit.name}", LogLevel.NORMAL, "Passive")

        return True


class PassiveCoagulation(BasePassive):
    id = "coagulation"
    name = "Свертываемость"
    description = "Каждый ход накладывает Сопротивление к кровотечению (урон от Bleed -33%)."

    def on_round_start(self, unit, log_func, **kwargs):
        # Накладываем статус на 1 ход (обновляется каждый раунд)
        unit.add_status("bleed_resist", 1, duration=1)

        if log_func:
            log_func(f"🩸 **{self.name}**: Кровь густеет (Resistance applied).")

        if hasattr(logger, 'log'):
            logger.log(f"🩸 Coagulation: Added bleed_resist to {unit.name}", LogLevel.VERBOSE, "Passive")


class PassiveMagneticPickaxe(BasePassive):
    id = "mech_magnetic_pickaxe"
    name = "Магнитный разряд"
    description = (
        "Пассивно: Удары накладывают 1 'Анти-Заряд' (если не на КД).\n"
        "Активно (КД 5): Заряжает ледорубы. Следующий удар нанесет x1.5 урона и 2 'Анти-Заряда'."
    )
    is_active_ability = True
    cooldown = 5

    def on_hit(self, ctx, **kwargs):
        unit = ctx.source
        target = ctx.target
        if not target: return

        # Проверяем, был ли активирован заряд (через статус)
        has_charge = unit.get_status("magnetic_charge") > 0

        # Если заряд есть (Активка была нажата)
        if has_charge:
            # 1. Усиленный эффект
            target.add_status("anti_charge", 2, 99)
            ctx.damage_multiplier *= 1.5

            ctx.log.append("⚡ **Магнитный Разряд**: x1.5 Урона + 2 Анти-Заряда!")
            if hasattr(logger, 'log'):
                logger.log(f"⚡ Magnetic Burst on {target.name}", LogLevel.NORMAL, "Passive")

    def activate(self, unit, *args, **kwargs):
        log_func = kwargs.get("log_func")
        # Проверка КД
        if unit.cooldowns.get(self.id, 0) > 0:
            return False

        # Накладываем статус "Заряд", который усилит следующий on_hit
        unit.add_status("magnetic_charge", 1, duration=1)  # Duration 2 чтобы точно хватило на удар

        # Ставим КД
        unit.cooldowns[self.id] = self.cooldown

        if log_func:
            log_func(f"🧲 **Магнит**: Ледорубы заряжены! Следующий удар будет сокрушительным.")

        if hasattr(logger, 'log'):
            logger.log(f"🧲 Magnetic Pickaxe activated by {unit.name}", LogLevel.NORMAL, "Passive")

        return True


# logic/character_changing/passives/dragon_slab.py
from logic.character_changing.passives.base_passive import BasePassive
from logic.context import RollContext
from core.enums import DiceType
from core.logging import logger, LogLevel


class PassiveDragonSlab(BasePassive):
    def __init__(self):
        super().__init__()
        self.id = "mech_dragon_slab"
        self.name = "Глыба Железа"
        self.description = (
            "«Глыба железа». Легендарный меч, чья тяжесть сопоставима с его мощью.\n\n"
            "• [Тяжесть]: Каждая атака (куб) требует 20 Силы (либо 20 Стойкости). Если сил не хватает — взмах проваливается.\n"
            "• [Адаптация]: Перед ударом выбирает наиболее эффективный тип урона (Рубящий или Дробящий).\n"
            "• [Берсерк]: Дает до +8 к результату броска и до +50% к конечному урону в зависимости от потерянного здоровья."
        )
        self.swings_this_round = 0

    def on_round_start(self, unit, *args, **kwargs):
        """Сбрасываем счетчик ударов в начале раунда."""
        self.swings_this_round = 0

    def on_roll(self, ctx: RollContext, stack: int = 0):
        """
        Механика Тяжести и Берсерка.
        Вызывается из RollContext.roll() -> _trigger_on_roll.
        """
        unit = ctx.source
        dice = ctx.dice

        if not dice:
            return

        # 1. Проверяем, является ли кубик атакующим
        is_attack = dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]

        if is_attack:
            # Получаем Силу (ищем в атрибутах или статах)
            strength = unit.attributes.get("strength", 0)
            endurance = unit.attributes.get("endurance", 0)

            # Лимит ударов: 20 силы = 1 удар, 40 = 2 удара и т.д.
            allowed_swings = (strength + endurance) // 20

            if self.swings_this_round < allowed_swings:
                # --- УСПЕШНЫЙ ЗАМАХ ---
                self.swings_this_round += 1

                # Расчет бонуса Берсерка
                hp_ratio = unit.current_hp / max(1, unit.max_hp)
                missing_hp_percent = 1.0 - hp_ratio

                # Баффы: База +3 Мощи (легендарка) + до +5 от Берсерка
                berserk_power = int(missing_hp_percent * 5)
                total_bonus = 3 + berserk_power

                ctx.modify_power(total_bonus, "Dragon Slab (Power)")

                # Увеличение множителя урона в контексте (до +50%)
                ctx.damage_multiplier += (missing_hp_percent * 0.5)

                logger.log(f"⚔️ {unit.name} взмахнул Глыбой (Удар {self.swings_this_round}/{allowed_swings} + {ctx.damage_multiplier*100}%)",
                           LogLevel.NORMAL, "Passive")
            else:
                # --- ТЯЖЕСТЬ МЕЧА (Сил не хватило) ---
                # Штраф -9999 гарантирует 0 в итоговом броске (как в calculate_power)
                ctx.modify_power(-9999, "Too Heavy 🚫")
                logger.log(f"🚫 {unit.name} не хватает силы для еще одного удара!", LogLevel.NORMAL, "Passive")

    def on_hit(self, ctx: RollContext, **kwargs):
        """
        Механика Адаптации:
        Смена типа урона на более выгодный перед расчетом урона.
        """
        target = ctx.target
        if not target or not ctx.dice:
            return

        # Получаем значения сопротивлений цели
        # (Предполагаем наличие метода get_resist_value или доступ к словарю)
        res_slash = target.hp_resists.slash
        res_blunt = target.hp_resists.blunt

        # Выбираем лучший тип (где множитель урона выше)
        if ctx.dice.dtype == DiceType.SLASH and res_blunt > res_slash:
            ctx.dice.dtype = DiceType.BLUNT
            ctx.log.append("Adaptation: Slashed -> Blunt")
        elif ctx.dice.dtype == DiceType.BLUNT and res_slash > res_blunt:
            ctx.dice.dtype = DiceType.SLASH
            ctx.log.append("Adaptation: Blunt -> Slash")