from core.logging import logger, LogLevel
from logic.character_changing.passives.base_passive import BasePassive


class PassiveAxisUnity(BasePassive):
    id = "axis_unity"
    name = "Единство Тела, Души и Разума"
    description = (
        "Пока Аксис на поле боя:\n"
        "- Если на персонаже есть Сила, Стойкость и Спешка (мин 1): +1 ко всем этим эффектам.\n"
        "- Если на персонаже есть Слабость, Паралич и Замедление (мин 1): +1 ко всем этим эффектам.\n"
        "Бонус дается 1 раз за 'сборку' комбинации. Статусы обновляются мгновенно."
    )
    is_active_ability = False

    def _get_max_duration(self, unit, status_id):
        if not hasattr(unit, '_status_effects'): return 0
        effects = unit._status_effects.get(status_id, [])
        if not effects: return 0
        return max((eff.get('duration', 0) for eff in effects), default=0)

    def _evaluate_triad(self, target):
        """Проверяет статусы цели и активирует триаду."""
        if not target: return

        # === 1. ПОЛОЖИТЕЛЬНАЯ ТРИАДА (Strength, Endurance, Haste) ===
        has_str = target.get_status("strength") >= 1
        has_end = target.get_status("endurance") >= 1
        has_haste = target.get_status("haste") >= 1

        is_active = target.memory.get("axis_buff_triad_active", False)

        if has_str and has_end and has_haste:
            if not is_active:
                # Активация!
                d_str = self._get_max_duration(target, "strength")
                d_end = self._get_max_duration(target, "endurance")
                d_has = self._get_max_duration(target, "haste")

                target.add_status("strength", 1, duration=d_str, trigger_events=False)
                target.add_status("endurance", 1, duration=d_end, trigger_events=False)
                target.add_status("haste", 1, duration=d_has, trigger_events=False)

                target.memory["axis_buff_triad_active"] = True
                logger.log(f"✨ Axis Unity: Buff Triad activated on {target.name}", LogLevel.NORMAL, "Passive")
        else:
            # Если хотя бы одного нет - сбрасываем флаг
            if is_active:
                target.memory["axis_buff_triad_active"] = False

        # === 2. НЕГАТИВНАЯ ТРИАДА (Weakness, Paralysis, Slow) ===
        has_weak = target.get_status("weakness") >= 1
        has_para = target.get_status("paralysis") >= 1
        has_slow = target.get_status("slow") >= 1

        is_active_debuff = target.memory.get("axis_debuff_triad_active", False)

        if has_weak and has_para and has_slow:
            if not is_active_debuff:
                d_weak = self._get_max_duration(target, "weakness")
                d_para = self._get_max_duration(target, "paralysis")
                d_slow = self._get_max_duration(target, "slow")

                target.add_status("weakness", 1, duration=d_weak, trigger_events=False)
                target.add_status("paralysis", 1, duration=d_para, trigger_events=False)
                target.add_status("slow", 1, duration=d_slow, trigger_events=False)

                target.memory["axis_debuff_triad_active"] = True
                logger.log(f"⛓️ Axis Unity: Debuff Triad activated on {target.name}", LogLevel.NORMAL, "Passive")
        else:
            if is_active_debuff:
                target.memory["axis_debuff_triad_active"] = False

    # --- ХУКИ ---

    def on_status_applied(self, unit, status_id, amount, **kwargs):
        """Когда статус накладывается на САМОГО Аксиса (владельца пассивки)."""
        self._evaluate_triad(unit)

    def on_status_applied_global(self, unit, target, status_id, amount, **kwargs):
        """
        Новый хук! Срабатывает, когда статус накладывается на ЛЮБОГО ДРУГОГО юнита (target).
        unit - это Аксис (наблюдатель).
        target - это тот, кто получил статус.
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

class PassivePseudoProtagonist(BasePassive):
    id = "pseudo_protagonist"
    name = "Псевдо-главный герой"
    description = (
        "Вне боя Аксис получает опыт за каждый брошенный кубик. "
        "Опыт = (Опыт текущего уровня) * (Результат броска / 100)."
    )
    is_active_ability = False

    def on_skill_check(self, unit, check_result: int, stat_key: str, **kwargs):
        # 1. Считаем базовую стоимость уровня (2^(lvl-1))
        # Защита от уровня 0 или меньше
        lvl = max(1, unit.level)
        level_xp_base = 2 ** lvl

        # 2. Считаем процент от броска
        # Результат 10 = 0.1 (10%), Результат 30 = 0.3 (30%)
        multiplier = check_result / 100.0

        # 3. Итоговый опыт (целое число)
        xp_gain = max(check_result, int(level_xp_base * multiplier))

        if xp_gain > 0:
            unit.total_xp += xp_gain

            # Логируем
            logger.log(f"📚 Pseudo Protagonist: {unit.name} gained {xp_gain} XP from roll {check_result}",
                       LogLevel.NORMAL, "System")

            # Пишем тост в интерфейс (чтобы игрок увидел сразу)
            import streamlit as st
            st.toast(f"Псевдо-ГГ: +{xp_gain} XP за бросок!", icon="📚")


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

    def on_check_roll(self, unit, attribute, context):
        # Проверяем, что атрибут - Красноречие
        if attribute.lower() in ["eloquence", "красноречие"]:
            context.is_disadvantage = True
            if hasattr(context, "log"):
                context.log.append(f"🌑 **{self.name}**: Помеха на Красноречие!")
            # Лог в консоль
            from core.logging import logger, LogLevel
            logger.log(f"🌑 Chthonic Nature: Disadvantage on Eloquence for {unit.name}", LogLevel.VERBOSE, "Passive")