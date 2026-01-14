import sys
import streamlit as st
from contextlib import contextmanager
from io import StringIO

from core.card import Card
from core.enums import CardType
from core.library import Library
from logic.character_changing.augmentations.augmentations import AUGMENTATION_REGISTRY
from logic.clash import ClashSystem
from logic.character_changing.passives import PASSIVE_REGISTRY
from logic.character_changing.talents import TALENT_REGISTRY
from logic.statuses.status_manager import StatusManager


@contextmanager
def capture_output():
    new_out = StringIO()
    old_out = sys.stdout
    try:
        sys.stdout = new_out
        yield new_out
    finally:
        sys.stdout = old_out


def get_teams():
    """Вспомогательная функция для получения команд из сессии."""
    return st.session_state.get('team_left', []), st.session_state.get('team_right', [])


def set_cooldowns(u):
    # Эта проверка гарантирует, что код внутри выполнится только 1 раз за бой
    if not u.memory.get("battle_initialized"):
        u.memory["battle_initialized"] = True

        # [FIX] НЕ сбрасываем словарь принудительно, если он уже существует
        # Это сохраняет кулдауны от предметов, использованных до боя
        if not hasattr(u, "card_cooldowns") or u.card_cooldowns is None:
            u.card_cooldowns = {}

        if getattr(u, 'deck', None):
            for card_id in u.deck:
                card = Library.get_card(card_id)
                if card:
                    # [FIX] Если кулдаун уже есть (от предмета), пропускаем расчет
                    if u.card_cooldowns.get(card_id, 0) > 0:
                        continue

                    elif card.card_type.upper() == CardType.ITEM.name:
                        continue

                    # Обычный расчет начального кулдауна (Tier - 1)
                    initial_cd = max(0, card.tier - 1)
                    if initial_cd > 0:
                        u.card_cooldowns[card_id] = initial_cd

        # === ВЫЗОВ ON_COMBAT_START ===
        l_team, r_team = get_teams()
        opponents = r_team if u in l_team else l_team
        my_allies = l_team if u in l_team else r_team

        def log_start(msg):
            if 'battle_logs' not in st.session_state:
                st.session_state['battle_logs'] = []

            st.session_state['battle_logs'].append({
                "round": "Start",
                "rolls": "Event",
                "details": f"🚩 **{u.name}**: {msg}"
            })

        if hasattr(u, "trigger_mechanics"):
            u.trigger_mechanics("on_combat_start", u, log_start,
                                enemies=opponents, allies=my_allies)


def roll_phase():
    """
        Фаза броска скорости.
        Порядок:
        1. Combat/Round Start (Баффы скорости)
        2. Recalc (Применение скорости)
        3. Roll Speed (Генерация слотов)
        4. Speed Rolled Events (Баффы от слотов)
        5. Recalc (Применение баффов от слотов)
        """
    l_team, r_team = get_teams()
    all_units = l_team + r_team

    # === 1. TRIGGERS (События начала) ===
    for u in all_units:
        u.recalculate_stats()
        set_cooldowns(u)

        # B. Round Start (Каждый раунд)
        opponents = r_team if u in l_team else l_team
        my_allies = l_team if u in l_team else r_team

        # Логгер для событий начала раунда
        def log_round(msg):
            if 'battle_logs' not in st.session_state: st.session_state['battle_logs'] = []
            st.session_state['battle_logs'].append({
                "round": "Round Start",
                "rolls": "Event",
                "details": f"🔄 **{u.name}**: {msg}"
            })

        if hasattr(u, "trigger_mechanics"):
            u.trigger_mechanics("on_round_start", u, log_round,
                                enemies=opponents, allies=my_allies)

    for u in all_units:
        u.recalculate_stats()

        if u.is_staggered():
            u.active_slots = [{
                'speed': 0, 'card': None,
                'target_unit_idx': -1, 'target_slot_idx': -1,
                'stunned': True, 'is_aggro': False
            }]
        else:
            u.roll_speed_dice()
            # Init fields
            for s in u.active_slots:
                s['target_unit_idx'] = -1;
                s['target_slot_idx'] = -1;
                s['is_aggro'] = False;
                s['force_clash'] = False

            # === 3. SPEED ROLLED EVENTS (Баффы от слотов) ===
    for u in all_units:
        opponents = r_team if u in l_team else l_team
        my_allies = l_team if u in l_team else r_team

        def log_speed(msg):
            if 'battle_logs' not in st.session_state: st.session_state['battle_logs'] = []
            st.session_state['battle_logs'].append({
                "round": "Speed Roll", "rolls": "Passive", "details": f"⚡ **{u.name}**: {msg}"
            })

        # Запускаем новый триггер
        if hasattr(u, "trigger_mechanics"):
            u.trigger_mechanics("on_speed_rolled", u, log_speed,
                                enemies=opponents, allies=my_allies)

        for u in all_units:
            u.recalculate_stats()

    # 2. Авто-таргетинг (Auto-Targeting)
    # По умолчанию левые бьют первых живых правых, и наоборот.
    def set_default_targets(source_team, target_team):
        if not target_team: return
        # Индексы живых врагов
        alive_targets = [i for i, t in enumerate(target_team) if not t.is_dead()]

        # Ищем провокаторов
        taunt_targets = [i for i, t in enumerate(target_team) if not t.is_dead() and t.get_status("taunt") > 0]

        # Если есть провокаторы, список целей сужается только до них
        valid_targets = taunt_targets if taunt_targets else alive_targets

        if not valid_targets: return  # Некого бить

        for u in source_team:
            if u.is_dead() or u.is_staggered(): continue
            for slot in u.active_slots:
                # Простое правило: бьем первого живого врага в первый слот
                slot['target_unit_idx'] = valid_targets[0]
                slot['target_slot_idx'] = 0

    set_default_targets(l_team, r_team)
    set_default_targets(r_team, l_team)

    st.session_state['phase'] = 'planning'
    st.session_state['turn_message'] = "🎲 Speed Rolled (Targets Auto-Assigned)"


