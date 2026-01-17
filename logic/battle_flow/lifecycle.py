import random
from logic.battle_flow.targeting import calculate_redirections
from logic.battle_flow.priorities import get_action_priority


def prepare_turn(engine, team_left: list, team_right: list):
    """
    Фаза 1: Сбор всех запланированных действий (Actions) и сортировка по скорости/приоритету.
    """
    engine.logs = []
    report = []
    all_units = team_left + team_right

    # Рассчитываем перехваты для обеих команд
    calculate_redirections(team_left, team_right)
    calculate_redirections(team_right, team_left)

    actions = []

    def collect_actions(source_team, target_team, is_left_side):
        for u_idx, unit in enumerate(source_team):
            if unit.is_dead(): continue
            for s_idx, slot in enumerate(unit.active_slots):
                card = slot.get('card')

                # Пропускаем, если карты нет или слот оглушен
                if not card or slot.get('stunned'):
                    continue

                base_prio = get_action_priority(card)
                # Левая сторона получает микро-бонус приоритета при прочих равных (convention)
                if base_prio >= 4000 and is_left_side: base_prio += 500
                score = base_prio + slot['speed'] + random.random()

                # --- ВЫБОР ЦЕЛИ ---
                t_u_idx = slot.get('target_unit_idx', -1)
                target_unit = None

                # 1. Попытка взять явно выбранную цель
                if slot.get('is_ally_target'):
                    if t_u_idx != -1 and t_u_idx < len(source_team):
                        target_unit = source_team[t_u_idx]
                else:
                    if t_u_idx != -1 and t_u_idx < len(target_team):
                        target_unit = target_team[t_u_idx]

                # 2. [FIX] АВТО-ТАРГЕТИНГ (Если цель не выбрана)
                if target_unit is None:
                    # Проверяем флаги карты
                    flags = getattr(card, 'flags', [])
                    is_friendly = "friendly" in flags
                    is_offensive = "offensive" in flags

                    # Сценарий А: Чистый бафф/хил -> применяем на СЕБЯ
                    if is_friendly and not is_offensive:
                        target_unit = unit
                        # Обновляем данные слота, чтобы executor понимал контекст
                        slot['target_unit_idx'] = u_idx
                        slot['is_ally_target'] = True

                    # Сценарий Б: Атака или Гибрид -> применяем на ВРАГА
                    else:
                        alive_enemies = [e for e in target_team if not e.is_dead()]
                        if alive_enemies:
                            # Приоритет 1: Провокация (Taunt)
                            taunted = [e for e in alive_enemies if e.get_status("taunt") > 0]

                            if taunted:
                                target_unit = taunted[0]
                            else:
                                # Приоритет 2: Просто первый живой
                                target_unit = alive_enemies[0]

                            # Если слот атаки не выбран, бьем в первый (0)
                            if slot.get('target_slot_idx', -1) == -1:
                                slot['target_slot_idx'] = 0

                # Добавляем действие в очередь, только если цель найдена (или авто-назначена)
                if target_unit:
                    actions.append({
                        'source': unit,
                        'source_idx': s_idx,
                        'target_unit': target_unit,
                        'target_slot_idx': slot.get('target_slot_idx', -1),
                        'slot_data': slot,
                        'score': score,
                        'is_left': is_left_side,
                        'card_type': str(card.card_type).lower(),
                        'opposing_team': target_team
                    })

    collect_actions(team_left, team_right, True)
    collect_actions(team_right, team_left, False)

    actions.sort(key=lambda x: x['score'], reverse=True)

    return report, actions


def finalize_turn(engine, all_units: list):
    """
    Фаза 3: Завершение хода (Events On Combat End).
    """
    engine.logs = []
    report = []

    if engine.logs:
        report.append({"round": "End", "rolls": "Events", "details": " | ".join(engine.logs)})

    return report