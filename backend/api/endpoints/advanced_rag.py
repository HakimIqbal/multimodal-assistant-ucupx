from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import re
from api.auth.auth_middleware import get_current_user
from src.rag import query_rag, detect_language
from models import *
from sentence_transformers import SentenceTransformer, util
import os
import requests
from src.db import supabase
from models import get_vector_store

router = APIRouter()

class HybridSearchRequest(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None
    search_type: str = "hybrid"  # hybrid, vector, keyword
    vector_weight: float = 0.7
    keyword_weight: float = 0.3
    max_results: int = 10
    similarity_threshold: float = 0.7
    include_metadata: bool = True

class QueryExpansionRequest(BaseModel):
    query: str
    expansion_type: str = "synonyms"  # synonyms, related, semantic
    max_expansions: int = 3
    language: str = "en"
    source_language: Optional[str] = None

class ConfidenceRequest(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    model_name: str

class MultiLanguageRequest(BaseModel):
    query: str
    target_language: str
    source_language: Optional[str] = None
    preserve_context: bool = True

class AdvancedRAGResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    search_type: str
    query_expansions: Optional[List[str]] = None
    processing_time: float
    metadata: Dict[str, Any]

# Initialize processors - use existing functions instead of classes
# rag_processor = RAGProcessor()  # Remove this
# vector_db = VectorDB()  # Remove this

# Language detection patterns
LANGUAGE_PATTERNS = {
    "en": r"[a-zA-Z]",
    "id": r"[a-zA-Z]",
    "ja": r"[一-龯]",
    "ko": r"[가-힣]",
    "zh": r"[一-龯]",
    "ar": r"[ء-ي]",
    "hi": r"[ऀ-ॿ]",
    "th": r"[ก-๛]"
}

# Semantic expansion
model = SentenceTransformer(os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2"))

def expand_query_synonyms(query: str, language: str = "en") -> List[str]:
    """Expand query using synonyms"""
    # Simple synonym expansion - in production, use proper thesaurus API
    synonyms = {
        "en": {
            "help": ["assist", "support", "aid"],
            "explain": ["describe", "clarify", "elucidate"],
            "analyze": ["examine", "study", "investigate"],
            "compare": ["contrast", "differentiate", "distinguish"],
            "create": ["generate", "produce", "make"],
            "find": ["locate", "discover", "identify"],
            "show": ["display", "present", "demonstrate"],
            "use": ["utilize", "employ", "apply"],
            "get": ["obtain", "acquire", "receive"],
            "make": ["create", "build", "construct"]
        },
        "id": {
            "bantu": ["tolong", "membantu", "mendukung"],
            "jelaskan": ["terangkan", "uraikan", "jelaskan"],
            "analisis": ["periksa", "pelajari", "selidiki"],
            "bandingkan": ["banding", "bedakan", "bandingkan"],
            "buat": ["ciptakan", "hasilkan", "buat"],
            "temukan": ["cari", "temukan", "identifikasi"],
            "tunjukkan": ["tampilkan", "perlihatkan", "demonstrasikan"],
            "gunakan": ["pakai", "gunakan", "terapkan"],
            "dapatkan": ["peroleh", "dapatkan", "terima"],
            "buat": ["ciptakan", "buat", "bangun"]
        }
    }
    
    expanded_queries = [query]
    query_words = query.lower().split()
    
    lang_synonyms = synonyms.get(language, synonyms["en"])
    
    for word in query_words:
        if word in lang_synonyms:
            for synonym in lang_synonyms[word]:
                new_query = query.lower().replace(word, synonym)
                if new_query not in expanded_queries:
                    expanded_queries.append(new_query)
    
    return expanded_queries[:5]  # Limit expansions

def expand_query_semantic(query: str, language: str = "en") -> List[str]:
    # Contoh: gunakan embedding similarity untuk cari query serupa dari daftar preset
    preset_queries = [
        "help me", "explain this", "analyze data", "compare results", "create summary", "find information", "show details", "use tool", "get answer", "make report"
    ]
    query_emb = model.encode(query, convert_to_tensor=True)
    preset_embs = model.encode(preset_queries, convert_to_tensor=True)
    similarities = util.pytorch_cos_sim(query_emb, preset_embs)[0]
    top_indices = similarities.argsort(descending=True)[:5]
    return [preset_queries[i] for i in top_indices]

def calculate_answer_confidence(query: str, answer: str, sources: List[Dict[str, Any]], model_name: str) -> float:
    """Calculate confidence score for answer"""
    try:
        # Simple confidence calculation based on multiple factors
        confidence_factors = []
        
        # 1. Source relevance (based on similarity scores)
        if sources:
            avg_similarity = sum(s.get("similarity", 0) for s in sources) / len(sources)
            confidence_factors.append(min(avg_similarity, 1.0))
        else:
            confidence_factors.append(0.3)  # Low confidence if no sources
        
        # 2. Answer length (reasonable length suggests completeness)
        answer_length = len(answer.split())
        if 10 <= answer_length <= 500:
            confidence_factors.append(0.8)
        elif answer_length < 10:
            confidence_factors.append(0.4)
        else:
            confidence_factors.append(0.6)
        
        # 3. Source count (more sources = higher confidence)
        source_count = len(sources)
        if source_count >= 3:
            confidence_factors.append(0.9)
        elif source_count >= 1:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.3)
        
        # 4. Query-answer relevance (simple keyword matching)
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        if query_words:
            overlap = len(query_words.intersection(answer_words)) / len(query_words)
            confidence_factors.append(min(overlap * 2, 1.0))
        else:
            confidence_factors.append(0.5)
        
        # 5. Model confidence (based on model type)
        model_confidence = {
            "gpt-4": 0.9,
            "gpt-3.5-turbo": 0.8,
            "claude-3": 0.9,
            "gemini-pro": 0.85,
            "groq-llama3": 0.8
        }.get(model_name.lower(), 0.7)
        
        confidence_factors.append(model_confidence)
        
        # Calculate final confidence as average of factors
        final_confidence = sum(confidence_factors) / len(confidence_factors)
        
        return round(final_confidence, 3)
        
    except Exception as e:
        print(f"Error calculating confidence: {e}")
        return 0.5  # Default confidence

@router.post("/advanced-rag/hybrid-search")
async def hybrid_search(request: HybridSearchRequest, user=Depends(get_current_user)):
    """
    Perform hybrid search combining vector and keyword search
    """
    try:
        start_time = datetime.utcnow()
        
        # Detect language
        language = detect_language(request.query)
        
        # Perform vector search
        vector_results = await perform_vector_search(
            request.query, 
            request.document_ids, 
            request.max_results
        )
        
        # Perform keyword search
        keyword_results = await perform_keyword_search(
            request.query, 
            request.document_ids, 
            request.max_results
        )
        
        # Combine results
        combined_results = combine_search_results(
            vector_results, 
            keyword_results, 
            request.vector_weight, 
            request.keyword_weight
        )
        
        # Filter by similarity threshold
        filtered_results = [
            result for result in combined_results 
            if result.get("similarity", 0) >= request.similarity_threshold
        ]
        
        # Generate response using RAG
        context = "\n".join([result.get("content", "") for result in filtered_results[:3]])
        prompt = f"Based on the following context, answer the question: {request.query}\n\nContext: {context}"
        
        answer, chat_history, source_info = query_rag(request.query)
        
        # Calculate confidence
        confidence = calculate_answer_confidence(
            request.query, 
            answer, 
            filtered_results, 
            "llama3-70b-8192"
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AdvancedRAGResponse(
            answer=answer,
            sources=filtered_results[:request.max_results] if request.include_metadata else [],
            confidence_score=confidence,
            search_type=request.search_type,
            query_expansions=None,
            processing_time=processing_time,
            metadata={
                "language": language,
                "vector_results_count": len(vector_results),
                "keyword_results_count": len(keyword_results),
                "combined_results_count": len(combined_results),
                "filtered_results_count": len(filtered_results)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")

async def perform_vector_search(query: str, document_ids: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Perform vector search using embeddings"""
    try:
        vector_store = get_vector_store()
        if not vector_store:
            return []
        
        # Perform similarity search
        results = vector_store.similarity_search_with_score(query, k=limit)
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity": 1 - score,  # Convert distance to similarity
                "source": "vector"
            })
        
        return formatted_results
        
    except Exception as e:
        print(f"Vector search error: {e}")
        return []

@router.post("/advanced-rag/query-expansion")
async def expand_query(request: QueryExpansionRequest, user=Depends(get_current_user)):
    """
    Expand query using synonyms, related terms, or semantic similarity
    """
    try:
        # Detect language if not specified
        if not request.source_language:
            detected_lang = detect_language(request.query)
        else:
            detected_lang = request.source_language
        
        expanded_queries = []
        
        if request.expansion_type == "synonyms":
            expanded_queries = expand_query_synonyms(request.query, detected_lang)
        elif request.expansion_type == "semantic":
            expanded_queries = expand_query_semantic(request.query, detected_lang)
        elif request.expansion_type == "related":
            # Combine synonyms and semantic
            synonym_queries = expand_query_synonyms(request.query, detected_lang)
            semantic_queries = expand_query_semantic(request.query, detected_lang)
            expanded_queries = list(set(synonym_queries + semantic_queries))
        
        # Limit expansions
        expanded_queries = expanded_queries[:request.max_expansions]
        
        return {
            "success": True,
            "original_query": request.query,
            "expanded_queries": expanded_queries,
            "expansion_type": request.expansion_type,
            "language": detected_lang,
            "total_expansions": len(expanded_queries)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query expansion failed: {str(e)}")

@router.post("/advanced-rag/confidence")
async def calculate_confidence(request: ConfidenceRequest, user=Depends(get_current_user)):
    """
    Calculate confidence score for an answer
    """
    try:
        confidence = calculate_answer_confidence(
            request.query,
            request.answer,
            request.sources,
            request.model_name
        )
        
        # Detailed confidence breakdown
        confidence_breakdown = {
            "overall_confidence": confidence,
            "factors": {
                "source_relevance": 0.0,
                "answer_completeness": 0.0,
                "source_count": 0.0,
                "query_relevance": 0.0,
                "model_confidence": 0.0
            },
            "recommendations": []
        }
        
        # Generate recommendations based on confidence
        if confidence < 0.5:
            confidence_breakdown["recommendations"].append("Consider rephrasing your question")
            confidence_breakdown["recommendations"].append("Add more specific context")
        elif confidence < 0.7:
            confidence_breakdown["recommendations"].append("Answer may need verification")
        
        return {
            "success": True,
            "confidence_score": confidence,
            "confidence_level": "high" if confidence >= 0.8 else "medium" if confidence >= 0.6 else "low",
            "breakdown": confidence_breakdown
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confidence calculation failed: {str(e)}")

@router.post("/advanced-rag/multilanguage")
async def multi_language_rag(request: MultiLanguageRequest, user=Depends(get_current_user)):
    """
    Perform RAG in multiple languages with translation
    """
    try:
        start_time = datetime.utcnow()
        
        # Detect source language if not provided
        source_lang = request.source_language or detect_language(request.query)
        
        # Translate query if needed
        translated_query = request.query
        if source_lang != request.target_language:
            translated_query = translate_text(request.query, source_lang, request.target_language)
        
        # Perform RAG with translated query
        answer, chat_history, source_info = query_rag(translated_query)
        
        # Translate answer back if needed
        final_answer = answer
        if source_lang != request.target_language and request.preserve_context:
            final_answer = translate_text(answer, request.target_language, source_lang)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AdvancedRAGResponse(
            answer=final_answer,
            sources=[],  # Sources would be available in source_info
            confidence_score=0.8,  # Default confidence
            search_type="multilanguage",
            query_expansions=None,
            processing_time=processing_time,
            metadata={
                "source_language": source_lang,
                "target_language": request.target_language,
                "translation_used": source_lang != request.target_language
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-language RAG failed: {str(e)}")

@router.get("/advanced-rag/languages")
async def get_supported_languages(user=Depends(get_current_user)):
    """
    Get list of supported languages for RAG
    """
    supported_languages = {
        "en": {"name": "English", "code": "en", "native_name": "English"},
        "id": {"name": "Indonesian", "code": "id", "native_name": "Bahasa Indonesia"},
        "ja": {"name": "Japanese", "code": "ja", "native_name": "日本語"},
        "ko": {"name": "Korean", "code": "ko", "native_name": "한국어"},
        "zh": {"name": "Chinese", "code": "zh", "native_name": "中文"},
        "ar": {"name": "Arabic", "code": "ar", "native_name": "العربية"},
        "hi": {"name": "Hindi", "code": "hi", "native_name": "हिन्दी"},
        "th": {"name": "Thai", "code": "th", "native_name": "ไทย"},
        "es": {"name": "Spanish", "code": "es", "native_name": "Español"},
        "fr": {"name": "French", "code": "fr", "native_name": "Français"},
        "de": {"name": "German", "code": "de", "native_name": "Deutsch"},
        "pt": {"name": "Portuguese", "code": "pt", "native_name": "Português"},
        "ru": {"name": "Russian", "code": "ru", "native_name": "Русский"},
        "it": {"name": "Italian", "code": "it", "native_name": "Italiano"},
        "nl": {"name": "Dutch", "code": "nl", "native_name": "Nederlands"}
    }
    
    return {
        "success": True,
        "languages": supported_languages,
        "total": len(supported_languages),
        "default_language": "en"
    }

# Helper functions
async def perform_keyword_search(query: str, document_ids: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Perform keyword-based search"""
    try:
        # Simple keyword search implementation
        # In production, use proper full-text search engine
        query_words = query.lower().split()
        
        # Search in document content
        search_conditions = []
        for word in query_words:
            search_conditions.append(f"content.ilike.%{word}%")
        
        # Build query
        query_builder = supabase.table("documents").select("*")
        
        if document_ids:
            query_builder = query_builder.in_("id", document_ids)
        
        # Add search conditions
        for condition in search_conditions:
            query_builder = query_builder.or_(condition)
        
        res = query_builder.limit(limit).execute()
        
        # Format results
        results = []
        for doc in res.data:
            results.append({
                "id": doc["id"],
                "content": doc.get("content", "")[:500],  # Truncate for display
                "filename": doc.get("filename", ""),
                "similarity": 0.8,  # Placeholder similarity score
                "metadata": {
                    "category": doc.get("category"),
                    "upload_timestamp": doc.get("upload_timestamp")
                }
            })
        
        return results
        
    except Exception as e:
        print(f"Keyword search error: {e}")
        return []

def combine_search_results(vector_results: List[Dict], keyword_results: List[Dict], 
                          vector_weight: float = 0.7, keyword_weight: float = 0.3) -> List[Dict]:
    """Combine vector and keyword search results"""
    combined = {}
    
    # Process vector results
    for i, result in enumerate(vector_results):
        doc_id = result.get("id")
        if doc_id:
            combined[doc_id] = {
                "id": doc_id,
                "content": result.get("content", ""),
                "filename": result.get("filename", ""),
                "similarity": result.get("similarity", 0) * vector_weight,
                "metadata": result.get("metadata", {}),
                "sources": ["vector"]
            }
    
    # Process keyword results
    for i, result in enumerate(keyword_results):
        doc_id = result.get("id")
        if doc_id:
            if doc_id in combined:
                # Combine scores
                combined[doc_id]["similarity"] += result.get("similarity", 0) * keyword_weight
                combined[doc_id]["sources"].append("keyword")
            else:
                combined[doc_id] = {
                    "id": doc_id,
                    "content": result.get("content", ""),
                    "filename": result.get("filename", ""),
                    "similarity": result.get("similarity", 0) * keyword_weight,
                    "metadata": result.get("metadata", {}),
                    "sources": ["keyword"]
                }
    
    # Sort by combined similarity score
    sorted_results = sorted(combined.values(), key=lambda x: x["similarity"], reverse=True)
    
    return sorted_results

# Translation
GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")
def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    # Fitur translate hanya tersedia di versi berbayar, tampilkan notif soon
    return "Translation feature coming soon (free version)" 