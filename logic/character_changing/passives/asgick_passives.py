from logic.character_changing.passives.base_passive import BasePassive
from logic.context import RollContext


class PassiveWitnessOfGroGoroth(BasePassive):
    id = "witness_gro_goroth"
    name = "Свидетель Гро-Горота"
    description = (
        "ПЛЮСЫ:\n"
        "+666% урона по Лиме и её родословной.\n"
        "+20 Харизмы.\n"
        "Все положительные статусы распространяются на команду (синхронизация в начале раунда).\n"
        "+6 Уровней (визуально/расчетно), +2 Таланта.\n"
        "100,000,000 Ан в тайнике.\n"
        "\n"
        "МИНУСЫ:\n"
        "-50 HP, -50 SP (Flat).\n"
        "-50% Выдержки (Pct).\n"
        "-1 Уровень угрозы.\n"
        "Нельзя Уклоняться и Блокировать.\n"
        "Получаемый урон увеличен на 20% (аналог +0.2 резиста).\n"
        "-15 Удачи.\n"
        "Особенность прокачки: 1 очко навыка и 1 очко хар-к за уровень (См. Профиль)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        stats = {
            "eloquence": 20,  # Харизма +20
            "luck": -15,  # Удача -15
            "hp_flat": -50,  # Здоровье -50
            "sp_flat": -50,  # Рассудок -50
            "stagger_pct": -50,  # Выдержка -50%
            "talent_slots": 2,  # +2 слота талантов
            "threat_level": -1,
            "damage_take_pct": 20,
            "disable_block": 1,
            "disable_evade": 1
        }
        return stats

    def on_combat_start(self, unit, log_func, **kwargs):
        allies = kwargs.get("allies", [])
        # Сохраняем ТОЛЬКО ИМЕНА (строки), а не объекты
        real_allies_names = [a.name for a in allies if a != unit]
        unit.memory['cached_allies_names'] = real_allies_names

        if log_func:
            log_func(f"👁️ **{self.name}**: Тело изменено. Связь с {len(real_allies_names)} союзниками установлена.")

    def on_hit(self, ctx: RollContext):
        # +666% урона по Лиме и её родословной
        if ctx.target and ("лима" in ctx.target.name.lower() or "lima" in ctx.target.name.lower()):
            ctx.damage_multiplier += 6.66
            ctx.log.append(f"🩸 **НЕНАВИСТЬ**: Урон по Лиме увеличен (+666%)!")

    def on_status_applied(self, unit, status_id, amount, duration=100, **kwargs):
        # Список распространяемых баффов
        POSITIVE_BUFFS = [
            "attack_power_up", "endurance", "haste", "protection", "barrier",
            "dmg_up", "power_up", "clash_power_up", "revenge_dmg_up",
            "self_control", "invisibility", "bullet_time", "adaptation", "clarity",
            "mental_protection", "stagger_resist", "bleed_resist", "regen_ganache", "ignore_satiety",
            "red_lycoris"
        ]

        if status_id in POSITIVE_BUFFS:
            # Получаем имена из памяти
            ally_names = unit.memory.get('cached_allies_names', [])
            if not ally_names: return

            # Импортируем streamlit для доступа к глобальным спискам команд
            import streamlit as st
            all_units = st.session_state.get('team_left', []) + st.session_state.get('team_right', [])

            # Находим живые объекты по именам
            shared_names = []
            for u in all_units:
                if u.name in ally_names and not u.is_dead():
                    u.add_status(status_id, amount, duration=duration, trigger_events=False)
                    shared_names.append(u.name)

            if shared_names:
                from core.logging import logger, LogLevel
                logger.log(f"👁️ Witness: Shared {amount} {status_id} with {', '.join(shared_names)}", LogLevel.VERBOSE,
                           "Passive")


class PassivePovar(BasePassive):
    id = "povar"
    name = "Поваренок"
    description = "Отлично готовишь и вкусно кушаешь! Автоматически получает доступ к талантам 4.4 и 4.5."

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        talents_to_learn = ["cheese", "confete"]
        # Добавляем таланты, если их нет (без логов, т.к. это происходит часто)
        for tid in talents_to_learn:
            if tid not in unit.talents:
                unit.talents.append(tid)

        return {"talent_slots": len(talents_to_learn)}


class PassiveDistortionGroGoroth(BasePassive):
    id = "distortionGroGoroth"
    name = "Traces of Gro-goroth"
    description = "Инкубационный период. +10 скорости. +1 ко всем картам"

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        stats = {
            "speed": 10,
        }
        return stats


class PassiveFoodLover(BasePassive):
    id = "food_lover"
    name = "Любитель поесть"
    description = "Сытый: Порог 27, нет штрафов. Голодный: Штрафы."
    is_active_ability = False

    def on_calculate_stats(self, unit, *args, **kwargs) -> dict:
        satiety = unit.get_status("satiety")
        if satiety <= 0:
            return {"hp_pct": -25, "sp_pct": -25}
        return {}

    def on_roll(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        # Штраф к проверкам за голод
        if ctx.source.get_status("satiety") <= 0:
            ctx.modify_power(-5, "Hunger")
            # [LOG] Добавляем визуальный лог
            ctx.log.append("🍗 **Hunger**: -5 Power penalty")

    def modify_satiety_penalties(self, unit, penalties: dict) -> dict:
        return {}