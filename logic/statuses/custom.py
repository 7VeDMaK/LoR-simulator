import random

from core.enums import DiceType
from core.logging import logger, LogLevel
from logic.context import RollContext
from logic.statuses.common import StatusEffect


class SelfControlStatus(StatusEffect):
    id = "self_control"

    def on_hit(self, ctx: RollContext, stack: int):
        chance = min(100, stack * 5)
        roll = random.randint(1, 100)
        if roll <= chance:
            ctx.damage_multiplier *= 2.0
            ctx.is_critical = True
            ctx.log.append(f"💨 CRIT! ({chance}%) x2 DMG")
            logger.log(f"💨 SelfControl Crit: {ctx.source.name} (Chance {chance}%) -> x2 Dmg", LogLevel.VERBOSE,
                       "Status")
            ctx.source.remove_status("self_control", 20)

    def on_round_end(self, unit, log_func, **kwargs):
        unit.remove_status("self_control", 20)
        return [f"💨 Self-Control decayed"]


class SmokeStatus(StatusEffect):
    id = "smoke"
    name = "Дым"

    def _get_limit(self, unit):
        # Базовый лимит 10, может быть увеличен талантами (например, Lung Processing)
        base_limit = 10

        # Проверяем талант 6.7 Lung Processing (Легкая броня)
        if "lung_processing" in getattr(unit, "talents", []):
            base_limit = 20

        bonus = unit.memory.get("smoke_limit_bonus", 0)
        return base_limit + bonus

    def on_roll(self, ctx: RollContext, **kwargs):
        stack = kwargs.get('stack', 0)
        # Если стаков >= 9, +1 к силе (базовая механика)
        if stack >= 9:
            ctx.modify_power(1, "Smoke (9+)")

    def modify_incoming_damage(self, unit, amount, damage_type, stack=0, **kwargs):
        """
        Влияние дыма на входящий урон.
        По умолчанию: +5% урона за стак (до 10).
        С талантом 6.1 (Hiding in Smoke): -3% урона за стак.
        С талантом 6.7 (Lung Processing): -50% если стаков >= 15.
        """
        if damage_type != "hp": return amount

        eff_stack = min(10, stack)  # Базовый кап эффекта

        # Талант 6.7 (Тяжелая артиллерия)
        if "lung_processing" in getattr(unit, "talents", []) and stack >= 15:
            # Снижение урона на 50%
            logger.log(f"🚬 Lung Processing: 50% dmg reduction for {unit.name}", LogLevel.VERBOSE, "Status")
            return int(amount * 0.5)

        # Талант 6.1 (Дым как защита)
        if unit.memory.get("smoke_is_defensive"):
            # Снижаем урон на 3% за стак (макс 30%)
            multiplier = 1.0 - (eff_stack * 0.03)
            return int(amount * multiplier)
        else:
            # Увеличиваем урон на 5% за стак (макс 50%)
            multiplier = 1.0 + (eff_stack * 0.05)
            return int(amount * multiplier)

    def on_round_end(self, unit, log_func, **kwargs):
        msgs = []
        log_func = kwargs.get('log_func')

        # 1. Естественное рассеивание (-1)
        # Это НЕ считается тратой для талантов типа "Очищение", поэтому не вызываем триггер
        current = unit.get_status("smoke")
        if current > 0:
            unit.remove_status("smoke", 1)
            msgs.append("💨 Smoke decayed (-1)")

        # 2. Проверка лимита
        current = unit.get_status("smoke")  # Обновляем после списания
        limit = self._get_limit(unit)

        if current > limit:
            loss = current - limit
            unit.remove_status("smoke", loss)
            msgs.append(f"💨 Smoke cap ({limit}) exceeded. Removed {loss}.")
            logger.log(f"💨 Smoke cap exceeded for {unit.name}: -{loss}", LogLevel.VERBOSE, "Status")

        return msgs

    def trigger_spend_mechanics(self, unit, amount, log_func=None):
        """
        [NEW] Вызывать этот метод при АКТИВНОЙ трате дыма.
        Запускает таланты (Очищение, Переработка и т.д.).
        """
        # Импортируем реестр талантов внутри метода, чтобы избежать циклов
        from logic.character_changing.talents import TALENT_REGISTRY

        if hasattr(unit, "talents"):
            for tid in unit.talents:
                talent = TALENT_REGISTRY.get(tid)
                if talent and hasattr(talent, "on_smoke_spent"):
                    talent.on_smoke_spent(unit, amount, log_func)