def step_start():
    """Начало пошагового боя."""
    l_team, r_team = get_teams()
    sys_clash = ClashSystem()

    # Подготовка хода (расчет инициативы, событий начала боя)
    init_logs, actions = sys_clash.prepare_turn(l_team, r_team)

    st.session_state['battle_logs'] = init_logs
    st.session_state['turn_actions'] = actions
    # Множество отыгранных слотов: (unit_name, slot_idx)
    st.session_state['executed_slots'] = set()
    st.session_state['turn_phase'] = 'fighting'
    st.session_state['action_idx'] = 0


def step_next():
    """Выполнение следующего действия в очереди."""
    actions = st.session_state.get('turn_actions', [])
    idx = st.session_state.get('action_idx', 0)

    if idx < len(actions):
        sys_clash = ClashSystem()
        act = actions[idx]
        # Выполняем действие
        logs = sys_clash.execute_single_action(act, st.session_state['executed_slots'])
        st.session_state['battle_logs'].extend(logs)
        st.session_state['action_idx'] += 1

    # Если действия кончились, завершаем раунд
    if st.session_state['action_idx'] >= len(actions):
        step_finish()


def step_finish():
    """Завершение фазы боя."""
    l_team, r_team = get_teams()
    sys_clash = ClashSystem()

    # События конца хода (End of Combat Events)
    end_logs = sys_clash.finalize_turn(l_team + r_team)
    st.session_state['battle_logs'].extend(end_logs)

    finish_round_logic()


def execute_combat_auto():
    """Автоматический расчет всего раунда."""
    l_team, r_team = get_teams()
    sys_clash = ClashSystem()

    with capture_output() as captured:
        logs = sys_clash.resolve_turn(l_team, r_team)

    st.session_state['battle_logs'] = logs
    st.session_state['script_logs'] = captured.getvalue()

    finish_round_logic()


def finish_round_logic():
    """
    Общая логика завершения раунда (очистка, кулдауны, реген).
    """
    l_team, r_team = get_teams()
    all_units = l_team + r_team
    msg = []

    def log_collector(message):
        msg.append(message)

    for u in all_units:
        # 1. Восстановление Stagger после стана
        if u.active_slots and u.active_slots[0].get('stunned'):
            u.current_stagger = u.max_stagger
            msg.append(f"✨ {u.name} recovered!")

        # Контекст союзников
        my_allies = l_team if u in l_team else r_team

        # 2. ЗАПУСК СОБЫТИЙ (Passives, Talents, Augmentations, Weapons, Statuses)
        # trigger_mechanics сам найдет все механики и вызовет у них on_round_end
        if hasattr(u, "trigger_mechanics"):
            u.trigger_mechanics("on_round_end", u, log_collector, allies=my_allies)

        # 3. Жизненный цикл статусов (снижение длительности)
        # Получаем логи (например, от активации Delayed статусов) и добавляем в общий список
        status_logs = StatusManager.process_turn_end(u)
        msg.extend(status_logs)

        # 4. Техническая очистка
        u.tick_cooldowns()
        u.active_slots = []
    st.session_state['round_number'] = st.session_state.get('round_number', 1) + 1
    st.session_state['turn_message'] = " ".join(msg) if msg else "Round Complete."
    st.session_state['phase'] = 'roll'
    st.session_state['turn_phase'] = 'done'


