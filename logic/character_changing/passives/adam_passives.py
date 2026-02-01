import random
from logic.character_changing.passives.base_passive import BasePassive
from core.logging import logger, LogLevel
from logic.context import RollContext


# ==========================================
# 1. САНДЕВИСТАН (Скорость + Ловкость + Мощь)
# ==========================================
class AugmentationSandevistan(BasePassive):
    id = "sandevistan"
    name = "Сандевистан (Mk.V)"
    description = (
        "Кибернетический имплант, ускоряющий рефлексы до предела.\n"
        "Пассивно: **+20 Скорости**, **+10 Ловкости**.\n"
        "Эффект: Победа в Столкновении (Clash Win) дает **+1 Strength**."
    )

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        # Теперь баффаем и Скорость, и Ловкость (Agility)
        return {
            "speed": 20,
            "agility": 10
        }

    def on_clash_win(self, ctx, **kwargs):
        # Если выиграл столкновение, баффаем Силу
        unit = ctx.source
        unit.add_status("attack_power_up", 1, duration=3)
        ctx.log.append("⚡ Sandevistan: Strength Boost")


# ==========================================
# 2. БЕЗЖАЛОСТНЫЙ ПРОТОКОЛ (Урон по слабым)
# ==========================================
class PassiveRuthlessProtocol(BasePassive):
    id = "ruthless_protocol"
    name = "Протокол: Ликвидация"
    description = "+50% урона по целям с HP < 50% или в Stagger."

    def on_roll(self, ctx: RollContext, **kwargs):
        target = ctx.target
        if not target: return

        hp_pct = target.current_hp / target.max_hp
        is_low_hp = hp_pct < 0.5
        is_staggered = target.current_stagger <= 0

        if is_low_hp or is_staggered:
            ctx.damage_multiplier += 0.5
            ctx.log.append("💀 Ruthless: +50% DMG")


# ==========================================
# 3. ТИТАНОВАЯ ДЕРМА (Статовая защита)
# ==========================================
class AugmentationTitaniumSkin(BasePassive):
    id = "titanium_skin"
    name = "Титановая Дерма"
    description = (
        "Под кожей находятся пластины из обогащенного титана.\n"
        "Пассивно: **+20 к навыку 'Прочная кожа' (Tough Skin)**.\n"
        "Эффект: Снижает входящий физ. урон на значение `(Tough Skin / 5)`."
    )

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        # Даем прямой бонус к навыку
        return {"tough_skin": 20}

    def modify_incoming_damage(self, unit, amount, damage_type, **kwargs):
        if damage_type in ["slash", "pierce", "blunt"]:
            # Получаем итоговое значение навыка (База + 20 от этой пассивки + другие баффы)
            skin_value = unit.skills.get("tough_skin", 0)

            reduction = skin_value // 5

            reduced_amount = max(0, amount - reduction)

            # Логирование для наглядности (опционально)
            if reduction > 0:
                logger.log(f"🛡️ Titanium Skin: {amount} -> {reduced_amount} (Skin {skin_value})", LogLevel.VERBOSE)

            return reduced_amount
        return amount


# ==========================================
# 4. ФАНТОМНАЯ БОЛЬ (Слабость к SP)
# ==========================================
class WeaknessPhantomPain(BasePassive):
    id = "phantom_pain"
    name = "Сбой: Фантомная Боль"
    description = "Память причиняет боль. x2 входящий урон по Рассудку (SP)."

    def modify_incoming_damage(self, unit, amount, damage_type, **kwargs):
        if damage_type == "sp" or damage_type == "sanity":
            return amount * 2
        return amount


# ==========================================
# 5. СИСТЕМНЫЙ ДИССОНАНС (Паралич)
# ==========================================
class WeaknessSystemDissonance(BasePassive):
    id = "system_dissonance"
    name = "Сбой: Диссонанс"
    description = "При проигрыше столкновения шанс 30% получить Паралич."

    def on_clash_lose(self, ctx, **kwargs):
        if random.random() < 0.30:
            # Паралич на 99 ходов (или пока не снимут) - жестко, как ты хотел в коде
            ctx.source.add_status("paralysis", 2, duration=99)
            ctx.log.append("⚠️ System Error: Paralysis applied!")