class RedLycorisStatus(StatusEffect):
    id = "red_lycoris"
    name = "Красный Ликорис" # Добавил имя для красивого лога
    prevents_stagger = True
    prevents_death = True

    def modify_active_slot(self, unit, slot):
        slot['prevent_redirection'] = True
        if not slot.get('source_effect'):
            slot['source_effect'] = "Lycoris 🩸"

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        return {"initiative": 999, "damage_take": 9999}

    def on_round_end(self, unit, log_func, **kwargs):
        return []

    # [NEW] Реализация иммунитета
    def prevents_damage(self, unit, attacker_ctx) -> bool:
        return True

class BlueHyacinthStatus(StatusEffect):
    id = "blue_hyacinth"
    name = "Синий Гиацинт" # Добавил имя для красивого лога
    prevents_stagger = True
    prevents_death = True

class SinisterAuraStatus(StatusEffect):
    id = "sinister_aura"

    def on_roll(self, ctx: RollContext, stack: int):
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            target = ctx.target
            if target:
                dmg_val = max(0, target.current_sp) // 10
                if dmg_val > 0:
                    ctx.source.take_sanity_damage(dmg_val)
                    ctx.log.append(f"🌑 Аура: -{dmg_val} SP (от величия {target.name})")
                    # [CHANGE] VERBOSE -> MINIMAL
                    logger.log(f"🌑 Sinister Aura: {ctx.source.name} took {dmg_val} SP dmg", LogLevel.MINIMAL, "Status")


class AdaptationStatus(StatusEffect):
    id = "adaptation"
    name = "Адаптация"
    description = ("Адаптация - накапливаемое до четырёх уровней состояние...")

    # [NEW] Реализация логики защиты (пункт 4.3 из старого кода)
    def modify_resistance(self, unit, res: float, damage_type: str, dice=None, stack=0, log_list=None) -> float:
        # Проверяем, к какому типу мы адаптировались
        active_type = unit.memory.get("adaptation_active_type")

        # Если тип кубика совпадает с адаптацией -> Снижаем получаемый урон (резист * 0.75)
        if active_type and dice and dice.dtype == active_type:
            new_res = res * 0.75
            if log_list is not None:
                log_list.append(f"🧬 **Adaptation**: -25% Dmg vs {active_type.name}")
            return new_res

        return res


class BulletTimeStatus(StatusEffect):
    id = "bullet_time"

    def on_roll(self, ctx: RollContext, stack: int):
        if ctx.dice.dtype == DiceType.EVADE:
            ctx.final_value = ctx.dice.max_val
            ctx.log.append(f"🕰️ **BULLET TIME**: Идеальное уклонение ({ctx.dice.max_val})")
            logger.log(f"🕰️ Bullet Time: {ctx.source.name} Evade Max ({ctx.dice.max_val})", LogLevel.VERBOSE, "Status")
        elif ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.final_value = 0
            ctx.damage_multiplier = 0.0
            ctx.log.append("🕰️ **BULLET TIME**: Атака отменена (0)")
            logger.log(f"🕰️ Bullet Time: {ctx.source.name} Attack Nullified", LogLevel.VERBOSE, "Status")


class ClarityStatus(StatusEffect):
    id = "clarity"

    def on_round_end(self, unit, log_func, **kwargs):
        return []


