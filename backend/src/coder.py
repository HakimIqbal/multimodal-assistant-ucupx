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

coder_chat_history = ChatMessageHistory()

def detect_language(query: str) -> str:
    indonesian_words = {"apa", "bagaimana", "siapa", "dimana", "kapan", "mengapa", "adalah"}
    query_lower = query.lower()
    if any(word in query_lower for word in indonesian_words):
        return "id"
    return "en"

def detect_non_coding_query(query: str) -> bool:
    non_coding_keywords = {"definisi", "pengertian", "apa itu", "sejarah", "fakta"}
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in non_coding_keywords) and "kode" not in query_lower and "code" not in query_lower

def chat_coder(query: str, model_name: str = "llama3-70b-8192", session_id: str = ""):
    # Intent detection
    coding_keywords = ["code", "python", "function", "bug", "error", "debug", "class", "variable", "loop", "array", "list", "dict", "compile", "syntax", "logic", "algoritma", "algoritme", "programming", "pemrograman"]
    q_lower = query.lower()
    if not any(word in q_lower for word in coding_keywords):
        return "Pertanyaan Anda tidak terdeteksi sebagai coding. Silakan gunakan fitur General Chat untuk pertanyaan umum."
    # Contextual memory per session
    if not hasattr(chat_coder, "session_histories"):
        chat_coder.session_histories = {}
    if session_id not in chat_coder.session_histories:
        chat_coder.session_histories[session_id] = ChatMessageHistory()
    if session_id is None:
        session_id = ""
    chat_history_store = chat_coder.session_histories[str(session_id)]
    # Prompt engineering
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        System: Anda adalah asisten coding yang memberikan jawaban detail, jelas, dan terstruktur. Gunakan Markdown dan sertakan contoh kode dalam blok kode (```). 
        - Jawab hanya pertanyaan terkait coding (misalnya, membuat kode, debugging, penjelasan konsep pemrograman).
        - Jika pertanyaan tidak terkait coding, jawab: 'Gunakan fitur General Chat untuk pertanyaan umum.'
        - Jika pertanyaan memerlukan dokumen, jawab: 'Gunakan fitur RAG System untuk pertanyaan berbasis dokumen.'
        - Gunakan bahasa yang sama dengan input pengguna.
        - Jika user mengirim error log, jelaskan penyebab error dan cara mengatasinya.
        - Berikan penjelasan singkat, contoh kode, dan tips best practice.
        """),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{query}")
    ])
    # Deteksi error log
    is_error_log = any(x in q_lower for x in ["traceback", "error", "exception", "line "])
    if is_error_log:
        query += "\nJelaskan error ini dan cara mengatasinya."
    llm = get_groq_model(model_name)
    prompt_msgs = prompt.format_messages(query=query, chat_history=chat_history_store.messages)
    response = llm.invoke(prompt_msgs)
    answer = response.content
    if isinstance(answer, str):
        answer = answer.strip()
    # Format kode rapi
    if "```" not in answer and ("def " in answer or "class " in answer or "import " in answer):
        answer = f"```python\n{answer}\n```"
    chat_history_store.add_user_message(query)
    chat_history_store.add_ai_message(answer)
    # Logging
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "input": query,
        "output": answer,
        "metadata": {
            "source": "Coder Chatbot",
            "model": model_name,
            "context": "Coding",
            "session_id": session_id
        }
    }
    log_to_supabase("coder_logs", log_entry)
    return answer