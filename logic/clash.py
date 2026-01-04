import random

# Импорт перечислений
from core.enums import CardType
# Импорт логики массовых атак
from logic.battle_flow.mass_attack import process_mass_attack
# Импорт миксина, в который мы вынесли низкоуровневую логику (ClashFlowMixin)
from logic.battle_flow.clash_flow import ClashFlowMixin


class ClashSystem(ClashFlowMixin):
    """
    Уровень 3: Управление боем (Дирижер).
    Отвечает за очередность ходов, фазы и выбор типа атаки.
    """

    def __init__(self):
        self.logs = []

    def log(self, message):
        self.logs.append(message)

    @staticmethod
    def calculate_redirections(atk_team: list, def_team: list):
        """
        Рассчитывает перехваты.
        Правило LoR: Перехват возможен, только если Spd(Atk) > Spd(Def).
        Исключение: Если Def уже целится в Atk, то это Clash по умолчанию.
        """
        for def_idx, defender in enumerate(def_team):
            if defender.is_dead(): continue

            for s_def_idx, s_def in enumerate(defender.active_slots):
                if s_def.get('prevent_redirection'): continue
                if s_def.get('stunned'): continue

                def_spd = s_def['speed']

                # Цель защитника (в кого он сам бьет)
                def_target_u_idx = s_def.get('target_unit_idx', -1)
                def_target_s_idx = s_def.get('target_slot_idx', -1)

                # Кандидаты на перехват
                valid_interceptors = []

                # Проходим по всем атакующим
                for atk_u_idx, atk_unit in enumerate(atk_team):
                    if atk_unit.is_dead(): continue

                    for s_atk_idx, s_atk in enumerate(atk_unit.active_slots):

                        if s_atk.get('is_ally_target'): continue
                        # Проверяем, бьет ли он в этот слот защитника
                        t_u = s_atk.get('target_unit_idx', -1)
                        t_s = s_atk.get('target_slot_idx', -1)

                        if t_u == def_idx and t_s == s_def_idx:
                            # Условие 1: Это "Естественный Clash" (Враг и так бьет в меня)?
                            # Проверяем: цель защитника совпадает с этим атакующим?
                            is_natural_clash = (
                                        def_target_u_idx == atk_u_idx)  # and def_target_s_idx == s_atk_idx (можно уточнить до слота, но обычно достаточно юнита в 1v1)

                            # Условие 2: Скорость атакующего > Скорости защитника
                            atk_spd = s_atk['speed']

                            has_athletic = ("athletic" in atk_unit.talents) or ("athletic" in atk_unit.passives)

                            if has_athletic:
                                # С талантом: строго больше ИЛИ равно
                                can_redirect = atk_spd >= def_spd
                            else:
                                # Без таланта: строго больше
                                can_redirect = atk_spd > def_spd

                            # Если это естественный бой ИЛИ возможен перехват
                            if is_natural_clash or can_redirect:
                                valid_interceptors.append(s_atk)
                            else:
                                # Если скорости не хватает и это не взаимная атака ->
                                # Атакующий НЕ МОЖЕТ вызвать Clash. Он будет бить One-Sided.
                                s_atk['force_clash'] = False
                                s_atk['force_onesided'] = True

                if not valid_interceptors: continue

                # Теперь выбираем победителя среди валидных кандидатов
                # Приоритет:
                # 1. Галочка Aggro
                # 2. Скорость
                def sort_key(slot):
                    aggro = 1000 if slot.get('is_aggro') else 0
                    return aggro + slot['speed']

                valid_interceptors.sort(key=sort_key, reverse=True)

                best_match = valid_interceptors[0]

                for s in valid_interceptors:
                    if s is best_match:
                        s['force_clash'] = True
                        s['force_onesided'] = False
                    else:
                        s['force_clash'] = False
                        s['force_onesided'] = True

    def get_action_priority(self, card):
        """
        Возвращает базовый приоритет действия на основе типа карты.
        Чем выше число, тем раньше сработает карта.
        """
        if not card: return 0

        # Приводим к нижнему регистру для надежности
        ctype = card.card_type.lower()

        # 1. Мгновенные эффекты
        if ctype == "on_play" or ctype == "on play": return 5000

        # 2. Массовые атаки (срабатывают до обычных столкновений)
        if "mass" in ctype: return 4000

        # 3. Стрелковые (бьют первыми в фазе боя)
        if ctype == "ranged": return 3000

        # 4. Наступательные (бьют перед обычными, но могут быть перехвачены)
        if ctype == "offensive": return 2000

        # 5. Обычные (Рукопашные)
        if ctype == "melee": return 1000

        return 0

    def prepare_turn(self, team_left: list, team_right: list):
        """
        Фаза 1: Сбор всех запланированных действий (Actions) и сортировка по скорости/приоритету.
        """
        self.logs = []
        report = []
        all_units = team_left + team_right

        self.calculate_redirections(team_left, team_right)
        self.calculate_redirections(team_right, team_left)  # На случай если враги тоже умеют выбирать

        # --- A. Триггеры начала боя (On Combat Start) ---
        for u in all_units:
            # Находим референс врага (просто чтобы был для скриптов)
            opponents = team_right if u in team_left else team_left
            opp_ref = next((e for e in opponents if not e.is_dead()), None)

            my_allies = team_left if u in team_left else team_right
            self._trigger_unit_event("on_combat_start", unit=u, log_func=self.log,
                                     opponent=opp_ref, enemies=opponents, allies=my_allies)

            # 2. === FIX: on_round_start (Здесь срабатывает Реген, Горение, Сыры и т.д.) ===
            self._trigger_unit_event("on_round_start", unit=u, log_func=self.log,
                                     opponent=opp_ref, enemies=opponents, allies=my_allies)
            if self.logs:
                report.append({"round": "Start", "rolls": "Events", "details": " | ".join(self.logs)})
            self.logs = []

        # --- B. Сбор действий ---
        actions = []

        def collect_actions(source_team, target_team, is_left_side):
            for u_idx, unit in enumerate(source_team):
                if unit.is_dead(): continue
                for s_idx, slot in enumerate(unit.active_slots):
                    card = slot.get('card')
                    if card and not slot.get('stunned'):
                        base_prio = self.get_action_priority(card)
                        if base_prio >= 4000 and is_left_side: base_prio += 500
                        score = base_prio + slot['speed'] + random.random()

                        # === ВЫБОР ЦЕЛИ (ИЗМЕНЕНО) ===
                        t_u_idx = slot.get('target_unit_idx', -1)
                        target_unit = None

                        # Если карта дружественная, ищем цель в СВОЕЙ команде
                        if slot.get('is_ally_target'):
                            if t_u_idx != -1 and t_u_idx < len(source_team):
                                target_unit = source_team[t_u_idx]
                        # Иначе стандартно во вражеской
                        else:
                            if t_u_idx != -1 and t_u_idx < len(target_team):
                                target_unit = target_team[t_u_idx]

                        actions.append({
                            'source': unit,
                            'source_idx': s_idx,
                            'target_unit': target_unit,
                            'target_slot_idx': slot.get('target_slot_idx', -1),
                            'slot_data': slot,
                            'score': score,
                            'is_left': is_left_side,
                            'card_type': card.card_type.lower(),
                            'opposing_team': target_team
                        })

        collect_actions(team_left, team_right, True)
        collect_actions(team_right, team_left, False)
        actions.sort(key=lambda x: x['score'], reverse=True)

        return report, actions

    def execute_single_action(self, act, executed_slots):
        """
        Фаза 2 (Микро): Выполнение конкретного действия из очереди.
        """
        self.logs = []
        source = act['source']
        s_idx = act['source_idx']

        # ID слота источника: (Имя, Индекс слота)
        src_id = (source.name, s_idx)

        # Если этот слот уже сыграл (например, был втянут в Clash защитником ранее), пропускаем
        if src_id in executed_slots: return []

        # Проверка состояния бойца
        if source.is_dead() or source.is_staggered(): return []

        # Загружаем карту в слот "current_card" для обработки
        source.current_card = act['slot_data'].get('card')
        if not source.current_card: return []

        # === 1. ДОСТАЕМ НАМЕРЕНИЕ ИГРОКА ===
        intent_src = act['slot_data'].get('destroy_on_speed', True)
        target = act['target_unit']

        # === ЛОГИКА ТИПОВ КАРТ ===

        # 1. MASS ATTACK (Массовая атака)
        if "mass" in act['card_type']:
            # Помечаем слот как сыгранный
            executed_slots.add(src_id)

            p_label = "Mass Atk" if act['is_left'] else "Enemy Mass"

            if source.current_card.id != "unknown":
                source.card_cooldowns[source.current_card.id] = source.current_card.tier
            # Вызываем логику из logic.battle_flow.mass_attack
            return process_mass_attack(self, act, act['opposing_team'], p_label)

        if "on_play" in act['card_type'] or "on play" in act['card_type']:
            executed_slots.add(src_id)
            self._process_card_self_scripts("on_use", source, target)
            tgt_name = f" on {target.name}" if target else ""

            # === FIX: Добавляем логи скриптов в отчет ===
            details = [f"⚡ {source.name} used {act['slot_data']['card'].name}{tgt_name}"]
            if self.logs:
                details.extend(self.logs)  # Добавляем сообщения о баффах

            if source.current_card.id != "unknown":
                source.card_cooldowns[source.current_card.id] = source.current_card.tier

            return [{"round": "On Play", "details": details}]

        # 3. STANDARD COMBAT (Melee, Ranged, Offensive)
        target = act['target_unit']
        t_s_idx = act['target_slot_idx']

        # Если цели нет или она мертва -> Действие сгорает (или One-Sided в никуда)
        if not target or target.is_dead():
            return []

        # Проверяем, будет ли Столкновение (Clash) или Односторонняя атака (One-Sided)
        is_clash = False
        tgt_id = (target.name, t_s_idx)
        target_slot = None

        slot_data = act['slot_data']

        if t_s_idx != -1 and t_s_idx < len(target.active_slots):
            target_slot = target.active_slots[t_s_idx]

            # Если принудительно One-Sided (проиграл конкуренцию за слот)
            if slot_data.get('force_onesided'):
                is_clash = False

            # Clash происходит, если:
            # 1. Слот цели еще не сыграл (не в executed_slots).
            # 2. В слоте цели есть карта.
            # 3. Цель не в стане (Stagger).
            elif (tgt_id not in executed_slots) and \
                    target_slot.get('card') and \
                    not target.is_staggered():
                is_clash = True

        # Устанавливаем кулдаун карты (если нужно для UI)
        if source.current_card.id != "unknown":
            source.card_cooldowns[source.current_card.id] = max(0, source.current_card.tier)

        battle_logs = []
        spd_src = act['slot_data']['speed']

        if is_clash:
            # === СЦЕНАРИЙ: CLASH (Столкновение) ===
            executed_slots.add(src_id)
            executed_slots.add(tgt_id)  # Слот защитника тоже считается сыгранным

            # Подготовка защитника
            target.current_card = target_slot.get('card')
            spd_tgt = target_slot['speed']
            intent_tgt = target_slot.get('destroy_on_speed', True)

            self.log(f"⚔️ Clash: {source.name} vs {target.name}")

            # Вызываем логику столкновения из миксина
            # (Там внутри учитывается Ranged vs Melee, Offensive Recycle и т.д.)
            logs = self._resolve_card_clash(
                source, target, "Clash", act['is_left'],
                spd_src, spd_tgt,
                intent_a=intent_src, intent_d=intent_tgt
            )
            battle_logs.extend(logs)

        else:
            # === СЦЕНАРИЙ: ONE-SIDED (Односторонняя атака) ===
            executed_slots.add(src_id)

            p_label = "L" if act['is_left'] else "R"

            # 1. Проверяем, была ли эта атака перенаправлена
            is_redirected = slot_data.get('force_onesided', False)

            # 2. Проверяем, ЗАНЯТ ЛИ СЛОТ ЦЕЛИ
            # Слот занят, если он уже в executed_slots
            is_target_busy = False
            if tgt_id in executed_slots:
                is_target_busy = True

            # Если атака перенаправлена, то цель по определению занята (кем-то другим)
            if is_redirected:
                is_target_busy = True

            # Скорость цели (для разрушения)
            spd_def_val = 0
            if target_slot: spd_def_val = target_slot['speed']

            # Вызываем логику односторонней атаки из миксина
            # (Там внутри проверяется пассивная защита Block/Evade, даже если слота нет в таргете)
            logs = self._resolve_one_sided(
                source, target, f"{p_label} Hit",
                spd_src, spd_def_val,
                intent_atk=intent_src,
                is_redirected=is_target_busy  # <--- ПЕРЕДАЕМ ОБЩИЙ ФЛАГ "ЗАНЯТОСТИ"
            )
            battle_logs.extend(logs)

        return battle_logs

    def finalize_turn(self, all_units: list):
        """
        Фаза 3: Завершение хода (Events On Combat End).
        """
        self.logs = []
        report = []

        for u in all_units:
            self._trigger_unit_event("on_combat_end", unit=u, log_func=self.log)

        if self.logs:
            report.append({"round": "End", "rolls": "Events", "details": " | ".join(self.logs)})

        return report

    def resolve_turn(self, team_left: list, team_right: list):
        """
        ГЛАВНЫЙ МЕТОД (Pipeline).
        Вызывается кнопкой FIGHT в симуляторе.
        """
        full_report = []

        # 1. Подготовка и Сортировка
        init_logs, actions = self.prepare_turn(team_left, team_right)
        full_report.extend(init_logs)

        # Множество сыгранных слотов (чтобы один слот не бил дважды)
        executed_slots = set()

        # 2. Выполнение действий по порядку приоритета
        for act in actions:
            logs = self.execute_single_action(act, executed_slots)
            full_report.extend(logs)

        # 3. Финализация
        end_logs = self.finalize_turn(team_left + team_right)
        full_report.extend(end_logs)

        return full_report