class EnrageTrackerStatus(StatusEffect):
    id = "enrage_tracker"

    def on_take_damage(self, unit, amount, source, **kwargs):
        log_func = kwargs.get("log_func")
        if amount > 0:
            unit.add_status("attack_power_up", amount, duration=2)
            if log_func:
                log_func(f"😡 **Разозлить**: Получено {amount} урона -> +{amount} Силы!")
            logger.log(f"😡 Enrage: {unit.name} gain +{amount} Strength from damage", LogLevel.VERBOSE, "Status")

    def on_round_end(self, unit, log_func, **kwargs):
        return []


class InvisibilityStatus(StatusEffect):
    id = "invisibility"

    def on_hit(self, ctx: RollContext, **kwargs):
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.source.remove_status("invisibility", 999)
            ctx.log.append("👻 **Невидимость**: Раскрыт после удара!")
            logger.log(f"👻 Invisibility broken (Attack) for {ctx.source.name}", LogLevel.NORMAL, "Status")

    def on_clash_lose(self, ctx: RollContext, **kwargs):
        if ctx.dice.dtype in [DiceType.SLASH, DiceType.PIERCE, DiceType.BLUNT]:
            ctx.source.remove_status("invisibility", 999)
            ctx.log.append("👻 **Невидимость**: Раскрыт (перехвачен)!")
            logger.log(f"👻 Invisibility broken (Clash Lose) for {ctx.source.name}", LogLevel.NORMAL, "Status")

    def on_round_end(self, unit, log_func, **kwargs):
        return ["👻 Невидимость рассеялась."]


class SatietyStatus(StatusEffect):
    id = "satiety"

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        stack = kwargs.get("stack")
        if stack is None:
            stack = 0
        if unit.get_status("ignore_satiety") > 0: return {}
        penalties = {}
        if stack >= 15:
            penalties = {"initiative": -3}
        if hasattr(unit, "apply_mechanics_filter"):
            penalties = unit.apply_mechanics_filter("modify_satiety_penalties", penalties)
        return penalties

    def on_round_end(self, unit, log_func, **kwargs):
        stack = kwargs.get("stack")
        msgs = []
        threshold = 20
        if "food_lover" in unit.passives: threshold = 27

        if stack > threshold:
            excess = stack - threshold
            damage = excess * 10
            unit.current_hp = max(0, unit.current_hp - damage)
            msgs.append(f"**Переедание**: {excess} лишних стаков -> -{damage} HP!")
            # [CHANGE] NORMAL -> MINIMAL
            logger.log(f"🍗 Satiety Overload: {unit.name} took {damage} HP damage", LogLevel.MINIMAL, "Status")

        unit.remove_status("satiety", 1)
        msgs.append("🍗 Сытость немного спала (-1)")
        return msgs


class ArrestedStatus(StatusEffect):
    id = "arrested"

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        """-20 ко всем основным атрибутам (strength, endurance, agility, wisdom, psych)."""
        return {
            "strength": -20,
            "endurance": -20,
            "agility": -20,
            "wisdom": -20,
            "psych": -20,
            "strike_power": -20,
            "medicine": -20,
            "willpower": -20,
            "luck": -20,
            "acrobatics": -20,
            "shields": -20,
            "tough_skin": -20,
            "speed": -20,
            "light_weapon": -20,
            "medium_weapon": -20,
            "heavy_weapon": -20,
            "firearms": -20,
            "eloquence": -20,
            "forging": -20,
            "engineering": -20,
            "programming": -20
        }

    def on_round_end(self, unit, log_func, **kwargs):
        # Статус длительный (99); не добавляем авто-логи здесь, чтобы не засорять.
        return []


# ==========================================
# Уменьшение резистов (для Ахиллесовой пяты)
# ==========================================
class SlashResistDownStatus(StatusEffect):
    id = "slash_resist_down"

    def modify_resistance(self, unit, res_value, damage_type=None, stack=0, **kwargs):
        if damage_type == "slash":
            if stack == 0:
                stack = unit.get_status(self.id)
            return res_value + 0.25 * stack
        return res_value


