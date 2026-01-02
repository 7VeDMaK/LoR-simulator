# logic/card_scripts.py
import math
import random
import streamlit as st  # <--- ВАЖНО: Добавлен импорт Streamlit
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logic.context import RollContext


def apply_status(context: 'RollContext', params: dict):
    status_name = params.get("status")
    stack = params.get("stack", 1)
    target_type = params.get("target", "target")
    duration = int(params.get("duration", 1))

    unit_to_affect = context.target if target_type == "target" else context.source
    if not unit_to_affect: return

    # === ИММУНИТЕТ ===
    if unit_to_affect.get_status("red_lycoris") > 0 and status_name not in ["red_lycoris"]:
        context.log.append(f"🚫 {unit_to_affect.name} Immune to {status_name}")
        return

    # Хак для Дыма (Smoke) - он вечный
    if status_name == "smoke": duration = 99

    targets = []
    if target_type == "self":
        targets.append(context.source)
    elif target_type == "target":
        targets.append(context.target)
    elif target_type == "all":
        if context.source: targets.append(context.source)
        if context.target: targets.append(context.target)



    if not status_name: return

    for unit in targets:
        if not unit: continue
        success, msg = unit.add_status(status_name, stack, duration=duration)

        if success:
            # Обычный лог успеха
            context.log.append(f"🧪 **{unit.name}**: +{stack} {status_name.capitalize()}")
        else:
            # Если заблокировано и есть сообщение (например, от Clarity)
            if msg:
                context.log.append(f"🛡️ **{unit.name}**: {msg}")


def steal_status(context: 'RollContext', params: dict):
    status_name = params.get("status")
    if not status_name: return
    thief, victim = context.source, context.target
    if not thief or not victim: return

    amount = victim.get_status(status_name)
    if amount > 0:
        victim.remove_status(status_name, amount)
        duration = 99 if status_name == "smoke" else 1
        thief.add_status(status_name, amount, duration=duration)

        # БЫЛО: ✋ **Steal**: 5 Smoke from 🎯 → 👤
        # СТАЛО: ✋ **Lilit** stole 5 Smoke from **Roland**
        context.log.append(f"✋ **{thief.name}** stole {amount} {status_name} from **{victim.name}**")
    else:
        # Можно добавить лог неудачи, если нужно
        pass


# === НОВЫЙ СКРИПТ ===
def apply_status_by_roll(context: 'RollContext', params: dict):
    """
    Накладывает статус в количестве, равном значению броска кубика.
    Используется для Зиккурата (Блок -> Барьер).
    """
    status_name = params.get("status", "barrier")
    target_type = params.get("target", "self")

    unit = context.source if target_type == "self" else context.target

    if unit:
        # Берем итоговое значение броска (с учетом силы и бонусов)
        amount = context.final_value

        if amount > 0:
            unit.add_status(status_name, amount, duration=2)  # Барьер обычно висит раунд-два
            context.log.append(f"🛡️ {status_name.capitalize()} +{amount} (Roll) to {unit.name}")

def multiply_status(context: 'RollContext', params: dict):
    status_name = params.get("status")
    multiplier = float(params.get("multiplier", 2.0))
    target_type = params.get("target", "target")
    unit = context.target if target_type == "target" else context.source
    if not unit: return

    current = unit.get_status(status_name)
    if current > 0:
        add = int(current * (multiplier - 1))
        duration = 99 if status_name == "smoke" else 1
        unit.add_status(status_name, add, duration=duration)

        context.log.append(f"✖️ **{unit.name}**: {status_name} x{multiplier} (+{add})")


def deal_custom_damage(context: 'RollContext', params: dict):
    dmg_type = params.get("type", "stagger")
    scale = float(params.get("scale", 1.0))
    target_mode = params.get("target", "target")
    prevent_std = params.get("prevent_standard", False)

    base = int(context.final_value * scale)
    targets = []
    if target_mode == "target":
        targets.append(context.target)
    elif target_mode == "self":
        targets.append(context.source)
    elif target_mode == "all":
        if context.source: targets.append(context.source)
        if context.target: targets.append(context.target)

    for unit in targets:
        if not unit: continue
        if dmg_type == "stagger":
            unit.current_stagger -= base
            context.log.append(f"😵 **{unit.name}**: -{base} Stagger")
        elif dmg_type == "hp":
            unit.current_hp -= base
            context.log.append(f"💥 **{unit.name}**: -{base} HP")

    if prevent_std:
        context.damage_multiplier = 0.0


def restore_hp(context: 'RollContext', params: dict):
    amount = params.get("amount", 0)
    target_type = params.get("target", "self")
    unit = context.source if target_type == "self" else context.target

    if unit:
        try:
            # Пытаемся передать source_unit, если метод обновлен
            heal = unit.heal_hp(amount)
        except TypeError:
            # Если нет, по старинке
            heal = unit.heal_hp(amount)

        # БЫЛО: 💚 Heal +5 HP
        # СТАЛО: 💚 **Roland**: Healed +5 HP
        context.log.append(f"💚 **{unit.name}**: Healed +{heal} HP")


