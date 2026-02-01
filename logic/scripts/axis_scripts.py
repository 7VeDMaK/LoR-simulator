from copy import deepcopy

from core.dice import Dice
from core.enums import DiceType
from core.logging import logger, LogLevel


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def _target_has_wincon(target):
    if not target: return False
    return target.get_status("win_condition") > 0


def _consume_wincon(target, amount=1):
    if _target_has_wincon(target):
        target.add_status("win_condition", -amount)
        return True
    return False


# === СКРИПТЫ КАРТ ===

def axis_radiance_clash_win(ctx, params=None):
    """I Сияние: On Clash Win -> 1 WinCon на этот ход (duration 1)"""
    if ctx.target:
        ctx.target.add_status("win_condition", 1, duration=1)
        ctx.log.append("✨ **Сияние**: Win Condition наложен!")


def axis_mcguffin_on_hit(ctx, params=None):
    """Прототип МакГаффина: On Hit -> 1 Перманентный WinCon"""
    if ctx.target:
        # duration 99 эмулирует перманентность
        ctx.target.add_status("win_condition", 1, duration=99)
        ctx.log.append("📦 **МакГаффин**: Перманентный Win Condition!")


def axis_plot_armor_clash(ctx, params=None):
    """
    Прототип Сюжетной Брони: On Clash -> Снять 1 WinCon -> Дебаффы
    """
    if _consume_wincon(ctx.target):
        ctx.target.add_status("fragile", 2)  # Слабость (Weak/Fragile)
        ctx.target.add_status("disarm", 2)  # Разоружение (Strength down?) или Bind? Обычно Disarm это Power Down
        ctx.target.add_status("bind", 2)  # Замедление
        ctx.log.append("🛡️ **Сюжетная Броня**: WinCon поглощен! Враг ослаблен.")


def axis_ex_machina_clash(ctx, params=None):
    """
    Прототип Экс Махины: On Clash -> Снять 1 WinCon -> Бафф союзника (саммона)
    """
    if _consume_wincon(ctx.target):
        # Ищем призванного союзника (полагаем, что это кто-то кроме Аксис)
        # Или можно искать по флагу is_summon, если он есть
        ally_found = False
        team = ctx.source.scene.teams[ctx.source.team_id]  # Получаем команду

        for unit in team:
            if unit != ctx.source and not unit.is_dead():
                # Нашли кого-то (предположительно саммона)
                unit.add_status("strength", 3, duration=2)
                unit.add_status("endurance", 3, duration=2)
                unit.add_status("haste", 3, duration=2)
                ctx.log.append(f"🤖 **Экс Махина**: {unit.name} усилен!")
                ally_found = True
                # Если нужно баффать только одного, делаем break. Если всех саммонов - убираем break.
                break

        if not ally_found:
            ctx.log.append("🤖 **Экс Махина**: Союзники не найдены.")


# === ЛОГИКА СИНЕРГИИ (ЮНИТИ) ===

def axis_small_failures_use(ctx, params=None):
    """
    Мелкие неудачи:
    1. Получает кубики от Меча, Копья и Кулака.
    2. Дает другим картам с Юнити 1 Блок (реализуем как добавление блока СЕБЕ,
       так как влиять на другие карты в руке сложно без пассивки).
       *Альтернатива*: Если мы хотим дать блок ЭТОЙ карте за наличие Юнити.
    """
    card = ctx.card
    source = ctx.source

    # Добавляем кубики от "Меча", "Копья", "Кулака"
    # Создаем новые дайсы. Значения примерные, настройте под баланс.

    # 1. Кубик Меча (Slash) - баффает Аксис
    die_sword = Dice(4, 8, DiceType.SLASH)
    die_sword.scripts = {"on_hit": [{"script_id": "restore_light_1"}]}  # Пример эффекта
    card.dice_list.append(die_sword)

    # 2. Кубик Копья (Pierce)
    die_spear = Dice(4, 8, DiceType.PIERCE)
    card.dice_list.append(die_spear)

    # 3. Кубик Кулака (Blunt)
    die_fist = Dice(4, 8, DiceType.BLUNT)
    card.dice_list.append(die_fist)

    ctx.log.append("🧩 **Мелкие неудачи**: Собраны осколки силы (Меч, Копье, Кулак)!")


def axis_weapon_synergy_use(ctx, params=None):
    """
    Скрипт для Меча, Копья и Кулака.
    Если есть синергия (например, 'Мелкие неудачи' в руке или сыграны), добавляет доп. эффекты.
    Пока реализуем простую версию: они просто сильные карты.
    Если нужно, чтобы они давали друг другу кубики:
    """
    # Здесь можно реализовать проверку истории карт (executed_cards)
    pass


def axis_apply_unity(ctx, params=None):
    """
    Механика Юнити:
    При использовании карты с Юнити, она раздает свой первый кубик всем
    другим картам с флагом 'unity', находящимся в руке.
    """
    source_unit = ctx.source
    played_card = ctx.card

    # 1. Определяем, какой кубик раздавать
    die_to_share = None

    if played_card.id == "axis_minor_setbacks":
        # Мелкие неудачи дают чистый блок 3-6
        die_to_share = Dice(3, 6, DiceType.BLOCK)
        die_to_share.scripts = {}
        log_msg = "🛡️ **Юнити (Неудачи)**: Раздан кубик Блока картам в руке!"

    elif played_card.dice_list:
        # Остальные карты отдают свой первый кубик (с эффектами)
        die_to_share = deepcopy(played_card.dice_list[0])
        log_msg = f"⚔️ **Юнити ({played_card.name})**: Кубик {die_to_share.dtype.name} добавлен картам в руке!"

    if not die_to_share:
        return

    # 2. Ищем цели в руке
    targets_found = False
    if hasattr(source_unit, "hand"):
        for card in source_unit.hand:
            if card == played_card: continue  # Не даем кубик самой себе

            if "unity" in getattr(card, "flags", []):
                # Добавляем копию кубика
                card.dice_list.append(deepcopy(die_to_share))
                targets_found = True

    if targets_found and hasattr(ctx, "log"):
        ctx.log.append(log_msg)