class PierceResistDownStatus(StatusEffect):
    id = "pierce_resist_down"

    def modify_resistance(self, unit, res_value, damage_type=None, stack=0, **kwargs):
        if damage_type == "pierce":
            if stack == 0:
                stack = unit.get_status(self.id)
            return res_value + 0.25 * stack
        return res_value


class BluntResistDownStatus(StatusEffect):
    id = "blunt_resist_down"

    def modify_resistance(self, unit, res_value, damage_type=None, stack=0, **kwargs):
        if damage_type == "blunt":
            if stack == 0:
                stack = unit.get_status(self.id)
            return res_value + 0.25 * stack
        return res_value




# === СТАТУСЫ КОНФЕТ ===
class IgnoreSatietyStatus(StatusEffect):
    id = "ignore_satiety"
    pass


class BleedResistStatus(StatusEffect):
    id = "bleed_resist"
    pass


class RegenGanacheStatus(StatusEffect):
    id = "regen_ganache"

    def on_round_start(self, unit, log_func, **kwargs):
        heal = int(unit.max_hp * 0.05)
        if heal > 0:
            unit.heal_hp(heal)
            if log_func: log_func(f"🍫 **Ганаш**: Регенерация +{heal} HP")
            logger.log(f"🍫 Ganache Regen: {unit.name} +{heal} HP", LogLevel.VERBOSE, "Status")

    def on_round_end(self, unit, log_func, **kwargs):
        return []


class RevengeDmgUpStatus(StatusEffect):
    id = "revenge_dmg_up"

    def on_hit(self, ctx: RollContext, stack: int):
        ctx.damage_multiplier *= 1.5
        ctx.log.append(f"🩸 **Месть**: Урон x1.5!")
        logger.log(f"🩸 Revenge Triggered: {ctx.source.name} Damage x1.5", LogLevel.VERBOSE, "Status")
        ctx.source.remove_status("revenge_dmg_up", 999)

    def on_round_end(self, unit, log_func, **kwargs):
        return []


class TauntStatus(StatusEffect):
    id = "taunt"


class FanatMarkStatus(StatusEffect):
    id = "fanat_mark"
    name = "Метка Фаната"
    description = "Цель получает +20 входящего урона от кубиков Фаната (через пассивку)."


class MentalProtectionStatus(StatusEffect):
    id = "mental_protection"
    name = "Ментальная защита"

    def modify_incoming_damage(self, unit, amount, damage_type, stack=0, log_list=None, **kwargs):
        # Работаем только если тип урона 'sp' (конвертированный)
        if damage_type == "sp":
            if stack == 0: stack = unit.get_status(self.id)

            if stack > 0:
                # 25% за стак, макс 50%
                pct_red = min(0.50, stack * 0.25)
                reduction = int(amount * pct_red)

                if reduction > 0:
                    if log_list is not None:
                        log_list.append(f"🧀 **Edam**: Blocked {reduction} SP dmg")

                    return amount - reduction
        return amount


class MainCharacterShellStatus(StatusEffect):
    """
    Статус для таланта 2.8 'Сюжетная броня'.
    Предотвращает смерть: HP и Stagger не могут опуститься ниже 1.
    Срабатывает один раз, после чего статус удаляется.
    """
    id = "main_character_shell"
    name = "Сюжетная броня"
    description = "HP и Stagger не могут опуститься ниже 1 (одноразово)"
    
    def modify_incoming_damage(self, unit, amount, damage_type, **kwargs):
        """Предотвращаем падение HP и Stagger ниже 1."""
        # Защита HP
        if damage_type == "hp" and unit.current_hp - amount <= 0:
            limited_damage = max(0, unit.current_hp - 1)
            logger.log(
                f"🛡️ Main Character Shell: {unit.name} HP protected! "
                f"Damage {amount} → {limited_damage}",
                LogLevel.NORMAL,
                "Status"
            )
            # Помечаем для удаления после срабатывания
            unit.memory["main_character_shell_triggered"] = True
            return limited_damage
        
        # Защита Stagger
        if damage_type == "stagger" and unit.current_stagger - amount <= 0:
            limited_damage = max(0, unit.current_stagger - 1)
            logger.log(
                f"🛡️ Main Character Shell: {unit.name} Stagger protected! "
                f"Damage {amount} → {limited_damage}",
                LogLevel.NORMAL,
                "Status"
            )
            # Помечаем для удаления после срабатывания
            unit.memory["main_character_shell_triggered"] = True
            return limited_damage
        
        return amount
    
    def on_round_end(self, unit, *args, **kwargs):
        """Удаляем статус после срабатывания."""
        if unit.memory.get("main_character_shell_triggered", False):
            unit.remove_status(self.id, 999)  # Удаляем полностью
            unit.memory["main_character_shell_triggered"] = False
            logger.log(
                f"🛡️ Main Character Shell: {unit.name} protection consumed and removed",
                LogLevel.NORMAL,
                "Status"
            )