def restore_sp(context: 'RollContext', params: dict):
    amount = int(params.get("amount", 0))
    unit = context.source

    if amount > 0:
        if hasattr(unit, 'restore_sp'):
            actual = unit.restore_sp(amount)
        else:
            # Фолбек
            old = unit.current_sp
            unit.current_sp = min(unit.max_sp, unit.current_sp + amount)
            actual = unit.current_sp - old

        context.log.append(f"🧠 **{unit.name}**: Restored +{actual} SP")


def add_hp_damage(context: 'RollContext', params: dict):
    """Добавляет к броску урон, равный % от Макс. HP (округление вверх)."""
    pct = params.get("percent", 0.05)  # 5% по умолчанию
    unit = context.source

    # math.ceil - округление всегда в большую сторону
    bonus = math.ceil(unit.max_hp * pct)

    # Добавляем бонус к значению кубика в контексте
    # Так как мы вызываем это в on_hit, это увеличит итоговый урон
    context.modify_power(bonus, "HP Scaling")


def self_harm_percent(context: 'RollContext', params: dict):
    """Наносит урон самому себе в % от ТЕКУЩЕГО здоровья."""
    pct = params.get("percent", 0.025)  # 2.5% по умолчанию
    unit = context.source

    # Урон от текущего HP
    dmg = int(unit.current_hp * pct)
    if dmg > 0:
        unit.current_hp -= dmg
        context.log.append(f"💔 Отдача: -{dmg} HP ({pct * 100}%)")


def add_luck_bonus_roll(context: 'RollContext', params: dict):
    """
    Повторяет бросок за каждые X удачи и добавляет к силе.
    """
    unit = context.source
    die = context.dice
    if not die: return  # Защита

    # Параметры из редактора
    step = params.get("step", 10)  # За каждые 10 удачи
    limit = params.get("limit", 7)  # Лимит повторений

    # Получаем Удачу
    luck_val = unit.skills.get("luck", 0)

    # Считаем количество доп. бросков
    extra_count = luck_val // step

    # Применяем лимит
    if extra_count > limit:
        extra_count = limit

    if extra_count > 0:
        total_bonus = 0
        rolls_history = []

        # Симулируем повторные броски того же кубика
        for _ in range(extra_count):
            r = random.randint(die.min_val, die.max_val)
            total_bonus += r
            rolls_history.append(str(r))

        # Применяем бонус
        context.modify_power(total_bonus, f"Luck x{extra_count}")

        # Красивый лог
        context.log.append(f"🍀 Luck Series: +{total_bonus} ({', '.join(rolls_history)})")


# === НОВЫЕ СКРИПТЫ ===

def pat_shoulder(context: 'RollContext', params: dict):
    mode = params.get("mode", "off")  # def или off
    amount = params.get("amount", 6)
    source = context.source

    # Теперь мы ожидаем, что target уже передан через UI
    target_unit = context.target

    # Фолбек, если цель не передана (например, в тестах или старом коде)
    if not target_unit:
        my_team = []
        if 'team_left' in st.session_state and source in st.session_state['team_left']:
            my_team = st.session_state['team_left']
        elif 'team_right' in st.session_state and source in st.session_state['team_right']:
            my_team = st.session_state['team_right']

        valid_allies = [u for u in my_team if not u.is_dead() and u != source]
        target_unit = random.choice(valid_allies) if valid_allies else source

    context.log.append(f"🤝 **{source.name}** выбрал **{target_unit.name}**.")

    if mode == "def":
        target_unit.add_status("endurance", amount, duration=1)
        target_unit.add_status("protection", 1, duration=1)  # Немного защиты сверху
        context.log.append(f"🛡️ Бафф: +{amount} к Защитным кубикам (Endurance).")

    elif mode == "off":
        target_unit.add_status("strength", amount, duration=1)
        context.log.append(f"⚔️ Бафф: +{amount} к Атакующим кубикам (Strength).")


def eloquence_clash(context: 'RollContext', params: dict):
    """
    Добавляет к броску разницу в красноречии.
    """
    if not context.target: return

    my_elo = context.source.skills.get("eloquence", 0)
    # Пытаемся получить Elo врага. Если это моб, у него может не быть скиллов, тогда 0.
    target_elo = getattr(context.target, "skills", {}).get("eloquence", 0)

    diff = my_elo - target_elo

    if diff > 0:
        context.modify_power(diff, f"Eloquence Diff ({my_elo}-{target_elo})")
    elif diff < 0:
        # Опционально: штраф, если у врага язык подвешен лучше?
        # В описании карты сказано "Увеличивает силу... на разницу". Обычно в плюс.
        pass

SCRIPTS_REGISTRY = {
    "apply_status": apply_status,
    "restore_hp": restore_hp,
    "restore_sp": restore_sp,
    "steal_status": steal_status,
    "multiply_status": multiply_status,
    "deal_custom_damage": deal_custom_damage,
    "add_hp_damage": add_hp_damage,       # <--- Регистрируем
    "self_harm_percent": self_harm_percent,
    "apply_status_by_roll": apply_status_by_roll,
    "add_luck_bonus_roll": add_luck_bonus_roll,
    "pat_shoulder": pat_shoulder,       # <--- Новое
    "eloquence_clash": eloquence_clash, # <--- Новое
}