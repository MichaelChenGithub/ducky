import streamlit as st
import time
from services.audio import record_audio, transcribe_audio, generate_gpt_response, speak_text
import threading

st.set_page_config(
    page_title="Voice Chat",
    page_icon="🎤",
    layout="wide"
)

import helpers.sidebar
helpers.sidebar.show()

st.header("Voice Chat")
st.write("Get instant answers to your software development and coding questions using the microphone.")

def process_audio():
    progress_placeholder = st.empty()
    
    with progress_placeholder.container():
        with st.spinner('Recording your question...'):
            if not record_audio():
                st.error("Failed to record audio")
                return

        with st.spinner('Processing your question...'):
            question = transcribe_audio()
            if not question:
                st.error("Failed to transcribe audio")
                return
            
            st.write("You asked:", question)
            
            response = generate_gpt_response(question)
            if not response:
                st.error("Failed to generate response")
                return
            
            st.write("Answer:", response)
            speak_text(response)

if st.button("🎤 Record (5 seconds)"):
    process_audio()
