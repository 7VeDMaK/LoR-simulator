import sys
import streamlit as st
from contextlib import contextmanager
from io import StringIO

from core.card import Card
from logic.clash import ClashSystem
from logic.passives import PASSIVE_REGISTRY
from logic.talents import TALENT_REGISTRY
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


def roll_phase():
    """
    Фаза броска скорости.
    Инициализирует слоты для всех юнитов в обеих командах.
    """
    l_team, r_team = get_teams()
    all_units = l_team + r_team

    # 1. Пересчет статов и бросок скорости
    for u in all_units:
        u.recalculate_stats()

        if u.is_staggered():
            # Оглушенный юнит получает 1 слот с 0 скорости
            u.active_slots = [{
                'speed': 0, 'card': None,
                'target_unit_idx': -1, 'target_slot_idx': -1,
                'stunned': True, 'is_aggro': False
            }]
        else:
            u.roll_speed_dice()
            # Инициализация полей цели для каждого слота
            for s in u.active_slots:
                s['target_unit_idx'] = -1
                s['target_slot_idx'] = -1
                s['is_aggro'] = False
                s['force_clash'] = False

    # 2. Авто-таргетинг (Auto-Targeting)
    # По умолчанию левые бьют первых живых правых, и наоборот.
    def set_default_targets(source_team, target_team):
        if not target_team: return
        # Индексы живых врагов
        alive_targets = [i for i, t in enumerate(target_team) if not t.is_dead()]

        if not alive_targets: return  # Некого бить

        for u in source_team:
            if u.is_dead() or u.is_staggered(): continue
            for slot in u.active_slots:
                # Простое правило: бьем первого живого врага в первый слот
                slot['target_unit_idx'] = alive_targets[0]
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
    """Общая логика завершения раунда (очистка, кулдауны, реген)."""
    l_team, r_team = get_teams()
    all_units = l_team + r_team
    msg = []

    def log_collector(message):
        msg.append(message)

    for u in all_units:
        # Восстановление Stagger, если был оглушен
        if u.active_slots and u.active_slots[0].get('stunned'):
            u.current_stagger = u.max_stagger
            msg.append(f"✨ {u.name} recovered!")

        # Определяем союзников для передачи в таланты
        my_allies = l_team if u in l_team else r_team

        # Пассивки и Таланты (On Round End)
        for pid in u.passives:
            if pid in PASSIVE_REGISTRY:
                PASSIVE_REGISTRY[pid].on_round_end(u, log_collector, allies=my_allies)
        for pid in u.talents:
            if pid in TALENT_REGISTRY:
                TALENT_REGISTRY[pid].on_round_end(u, log_collector, allies=my_allies)
        # Статусы (снижение длительности, эффекты конца хода)
        StatusManager.process_turn_end(u)

        # Кулдауны
        u.tick_cooldowns()

        # Очистка слотов
        u.active_slots = []

    st.session_state['turn_message'] = " ".join(msg) if msg else "Round Complete."
    st.session_state['phase'] = 'roll'
    st.session_state['turn_phase'] = 'done'


