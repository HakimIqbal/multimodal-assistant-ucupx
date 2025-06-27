import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from models import get_groq_model
from src.db import log_to_supabase

# Get LANGSMITH_TRACING from environment variable
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

chat_history_store = ChatMessageHistory()

prompt_template = ChatPromptTemplate.from_messages([
    ("system", """
    System: Anda adalah asisten AI untuk pertanyaan umum. Jawab singkat, langsung ke inti, dan gunakan Markdown.
    - HANYA jawab pertanyaan umum (misalnya, definisi, fakta sederhana).
    - Jika pertanyaan terkait coding (misalnya, membuat kode, debugging), jawab: "Gunakan fitur Coder Chat untuk pertanyaan coding."
    - Jika pertanyaan memerlukan dokumen, jawab: "Gunakan fitur RAG System untuk pertanyaan berbasis dokumen."
    - Gunakan bahasa yang sama dengan input pengguna.
    """),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{query}")
])

def detect_language(query: str) -> str:
    indonesian_words = {"apa", "bagaimana", "siapa", "dimana", "kapan", "mengapa", "adalah"}
    query_lower = query.lower()
    if any(word in query_lower for word in indonesian_words):
        return "id"
    return "en"

def detect_coding_query(query: str) -> bool:
    coding_keywords = {"kode", "code", "program", "fungsi", "function", "debug", "error", "script", "buatkan", "generate", "perbaiki"}
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in coding_keywords)

def chat_general(query: str, model_name: str = "llama3-70b-8192", session_id: str = ""):
    # Intent detection
    coding_keywords = ["code", "python", "function", "bug", "error", "debug", "class", "variable", "loop", "array", "list", "dict", "compile", "syntax", "logic", "algoritma", "algoritme", "programming", "pemrograman"]
    doc_keywords = ["pdf", "dokumen", "document", "file", "rag", "extract", "ringkas", "summary", "upload"]
    q_lower = query.lower()
    if any(word in q_lower for word in coding_keywords):
        return "Pertanyaan Anda terdeteksi sebagai coding. Silakan gunakan fitur Coder Chat untuk pertanyaan terkait pemrograman."
    if any(word in q_lower for word in doc_keywords):
        return "Pertanyaan Anda terdeteksi terkait dokumen. Silakan gunakan fitur RAG System untuk pertanyaan berbasis dokumen."
    # Contextual memory per session
    if not hasattr(chat_general, "session_histories"):
        chat_general.session_histories = {}
    session_id_str = str(session_id) if session_id else "default"
    if session_id_str not in chat_general.session_histories:
        chat_general.session_histories[session_id_str] = ChatMessageHistory()
    chat_history_store = chat_general.session_histories[session_id_str]
    # Prompt
    prompt = prompt_template.format_messages(query=query, chat_history=chat_history_store.messages)
    llm = get_groq_model(model_name)
    response = llm.invoke(prompt)
    answer = response.content
    if isinstance(answer, str):
        answer = answer.strip()
    else:
        answer = str(answer).strip()
        if len(answer.split()) > 50 and "\n" not in answer:
            answer = "\n".join([answer[i:i+100] for i in range(0, len(answer), 100)])
        chat_history_store.add_user_message(query)
        chat_history_store.add_ai_message(answer)
    return answer