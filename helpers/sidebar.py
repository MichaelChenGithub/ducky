import streamlit as st

def show() -> None:
    st.markdown("""
        <style>
        /* Fix the sidebar image position */
        .sidebar-img {
            position: fixed;
            top: 0rem;
            margin-top: 1rem;
            margin-left: 1rem;
            z-index: 1;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"""
            <a href="/" style="color:black;text-decoration: none;">
                <div class="sidebar-img">
                    <img src="app/static/logo.png" width="140"><span style="color: white">
                </div>
            </a>
            <br>
                """, unsafe_allow_html=True)

        reload_button = st.button("↪︎  Reload Page")
        if reload_button:
            st.session_state.clear()
            st.rerun()
