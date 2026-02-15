import streamlit as st


def render_roulette_page():
    """Рулетка Рейна - главная страница"""
    
    st.title("🎰 Рулетка Рейна")
    
    # Центрируем кнопку
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🎲 Крутить", use_container_width=True, type="primary"):
            st.balloons()
            st.success("Крутим рулетку!")
