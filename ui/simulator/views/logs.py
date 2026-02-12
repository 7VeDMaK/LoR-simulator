import streamlit as st

from core.logging import logger, LogLevel


def render_logs(current_log_level, log_mode_label):
    st.divider()
    jackpot_url = st.session_state.get("azino_jackpot_url")
    if jackpot_url:
        st.markdown(
            "<div style=\"margin-bottom:8px;\">🎶 Azino Jackpot Video</div>"
            f"<iframe width=\"100%\" height=\"315\" "
            f"src=\"https://www.youtube.com/embed/34Pl2DTuwoQ?si=0ojgA65awwY4dMEB\" "
            "title=\"YouTube video player\" frameborder=\"0\" "
            "allow=\"accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share\" "
            "allowfullscreen></iframe>",
            unsafe_allow_html=True
        )
    tab_visual, tab_system = st.tabs(["📜 Visual Report (Cards)", f"🛠️ System Log ({log_mode_label})"])

    # 1. VISUAL REPORT
    with tab_visual:
        visual_logs = st.session_state.get('battle_logs', [])
        if not visual_logs:
            st.caption("Нет данных о столкновениях в этом раунде.")
        else:
            for log in visual_logs:
                if "left" in log and "right" in log:
                    _render_clash_card(log)
                elif current_log_level > LogLevel.MINIMAL:
                    st.caption(f"ℹ️ {log.get('round', '')}: {log.get('details', '')}")

    # 2. SYSTEM LOG
    with tab_system:
        system_logs = logger.get_logs_for_ui(current_log_level)

        if system_logs:
            all_cats = sorted(list(set(l['category'] for l in system_logs)))
            selected_cats = st.multiselect("Фильтр категорий", all_cats, default=all_cats, key="log_cat_filter")
        else:
            selected_cats = []

        log_html = '<div class="log-container">'
        if not system_logs:
            log_html += '<div class="log-entry">Нет логов для отображения.</div>'

        for entry in system_logs:
            if entry['category'] in selected_cats:
                lvl_class = f"lvl-{entry['level'].name}"
                cat_class = f"cat-{entry['category']}"
                row = (
                    f'<div class="log-entry {lvl_class}">'
                    f'<span class="log-time">[{entry["time"]}]</span>'
                    f'<span class="log-cat {cat_class}">[{entry["category"]}]</span>'
                    f'<span class="log-msg">{entry["message"]}</span>'
                    f'</div>'
                )
                log_html += row
        log_html += '</div>'
        st.markdown(log_html, unsafe_allow_html=True)


def _render_clash_card(log):
    """Отрисовка одной карточки столкновения."""
    with st.container(border=True):
        l = log['left']
        r = log['right']
        outcome = log.get('outcome', '-')

        c_l, c_c, c_r = st.columns([5, 1, 5])

        with c_l:
            st.markdown(
                f"<div style='text-align:right'><b>{l['unit']}</b> <span style='color:gray; font-size:0.8em'>({l['card']})</span><br>"
                f"{l['dice']} <span style='font-size:1.4em; font-weight:bold; color:#4ecdc4'>{l['val']}</span> <span style='font-size:0.8em; color:gray'>[{l['range']}]</span></div>",
                unsafe_allow_html=True)

        with c_c:
            st.markdown("<div style='text-align:center; font-weight:bold; padding-top:10px; color:#555'>VS</div>",
                        unsafe_allow_html=True)

        with c_r:
            st.markdown(
                f"<b>{r['unit']}</b> <span style='color:gray; font-size:0.8em'>({r['card']})</span><br>"
                f"<span style='font-size:1.4em; font-weight:bold; color:#ff6b6b'>{r['val']}</span> {r['dice']} <span style='font-size:0.8em; color:gray'>[{r['range']}]</span>",
                unsafe_allow_html=True)

        st.caption(f"🏁 {outcome}")
        if 'details' in log and log['details']:
            with st.expander("Подробности"):
                for d in log['details']:
                    st.markdown(f"- {d}")