def reset_game():
    """
    Сброс боя. Восстанавливает состояние персонажей до того момента,
    как они вступили в бой (start_of_battle_stats).
    """
    l_team, r_team = get_teams()
    all_units = l_team + r_team

    for u in all_units:
        # 1. Чистим память боя
        u.memory.pop("battle_initialized", None)  # Чтобы сработал on_combat_start заново

        # Сохраняем временные ключи, которые нужны (например, сам снимок)
        saved_stats = u.memory.get('start_of_battle_stats')

        # 2. Восстанавливаем статы из снимка
        if saved_stats:
            u.current_hp = saved_stats['hp']
            u.current_sp = saved_stats['sp']
            u.current_stagger = saved_stats['stagger']
        else:
            # Если снимка нет (легаси), сбрасываем в макс (как было раньше)
            u.current_hp = u.max_hp
            u.current_stagger = u.max_stagger
            u.current_sp = u.max_sp

        # 3. Очистка эффектов
        u.active_buffs = {}
        u.card_cooldowns = {}
        u.cooldowns = {}
        u.recalculate_stats()
        u._status_effects = {}
        u.delayed_queue = []
        u.active_slots = []

    st.session_state['battle_logs'] = []
    st.session_state['script_logs'] = ""
    st.session_state['turn_message'] = "Game Reset to Pre-Battle State. Press 'Roll Initiative'."
    st.session_state['phase'] = 'roll'
    st.session_state['round_number'] = 1


def sync_state_from_widgets(team_left: list, team_right: list):
    """
    Считывает значения из виджетов Streamlit и обновляет объекты юнитов.
    Ключи должны совпадать с теми, что генерируются в simulator_components.py.
    Format ключа: {prefix}_{unit.name}_{type}_{slot_idx}
    """

    def sync_unit(unit, prefix):
        for i, slot in enumerate(unit.active_slots):
            if slot.get('stunned'): continue

            base_key = f"{prefix}_{unit.name}"

            # 1. TARGET (Цель)
            tgt_key = f"{base_key}_tgt_{i}"
            if tgt_key in st.session_state:
                val = st.session_state[tgt_key]
                # val format: "1:1 | Label" OR "None" (где 1:1 это UI индексы)

                if val == "None":
                    slot['target_unit_idx'] = -1
                    slot['target_slot_idx'] = -1
                else:
                    try:
                        # Парсим "1:1 | Name..."
                        parts = val.split('|')[0].strip().split(':')
                        # [FIX] Вычитаем 1 при сохранении в структуру юнита
                        slot['target_unit_idx'] = int(parts[0]) - 1
                        slot['target_slot_idx'] = int(parts[1]) - 1
                    except:
                        pass  # Ошибка парсинга

            # 2. CARD (Карта)
            card_key = f"{base_key}_card_{i}"
            if card_key in st.session_state:
                val = st.session_state[card_key]
                if isinstance(val, Card):
                    slot['card'] = val
                elif val is None:
                    slot['card'] = None

            # 3. AGGRO (Перехват)
            aggro_key = f"{base_key}_aggro_{i}"
            if aggro_key in st.session_state:
                slot['is_aggro'] = st.session_state[aggro_key]

    # Синхронизируем Левую команду (prefix l_i)
    for i, u in enumerate(team_left):
        sync_unit(u, f"l_{i}")

    # Синхронизируем Правую команду (prefix r_i)
    for i, u in enumerate(team_right):
        sync_unit(u, f"r_{i}")


