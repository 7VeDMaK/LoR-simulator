def calculate_redirections(atk_team: list, def_team: list):
    """
    Рассчитывает перехваты.
    Правило LoR: Перехват возможен, только если Spd(Atk) > Spd(Def).
    Исключение: Если Def уже целится в Atk (В ТОТ ЖЕ СЛОТ), то это Clash по умолчанию.
    """
    for def_idx, defender in enumerate(def_team):
        if defender.is_dead(): continue

        for s_def_idx, s_def in enumerate(defender.active_slots):
            if s_def.get('prevent_redirection'): continue
            if s_def.get('stunned'): continue

            def_spd = s_def['speed']

            # Цель защитника (в кого он сам бьет)
            def_target_u_idx = s_def.get('target_unit_idx', -1)

            # === [FIX] Достаем индекс слота цели ===
            def_target_s_idx = s_def.get('target_slot_idx', -1)
            # =======================================

            valid_interceptors = []

            for atk_u_idx, atk_unit in enumerate(atk_team):
                if atk_unit.is_dead(): continue

                for s_atk_idx, s_atk in enumerate(atk_unit.active_slots):

                    if s_atk.get('is_ally_target'): continue

                    t_u = s_atk.get('target_unit_idx', -1)
                    t_s = s_atk.get('target_slot_idx', -1)

                    if t_u == def_idx and t_s == s_def_idx:
                        # === [FIX] Проверяем совпадение И Юнита, И Слота ===
                        # Clash будет "естественным", только если защитник бьет именно в ЭТОТ слот атакующего
                        is_natural_clash = (def_target_u_idx == atk_u_idx and def_target_s_idx == s_atk_idx)
                        # ===================================================

                        atk_spd = s_atk['speed']

                        can_redirect_equal = False
                        if hasattr(atk_unit, "iter_mechanics"):
                            for mech in atk_unit.iter_mechanics():
                                if mech.can_redirect_on_equal_speed(atk_unit):
                                    can_redirect_equal = True
                                    break

                        if can_redirect_equal:
                            can_redirect = atk_spd >= def_spd
                        else:
                            can_redirect = atk_spd > def_spd

                        if is_natural_clash or can_redirect:
                            valid_interceptors.append(s_atk)
                        else:
                            # Скорости не хватает и мы не цель защитника -> One Sided
                            s_atk['force_clash'] = False
                            s_atk['force_onesided'] = True

            # ... (остальной код сортировки без изменений)
            if not valid_interceptors: continue

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