from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# 6. БРИТВА ОККАМА (Бонус за пустые слоты)
# ==========================================
class AugmentationOckhamsRazor(BasePassive):
    id = "ockhams_razor"
    name = "Протокол: Бритва Оккама"
    description = (
        "«Не умножай сущности без необходимости».\n"
        "За каждый **пустой** слот скорости (не занятый картой) "
        "текущая карта получает **+3** к Мощи (Power)."
    )

    def on_roll(self, ctx: RollContext, **kwargs):
        unit = ctx.source

        # 1. Проверяем наличие активных слотов (создаются в SpeedRollMixin)
        if not hasattr(unit, 'active_slots') or not unit.active_slots:
            return

        # 2. Считаем пустые слоты
        # В speed.py слот инициализируется как {'card': None, ...}
        # Если карта назначена, там будет объект карты. Если нет — None.
        empty_slots = 0
        for slot in unit.active_slots:
            if slot.get('card') is None:
                empty_slots += 1

        # 3. Применяем бонус
        if empty_slots > 0:
            bonus = empty_slots * 3
            ctx.modify_power(bonus, f"Ockham ({empty_slots} free)")


# ==========================================
# 7. БОЕВОЙ ТРАНС (Накопление критов)
# ==========================================
class AugmentationCombatTrance(BasePassive):
    id = "combat_trance"
    name = "Боевой Транс"
    description = (
        "Нейро-стимуляторы разгоняют восприятие.\n"
        "• Начало раунда: **+5** Самообладания (Self-Control).\n"
        "• При попадании: **+2** Самообладания."
    )

    def on_round_start(self, unit, log_func, **kwargs):
        unit.add_status("self_control", 5, duration=99)
        if log_func:
            log_func(f"🧘 **Транс**: Адам фокусируется (+5 Самообладания)")
        return []

    def on_hit(self, ctx: RollContext, **kwargs):
        ctx.source.add_status("self_control", 2, duration=99)

    # === ДОБАВИТЬ ЭТОТ МЕТОД ===
    def on_round_end(self, unit, *args, **kwargs):
        log_func = kwargs.get("log_func")
        """
        Проверяем, не провалили ли мы ульту в этом броске.
        """

        # Если стоит флаг провала (поставленный скриптом)
        if unit.memory.get("wethermon_failed"):
            # 1. Снимаем флаг, чтобы не убило дважды
            unit.memory["wethermon_failed"] = False

            # 2. Наносим урон и ломаем стаггер
            dmg = int(unit.max_hp * 0.2)  # 20% HP
            unit.take_damage(dmg)
            unit.current_stagger = 0  # Ломаем стаггер в ноль
            unit.add_status("fragile", 5)  # Вешаем хрупкость

            # Лог
            log_func.append(f"💀 **POST-MORTEM**: Stagger Broken! -{dmg} HP")
            if hasattr(unit, "log_battle_message"):
                unit.log_battle_message("💀 **УЯЗВИМОСТЬ!** (Stagger Broken)")


