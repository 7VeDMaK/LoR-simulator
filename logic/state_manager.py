import json
import os

STATE_FILE = "data/simulator_state.json"


class StateManager:
    @staticmethod
    def save_state(session_state):
        """
        Сохраняет полный стейт симулятора, включая бой.
        """
        # Сначала пробуем собрать данные
        try:
            data = {
                "page": session_state.get("nav_page", "⚔️ Simulator"),

                # 1. Команды
                "team_left_data": [u.to_dict() for u in session_state.get('team_left', [])],
                "team_right_data": [u.to_dict() for u in session_state.get('team_right', [])],

                # 2. Глобальные переменные боя
                "phase": session_state.get('phase', 'roll'),
                "round_number": session_state.get('round_number', 1),
                "turn_message": session_state.get('turn_message', ""),
                "battle_logs": session_state.get('battle_logs', []),
                "script_logs": session_state.get('script_logs', ""),

                # 3. Состояние выполнения хода
                "turn_phase": session_state.get('turn_phase', 'planning'),
                "action_idx": session_state.get('action_idx', 0),
                "executed_slots": list(session_state.get('executed_slots', [])),

                # 4. Очередь действий
                "turn_actions": StateManager._serialize_actions(
                    session_state.get('turn_actions', []),
                    session_state.get('team_left', []),
                    session_state.get('team_right', [])
                ),

                # 5. Селекторы UI
                "profile_unit": session_state.get("profile_selected_unit"),
                "leveling_unit": session_state.get("leveling_selected_unit"),
                "tree_unit": session_state.get("tree_selected_unit"),
                "checks_unit": session_state.get("checks_selected_unit"),
            }

            os.makedirs("data", exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Error saving state: {e}")

    @staticmethod
    def load_state():
        if not os.path.exists(STATE_FILE):
            return {}
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _serialize_actions(actions, team_left, team_right):
        serialized = []
        for act in actions:
            src_side, src_idx = StateManager._find_unit_index(act['source'], team_left, team_right)
            tgt_side, tgt_idx = StateManager._find_unit_index(act['target_unit'], team_left, team_right)

            serialized.append({
                "source_ref": [src_side, src_idx],
                "target_ref": [tgt_side, tgt_idx],
                "source_idx": act['source_idx'],
                "target_slot_idx": act['target_slot_idx'],
                "score": act['score'],
                "is_left": act['is_left'],
                "card_type": act['card_type'],
                "slot_meta": {
                    "speed": act['slot_data'].get('speed'),
                    "is_aggro": act['slot_data'].get('is_aggro'),
                    "destroy_on_speed": act['slot_data'].get('destroy_on_speed')
                }
            })
        return serialized

    @staticmethod
    def restore_actions(serialized_actions, team_left, team_right):
        restored = []
        for s_act in serialized_actions:
            source = StateManager._get_unit_by_index(s_act['source_ref'], team_left, team_right)
            target = StateManager._get_unit_by_index(s_act['target_ref'], team_left, team_right)

            if not source: continue

            slot_idx = s_act['source_idx']
            real_slot = None
            if 0 <= slot_idx < len(source.active_slots):
                real_slot = source.active_slots[slot_idx]

            if not real_slot: continue

            opposing_team = team_right if s_act['is_left'] else team_left

            restored.append({
                'source': source,
                'source_idx': slot_idx,
                'target_unit': target,
                'target_slot_idx': s_act['target_slot_idx'],
                'slot_data': real_slot,
                'score': s_act['score'],
                'is_left': s_act['is_left'],
                'card_type': s_act['card_type'],
                'opposing_team': opposing_team
            })
        return restored

    @staticmethod
    def _find_unit_index(unit, team_left, team_right):
        if unit in team_left: return "left", team_left.index(unit)
        if unit in team_right: return "right", team_right.index(unit)
        return None, -1

    @staticmethod
    def _get_unit_by_index(ref, team_left, team_right):
        side, idx = ref
        if idx == -1: return None
        if side == "left" and 0 <= idx < len(team_left): return team_left[idx]
        if side == "right" and 0 <= idx < len(team_right): return team_right[idx]
        return None