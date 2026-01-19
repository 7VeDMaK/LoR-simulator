import math

from core.logging import logger, LogLevel  # [NEW] Import
from logic.character_changing.passives.base_passive import BasePassive


class PassiveSCells(BasePassive):
    id = "s_cells"
    name = "S-клетки"
    description = "В начале боя восстанавливает 10 HP за каждый имеющийся слот скорости."

    def on_speed_rolled(self, unit, log_func, **kwargs):
        # Считаем количество активных слотов (кубиков скорости)
        dice_count = len(unit.active_slots)

        if dice_count > 0:
            heal_amount = dice_count * 10
            actual_heal = unit.heal_hp(heal_amount)

            if log_func:
                log_func(f"🧬 {self.name}: {dice_count} слотов x 10 = Восстановлено {actual_heal} HP")

            logger.log(f"🧬 S-Cells: Healed {actual_heal} HP for {unit.name}", LogLevel.VERBOSE, "Passive")


class PassiveNewDiscovery(BasePassive):
    id = "new_discovery"
    name = "Новое открытие (Сенсоры 2%)"
    description = "Пассивно: Мудрость +10, Интеллект +2.\nАвтоматически открывает 'Тактический анализ'."
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {
            "wisdom": 10,
            "bonus_intellect": 2,
        }

    def on_combat_start(self, unit, log_func, **kwargs):
        if log_func:
            log_func(f"👁️ {self.name}: Сенсоры активны.")


class TalentRedLycoris(BasePassive):
    id = "red_lycoris"
    name = "Красный Ликорис"
    description = (
        "Активно (при Stagger < 50%): Переход в состояние жизни и смерти на 4 цикла.\n"
        "Эффекты: Иммунитет к негативным эффектам. Инициатива равна противнику.\n"
        "Действия восстанавливают 5% HP/SP/Stagger.\n"
        "Нельзя перенаправлять атаки. Перезарядка 7 ходов."
    )
    is_active_ability = True
    cooldown = 7
    duration = 1

    def activate(self, unit, log_func, **kwargs):
        from logic.statuses.status_definitions import NEGATIVE_STATUSES

        if unit.cooldowns.get(self.id, 0) > 0:
            return False

        # Проверка Stagger < 50%
        stagger_pct = unit.current_stagger / unit.max_stagger
        if stagger_pct > 0.5:
            if log_func: log_func(f"❌ {self.name}: Выдержка слишком высока ({int(stagger_pct * 100)}%)")
            return False

        removed_list = []
        current_statuses = list(unit.statuses.keys())
        for status_id in current_statuses:
            # УДАЛЯЕМ ТОЛЬКО ЕСЛИ ЭТО НЕГАТИВНЫЙ СТАТУС
            if status_id in NEGATIVE_STATUSES:
                unit.remove_status(status_id)
                removed_list.append(status_id)

        # 2. Очищаем отложенные негативные статусы (Delayed)
        if hasattr(unit, "delayed_queue"):
            new_queue = []
            for item in unit.delayed_queue:
                s_name = item.get("name")
                if s_name in NEGATIVE_STATUSES:
                    removed_list.append(f"{s_name} (Delayed)")
                else:
                    new_queue.append(item)
            unit.delayed_queue = new_queue

        if log_func and removed_list:
            log_func(f"✨ Ликорис: Сожжены негативные эффекты ({', '.join(removed_list)})")

        # Накладываем статус Ликориса
        unit.add_status("red_lycoris", 1, duration=self.duration)
        unit.cooldowns[self.id] = self.cooldown

        if log_func:
            log_func(f"🩸 {self.name}: Активирован! Иммунитет к негативу и синхронизация.")

        logger.log(f"🩸 Red Lycoris activated by {unit.name}. Cleared: {removed_list}", LogLevel.NORMAL, "Passive")
        return True

    def on_speed_rolled(self, unit, log_func, **kwargs):
        # Если статус активен, запускаем регенерацию
        if unit.get_status("red_lycoris") > 0:
            dice_count = len(unit.active_slots)

            # Если вдруг слотов нет (стан и т.д.), берем базу
            if dice_count == 0:
                dice_count = getattr(unit, 'speed_dice_count', 1)

            # 5% за каждый кубик
            pct = 0.05 * dice_count

            h_amt = math.ceil(unit.max_hp * pct)
            s_amt = math.ceil(unit.max_sp * pct)
            stg_amt = math.ceil(unit.max_stagger * pct)

            unit.heal_hp(h_amt)
            unit.current_sp = min(unit.max_sp, unit.current_sp + s_amt)
            unit.current_stagger = min(unit.max_stagger, unit.current_stagger + stg_amt)

            if log_func:
                log_func(
                    f"🩸 Ликорис ({dice_count} д.): Восстановлено {int(pct * 100)}% ({h_amt} HP, {s_amt} SP, {stg_amt} Stg)")

            logger.log(f"🩸 Red Lycoris regen for {unit.name}: {h_amt} HP, {s_amt} SP, {stg_amt} Stg", LogLevel.VERBOSE,
                       "Passive")

    # === [НОВОЕ] Перехват наложения статусов ===
    def on_before_status_add(self, unit, status_id, amount):
        from logic.statuses.status_definitions import NEGATIVE_STATUSES

        # Если Ликорис активен -> Блокируем только негативные статусы
        if unit.get_status("red_lycoris") > 0:
            if status_id in NEGATIVE_STATUSES:
                logger.log(f"🩸 Red Lycoris blocked status {status_id} for {unit.name}", LogLevel.VERBOSE, "Passive")
                return False, f"🩸 Lycoris blocked {status_id}"

        # Положительные статусы пропускаем
        return True, None


class TalentShadowOfMajesty(BasePassive):
    id = "shadow_majesty"
    name = "Тень Величия"
    description = "Пассивно: +5 Красноречия. Аура на слабых врагов (-SP при атаке)."
    is_active_ability = False

    def on_calculate_stats(self, unit) -> dict:
        return {"eloquence": 5}

    def on_combat_start(self, unit, log_func, **kwargs):
        # ТЕПЕРЬ МЫ БЕРЕМ ОППОНЕНТА ИЗ АРГУМЕНТОВ
        opponent = kwargs.get("opponent")

        # Fallback to enemies list if opponent is not directly provided
        if not opponent:
            enemies = kwargs.get("enemies")
            if enemies and len(enemies) > 0:
                opponent = enemies[0]

        if opponent:
            threshold = unit.level // 2

            if opponent.level < threshold:
                opponent.add_status("sinister_aura", 1, duration=99)
                if log_func:
                    log_func(f"🌑 {self.name}: {opponent.name} (Lvl {opponent.level}) подавлен Величием")
                logger.log(f"🌑 Shadow of Majesty: Applied Sinister Aura to {opponent.name}", LogLevel.NORMAL, "Passive")
            else:
                if log_func:
                    log_func(f"🛡️ {self.name}: {opponent.name} (Lvl {opponent.level}) сопротивляется Ауре")
                logger.log(f"🛡️ Shadow of Majesty: {opponent.name} resisted aura", LogLevel.VERBOSE, "Passive")