class WeaponMuramasaPassive(BasePassive):
    id = "weapon_muramasa"
    name = "Эффект: Мурамаса"
    description = (
        "1. **Кровавая плата**: Атака стоит 5% HP. Крит наносит x2.0 урона.\n"
        "2. **ВЧ-Лезвие**: Пробивает защиту (+0.3 к эфф. резиста если он <0.5, иначе +0.5).\n"
        "3. **Зандатсу**: При убийстве или Stagger'е восстанавливает 20% от вашего Макс. HP."
    )

    def on_roll(self, ctx, **kwargs):
        """
        Плата за силу перед броском.
        """
        unit = ctx.source

        # Самоурон 5% от Макс HP
        pay_hp = int(unit.max_hp * 0.05)
        if pay_hp > 0:
            unit.heal_hp(-pay_hp)
            # Лог можно закомментировать, если спамит
            # ctx.log.append(f"🩸 Плата: -{pay_hp} HP")

    def on_hit(self, ctx, stack=None, *args, **kwargs):
        """
        Main mechanics: Penetration, Crit Boost, Zandatsu.
        """
        unit = ctx.source
        target = ctx.target
        if not target: return

        # === 1. HF-Blade (Resistance Modification) ===

        # 1. Определяем тип урона (String)
        raw_type = ctx.dice.dtype
        if hasattr(raw_type, "value"):
            dmg_type = str(raw_type.value).lower()
        else:
            dmg_type = str(raw_type).lower()

        # 2. Получаем текущий резист цели
        current_res = 1.0
        if hasattr(target, "hp_resists"):
            # Безопасно берем атрибут (slash/pierce/blunt)
            current_res = getattr(target.hp_resists, dmg_type, 1.0)
        elif hasattr(target, "resistances"):
            current_res = target.resistances.get(dmg_type, 1.0)

        # 3. Логика пробития
        # Если резист < 0.5 (Ineffective/Fatal), добавляем +0.3
        # Если резист >= 0.5 (Normal/Endured), добавляем +0.5
        bonus_res = 0.3 if current_res < 0.5 else 0.5

        # 4. Применяем и ЛОГИРУЕМ
        if current_res > 0.01:
            # Считаем, сколько должно получиться
            effective_res = current_res + bonus_res

            # Считаем множитель, чтобы достичь этого значения
            # (Math trick: Урон * (НовыйРез / СтарыйРез) = Урон по НовомуРезу)
            res_factor = effective_res / current_res
            ctx.damage_multiplier *= res_factor

            # [ВАЖНО] Добавляем красивый лог
            ctx.log.append(f"🛡️ **ВЧ-Лезвие**: Пробив [Res {current_res:.1f} + {bonus_res} -> {effective_res:.1f}]")

        # === 2. Crit Boost (x2 -> x3.0) ===
        if ctx.is_critical:
            ctx.damage_multiplier *= 1.333
            ctx.log.append("⚡ **ВЧ-Крит**: x3.0")

        # === 3. Zandatsu (Heal on Kill/Stagger) ===
        is_dead = target.current_hp <= 0
        is_staggered = target.current_stagger <= 0

        if is_dead or is_staggered:
            max_stagger = getattr(unit, "max_stagger", 100)
            heal_val = int(max_stagger * 0.10)

            if heal_val > 0:
                unit.heal_hp(heal_val)
                ctx.log.append(f"🔋 **Zandatsu**: +{heal_val} HP")


class ArmorGhostExoPassive(BasePassive):
    id = "armor_ghost_exo"
    name = "Экзоскелет: Призрак"
    description = (
        "1. **Камуфляж**: -20% урона, если ваша Скорость >= Скорости атакующего.\n"
        "2. **Нано-ремонт**: +5% HP и +10 Stagger в начале хода.\n"
        "3. **Перегрузка**: Первое ошеломление отменяется и восстанавливает 50 Stagger."
    )

    def modify_incoming_damage(self, unit, amount, damage_type, attacker_ctx=None, **kwargs):
        """
        1. Оптический Камуфляж
        """
        if attacker_ctx and attacker_ctx.source:
            attacker = attacker_ctx.source

            # Пытаемся получить текущие значения скорости (роллы), если нет — берем статы
            my_speed = getattr(unit, "speed_roll", 0) or unit.attributes.get("speed", 0)
            enemy_speed = getattr(attacker, "speed_roll", 0) or attacker.attributes.get("speed", 0)

            # Если мы быстрее или равны -> активируем камуфляж
            if my_speed >= enemy_speed:
                reduced = int(amount * 0.8)  # Снижаем на 20%
                # Лог для наглядности (опционально)
                # if reduced < amount:
                #     pass
                return reduced

        return amount

    def on_round_start(self, unit, log_func, **kwargs):
        """
        2. Нано-ремонт
        """
        max_hp = unit.max_hp
        # Безопасное получение макс. стаггера
        max_stagger = getattr(unit, "max_stagger", 100)

        heal_hp = int(max_hp * 0.05)
        heal_stagger = int(max_stagger * 0.10)

        if heal_hp > 0: unit.heal_hp(heal_hp)
        if heal_stagger > 0: unit.restore_stagger(heal_stagger)

        if log_func:
            log_func(f"⚙️ **Нано-ремонт**: +{heal_hp} HP, +{heal_stagger} Stagger")
        return []

    def modify_incoming_stagger_damage(self, unit, amount, **kwargs):
        """
        3. Перегрузка (Защита от стаггера 1 раз за бой)
        """
        current_stagger = unit.current_stagger

        # Если урон опустит стаггер до 0 или ниже
        if current_stagger - amount <= 0:
            # Проверяем память: срабатывала ли уже перегрузка?
            if not unit.memory.get("ghost_overdrive_triggered"):
                unit.memory["ghost_overdrive_triggered"] = True

                # Спасаем: Устанавливаем стаггер на 50
                unit.current_stagger = 50

                # Лог
                if hasattr(unit, "log_battle_message"):
                    unit.log_battle_message("⚡ **ПЕРЕГРУЗКА РЕАКТОРА!** (Stagger Prevented)")

                return 0

        return amount