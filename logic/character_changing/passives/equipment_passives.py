# logic/passives/equipment_passives.py
from logic.character_changing.passives.base_passive import BasePassive
from core.enums import DiceType


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
        else:
            ctx.log.append("🔇 **Click**: Пусто...")


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


# === ОБНОВЛЕННЫЙ ГАНИТАР ===
class PassiveGanitar(BasePassive):
    id = "mech_ganitar"
    name = "Мех: Дуэльный Ганитар [WIP]"
    description = "Активно (1 раз в бой): Отключает пассивные способности ВСЕХ врагов."
    is_active_ability = True
    cooldown = 99

    def on_combat_start(self, unit, log_func, **kwargs):
        # 1. Запоминаем список врагов в начале боя
        enemies = kwargs.get("enemies", [])
        if not enemies:
            # Фолбек, если список не пришел (например в старых версиях движка)
            op = kwargs.get("opponent")
            if op: enemies = [op]

        # Сохраняем в память юнита, чтобы кнопка Activate могла их достать
        unit.memory['cached_enemies'] = enemies

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        # Достаем врагов из памяти
        enemies = unit.memory.get('cached_enemies', [])

        if not enemies:
            if log_func: log_func("❌ Ганитар: Цели не найдены.")
            return False

        count = 0
        for enemy in enemies:
            if not enemy.is_dead():
                # Накладываем статус блокировки
                enemy.add_status("passive_lock", 1, duration=99)
                count += 1

        unit.cooldowns[self.id] = self.cooldown

        if log_func:
            log_func(f"📿 **Ганитар**: Активирован! Пассивки отключены у {count} врагов.")
        return True


# === ЛИМАГАН ===
class PassiveLimagun(BasePassive):
    id = "mech_limagun"
    name = "Мех: ЛИМАГАН"
    description = "+666% урона по целям с именем 'Лима'."

    def on_hit(self, ctx, **kwargs):
        stack = kwargs.get("stack", 0)
        if not ctx.target: return

        name = ctx.target.name.lower()
        if "лима" in name or "lima" in name:
            ctx.damage_multiplier += 6.66
            ctx.log.append("🚪 **ЛИМАГАН**: x6.66 Урона по Лиме!")