def precalculate_interactions(team_left: list, team_right: list):
    """
    Финальная версия с визуализацией сломанных кубиков (Speed Break).
    """
    ClashSystem.calculate_redirections(team_left, team_right)
    ClashSystem.calculate_redirections(team_right, team_left)

    def update_ui_status(my_team, enemy_team):
        for my_idx, me in enumerate(my_team):
            for my_slot_idx, my_slot in enumerate(me.active_slots):

                if my_slot.get('stunned'):
                    my_slot['ui_status'] = {"text": "ОГЛУШЕН", "icon": "❌", "color": "gray"}
                    continue

                # Данные о МОЕЙ цели
                t_u_idx = my_slot.get('target_unit_idx', -1)
                t_s_idx = my_slot.get('target_slot_idx', -1)
                is_friendly = my_slot.get('is_ally_target', False)
                target_team_list = my_team if is_friendly else enemy_team

                # --- 1. ПРОВЕРКА: ПЕРЕХВАТИЛИ ЛИ МЕНЯ? ---
                intercepted_by = None
                if not is_friendly:
                    for e_idx, enemy in enumerate(enemy_team):
                        if enemy.is_dead(): continue
                        for e_s_idx, e_slot in enumerate(enemy.active_slots):
                            if e_slot.get('force_clash'):
                                # Враг перехватывает именно этот слот
                                if e_slot.get('target_unit_idx') == my_idx and \
                                        e_slot.get('target_slot_idx') == my_slot_idx:

                                    # Если я тоже целюсь в него в этот слот - это Взаимно, не перехват
                                    if t_u_idx == e_idx and t_s_idx == e_s_idx:
                                        continue

                                    intercepted_by = (enemy, e_slot, e_s_idx)
                                    break
                        if intercepted_by: break

                if intercepted_by:
                    enemy, e_slot, e_s_idx = intercepted_by

                    # === ПРОВЕРКА: Ломает ли враг меня (даже пустым слотом с талантом) ===
                    is_broken = False

                    spd_diff = e_slot['speed'] - my_slot['speed']
                    if spd_diff >= 8:
                        # Условия поломки:
                        # 1. Галочка (Intent) у врага включена (по умолчанию True)
                        e_intent = e_slot.get('destroy_on_speed', True)

                        # 2. У врага есть карта ИЛИ Талант Behavior Study
                        e_has_card = e_slot.get('card') is not None
                        e_has_talent = "behavior_study" in enemy.talents  # Упрощенная проверка для UI

                        if e_intent and (e_has_card or e_has_talent):
                            is_broken = True

                    if is_broken:
                        my_slot['ui_status'] = {
                            "text": f"🚫 BROKEN vs {enemy.name} [S{e_s_idx + 1}] | Speed Gap {spd_diff}",
                            "icon": "💥",
                            "color": "red"
                        }
                    else:
                        my_slot['ui_status'] = {
                            "text": f"CLASH vs {enemy.name} [S{e_s_idx + 1}] | Перехвачен ({my_slot['speed']} < {e_slot['speed']})",
                            "icon": "⚠️",
                            "color": "orange"
                        }
                    continue

                # --- ДАЛЕЕ СТАНДАРТНАЯ ЛОГИКА (Если не перехвачен) ---
                if t_u_idx == -1 or t_u_idx >= len(target_team_list):
                    my_slot['ui_status'] = {"text": "НЕТ ЦЕЛИ", "icon": "⛔", "color": "gray"}
                    continue

                target_unit = target_team_list[t_u_idx]
                if target_unit.is_dead():
                    my_slot['ui_status'] = {"text": "ЦЕЛЬ МЕРТВА", "icon": "💀", "color": "gray"}
                    continue

                tgt_slot_label = "?"
                target_slot = None
                tgt_spd = 0

                if t_s_idx != -1 and t_s_idx < len(target_unit.active_slots):
                    target_slot = target_unit.active_slots[t_s_idx]
                    tgt_spd = target_slot['speed']
                    tgt_slot_label = f"S{t_s_idx + 1}"

                if is_friendly:
                    my_slot['ui_status'] = {"text": f"BUFF -> {target_unit.name}", "icon": "✨", "color": "green"}
                    continue

                # === ПРОВЕРКА: ЛОМАЮ ЛИ Я ВРАГА? ===
                # Это может произойти и в One Sided, и во взаимном Clash
                # Условия: Моя скорость > Врага на 8, Галочка Break, Карта или Талант

                i_break_enemy = False
                if target_slot:
                    my_diff = my_slot['speed'] - tgt_spd
                    if my_diff >= 8:
                        my_intent = my_slot.get('destroy_on_speed', True)
                        my_has_card = my_slot.get('card') is not None
                        my_has_talent = "behavior_study" in me.talents

                        if my_intent and (my_has_card or my_has_talent):
                            i_break_enemy = True

                # === ОПРЕДЕЛЕНИЕ СТАТУСА ===
                is_mutual = False
                if target_slot:
                    if target_slot.get('target_unit_idx') == my_idx and \
                            target_slot.get('target_slot_idx') == my_slot_idx:
                        is_mutual = True

                # Приоритет отображения:
                # 1. Если я ломаю врага (это круто) -> SPEED BREAK
                # 2. Если я проигрываю взаимный клэш и меня ломают -> BROKEN
                # 3. Обычный Clash / One Sided

                enemy_breaks_me_mutual = False
                if is_mutual:
                    # Проверяем, не ломает ли он меня в ответ (взаимный клэш)
                    diff_rev = tgt_spd - my_slot['speed']
                    if diff_rev >= 8:
                        e_intent = target_slot.get('destroy_on_speed', True)
                        e_has = target_slot.get('card') or ("behavior_study" in target_unit.talents)
                        if e_intent and e_has:
                            enemy_breaks_me_mutual = True

                if i_break_enemy:
                    my_slot['ui_status'] = {
                        "text": f"✨ SPEED BREAK -> {target_unit.name} | Уничтожение ({my_slot['speed']} >> {tgt_spd})",
                        "icon": "⚡",
                        "color": "green"
                    }
                    # Если у меня нет карты, но я ломаю талантом - это валидное действие
                    continue

                    # Если нет карты и я НЕ ломаю врага -> я ничего не делаю
                if not my_slot.get('card'):
                    my_slot['ui_status'] = {"text": "НЕТ КАРТЫ", "icon": "⛔", "color": "gray"}
                    continue

                if enemy_breaks_me_mutual:
                    my_slot['ui_status'] = {
                        "text": f"🚫 BROKEN vs {target_unit.name} | Взаимно, он быстрее",
                        "icon": "💥",
                        "color": "red"
                    }

                elif my_slot.get('force_onesided'):
                    my_slot['ui_status'] = {
                        "text": f"ONE SIDED (Провал) -> {target_unit.name} | Слаб",
                        "icon": "🐌",
                        "color": "orange"
                    }

                elif my_slot.get('force_clash'):
                    # Я кого-то перехватил
                    my_slot['ui_status'] = {
                        "text": f"CLASH vs {target_unit.name} [{tgt_slot_label}] | Перехват!",
                        "icon": "⚡",
                        "color": "red"
                    }

                elif is_mutual:
                    # Взаимная атака (без перехвата, просто совпали слоты)
                    my_slot['ui_status'] = {
                        "text": f"CLASH vs {target_unit.name} [{tgt_slot_label}] | Взаимно",
                        "icon": "⚔️",
                        "color": "red"
                    }

                else:
                    reason = "Свободно"
                    if target_slot and target_slot.get('stunned'):
                        reason = "Враг оглушен"
                    elif target_slot:
                        reason = "Враг занят/игнор"

                    my_slot['ui_status'] = {
                        "text": f"ATK -> {target_unit.name} [{tgt_slot_label}] | {reason}",
                        "icon": "🏹",
                        "color": "blue"
                    }

    update_ui_status(team_left, team_right)
    update_ui_status(team_right, team_left)