# logic/statuses/custom.py

class AzinoJackpotStatus(StatusEffect):
    id = "azino_jackpot"
    name = "ДЖЕКПОТ (Бессмертие)"
    description = "Вы сорвали куш! HP не падает ниже 1. Иммунитет к эффектам. Все броски максимальны."

    # === МЕХАНИКА БЕССМЕРТИЯ (Хакари) ===
    prevents_death = True
    prevents_stagger = True

    def prevents_damage(self, unit, attacker_ctx) -> bool:
        """Полный иммунитет к урону."""
        return True

    def on_roll(self, ctx: RollContext, stack: int):
        """Музыка играет громче! Все броски максимальны."""
        # Устанавливаем значение кубика на максимум
        ctx.final_value = ctx.dice.max_val
        ctx.is_critical = True  # Всегда крит
        # Добавляем пафосное сообщение
        if "jackpot_msg" not in ctx.source.memory:
            ctx.log.append("🎶 **JACKPOT**: Бессмертие и Бесконечная Удача!")
            ctx.source.memory["jackpot_msg"] = True

    def on_status_applied(self, unit, status_id, amount, duration=1, **kwargs):
        if status_id != self.id:
            return
        if unit.memory.get("azino_jackpot_link_opened"):
            return

        unit.memory["azino_jackpot_link_opened"] = True
        url = "https://youtu.be/34Pl2DTuwoQ?si=0ojgA65awwY4dMEB"
        try:
            import streamlit as st
            st.session_state["azino_jackpot_url"] = url
        except Exception:
            pass

        logger.log(
            f"🎶 Azino Jackpot: opened link for {unit.name}",
            LogLevel.NORMAL,
            "Status"
        )

    def on_round_end(self, unit, log_func, **kwargs):
        unit.memory.pop("jackpot_msg", None)
        return ["🎶 Музыка продолжает играть..."]


class AzinoBeastStatus(StatusEffect):
    id = "azino_beast"
    name = "Число Зверя (666)"
    description = "Сила Преисподней. Урон x1.66, но вы получаете 6 урона за каждую атаку."

    def on_calculate_stats(self, unit, stack=0) -> dict:
        # +6 ко всем статам
        return {
            "strength": 6,
            "endurance": 6,
            "agility": 6
        }

    def on_hit(self, ctx: RollContext, stack: int):
        # Множитель урона 1.66
        ctx.damage_multiplier *= 1.66

        # Плата кровью
        dmg_self = 6
        ctx.source.take_damage(dmg_self)
        ctx.log.append(f"😈 **666**: Урон усилен, получено {dmg_self} отдачи.")


# logic/statuses/custom.py

