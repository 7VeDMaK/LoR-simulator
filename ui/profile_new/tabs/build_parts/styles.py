import streamlit as st

def inject_build_tab_css():
    st.markdown("""
        <style>
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
            gap: 0.4rem;
        }

        /* CARD WRAPPER */
        .card-wrapper {
            background-color: #1a1a1a;
            border: 2px solid #444;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 5px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        /* BORDERS */
        .border-melee { border-color: #ff6b6b; box-shadow: 0 0 5px rgba(255, 107, 107, 0.1); }
        .border-ranged { border-color: #4ecdc4; box-shadow: 0 0 5px rgba(78, 205, 196, 0.1); }
        .border-item { border-color: #feca57; box-shadow: 0 0 5px rgba(254, 202, 87, 0.1); }
        .border-defense { border-color: #5f27cd; }

        /* HEADER */
        .card-header-row {
            display: flex; align-items: center; justify-content: space-between;
            border-bottom: 1px solid #333; padding-bottom: 6px; margin-bottom: 2px;
        }
        .card-cost-badge {
            display: flex; align-items: center; justify-content: center;
            width: 26px; height: 26px; background: #ffd700; color: #000;
            border-radius: 50%; font-weight: bold; font-size: 15px; margin-right: 10px;
            flex-shrink: 0;
        }
        .card-name { font-weight: bold; font-size: 16px; flex-grow: 1; line-height: 1.2; }
        .card-type-badge {
            font-size: 11px; text-transform: uppercase; padding: 3px 8px;
            border-radius: 4px; background: #333; color: #aaa; margin-left: 8px; font-weight: bold;
            flex-shrink: 0;
        }

        /* DICE */
        .dice-block {
            background: #252525; margin: 4px 0; padding: 6px 10px;
            border-radius: 6px; border-left: 4px solid #555; font-size: 14px;
            display: flex; flex-direction: column;
        }
        .dice-header { display: flex; align-items: center; font-weight: bold; font-size: 15px; margin-bottom: 2px;}

        .dice-slash { color: #ff6b6b; border-left-color: #ff6b6b !important; }
        .dice-pierce { color: #4ecdc4; border-left-color: #4ecdc4 !important; }
        .dice-blunt { color: #45b7d1; border-left-color: #45b7d1 !important; }
        .dice-block-def { color: #5f27cd; border-left-color: #5f27cd !important; }
        .dice-evade { color: #feca57; border-left-color: #feca57 !important; }

        /* SCRIPTS */
        .script-container { margin-top: 4px; display: flex; flex-direction: column; gap: 2px; }
        .script-line { 
            font-size: 13px; color: #eee; margin-left: 0px; line-height: 1.5; 
            display: flex; align-items: baseline; flex-wrap: wrap;
        }

        .trigger-tag {
            font-weight: bold; font-size: 10px; padding: 2px 6px;
            border-radius: 4px; margin-right: 8px; text-transform: uppercase;
            white-space: nowrap; display: inline-block;
        }
        .tr-hit { color: #ff9f43; background: rgba(255, 159, 67, 0.15); border: 1px solid rgba(255, 159, 67, 0.3); }
        .tr-use { color: #54a0ff; background: rgba(84, 160, 255, 0.15); border: 1px solid rgba(84, 160, 255, 0.3); }
        .tr-win { color: #1dd1a1; background: rgba(29, 209, 161, 0.15); border: 1px solid rgba(29, 209, 161, 0.3); }
        .tr-lose { color: #ff6b6b; background: rgba(255, 107, 107, 0.15); border: 1px solid rgba(255, 107, 107, 0.3); }
        .tr-start { color: #feca57; background: rgba(254, 202, 87, 0.15); border: 1px solid rgba(254, 202, 87, 0.3); }
        .tr-roll { color: #a29bfe; background: rgba(162, 155, 254, 0.15); border: 1px solid rgba(162, 155, 254, 0.3); }

        .param-highlight { color: #fff; font-weight: bold; text-decoration: underline dotted #555; }

        .card-desc-text { 
            font-size: 13px; color: #aaa; margin-top: 8px; border-top: 1px solid #333; 
            padding-top: 6px; white-space: pre-wrap; font-style: italic; line-height: 1.4;
        }

        .tags-row { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
        .card-flag { font-size: 11px; background: #333; padding: 2px 6px; border-radius: 4px; color: #ccc; }
        </style>
    """, unsafe_allow_html=True)