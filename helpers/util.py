from typing import List, Dict, Union, Tuple

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

import services.llm


async def run_conversation(messages: List[Dict[str, str]], message_placeholder: Union[DeltaGenerator, None] = None) \
        -> Tuple[List[Dict[str, str]], str]:
    full_response = ""

    chunks = services.llm.converse(messages)
    chunk = await anext(chunks, "END OF CHAT")
    while chunk != "END OF CHAT":
        print(f"Received chunk from LLM service: {chunk}")
        if chunk.startswith("EXCEPTION"):
            full_response = ":red[We are having trouble generating advice.  Please wait a minute and try again.]"
            break
        full_response = full_response + chunk

        if message_placeholder is not None:
            message_placeholder.code(full_response + "▌")

        chunk = await anext(chunks, "END OF CHAT")

    if message_placeholder is not None:
        message_placeholder.code(full_response)

    messages.append({"role": "assistant", "content": full_response})
    return messages, full_response


# Chat with the LLM, and update the messages list with the response.
# Handles the chat UI and partial responses along the way.
async def chat(messages, prompt):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        messages, response = await run_conversation(messages, message_placeholder)
        st.session_state.messages = messages
    return messages


async def generate_code(messages):
    # Generate the assistant's response
    message_placeholder = st.empty()
    messages, response = await run_conversation(messages, message_placeholder)
    st.session_state.messages = messages
    # Split the response into code and explanation
    import re
    code_blocks = re.findall(r'```(?:\w*\n)?(.*?)```', response, re.DOTALL)
    if code_blocks:
        code_content = code_blocks[0].strip()  # Extract and clean the code block
        # Remove the code block from the response to get the explanation
        explanation = re.sub(r'```.*?```', '', response, flags=re.DOTALL).strip()
        # Store the code_content in session_state so it can be used in the main code
        st.session_state["code"] = code_content
        # Increment key counter and rerun to update st_ace editor
        st.session_state.ace_key_counter += 1
        st.session_state.code_updated = True
    else:
        explanation = response.strip()
    
    # Display the explanation as markdown
    st.session_state["explanation"] = explanation
    return messages


async def review_code(messages):
    # Generate the assistant's response
    message_placeholder = st.empty()
    messages, response = await run_conversation(messages, message_placeholder)
    st.session_state.messages = messages

    # Display the messages as markdown
    st.session_state["explanation"] = response
    return messages


import PyPDF2
import base64
import io

from services.embedding import PDFSemanticSearch

async def ask_book(messages: List[Dict], prompt: str):
    """Chat with RAG using The Pragmatic Programmer book"""
    # Initialize the semantic search system
    searcher = PDFSemanticSearch()

    # Define paths
    pdf_path = "data/ThePragmaticProgrammer.pdf"
    embedding_csv_path = "data/ThePragmaticProgrammer.embeddings.csv"

    # Process or load embeddings
    df = searcher.process_embeddings(pdf_path, embedding_csv_path)

    relevant_chunks = searcher.find_relevant_chunks(prompt, df)

    if not relevant_chunks:
        await chat(messages, prompt)
        return messages
    
    # Construct RAG prompt
    context = "\n\n".join([
        f"From page {chunk['page_number']}:\n{chunk['context']}" 
        for chunk in relevant_chunks
    ])
    
    rag_prompt = f"""Based on the following excerpts from The Pragmatic Programmer, answer the user's question:

    Context from the book:
    {context}

    User's question: {prompt}

    Please provide a comprehensive answer that incorporates insights from the book. If the context doesn't fully address the question, you may add general software development knowledge to provide a complete response."""


    await chat(messages, prompt)
    st.session_state.page_number = relevant_chunks[0]['page_number']
    return messages

import streamlit as st
from pdf2image import convert_from_path
from PIL import Image
import os
import tempfile

def convert_pdf_to_image(pdf_path: str, page_number: int) -> Image.Image:
    """
    將 PDF 檔案的特定頁面轉換為圖片
    
    Parameters:
        pdf_path (str): PDF 檔案的路徑
        page_number (int): 要轉換的頁數 (從 1 開始)
        
    Returns:
        Image.Image: 轉換後的圖片物件
    """
    try:
        # 檢查輸入參數
        if not os.path.exists(pdf_path):
            raise FileNotFoundError("Cannot find PDF")
            
        # 使用 tempfile 來處理 Windows 中的問題
        with tempfile.TemporaryDirectory() as temp_dir:
            # 將 PDF 轉換為圖片
            # first_page 和 last_page 設定為相同數字來只轉換特定頁面
            images = convert_from_path(
                pdf_path,
                first_page=page_number,
                last_page=page_number,
                poppler_path=None,  # 如果在 Windows 上需要設定 poppler 路徑
                output_folder=temp_dir
            )
            
            if not images:
                raise ValueError(f"Cannot convert page {page_number}")
                
            return images[0]  # 返回轉換後的圖片
            
    except Exception as e:
        raise Exception(f"Convert error: {str(e)}")