class LuckyCoinStatus(StatusEffect):
    id = "lucky_coin_status"
    name = "Подброшенная монета"
    description = "Вся атака под влиянием Судьбы. Орел: Все кубики побеждают. Решка: Все кубики ломаются."

    def prevents_specific_die_destruction(self, unit, die) -> bool:
        return True

    def on_roll(self, ctx: RollContext, stack: int):
        """
        Логика монетки для всей карты.
        Результат (Орел/Решка) фиксируется при первом броске карты и действует до конца.
        """
        unit = ctx.source

        # Ключ памяти для хранения результата текущей карты
        # Мы используем ID карты, чтобы различать разные атаки
        card_id = getattr(unit.current_card, 'id', 'unknown_card')
        memory_key = f"lucky_coin_result_{card_id}"

        # Проверяем, кидали ли мы уже монетку для этой карты
        coin_result = unit.memory.get(memory_key)

        if coin_result is None:
            # Первый кубик карты: Бросаем монетку
            import random
            is_heads = random.choice([True, False])
            coin_result = "HEADS" if is_heads else "TAILS"
            unit.memory[memory_key] = coin_result

            # Логируем сам факт броска
            result_str = "ОРЕЛ (Победа)" if is_heads else "РЕШКА (Провал)"
            logger.log(f"🪙 Lucky Coin Flip for {card_id}: {result_str}", LogLevel.NORMAL, "Status")

        # === ПРИМЕНЕНИЕ РЕЗУЛЬТАТА К ТЕКУЩЕМУ КУБИКУ ===

        real_roll = ctx.final_value
        if real_roll <= 0: real_roll = 1

        if coin_result == "HEADS":
            # --- ОРЕЛ (ВСЕ КУБИКИ ПОБЕЖДАЮТ) ---
            win_val = 9999
            ctx.dice.value = win_val
            ctx.final_value = win_val
            ctx.is_critical = True

            # Коррекция урона (чтобы не бить на 9999)
            correction_factor = real_roll / win_val
            ctx.damage_multiplier *= correction_factor

            ctx.log.append(f"🪙 **ОРЕЛ**: Авто-победа (Base {real_roll})")

        else:
            # --- РЕШКА (ВСЕ КУБИКИ ПРОИГРЫВАЮТ) ---
            ctx.dice.value = 0
            ctx.final_value = 0
            ctx.damage_multiplier = 0
            ctx.dice.is_broken = True

            ctx.log.append(f"💀 **РЕШКА**: Слом... (Base {real_roll})")

            # Урон по себе (только 1 раз за карту или за каждый кубик?
            # Если за каждый - это очень больно. Сделаем проверку, чтобы бил 1 раз)
            dmg_key = f"lucky_coin_dmg_{card_id}"
            if not unit.memory.get(dmg_key):
                self_dmg = int(unit.max_hp * 0.15)
                if self_dmg > 0:
                    unit.heal_hp(-self_dmg)
                    ctx.log.append(f"💀 Отдача: -{self_dmg} HP")
                    unit.memory[dmg_key] = True  # Помечаем, что урон уже нанесен

    def on_round_end(self, unit, log_func, **kwargs):
        """Очистка в конце раунда"""
        # Удаляем статус
        unit.remove_status(self.id, 999)

        # Очищаем память от результатов бросков
        keys_to_remove = [k for k in unit.memory.keys() if k.startswith("lucky_coin_")]
        for k in keys_to_remove:
            unit.memory.pop(k)

        return ["🪙 Монета вернулась в карман."]


class StatusAntiCharge(StatusEffect):
    id = "anti_charge"
    name = "Анти-Заряд"
    description = "-3 к Мощи и -3 к Скорости за стак. Спадает на 1 в конце раунда."
    is_debuff = True

    # 1. Механика силы (как в StrengthStatus)
    def on_roll(self, ctx, **kwargs):
        stack = kwargs.get('stack', 0)
        if stack == 0 and hasattr(self, 'stack'):
            stack = self.stack

        if stack > 0:
            # -3 за каждый стак
            penalty = -3 * stack
            # Применяем ко всем кубикам (Атака и Защита)
            ctx.modify_power(penalty, f"Anti-Charge ({stack})")

    # 2. Механика скорости (как в HasteStatus)
    def get_speed_dice_value_modifier(self, unit, stack=0) -> int:
        if stack == 0:
            # Если стак не передали, пробуем взять из юнита или себя
            stack = unit.get_status(self.id) if hasattr(unit, "get_status") else getattr(self, "stack", 0)

        # -3 за каждый стак
        return -3 * stack

    # 3. Спад стаков
    def on_round_end(self, unit, log_func, **kwargs):
        unit.remove_status("anti_charge", 1)



