import streamlit as st
import requests
import os
import tempfile
from models import SUPPORTED_GENERAL_CHAT_MODELS, SUPPORTED_CODER_CHAT_MODELS, SUPPORTED_PDF_CHAT_MODELS, SUPPORTED_GROQ_DEFAULT_MODELS, SUPPORTED_GEMINI_DEFAULT_MODELS
import io

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Multimodal Assistant", layout="wide")
st.title("🤖 Multimodal Assistant")
st.write("Pilih fitur di bawah untuk berinteraksi dengan asisten!")

if "general_chat_history" not in st.session_state:
    st.session_state["general_chat_history"] = []
if "coder_chat_history" not in st.session_state:
    st.session_state["coder_chat_history"] = []
if "rag_chat_history" not in st.session_state:
    st.session_state["rag_chat_history"] = []

tab1, tab2, tab3 = st.tabs(["General Chat", "Coder Chat", "RAG System"])  # Hapus tab OCR

with tab1:
    st.header("💬 General Chat")
    st.write("Tanyakan pertanyaan umum (misalnya, definisi atau fakta sederhana). Untuk coding, gunakan Coder Chat.")
    model_general = st.selectbox(
        "Pilih Model (General Chat):",
        SUPPORTED_GENERAL_CHAT_MODELS + SUPPORTED_GROQ_DEFAULT_MODELS + SUPPORTED_GEMINI_DEFAULT_MODELS,
        index=0,
        key="model_general"
    )
    query_general = st.text_input("Masukkan pertanyaan (General):", key="query_general")
    if st.button("Tanya (General)"):
        response = requests.post(f"{API_URL}/chat/general/", json={"query": query_general, "model_name": model_general})
        if response.status_code == 200:
            st.markdown("**Jawaban:**")
            st.markdown(response.json()["response"])
            st.write(f"**Model Digunakan:** {response.json()['model']}")
            st.session_state["general_chat_history"].append({"user": query_general, "assistant": response.json()["response"]})
        else:
            st.error(f"Gagal mendapatkan jawaban: {response.status_code} - {response.text}")
    
    if st.session_state["general_chat_history"]:
        st.subheader("Riwayat Percakapan")
        for chat in st.session_state["general_chat_history"]:
            st.markdown(f"**User:** {chat['user']}")
            st.markdown(f"**Assistant:** {chat['assistant']}")
            st.markdown("---")

with tab2:
    st.header("💻 Coder Chat")
    st.write("Tanyakan hal terkait coding (misalnya, membuat kode, debugging, atau penjelasan konsep pemrograman)!")
    model_coder = st.selectbox(
        "Pilih Model (Coder Chat):",
        SUPPORTED_CODER_CHAT_MODELS + SUPPORTED_GROQ_DEFAULT_MODELS + SUPPORTED_GEMINI_DEFAULT_MODELS,
        index=0,
        key="model_coder"
    )
    query_coder = st.text_input("Masukkan pertanyaan coding:", key="query_coder")
    if st.button("Tanya (Coder)"):
        response = requests.post(f"{API_URL}/coder/coder/", json={"query": query_coder, "model_name": model_coder})
        if response.status_code == 200:
            st.markdown("**Jawaban:**")
            st.markdown(response.json()["response"])
            st.write(f"**Model Digunakan:** {response.json()['model']}")
            st.session_state["coder_chat_history"].append({"user": query_coder, "assistant": response.json()["response"]})
        else:
            st.error(f"Gagal mendapatkan jawaban: {response.status_code} - {response.text}")
    
    if st.session_state["coder_chat_history"]:
        st.subheader("Riwayat Percakapan")
        for chat in st.session_state["coder_chat_history"]:
            st.markdown(f"**User:** {chat['user']}")
            st.markdown(f"**Assistant:** {chat['assistant']}")
            st.markdown("---")

with tab3:
    st.header("📜 RAG System")
    st.write("Unggah dokumen (PDF, maksimal 10MB) dan tanyakan sesuatu berdasarkan dokumen tersebut!")  
    st.subheader("Upload Dokumen")
    uploaded_files = st.file_uploader("Pilih file dokumen", type=["pdf"], accept_multiple_files=True) 
    skip_duplicates = st.checkbox("Lewati file duplikat (jika nama sudah ada)")
    if st.button("Upload"):
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_content = uploaded_file.read()
                if len(file_content) > 10 * 1024 * 1024:
                    st.error(f"❌ File '{uploaded_file.name}' melebihi batas ukuran 10MB.")
                    continue
                files = [("files", (uploaded_file.name, file_content, uploaded_file.type))]
                response = requests.post(f"{API_URL}/rag/upload/", files=files, data={"skip_duplicates": skip_duplicates})
                if response.status_code == 200:
                    st.success(f"✅ Berhasil mengupload: {uploaded_file.name}")
                    st.write("**System Message:**", response.json()["system_message"])
                    for result in response.json()["results"]:
                        if result["status"] == "error":
                            st.error(f"❌ Gagal memproses {result['filename']}: {result['text']}")
                        elif result["status"] == "skipped":
                            st.warning(f"⚠️ {result['text']}")
                        else:
                            st.info(f"📄 File {result['filename']}: {result['text']}")
                            if "preview" in result:
                                st.write(f"**Pratinjau Teks (100 karakter pertama):** {result['preview']}")
                else:
                    st.error(f"❌ Gagal upload: {uploaded_file.name} - {response.status_code} - {response.text}")
        else:
            st.warning("Tidak ada file yang dipilih untuk diupload.")
    
    st.subheader("Tanya Berdasarkan Dokumen")
    model_rag = st.selectbox(
        "Pilih Model (RAG System):",
        SUPPORTED_PDF_CHAT_MODELS + SUPPORTED_GROQ_DEFAULT_MODELS + SUPPORTED_GEMINI_DEFAULT_MODELS,
        index=0,
        key="model_rag"
    )
    query_rag = st.text_input("Masukkan pertanyaan (RAG):", key="query_rag")
    if st.button("Tanya (RAG)"):
        response = requests.post(f"{API_URL}/rag/query/", json={
            "question": query_rag,
            "chat_history": st.session_state["rag_chat_history"]
        })
        if response.status_code == 200:
            st.markdown("**Jawaban:**")
            st.markdown(response.json()["answer"])
            st.write(f"**Model Digunakan:** {model_rag}")
            st.session_state["rag_chat_history"] = response.json()["chat_history"]
        else:
            st.error(f"Gagal mendapatkan jawaban: {response.status_code} - {response.text}")
    
    if st.session_state["rag_chat_history"]:
        st.subheader("Riwayat Percakapan")
        for i in range(0, len(st.session_state["rag_chat_history"]), 2):
            user_msg = st.session_state["rag_chat_history"][i]
            assistant_msg = st.session_state["rag_chat_history"][i + 1]
            st.markdown(f"**User:** {user_msg['content']}")
            st.markdown(f"**Assistant:** {assistant_msg['content']}")
            st.markdown("---")