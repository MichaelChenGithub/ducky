import streamlit as st
from streamlit_ace import st_ace
import helpers.sidebar
import helpers.util
from services import prompts
from helpers import util
st.set_page_config(
    page_title="Generate Code",
    page_icon="📄",
    layout="wide"
)
import asyncio
# Add comments to explain the purpose of the code sections

# Show sidebar
helpers.sidebar.show()

#############################################################################
st.header("Welcome to the code generator!")
st.write("This tool is designed to help you generate code for your software projects.")


# Initialize session state needed variables
## messages
if "messages" not in st.session_state:
    initial_messages = [{
        "role": "system",
        "content": prompts.general_ducky_code_starter_prompt()
    }]
    st.session_state.messages = initial_messages


if "ace_key_counter" not in st.session_state:
    st.session_state.ace_key_counter = 0

## code
if "code" not in st.session_state:
    st.session_state.code = ""

if "code_updated" not in st.session_state:
    st.session_state.code_updated = False

## explanation
if "explanation" not in st.session_state:
    st.session_state.explanation = ""

## input block
if "show_input" not in st.session_state:
    st.session_state.show_input = None  # Initially not showing the input form


# set the button modify, debug, review, reset
## button style
st.markdown(
    """
    <style>
    .element-container:has(style){
        display: none;
    }
    #button-after {
        display: none;
    }
    .element-container:has(#button-after) {
        display: none;
    }
    .element-container:has(#button-after) + div button {
        height: 50px;
        width: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<span id="button-after"></span>', unsafe_allow_html=True)

## Create a total of 5 columns: 3 for left buttons, 1 spacer, 1 for Reset
button_columns = st.columns([1, 1, 1, 5, 1])

## First three columns for left-aligned buttons
with button_columns[0]:
    if st.button("👀 Review"):
        st.session_state.show_input = "review"

with button_columns[1]:
    if st.button("🔧 Debug"):
        st.session_state.show_input = "debug"

with button_columns[2]:
    if st.button("📝 Modify"):
        st.session_state.show_input = "modify"

## Fourth column acts as a spacer (no content)

## Fifth column for Reset button
with button_columns[4]:
    if st.button("🔄 Reset"):
        st.session_state.ace_key_counter += 1
        st.session_state.code = ""  # Clear the code editor
        st.session_state.explanation = ""  # Clear the explanation if needed
        initial_messages = [{
            "role": "system",
            "content": prompts.general_ducky_code_starter_prompt()
        }]
        st.session_state.messages = initial_messages
        st.rerun()  # Rerun to update the UI immediately

# Display the code editor and the explanation
st.write("Write or paste your code below:")

# Check if code was updated and reset the flag
if st.session_state.code_updated:
    # The key has already been incremented in generate_code()
    st.session_state.code_updated = False

code = st_ace(
    value=st.session_state.code,
    placeholder="Write or paste your code here...",
    language='python',
    theme='dracula',
    auto_update=True,
    key=f"ace_editor_{st.session_state.ace_key_counter}"
)
# Update session state with the latest code
st.session_state.code = code
st.markdown(st.session_state.explanation)


# Process the user input based on the selected action
if st.session_state.show_input == "modify":
    # Use a form to better manage user input and resetting
    with st.form(key='input_form', clear_on_submit=True):
        modify_system_prompt = prompts.modify_code_prompt(code)
        st.session_state.messages.append({"role": "system", "content": modify_system_prompt})
        user_input_form = st.text_input("📝 How should I modify your code?", key='user_input')
        submit_form = st.form_submit_button(label='Submit')

        if submit_form and user_input_form.strip():
            # Process the input as above
            st.session_state.messages.append({"role": "user", "content": user_input_form})
            with st.spinner("I'm thinking..."):
                asyncio.run(util.generate_code(st.session_state.messages))
            st.rerun()
            
if st.session_state.show_input == "debug":
    # Use a form to better manage user input and resetting
    with st.form(key='input_form', clear_on_submit=True):
        debug_system_prompt = prompts.modify_code_prompt(code)
        st.session_state.messages.append({"role": "system", "content": debug_system_prompt})
        user_input_form = st.text_input("🔥 Paste your error text here if any...", key='user_input')
        submit_form = st.form_submit_button(label='Submit')

        if submit_form and user_input_form.strip():
            # Process the input as above
            st.session_state.messages.append({"role": "user", "content": user_input_form})
            with st.spinner("I'm thinking..."):
                asyncio.run(util.generate_code(st.session_state.messages))
            st.rerun()

if st.session_state.show_input == "review":
    review_system_prompt = prompts.review_prompt(code)
    st.session_state.messages.append({"role": "system", "content": review_system_prompt})
    with st.spinner("I'm thinking..."):
        asyncio.run(util.review_code(st.session_state.messages))
    st.session_state.show_input = None
    st.rerun()