class StatusWinCondition(StatusEffect):
    id = "win_condition"
    name = "Win Condition"
    description = "Особый статус Аксис. Сам по себе ничего не делает, но взаимодействует с её картами."
    is_debuff = True  # Считаем дебаффом, так как висит на враге и вредит ему при взаимодействии

    # Можно попробовать найти иконку контракта, если она есть в ассетах,
    # или движок подставит дефолтную по названию.

    # Если нужно, чтобы он не спадал сам по себе (для перманентного):
    def on_round_end(self, unit):
        # Если длительность > 50, считаем перманентным и не снижаем (или снижаем, но медленно)
        if self.duration < 50:
            self.reduce_stack(1)


class UnderCrosshairsStatus(StatusEffect):
    id = "under_crosshairs"
    name = "Под Прицелом"
    description = "Получает на 25% больше урона за каждый стак (складывается). Статус от 8 ветки (Военная)."
    is_debuff = True

    def modify_incoming_damage(self, unit, amount, damage_type, stack=0, **kwargs):
        if damage_type == "hp":
            if stack == 0: stack = unit.get_status(self.id)
            if stack > 0:
                # Каждый стак добавляет 25% урона (складывается)
                multiplier = 1.0 + (0.25 * stack)
                new_amount = int(amount * multiplier)
                logger.log(
                    f"🎯 Under Crosshairs: {unit.name} takes increased damage: {amount} -> {new_amount} (stack: {stack}, x{multiplier:.2f})",
                    LogLevel.VERBOSE, "Status"
                )
                return new_amount
        return amount


# ==========================================
# AMMO STATUS - Боеприпасы для оружия типа "gun"
# ==========================================
class AmmoStatus(StatusEffect):
    id = "ammo"
    name = "Боеприпасы"
    description = "Боеприпасы. Каждый кубик оружия типа 'gun' тратит 1 Ammo и получает усиление. Если Ammo недостаточно, кубик не усиливается."

    def on_roll(self, ctx: RollContext, **kwargs):
        """
        Вызывается при каждом броске кубика.
        Если оружие типа 'gun' - тратим 1 Ammo и баффаем кубик.
        """
        # Получаем количество Ammo напрямую из юнита (не из kwargs!)
        unit = ctx.source
        ammo_count = unit.get_status("ammo")
        
        if ammo_count <= 0:
            return  # Нет патронов - ничего не делаем

        # Проверяем, является ли оружие источника типом "gun"
        weapon_id = getattr(unit, 'weapon_id', 'none')
        
        # Получаем объект оружия из реестра
        from logic.weapon_definitions import WEAPON_REGISTRY
        weapon = WEAPON_REGISTRY.get(weapon_id)
        
        if weapon and hasattr(weapon, 'weapon_type') and weapon.weapon_type == "gun":
            # Тратим 1 патрон
            unit.remove_status("ammo", 1)
            
            # Баффаем кубик (например, +2 к мощности)
            bonus = 2
            ctx.modify_power(bonus, "Ammo 🔫")
            
            ctx.log.append(f"🔫 Ammo: +{bonus} мощи (-1 патрон)")
            logger.log(
                f"🔫 Ammo consumed: {unit.name} spent 1 ammo, gained +{bonus} power",
                LogLevel.VERBOSE, "Status"
            )

    def on_round_end(self, unit, log_func, **kwargs):
        """Патроны не тратятся сами по себе в конце раунда"""
        return []


