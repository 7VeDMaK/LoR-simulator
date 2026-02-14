from core.logging import logger, LogLevel
from logic.character_changing.passives.base_passive import BasePassive

import math
from core.logging import logger, LogLevel
from logic.character_changing.passives.base_passive import BasePassive


class PassiveAxisUnity(BasePassive):
    id = "axis_unity"
    name = "Единство Тела, Души и Разума"
    description = (
        "Пока Аксис на поле боя:\n"
        "- Если на персонаже есть Сила, Стойкость и Спешка (мин 1): +1 ко всем этим эффектам.\n"
        "  ДОПОЛНИТЕЛЬНО: Каждые 3 Силы дают +1 Спешку, каждые 3 Стойкости -> +1 Силу, каждые 3 Спешки -> +1 Стойкость.\n"
        "- Если на персонаже есть Слабость, Уязвимость и Связывание (мин 1): +1 ко всем этим эффектам (с усилением).\n"
        "  ДОПОЛНИТЕЛЬНО: Каждые 3 Слабости дают +1 Связывание, каждые 3 Уязвимости -> +1 Слабость, каждые 3 Связывания -> +1 Уязвимость.\n"
        "Бонус дается 1 раз за 'сборку' комбинации и обновляется при изменении статусов."
    )
    is_active_ability = False

    def _get_max_duration(self, unit, status_id):
        if not hasattr(unit, '_status_effects'): return 0
        effects = unit._status_effects.get(status_id, [])
        if not effects: return 0
        return max((eff.get('duration', 0) for eff in effects), default=0)

    def _evaluate_triad(self, target):
        """
        Проверяет статусы цели и активирует/обновляет триаду с усилением.
        Использует цикл сходимости (до 3 итераций), чтобы бонусы обновляли друг друга мгновенно.
        """
        if not target: return

        # [FIX] Цикл сходимости: прогоняем проверки несколько раз,
        # чтобы рост Силы тут же вызывал рост Спешки в рамках одного события.
        # 3 раза достаточно для замыкания круга (Str -> Haste -> End -> Str).
        for _ in range(3):
            changes_made = False

            # =========================================================
            # 1. ПОЛОЖИТЕЛЬНАЯ ТРИАДА (Strength, Endurance, Haste)
            # =========================================================
            cur_str = target.get_status("attack_power_up")
            cur_end = target.get_status("endurance")
            cur_haste = target.get_status("haste")

            has_str = cur_str >= 1
            has_end = cur_end >= 1
            has_haste = cur_haste >= 1

            # Ключи для памяти
            mem_key_str = "axis_applied_bonus_str"
            mem_key_end = "axis_applied_bonus_end"
            mem_key_haste = "axis_applied_bonus_haste"

            if has_str and has_end and has_haste:
                # --- РАСЧЕТ ЦЕЛЕВОГО БОНУСА ---
                target_bonus_str = 1 + (cur_end // 3)  # Str растет от End
                target_bonus_end = 1 + (cur_haste // 3)  # End растет от Haste
                target_bonus_haste = 1 + (cur_str // 3)  # Haste растет от Str

                # --- ПОЛУЧЕНИЕ УЖЕ ВЫДАННОГО ---
                applied_str = target.memory.get(mem_key_str, 0)
                applied_end = target.memory.get(mem_key_end, 0)
                applied_haste = target.memory.get(mem_key_haste, 0)

                # [FIX] СИНХРОНИЗАЦИЯ ВНИЗ (если статы упали - забываем старый бонус)
                if target_bonus_str < applied_str:
                    applied_str = target_bonus_str
                    target.memory[mem_key_str] = applied_str

                if target_bonus_end < applied_end:
                    applied_end = target_bonus_end
                    target.memory[mem_key_end] = applied_end

                if target_bonus_haste < applied_haste:
                    applied_haste = target_bonus_haste
                    target.memory[mem_key_haste] = applied_haste

                # --- РАСЧЕТ РАЗНИЦЫ (DELTA) ---
                diff_str = max(0, target_bonus_str - applied_str)
                diff_end = max(0, target_bonus_end - applied_end)
                diff_haste = max(0, target_bonus_haste - applied_haste)

                if diff_str > 0 or diff_end > 0 or diff_haste > 0:
                    d_str = self._get_max_duration(target, "attack_power_up")
                    d_end = self._get_max_duration(target, "endurance")
                    d_haste = self._get_max_duration(target, "haste")

                    if diff_str > 0:
                        target.add_status("attack_power_up", diff_str, duration=d_str, trigger_events=False)
                        target.memory[mem_key_str] = target_bonus_str

                    if diff_end > 0:
                        target.add_status("endurance", diff_end, duration=d_end, trigger_events=False)
                        target.memory[mem_key_end] = target_bonus_end

                    if diff_haste > 0:
                        target.add_status("haste", diff_haste, duration=d_haste, trigger_events=False)
                        target.memory[mem_key_haste] = target_bonus_haste

                    target.memory["axis_buff_triad_active"] = True
                    changes_made = True  # [FLAG] Были изменения, нужен повторный проход

                    logger.log(
                        f"✨ Axis Unity Update: Added delta (+{diff_str} Str, +{diff_end} End, +{diff_haste} Haste). "
                        f"Total from Passive: ({target_bonus_str}/{target_bonus_end}/{target_bonus_haste})",
                        LogLevel.NORMAL, "Passive"
                    )
            else:
                # Сброс при разрыве триады
                if target.memory.get("axis_buff_triad_active", False):
                    target.memory["axis_buff_triad_active"] = False
                    target.memory[mem_key_str] = 0
                    target.memory[mem_key_end] = 0
                    target.memory[mem_key_haste] = 0
                    logger.log(f"📉 Axis Unity: Buff Triad broken on {target.name}. Reset counters.", LogLevel.VERBOSE,
                               "Passive")

            # =========================================================
            # 2. НЕГАТИВНАЯ ТРИАДА (attack_power_down, vulnerable, Bind)
            # =========================================================
            cur_weak = target.get_status("attack_power_down")
            cur_vuln = target.get_status("vulnerable")
            cur_bind = target.get_status("bind")

            has_weak = cur_weak >= 1
            has_vuln = cur_vuln >= 1
            has_bind = cur_bind >= 1

            mem_key_weak = "axis_applied_malus_weak"
            mem_key_vuln = "axis_applied_malus_vuln"
            mem_key_bind = "axis_applied_malus_bind"

            if has_weak and has_vuln and has_bind:
                target_malus_weak = 1 + (cur_vuln // 3)  # Weakness растет от Vuln
                target_malus_vuln = 1 + (cur_bind // 3)  # Vuln растет от Bind
                target_malus_bind = 1 + (cur_weak // 3)  # Bind растет от Weakness

                applied_weak = target.memory.get(mem_key_weak, 0)
                applied_vuln = target.memory.get(mem_key_vuln, 0)
                applied_bind = target.memory.get(mem_key_bind, 0)

                # [FIX] СИНХРОНИЗАЦИЯ ВНИЗ
                if target_malus_weak < applied_weak:
                    applied_weak = target_malus_weak
                    target.memory[mem_key_weak] = applied_weak
                if target_malus_vuln < applied_vuln:
                    applied_vuln = target_malus_vuln
                    target.memory[mem_key_vuln] = applied_vuln
                if target_malus_bind < applied_bind:
                    applied_bind = target_malus_bind
                    target.memory[mem_key_bind] = applied_bind

                diff_weak = max(0, target_malus_weak - applied_weak)
                diff_vuln = max(0, target_malus_vuln - applied_vuln)
                diff_bind = max(0, target_malus_bind - applied_bind)

                if diff_weak > 0 or diff_vuln > 0 or diff_bind > 0:
                    d_weak = self._get_max_duration(target, "attack_power_down")
                    d_vuln = self._get_max_duration(target, "vulnerable")
                    d_bind = self._get_max_duration(target, "bind")

                    if diff_weak > 0:
                        target.add_status("attack_power_down", diff_weak, duration=d_weak, trigger_events=False)
                        target.memory[mem_key_weak] = target_malus_weak

                    if diff_vuln > 0:
                        target.add_status("vulnerable", diff_vuln, duration=d_vuln, trigger_events=False)
                        target.memory[mem_key_vuln] = target_malus_vuln

                    if diff_bind > 0:
                        target.add_status("bind", diff_bind, duration=d_bind, trigger_events=False)
                        target.memory[mem_key_bind] = target_malus_bind

                    target.memory["axis_debuff_triad_active"] = True
                    changes_made = True  # [FLAG] Были изменения, нужен повторный проход

                    logger.log(
                        f"⛓️ Axis Unity Update: Added Malus (+{diff_weak} Weak, +{diff_vuln} Vuln, +{diff_bind} Bind). "
                        f"Total: ({target_malus_weak}/{target_malus_vuln}/{target_malus_bind})",
                        LogLevel.NORMAL, "Passive"
                    )
            else:
                if target.memory.get("axis_debuff_triad_active", False):
                    target.memory["axis_debuff_triad_active"] = False
                    target.memory[mem_key_weak] = 0
                    target.memory[mem_key_vuln] = 0
                    target.memory[mem_key_bind] = 0
                    logger.log(f"⛓️ Axis Unity: Debuff Triad broken on {target.name}. Reset counters.",
                               LogLevel.VERBOSE, "Passive")

            # Если на этом проходе ничего не поменялось - система стабильна, выходим
            if not changes_made:
                break

    # --- ХУКИ ---

    def on_status_applied(self, unit, status_id, amount, **kwargs):
        """Когда статус накладывается на САМОГО Аксиса (владельца пассивки)."""
        self._evaluate_triad(unit)

    def on_status_applied_global(self, unit, target, status_id, amount, **kwargs):
        """
        Срабатывает, когда статус накладывается на ЛЮБОГО ДРУГОГО юнита (target).
        """
        self._evaluate_triad(target)

    def on_round_start(self, unit, log_func, allies=None, enemies=None, **kwargs):
        """Контрольная проверка в начале раунда для всех."""
        all_units = [unit]
        if allies: all_units.extend(allies)
        if enemies: all_units.extend(enemies)

        for u in all_units:
            self._evaluate_triad(u)

# === НОВЫЕ ПАССИВКИ (СИЛЬНЫЕ СТОРОНЫ) ===

from core.logging import logger, LogLevel
from logic.character_changing.passives.base_passive import BasePassive
import streamlit as st

class PassivePseudoProtagonist(BasePassive):
    id = "pseudo_protagonist"
    name = "Псевдо-главный герой"
    description = (
        "Вне боя Аксис получает опыт за каждый брошенный кубик (Навыки и Удача). "
        "Опыт = (Опыт текущего уровня) * (Результат броска / 100)."
    )
    is_active_ability = False

    def on_skill_check(self, unit, check_result: int, stat_key: str, **kwargs):
        """
        Основная логика начисления опыта за проверки.
        """
        # 1. Считаем базовую стоимость уровня (2^(lvl-1))
        lvl = max(1, unit.level)
        level_xp_base = 2 ** lvl

        # 2. Считаем процент от броска
        # Результат 10 = 0.1, 50 = 0.5, 100 = 1.0
        multiplier = check_result / 100.0

        # 3. Итоговый опыт (минимум равен результату броска)
        xp_gain = max(check_result, int(level_xp_base * multiplier))

        if xp_gain > 0:
            unit.total_xp += xp_gain

            # Логирование
            check_type = "Luck" if stat_key == "luck" else "Skill"
            logger.log(f"📚 Pseudo Protagonist: {unit.name} gained {xp_gain} XP from {check_type} roll {check_result}",
                       LogLevel.NORMAL, "System")

            # Тост для игрока
            st.toast(f"Псевдо-ГГ: +{xp_gain} XP ({check_type})!", icon="📚")

    def on_luck_check(self, unit, result: int, **kwargs):
        """
        Перехватывает броски удачи (trigger_hooks('on_luck_check')) и направляет их в общую логику.
        """
        # Передаем результат броска удачи как check_result, а ключ как 'luck'
        self.on_skill_check(unit, result, "luck")


class PassiveSourceAccess(BasePassive):
    id = "source_access"
    name = "Доступ к истокам"
    description = (
        "В бою все кубики (кроме скорости) зависят не от характеристик, "
        "а от Удачи (Luck). (Соотношение 1 к 5 от прокачиваемого стата)."
    )
    is_active_ability = False

    def override_roll_base_stat(self, unit, current_pair, dice=None, **kwargs):
        # 1. Получаем значение прокачиваемого навыка Удачи
        # unit.skills["luck"] хранит вложенные очки + бонусы от пассивок
        luck_val = unit.skills.get("luck", 0)

        # 2. Считаем бонус (1 к 5)
        new_val = luck_val // 5

        # 3. Возвращаем новое значение и название для лога
        return (new_val, f"Luck ({luck_val}//5)")


class PassiveMetaAwareness(BasePassive):
    id = "meta_awareness"
    name = "Мета осознание"
    description = (
        "Персонаж может ломать четвёртую стену, читать посты и даже НРП чаты. "
        "Знание - сила, даже если оно не должно существовать."
    )
    is_active_ability = False
    # Чисто РП пассивка, механики не требует


# === НОВЫЕ ПАССИВКИ (СЛАБЫЕ СТОРОНЫ) ===

class PassiveChthonic(BasePassive):
    id = "chthonic_nature"
    name = "Хтонь"
    description = "Любой бросок Красноречия проходит с Помехой (Disadvantage)."
    is_active_ability = False

    def on_check_roll(self, unit, attribute, context, **kwargs):
        # Проверяем, что атрибут - Красноречие
        if attribute.lower() in ["eloquence", "красноречие"]:
            context.is_disadvantage = True
            if hasattr(context, "log"):
                context.log.append(f"🌑 **{self.name}**: Помеха на Красноречие!")
            # Лог в консоль
            from core.logging import logger, LogLevel
            logger.log(f"🌑 Chthonic Nature: Disadvantage on Eloquence for {unit.name}", LogLevel.VERBOSE, "Passive")