def reset_game():
    """Полный сброс состояния боя."""
    l_team, r_team = get_teams()
    all_units = l_team + r_team

    for u in all_units:
        u.recalculate_stats()
        u.current_hp = u.max_hp
        u.current_stagger = u.max_stagger
        u.current_sp = u.max_sp
        u._status_effects = {}
        u.delayed_queue = []
        u.active_slots = []
        u.cooldowns = {}
        u.active_buffs = {}
        u.memory = {}

    st.session_state['battle_logs'] = []
    st.session_state['script_logs'] = ""
    st.session_state['turn_message'] = "Game Reset."
    st.session_state['phase'] = 'roll'


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
                # val format: "u_idx:s_idx | Label" OR "None"

                if val == "None":
                    slot['target_unit_idx'] = -1
                    slot['target_slot_idx'] = -1
                else:
                    try:
                        # Парсим "0:1 | Name..."
                        parts = val.split('|')[0].strip().split(':')
                        slot['target_unit_idx'] = int(parts[0])
                        slot['target_slot_idx'] = int(parts[1])
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
    Обновляет UI-статусы слотов (Clash/Attack/No Target).
    Вызывается перед отрисовкой страницы.
    """
    # Сначала считаем логические перенаправления
    ClashSystem.calculate_redirections(team_left, team_right)
    ClashSystem.calculate_redirections(team_right, team_left)

    def update_ui_status(my_team, enemy_team):
        for my_idx, me in enumerate(my_team):
            for my_slot_idx, my_slot in enumerate(me.active_slots):
                if my_slot.get('stunned'):
                    my_slot['ui_status'] = {"text": "STAGGERED", "icon": "❌", "color": "gray"}
                    continue

                t_u_idx = my_slot.get('target_unit_idx', -1)
                t_s_idx = my_slot.get('target_slot_idx', -1)

                # Нет цели
                if t_u_idx == -1 or t_u_idx >= len(enemy_team):
                    my_slot['ui_status'] = {"text": "NO TARGET", "icon": "⛔", "color": "gray"}
                    continue

                target_unit = enemy_team[t_u_idx]

                if target_unit.is_dead():
                    my_slot['ui_status'] = {"text": "DEAD TARGET", "icon": "💀", "color": "gray"}
                    continue

                # === ЛОГИКА ОТОБРАЖЕНИЯ ===

                # 1. Если этот слот был ПЕРЕНАПРАВЛЕН (проиграл конкуренцию за Clash)
                if my_slot.get('force_onesided'):
                    # Он бьет, но безответно, потому что слот врага занят кем-то другим
                    my_slot['ui_status'] = {
                        "text": f"One Sided > {target_unit.name}",
                        "icon": "↪️",
                        "color": "orange"
                    }
                    continue

                # 2. Если этот слот ВЫИГРАЛ право на Clash (force_clash)
                # Или если это обычный Clash без конкуренции
                is_clash = False

                if t_s_idx != -1 and t_s_idx < len(target_unit.active_slots):
                    target_slot = target_unit.active_slots[t_s_idx]

                    # Проверка: Враг тоже целится в меня? (В меня лично или в мой слот?)
                    # В базовой логике Clash - это взаимная атака.
                    # Но если я перехватил (force_clash), то Clash гарантирован, даже если враг бил другого.

                    if my_slot.get('force_clash'):
                        is_clash = True
                    elif target_slot.get('target_unit_idx') == my_idx and \
                            target_slot.get('target_slot_idx') == my_slot_idx:
                        is_clash = True

                if is_clash:
                    # Если мы перехватили (Aggro), добавим значок
                    icon = "⚔️"
                    text = f"CLASH > {target_unit.name}"
                    if my_slot.get('force_clash'):
                        icon = "🔥"  # Значок успешного перехвата
                        text += ""

                    my_slot['ui_status'] = {"text": text, "icon": icon, "color": "red"}
                else:
                    my_slot['ui_status'] = {"text": f"ATK > {target_unit.name}", "icon": "🏹", "color": "orange"}

    update_ui_status(team_left, team_right)
    update_ui_status(team_right, team_left)


def use_item_action(unit, card):
    """
    Мгновенно применяет эффект предмета.
    """
    # Логируем действие
    msg = f"💊 **{unit.name}** uses **{card.name}**!"

    # Запускаем скрипты карты (триггер "on_use")
    # Создаем список для логов конкретно этого действия
    item_logs = [msg]

    # Используем process_card_self_scripts, передавая item_logs как custom_log_list
    # target=None, так как предметы обычно на себя (self). Если нужен таргет, придется усложнять UI.
    # Пока считаем, что таблетки пьют сами.
    from logic.mechanics.scripts import process_card_self_scripts
    process_card_self_scripts("on_use", unit, None, logs=None, custom_log_list=item_logs, card_override=card)
    # Добавляем в общий лог боя
    st.session_state['battle_logs'].append({
        "round": "Item",
        "rolls": "Consumable",
        "details": item_logs
    })