# ==========================================
# STAGGER IMMUNE - Иммунитет к урону по выдержке
# ==========================================
class StaggerImmuneStatus(StatusEffect):
    id = "stagger_immune"
    name = "Иммунитет к урону по Стаггеру"
    description = "Персонаж не получает урон по Выдержке (Stagger). Полная защита от потери выдержки."

    def modify_incoming_damage(self, unit, amount, damage_type, stack=0, log_list=None, **kwargs):
        """Блокирует весь урон по стаггеру"""
        if damage_type == "stagger":
            if log_list is not None:
                log_list.append(f"🛡️ **Stagger Immune**: Blocked {amount} Stagger dmg")
            
            logger.log(
                f"🛡️ Stagger Immune: {unit.name} blocked {amount} stagger damage",
                LogLevel.VERBOSE, "Status"
            )
            return 0  # Урон по стаггеру обнуляется
        
        return amount

    def on_round_end(self, unit, log_func, **kwargs):
        """Статус постоянный, не спадает сам по себе"""
        return []


class ExhaustionStatus(StatusEffect):
    id = "exhaustion"
    name = "Истощение"
    description = "До 2 стаков не дает эффекта. На 3 стаках цель взрывается и получает 25% урона от максимального HP."
    is_debuff = True

    def on_round_end(self, unit, log_func, **kwargs):
        stack = kwargs.get("stack")
        if stack is None:
            stack = unit.get_status(self.id)

        if stack >= 3:
            damage = int(unit.max_hp * 0.25)
            if damage > 0:
                unit.take_damage(damage)
                if log_func:
                    log_func(f"💥 **Истощение**: Взрыв! -{damage} HP")
                logger.log(
                    f"💥 Exhaustion: {unit.name} took {damage} HP ({stack} stacks)",
                    LogLevel.NORMAL,
                    "Status"
                )
            unit.remove_status(self.id, 999)
        return []


class MarkedFleshStatus(StatusEffect):
    id = "marked_flesh"
    name = "Помеченная плоть"
    description = "Цель становится единственной целью Зафиэля и получает двойной урон от его атак."
    is_debuff = True

    def on_take_damage(self, unit, amount, source, **kwargs):
        if unit.current_hp > 0:
            return

        marked_by = unit.memory.get("marked_flesh_by")
        if not marked_by:
            return

        if source and hasattr(source, "name") and source.name == marked_by:
            heal = int(source.max_hp * 0.25)
            if heal > 0:
                source.heal_hp(heal)
            source.remove_status("exhaustion", 2)

            log_func = kwargs.get("log_func")
            if log_func:
                log_func(f"🩸 **Marked Flesh**: {source.name} healed +{heal} HP, -2 Exhaustion")

            logger.log(
                f"🩸 Marked Flesh kill: {source.name} healed {heal} HP and removed 2 Exhaustion",
                LogLevel.NORMAL,
                "Status"
            )

        if unit.memory.get("marked_flesh_transferred"):
            return

        unit.memory["marked_flesh_transferred"] = True
        self._transfer_mark(unit)

    def _transfer_mark(self, unit):
        try:
            import streamlit as st
        except Exception:
            return

        team_left = st.session_state.get("team_left", [])
        team_right = st.session_state.get("team_right", [])

        if unit in team_left:
            team = team_left
        elif unit in team_right:
            team = team_right
        else:
            return

        candidates = [u for u in team if not u.is_dead() and u is not unit]
        if not candidates:
            return

        new_target = min(candidates, key=lambda u: u.current_hp)

        for u in team:
            if u.get_status(self.id) > 0:
                u.remove_status(self.id, 999)

        new_target.add_status(self.id, 1, duration=99)
        new_target.memory["marked_flesh_by"] = unit.memory.get("marked_flesh_by")
        new_target.memory.pop("marked_flesh_transferred", None)

        logger.log(
            f"🩸 Marked Flesh transferred: {unit.name} -> {new_target.name}",
            LogLevel.NORMAL,
            "Status"
        )

    def on_round_end(self, unit, log_func, **kwargs):
        return []