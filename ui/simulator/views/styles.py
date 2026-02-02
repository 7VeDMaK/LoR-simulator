import streamlit as st

def inject_simulator_styles():
    st.markdown("""
        <style>
            /* Контейнер счетчика раундов */
            .turn-counter-static {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                margin: 0 auto 10px auto; 
                padding: 5px 20px;
                width: fit-content;
                min-width: 120px;
                background: linear-gradient(135deg, rgba(35, 37, 46, 1) 0%, rgba(20, 20, 25, 1) 100%);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }
            .counter-label {
                font-family: sans-serif; font-size: 10px; letter-spacing: 2px;
                text-transform: uppercase; color: #8d99ae; margin-bottom: 2px;
            }
            .counter-value {
                font-family: 'Courier New', monospace; font-size: 24px;
                font-weight: 700; color: #edf2f4; text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
                line-height: 1;
            }

            /* Стили логов */
            .log-container {
                background-color: #0e1117;
                border: 1px solid #30333d;
                border-radius: 5px;
                padding: 10px;
                max-height: 500px;
                overflow-y: auto;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
            }
            .log-entry {
                padding: 3px 0;
                border-bottom: 1px solid #1c1f26;
                display: flex;
                align-items: baseline;
            }
            .log-time { color: #6c757d; margin-right: 10px; min-width: 70px; font-size: 0.9em; }

            /* Категории */
            .cat-Combat { color: #ff6b6b; font-weight: bold; } 
            .cat-Status { color: #4ecdc4; } 
            .cat-Effect { color: #feca57; } 
            .cat-Stats { color: #54a0ff; } 
            .cat-System { color: #8395a7; } 
            .cat-Clash { color: #ff9ff3; font-weight: bold; } 
            .cat-Damage { color: #ff4757; font-weight: bold; text-decoration: underline; } 

            .log-cat { margin-right: 10px; min-width: 80px; text-transform: uppercase; font-size: 0.85em; }

            /* Уровни важности */
            .lvl-NORMAL { color: #e9ecef; }
            .lvl-MINIMAL { color: #ffffff; font-weight: bold; border-left: 2px solid #fff; padding-left: 5px; }
            .lvl-VERBOSE { color: #636e72; font-style: italic; }

            /* Game Master Panel Styles */
            .gm-panel-container {
                background: linear-gradient(135deg, rgba(20, 20, 30, 0.95) 0%, rgba(10, 10, 15, 0.95) 100%);
                border: 2px solid rgba(255, 215, 0, 0.3);
                border-radius: 10px;
                padding: 15px;
                margin-top: 15px;
                box-shadow: 0 4px 15px rgba(255, 215, 0, 0.1);
            }
            
            .gm-panel-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
                padding-bottom: 10px;
                border-bottom: 1px solid rgba(255, 215, 0, 0.2);
            }
            
            .gm-warning {
                background: rgba(255, 193, 7, 0.1);
                border-left: 3px solid #ffc107;
                padding: 8px 12px;
                margin: 10px 0;
                border-radius: 4px;
                font-size: 0.9em;
                color: #ffc107;
            }
        </style>
    """, unsafe_allow_html=True)