def use_item_action(unit, card):
    """
    Мгновенно применяет эффект предмета.
    """

    current_cd = unit.card_cooldowns.get(card.id, 0)
    if current_cd > 0:
        st.toast(f"Предмет {card.name} на перезарядке ({current_cd} х.)!", icon="⏳")
        return

    msg = f"💊 **{unit.name}** uses **{card.name}**!"
    item_logs = [msg]

    # Используем process_card_self_scripts, передавая item_logs как custom_log_list
    # target=None, так как предметы обычно на себя (self). Если нужен таргет, придется усложнять UI.
    # Пока считаем, что таблетки пьют сами.
    from logic.mechanics.scripts import process_card_self_scripts
    process_card_self_scripts("on_use", unit, None, logs=None, custom_log_list=item_logs, card_override=card)

    cooldown = max(0, card.tier - 1)
    if cooldown > 0:
        unit.card_cooldowns[card.id] = cooldown
        # Можно добавить лог про кд, если нужно, но обычно это визуально видно
        # item_logs.append(f"(Cooldown: {cooldown})")
    # Добавляем в общий лог боя
    st.session_state['battle_logs'].append({
        "round": "Item",
        "rolls": "Consumable",
        "details": item_logs
    })

def render_inventory(unit, unit_key):
    """
    Рендерит секцию инвентаря с предметами (CardType.ITEM).
    """
    # Фильтруем карты в колоде, оставляя только предметы
    inventory_cards = []
    if unit.deck:
        for cid in unit.deck:
            card = Library.get_card(cid)
            # Проверяем тип
            if card and str(card.card_type).lower() == "item":
                inventory_cards.append(card)

    if not inventory_cards:
        return

    with st.expander("🎒 Inventory (Consumables)", expanded=False):
        for card in inventory_cards:
            btn_key = f"use_item_{unit_key}_{card.id}"
            desc = card.description if card.description else "No description"

            # Кнопка использования
            if st.button(f"💊 {card.name}", key=btn_key, help=desc, use_container_width=True):
                from ui.simulator.simulator_logic import use_item_action
                use_item_action(unit, card)
                st.rerun()