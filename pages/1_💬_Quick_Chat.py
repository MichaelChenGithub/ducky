import streamlit as st

from services import prompts
from helpers import util

st.set_page_config(
    page_title="Quick Chat",
    page_icon="💬",
    layout="wide"
)

import helpers.sidebar
import asyncio

helpers.sidebar.show()

st.header("Quick Chat")
st.write("Get instant answers to your software development and coding questions.")
# ask_book = st.checkbox("Ask the Pragmatic Programmer book?", value=False)

# Ensure the session state is initialized
if "messages" not in st.session_state:
    initial_messages = [{"role": "system",
                         "content": prompts.quick_chat_system_prompt()}]
    st.session_state.messages = initial_messages

# Ensure the session state is initialized
if "page_number" not in st.session_state:
    st.session_state.page_number = None



# Create a checkbox
ask_book = st.checkbox("Use *The Pragmatic Programmer* as context", value=False)

# Print all messages in the session state
for message in [m for m in st.session_state.messages if m["role"] != "system"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ask a question
if prompt := st.chat_input("Ask a software development or coding question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    if ask_book:
        asyncio.run(util.ask_book(st.session_state.messages, prompt))
        if st.session_state.page_number:
            image = util.convert_pdf_to_image("data/ThePragmaticProgrammer.pdf", st.session_state.page_number)
            if image:
                # 創建一個可收合的區塊
                with st.expander(f"Page - {st.session_state.page_number}", expanded=True):  # expanded=True 表示預設展開
                    # 在可收合區塊中顯示圖片
                    st.image(image, use_column_width=True)
    else:
        asyncio.run(util.chat(st.session_state.messages, prompt))
        st.session_state.page_number = None
