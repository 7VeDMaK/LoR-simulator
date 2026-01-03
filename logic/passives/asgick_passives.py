from logic.context import RollContext
from logic.passives.base_passive import BasePassive


class PassiveWitnessOfGroGoroth(BasePassive):
    id = "witness_gro_goroth"
    name = "Свидетель Гро-Горота"
    description = (
        "ПЛЮСЫ:\\n"
        "+666% урона по Лиме и её родословной.\\n"
        "+20 Харизмы.\\n"
        "Все положительные статусы распространяются на команду (синхронизация в начале раунда).\\n"
        "+6 Уровней (визуально/расчетно), +2 Таланта.\\n"
        "100,000,000 Ан в тайнике.\\n"
        "\\n"
        "МИНУСЫ:\\n"
        "-50 HP, -50 SP (Flat).\\n"
        "-50% Выдержки (Pct).\\n"
        "-1 Уровень угрозы.\\n"
        "Нельзя Уклоняться и Блокировать.\\n"
        "Получаемый урон увеличен на 20% (аналог +0.2 резиста).\\n"
        "-3 ко всем характеристикам и навыкам.\\n"
        "-15 Удачи.\\n"
        "Особенность прокачки: 1 очко навыка и 1 очко хар-к за уровень (См. Профиль)."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        stats = {
            "eloquence": 20,  # Харизма +20
            "luck": -15,  # Удача -15
            "hp_flat": -50,  # Здоровье -50
            "sp_flat": -50,  # Рассудок -50
            "stagger_pct": -50,  # Выдержка -50%
            "talent_slots": 2,  # <--- ДОБАВЛЕНО: +2 слота талантов

            # Эмуляция +0.2 резиста (+20% входящего урона)
            # Это безопаснее, чем менять unit.hp_resists напрямую
            "damage_take_pct": 2000,

            # Угроза -1 (влияет на приоритет атак врага)
            "threat_level": -1,

            "disable_block": 1,
            "disable_evade": 1
        }

        # -3 ко всем характеристикам
        attributes = ["strength", "endurance", "agility", "wisdom", "psych"]
        for attr in attributes:
            stats[attr] = -3

        # -3 ко всем навыкам
        all_skills = [
            "strike_power", "medicine", "willpower", "acrobatics", "shields",
            "tough_skin", "speed", "light_weapon", "medium_weapon",
            "heavy_weapon", "firearms", "forging", "engineering", "programming"
        ]
        for skill in all_skills:
            stats[skill] = -3

        return stats

    def on_combat_start(self, unit, log_func, **kwargs):
        allies = kwargs.get("allies", [])
        # Оставляем только живых союзников, исключая себя
        real_allies = [a for a in allies if a != unit]
        unit.memory['cached_allies'] = real_allies

        if not unit.memory.get("grogoroth_resists_applied"):
            unit.hp_resists.slash += 0.2
            unit.hp_resists.blunt += 0.2
            unit.memory["grogoroth_resists_applied"] = True

        if log_func:
            log_func(f"👁️ **{self.name}**: Тело изменено. Связь с {len(real_allies)} союзниками установлена.")

    def on_hit(self, ctx: RollContext):
        # +666% урона по Лиме и её родословной
        if ctx.target and ("лима" in ctx.target.name.lower() or "lima" in ctx.target.name.lower()):
            ctx.damage_multiplier += 6.66
            ctx.log.append(f"🩸 **НЕНАВИСТЬ**: Урон по Лиме увеличен (+666%)!")

        # === НОВЫЙ ХУК: РАСПРОСТРАНЕНИЕ БАФФОВ ===
    def on_status_applied(self, unit, status_id, amount, duration=1, **kwargs):
        # Список распространяемых баффов
        POSITIVE_BUFFS = [
            "strength", "haste", "endurance", "protection",
            "dmg_up", "power_up", "clash_power_up", "invisibility"
        ]

        if status_id in POSITIVE_BUFFS:
            # Берем союзников из памяти (закэшированных в начале боя/раунда)
            allies = unit.memory.get('cached_allies', [])

            if not allies:
                return

            for ally in allies:
                if not ally.is_dead():
                    # ВАЖНО: trigger_events=False предотвращает бесконечный цикл,
                    # если у союзника тоже есть такая пассивка или триггеры
                    ally.add_status(status_id, amount, duration=duration, trigger_events=False)


class PassivePovar(BasePassive):
    id = "povar"
    name = "Поваренок"
    description = "Отлично готовишь и вкусно кушаешь! Автоматически получает доступ к талантам 4.4 и 4.5."

    def on_calculate_stats(self, unit) -> dict:
        talents_to_learn = ["cheese", "confete"]

        for tid in talents_to_learn:
            if tid not in unit.talents:
                unit.talents.append(tid)

        return {"talent_slots": len(talents_to_learn)}


class PassiveFoodLover(BasePassive):
    id = "food_lover"
    name = "Любитель поесть"
    description = (
        "😋 **Сытый**: Порог переедания 27 (вместо 20). Нет штрафов к статам от сытости.\n"
        "😨 **Голодный (0 сытости)**: -5 ко всем проверкам (броскам). -25% Макс. HP и SP."
    )
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        # Проверяем голод
        satiety = unit.get_status("satiety")

        if satiety <= 0:
            # Штраф -25% к макс статам
            return {
                "hp_pct": -25,
                "sp_pct": -25
            }
        return {}

    def on_roll(self, ctx):
        # Штраф к проверкам (броскам)
        satiety = ctx.source.get_status("satiety")

        if satiety <= 0:
            ctx.modify_power(-5, "Hunger (Gurgle...)")