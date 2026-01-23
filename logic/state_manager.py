import json
import os
import glob
import copy
import streamlit as st

# Папка для хранения стейтов
STATES_DIR = "data/states"


class StateManager:
    @staticmethod
    def ensure_dir():
        if not os.path.exists(STATES_DIR):
            os.makedirs(STATES_DIR, exist_ok=True)
            default_path = os.path.join(STATES_DIR, "default.json")
            if not os.path.exists(default_path):
                with open(default_path, "w", encoding="utf-8") as f:
                    json.dump({}, f)

    @staticmethod
    def get_available_states():
        StateManager.ensure_dir()
        files = glob.glob(os.path.join(STATES_DIR, "*.json"))
        names = [os.path.splitext(os.path.basename(f))[0] for f in files]
        return sorted(names)

    @staticmethod
    def create_new_state(name):
        StateManager.ensure_dir()
        filename = f"{name}.json"
        path = os.path.join(STATES_DIR, filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)
            return True
        return False

    @staticmethod
    def delete_state(name):
        path = os.path.join(STATES_DIR, f"{name}.json")
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    # ==========================================
    # SNAPSHOTS
    # ==========================================

    @staticmethod
    def get_state_snapshot(session_state):
        """
        Создает ПОЛНЫЙ слепок состояния (Keyframe).
        [FIX] НЕ СОХРАНЯЕТ undo_stack здесь, чтобы избежать рекурсии.
        """
        return {
            "type": "full",
            "page": session_state.get("nav_page", "⚔️ Simulator"),

            "team_left_data": [u.to_dict() for u in session_state.get('team_left', [])],
            "team_right_data": [u.to_dict() for u in session_state.get('team_right', [])],

            "phase": session_state.get('phase', 'roll'),
            "round_number": session_state.get('round_number', 1),
            "turn_message": session_state.get('turn_message', ""),
            "battle_logs": session_state.get('battle_logs', []),
            "script_logs": session_state.get('script_logs', ""),

            "turn_phase": session_state.get('turn_phase', 'planning'),
            "action_idx": session_state.get('action_idx', 0),
            "executed_slots": list(session_state.get('executed_slots', [])),

            "turn_actions": StateManager._serialize_actions(
                session_state.get('turn_actions', []),
                session_state.get('team_left', []),
                session_state.get('team_right', [])
            ),

            "profile_unit": session_state.get("profile_selected_unit"),
            "leveling_unit": session_state.get("leveling_selected_unit"),
            "tree_unit": session_state.get("tree_selected_unit"),
            "checks_unit": session_state.get("checks_selected_unit"),
        }

    @staticmethod
    def get_dynamic_snapshot(session_state):
        """
        Создает ДИНАМИЧЕСКИЙ слепок (Delta).
        """
        return {
            "type": "dynamic",
            "team_left_dyn": [u.get_dynamic_state() for u in session_state.get('team_left', [])],
            "team_right_dyn": [u.get_dynamic_state() for u in session_state.get('team_right', [])],

            "phase": session_state.get('phase', 'roll'),
            "round_number": session_state.get('round_number', 1),
            "turn_message": session_state.get('turn_message', ""),
            "battle_logs": session_state.get('battle_logs', []),

            "turn_actions": StateManager._serialize_actions(
                session_state.get('turn_actions', []),
                session_state.get('team_left', []),
                session_state.get('team_right', [])
            ),

            "turn_phase": session_state.get('turn_phase', 'planning'),
            "action_idx": session_state.get('action_idx', 0),
            "executed_slots": list(session_state.get('executed_slots', [])),
        }

    @staticmethod
    def restore_from_dynamic_snapshot(session_state, dynamic_data, base_data):
        from core.unit.unit import Unit

        # 1. Base
        l_base = base_data.get("team_left_data", [])
        r_base = base_data.get("team_right_data", [])

        team_left = []
        for d in l_base:
            try:
                u = Unit.from_dict(d)
                team_left.append(u)
            except Exception as e:
                print(f"Error restoring base unit left: {e}")

        team_right = []
        for d in r_base:
            try:
                u = Unit.from_dict(d)
                team_right.append(u)
            except Exception as e:
                print(f"Error restoring base unit right: {e}")

        # 2. Delta
        l_dyn = dynamic_data.get("team_left_dyn", [])
        r_dyn = dynamic_data.get("team_right_dyn", [])

        for i, u in enumerate(team_left):
            if i < len(l_dyn):
                u.apply_dynamic_state(l_dyn[i])

        for i, u in enumerate(team_right):
            if i < len(r_dyn):
                u.apply_dynamic_state(r_dyn[i])

        for u in team_left + team_right:
            u.recalculate_stats()

        session_state['team_left'] = team_left
        session_state['team_right'] = team_right

        session_state['phase'] = dynamic_data.get('phase', 'roll')
        session_state['round_number'] = dynamic_data.get('round_number', 1)
        session_state['turn_message'] = dynamic_data.get('turn_message', "")
        session_state['battle_logs'] = dynamic_data.get('battle_logs', [])

        session_state['turn_phase'] = dynamic_data.get('turn_phase', 'planning')
        session_state['action_idx'] = dynamic_data.get('action_idx', 0)

        session_state['executed_slots'] = set()
        for item in dynamic_data.get('executed_slots', []):
            session_state['executed_slots'].add(tuple(item))

        raw_actions = dynamic_data.get('turn_actions', [])
        if raw_actions:
            session_state['turn_actions'] = StateManager.restore_actions(
                raw_actions, team_left, team_right
            )
        else:
            session_state['turn_actions'] = []

        session_state['teams_loaded'] = True

    @staticmethod
    def restore_state_from_snapshot(session_state, data):
        from core.unit.unit import Unit

        l_data = data.get("team_left_data", [])
        r_data = data.get("team_right_data", [])

        team_left = []
        for d in l_data:
            try:
                u = Unit.from_dict(d)
                team_left.append(u)
            except Exception as e:
                print(f"Error restoring left unit: {e}")

        team_right = []
        for d in r_data:
            try:
                u = Unit.from_dict(d)
                team_right.append(u)
            except Exception as e:
                print(f"Error restoring right unit: {e}")

        for u in team_left + team_right:
            u.recalculate_stats()

        session_state['team_left'] = team_left
        session_state['team_right'] = team_right

        session_state['phase'] = data.get('phase', 'roll')
        session_state['round_number'] = data.get('round_number', 1)
        session_state['turn_message'] = data.get('turn_message', "")
        session_state['battle_logs'] = data.get('battle_logs', [])
        session_state['script_logs'] = data.get('script_logs', "")
        session_state['turn_phase'] = data.get('turn_phase', 'planning')
        session_state['action_idx'] = data.get('action_idx', 0)

        session_state['executed_slots'] = set()
        for item in data.get('executed_slots', []):
            session_state['executed_slots'].add(tuple(item))

        raw_actions = data.get('turn_actions', [])
        if raw_actions:
            session_state['turn_actions'] = StateManager.restore_actions(
                raw_actions, team_left, team_right
            )
        else:
            session_state['turn_actions'] = []

        selector_mapping = {
            "profile_unit": "profile_selected_unit",
            "leveling_unit": "leveling_selected_unit",
            "tree_unit": "tree_selected_unit",
            "checks_unit": "checks_selected_unit",
        }
        for json_key, session_key in selector_mapping.items():
            saved_val = data.get(json_key)
            if saved_val:
                session_state[session_key] = saved_val

        try:
            session_state['nav_page'] = data.get("page", "⚔️ Simulator")
        except Exception:
            pass

        # [FIX] Восстанавливаем историю только если загружаем из файла
        if "undo_stack" in data:
            session_state['undo_stack'] = data["undo_stack"]

        session_state['teams_loaded'] = True

    # ==========================================
    # FILE OPERATIONS
    # ==========================================

    @staticmethod
    def save_state(session_state, filename="default"):
        StateManager.ensure_dir()
        target_file = os.path.join(STATES_DIR, f"{filename}.json")
        try:
            # Получаем чистый слепок
            data = StateManager.get_state_snapshot(session_state)

            # [FIX] Добавляем историю ТОЛЬКО при сохранении в файл
            # При этом сама история (список диктов) корректно сериализуется
            data["undo_stack"] = session_state.get("undo_stack", [])

            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving state to {filename}: {e}")

    @staticmethod
    def load_state(filename="default"):
        StateManager.ensure_dir()
        target_file = os.path.join(STATES_DIR, f"{filename}.json")
        if not os.path.exists(target_file):
            return {}
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    # ==========================================
    # HELPERS
    # ==========================================
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