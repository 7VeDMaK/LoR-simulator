from core.enums import DiceType
from logic.character_changing.passives.base_passive import BasePassive


# ==========================================
# 4 и 6: Кадильница (Медик + Курильщик)
# ==========================================
class TalentCenser(BasePassive):
    id = "censer"
    name = "Кадильница"
    description = (
        "Связь (Медик + Курильщик). Требуется 5-й уровень в обеих ветках.\n"
        "Активно (КД 8): Тратит весь дым (2 Дыма -> 1 HP). Лечит до 5 союзников.\n"
        "Пассивно: Рецепт исцеляющего табака."
    )
    is_active_ability = True
    cooldown = 8

    def activate(self, unit, log_func, **kwargs):
        if unit.cooldowns.get(self.id, 0) > 0: return False

        smoke = unit.get_status("smoke")
        if smoke < 2:
            if log_func: log_func("💨 Недостаточно дыма для Кадильницы.")
            return False

        # Конвертация 2 к 1
        heal_amount = smoke // 2

        # Тратим дым
        unit.remove_status("smoke", smoke)

        # Лечим (в симуляторе лечим себя, в лог пишем про союзников)
        unit.heal_hp(heal_amount)

        unit.cooldowns[self.id] = self.cooldown
        if log_func: log_func(f"🚬 **Кадильница**: Потрачено {smoke} дыма -> Исцеление {heal_amount} HP (АоЕ).")
        return True


# ==========================================
# 5 и 3: Пылкая оборона (Берсерк + Танк)
# ==========================================
class TalentArdentDefense(BasePassive):
    id = "ardent_defense"
    name = "Пылкая оборона"
    description = (
        "Связь (Берсерк + Неутомимый).\n"
        "Если активна Ярость или Полная концентрация: Защитные кости +2."
    )
    is_active_ability = False

    def on_roll(self, ctx):
        unit = ctx.source
        # Проверяем статусы берсерка
        # (Ярость обычно вешает бафф berserker_rage или raging_fury, концентрация full_concentration)
        has_rage = (unit.active_buffs.get("berserker_rage", 0) > 0 or
                    unit.active_buffs.get("full_concentration", 0) > 0)

        if has_rage:
            if ctx.dice.dtype in [DiceType.BLOCK, DiceType.EVADE]:
                ctx.modify_power(2, "Ardent Defense")


# ==========================================
# 9 и 12: Ассортимент Хитмана (Тень + Технолог)
# ==========================================
class TalentHitmanAssortment(BasePassive):
    id = "hitman_assortment"
    name = "Ассортимент Хитмана"
    description = (
        "Связь (Тень + Технолог).\n"
        "Рецепты: Сканер органики, Ловушки быстрой расстановки, Компактор пространства."
    )
    is_active_ability = False


# ==========================================
# 10 и 11 А: Термическая энергия
# ==========================================
class TalentThermalEnergy(BasePassive):
    id = "thermal_energy"
    name = "Термическая энергия (А)"
    description = (
        "Связь (Энергия + Пламя).\n"
        "За каждые 5 урона от Горения (полученного) -> +1 Заряд."
    )
    is_active_ability = False

    def on_take_damage(self, unit, amount, source, **kwargs):
        # 1. Извлекаем функцию логгирования (вернет None, если её нет)
        log_func = kwargs.get("log_func")
        dmg_type = kwargs.get("dmg_type")
        # Предположим dmg_type == "burn" (нужна поддержка в системе статусов)
        if dmg_type == "burn" and amount > 0:
            charge_gain = amount // 5
            if charge_gain > 0:
                unit.add_status("charge", charge_gain, duration=99)
                if log_func: log_func(f"⚡ **Термическая энергия**: {amount} урона огнем -> +{charge_gain} Заряда.")


# ==========================================
# 10 и 11 Б: Обжигающее мастерство
# ==========================================
class TalentScorchingMastery(BasePassive):
    id = "scorching_mastery"
    name = "Обжигающее мастерство (Б)"
    description = (
        "Связь (Энергия + Пламя).\n"
        "Каждая 3-я победа в столкновении -> 4 Горения (Вам или Врагу)."
    )
    is_active_ability = False

    def on_clash_win(self, ctx):
        # Счетчик
        count = ctx.source.memory.get("scorching_mastery_count", 0) + 1
        ctx.source.memory["scorching_mastery_count"] = count

        if count % 3 == 0:
            # Накладываем горение. По умолчанию врагу, так выгоднее.
            if ctx.target:
                ctx.target.add_status("burn", 4, duration=3)
                ctx.log.append("🔥 **Обжигающее мастерство**: Враг получил 4 Горения (3-я победа).")