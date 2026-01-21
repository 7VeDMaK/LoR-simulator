import sys
from contextlib import contextmanager
from io import StringIO

import streamlit as st

from core.card import Card
from core.enums import CardType
from core.library import Library


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
    if not u.memory.get("battle_initialized"):
        u.memory["battle_initialized"] = True

        if not hasattr(u, "card_cooldowns") or u.card_cooldowns is None:
            u.card_cooldowns = {}

        if getattr(u, 'deck', None):
            # Считаем, сколько копий каждой карты
            from collections import Counter
            deck_counts = Counter(u.deck)

            for card_id, count in deck_counts.items():
                card = Library.get_card(card_id)
                if card:
                    # Пропускаем предметы
                    if card.card_type.upper() == CardType.ITEM.name:
                        continue

                    # Начальный кулдаун (Tier - 1)
                    initial_cd = max(0, card.tier - 1)

                    if initial_cd > 0:
                        # Если есть "разогрев", он накладывается на ВСЕ копии карты в начале боя
                        # Создаем список длиной равной количеству копий
                        u.card_cooldowns[card_id] = [initial_cd] * count

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


def sync_state_from_widgets(team_left: list, team_right: list):
    """
    Считывает значения из виджетов Streamlit и обновляет объекты юнитов перед сохранением.
    """

    def sync_unit(unit, prefix):
        for i, slot in enumerate(unit.active_slots):
            if slot.get('stunned'): continue
            base_key = f"{prefix}_{unit.name}"

            # 1. TARGET
            tgt_key = f"{base_key}_tgt_{i}"
            if tgt_key in st.session_state:
                val = st.session_state[tgt_key]
                if val == "None":
                    slot['target_unit_idx'] = -1
                    slot['target_slot_idx'] = -1
                else:
                    try:
                        parts = val.split('|')[0].strip().split(':')
                        slot['target_unit_idx'] = int(parts[0]) - 1
                        slot['target_slot_idx'] = int(parts[1]) - 1
                    except:
                        pass

            # 2. CARD
            card_key = f"{base_key}_card_{i}"
            if card_key in st.session_state:
                val = st.session_state[card_key]
                if isinstance(val, Card):
                    slot['card'] = val
                elif val is None:
                    slot['card'] = None

            # 3. AGGRO & DESTROY
            aggro_key = f"{base_key}_aggro_{i}"
            if aggro_key in st.session_state:
                slot['is_aggro'] = st.session_state[aggro_key]

            destroy_key = f"{base_key}_destroy_{i}"
            if destroy_key in st.session_state:
                slot['destroy_on_speed'] = st.session_state[destroy_key]

    for i, u in enumerate(team_left): sync_unit(u, f"l_{i}")
    for i, u in enumerate(team_right): sync_unit(u, f"r_{i}")