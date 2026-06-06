from logic.character_changing.passives.base_passive import BasePassive


class WeaponHollowMoonPassive(BasePassive):
    id = "weapon_hollow_moon"
    name = "Эффект: Меч полой луны"
    description = (
        "Если у цели атаки сопротивление режущему урону ниже 1.0, "
        "оно считается более высоким (максимум повышает на 0.25. Цель - 1.0)."
    )

    def on_hit(self, ctx, stack=None, *args, **kwargs):
        unit = ctx.source
        target = ctx.target
        if not target:
            return

        # 1. Получаем тип урона из броска
        raw_type = ctx.dice.dtype
        if hasattr(raw_type, "value"):
            dmg_type = str(raw_type.value).lower()
        else:
            dmg_type = str(raw_type).lower()

        # Эффект работает только для режущего урона (slash)
        if dmg_type != "slash":
            return

        # 2. Получаем текущий резист цели
        current_res = 1.0
        if hasattr(target, "hp_resists"):
            current_res = getattr(target.hp_resists, dmg_type, 1.0)
        elif hasattr(target, "resistances"):
            current_res = target.resistances.get(dmg_type, 1.0)

        # 3. Если резист меньше 1.0, применяем пробитие
        if 0.01 < current_res < 1.0:
            # Увеличиваем резист максимум на 0.25, но не делаем его больше 1.0
            effective_res = min(1.0, current_res + 0.25)

            # Пересчитываем множитель урона кубика для имитации изменения резиста
            res_factor = effective_res / current_res
            ctx.damage_multiplier *= res_factor

            # Добавляем лог для наглядности
            ctx.log.append(f"🌙 **Стигийское лезвие**: Пробив [Res {current_res:.2f} -> {effective_res:.2f}]")

            from logic.character_changing.passives.base_passive import BasePassive
            from logic.context import RollContext

# ==========================================
# 1. Спираль гордыни (Слабость)
# ==========================================
class PassiveSpiralOfPride(BasePassive):
    id = "spiral_of_pride"
    name = "Спираль гордыни"
    description = (
        "Если рассудок менее 20% от максимального, теряет 5 самообладания в конце хода. "
        "Если нет самообладания, получает 4 слабости в конце хода."
    )
    is_active_ability = False

    def on_round_end(self, unit, log_func, **kwargs):
        msgs = []

        # Проверяем условие: рассудок меньше 20% от максимального
        if unit.current_sp < (unit.max_sp * 0.20):
            self_control_stacks = unit.get_status("self_control")

            if self_control_stacks <= 0:
                # Если самообладания нет (0 или меньше), накидываем статус слабости
                unit.add_status("weakness", 4, duration=1)
                msgs.append(
                    "🌪️ **Спираль гордыни**: Рассудок критический, а самообладания нет! Получено 4 Слабости.")
            else:
                # Если самообладание есть, отнимаем до 5 стаков
                loss = min(5, self_control_stacks)
                unit.remove_status("self_control", loss)
                msgs.append(
                    f"🌪️ **Спираль гордыни**: Из-за низкого рассудка потеряно {loss} Самообладания.")

        return msgs

# ==========================================
# 2. Стальночешуйчатая боевая стойка
# ==========================================
class PassiveSteelScaledStance(BasePassive):
    id = "steel_scaled_stance"
    name = "Стальночешуйчатая боевая стойка[鋼鱗戰鬥姿態]"
    description = (
        "Каждые 5 ходов (начиная с третьего хода), получает временное здоровье на 5 ходов, "
        "равное самообладанию/10. Временное здоровье не может превышать 10."
    )
    is_active_ability = False

    def on_round_end(self, unit, log_func, **kwargs):
        msgs = []

        # Читаем счетчик ходов для этой пассивки из памяти (по умолчанию 1)
        current_turn = unit.memory.get("steel_stance_turn", 1)

        # Логика срабатывания: 3-й ход, затем каждые 5 ходов (8, 13, 18 и т.д.)
        if current_turn >= 3 and (current_turn - 3) % 5 == 0:
            self_control_stacks = unit.get_status("self_control")
            temp_hp_to_gain = self_control_stacks // 10  # Целочисленное деление

            if temp_hp_to_gain > 0:
                # В качестве временного здоровья используем статус "barrier"
                current_barrier = unit.get_status("barrier")

                # Рассчитываем так, чтобы суммарный барьер/временное здоровье не превысило 10
                actual_gain = min(temp_hp_to_gain, 10 - current_barrier)

                if actual_gain > 0:
                    unit.add_status("barrier", actual_gain, duration=5)
                    msgs.append(
                        f"🛡️ **Стальночешуйчатая стойка**: Получено {actual_gain} временного здоровья на 5 ходов!")
                else:
                    msgs.append(
                        "🛡️ **Стальночешуйчатая стойка**: Сработала, но временное здоровье уже на максимуме (10).")

        # Увеличиваем счетчик ходов в конце раунда
        unit.memory["steel_stance_turn"] = current_turn + 1

        return msgs