# -*- coding: utf-8 -*-
"""
Retrieval Strategies - Các chiến lược tìm kiếm khác nhau
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .types import RetrievalContext, SearchResult, SearchStrategy
import logging

logger = logging.getLogger(__name__)

class BaseRetrievalStrategy(ABC):
    """Base class cho các retrieval strategies"""
    
    def __init__(self, pgvector_service, embeddings):
        self.pgvector_service = pgvector_service
        self.embeddings = embeddings
    
    @abstractmethod
    def retrieve(self, context: RetrievalContext) -> List[SearchResult]:
        """Thực hiện retrieval dựa trên strategy"""
        pass
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding cho text"""
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

class SemanticRetrievalStrategy(BaseRetrievalStrategy):
    """Chiến lược tìm kiếm semantic thuần túy"""
    
    def retrieve(self, context: RetrievalContext) -> List[SearchResult]:
        """Tìm kiếm dựa trên semantic similarity"""
        try:
            # Generate embedding cho query
            query_embedding = self._generate_embedding(context.query)
            if not query_embedding:
                return []
            
            # Build where clause từ filters
            where_clause, where_params = self._build_where_clause(context.filters)
            
            # Thực hiện similarity search
            results = self.pgvector_service.similarity_search(
                query_embedding=query_embedding,
                limit=context.max_results,
                where_clause=where_clause,
                where_params=where_params
            )
            
            # Convert sang SearchResult format
            search_results = []
            for result in results:
                if result.get("similarity_score", 0) >= context.similarity_threshold:
                    search_results.append(SearchResult(
                        establishment_id=result["establishment_id"],
                        name=result["metadata"].get("name", "Unknown"),
                        relevance_score=result["similarity_score"],
                        metadata=result["metadata"],
                        explanation=f"Tìm thấy dựa trên semantic similarity (score: {result['similarity_score']:.3f})"
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in semantic retrieval: {e}")
            return []

class HybridRetrievalStrategy(BaseRetrievalStrategy):
    """Chiến lược tìm kiếm hybrid kết hợp semantic và keyword"""
    
    def retrieve(self, context: RetrievalContext) -> List[SearchResult]:
        """Tìm kiếm hybrid với semantic + keyword matching"""
        try:
            # Semantic search
            semantic_results = self._semantic_search(context)
            
            # Keyword search
            keyword_results = self._keyword_search(context)
            
            # Combine và rank results
            combined_results = self._combine_results(semantic_results, keyword_results)
            
            return combined_results[:context.max_results]
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {e}")
            return []
    
    def _semantic_search(self, context: RetrievalContext) -> List[SearchResult]:
        """Thực hiện semantic search"""
        query_embedding = self._generate_embedding(context.query)
        if not query_embedding:
            return []
        
        where_clause, where_params = self._build_where_clause(context.filters)
        
        results = self.pgvector_service.similarity_search(
            query_embedding=query_embedding,
            limit=context.max_results * 2,  # Lấy nhiều hơn để có thể combine
            where_clause=where_clause,
            where_params=where_params
        )
        
        search_results = []
        for result in results:
            if result.get("similarity_score", 0) >= context.similarity_threshold * 0.8:  # Threshold thấp hơn
                search_results.append(SearchResult(
                    establishment_id=result["establishment_id"],
                    name=result["metadata"].get("name", "Unknown"),
                    relevance_score=result["similarity_score"],
                    metadata=result["metadata"],
                    explanation=f"Semantic match (score: {result['similarity_score']:.3f})"
                ))
        
        return search_results
    
    def _keyword_search(self, context: RetrievalContext) -> List[SearchResult]:
        """Thực hiện keyword search"""
        # Extract keywords từ query
        keywords = self._extract_keywords(context.query)
        
        # Tạo keyword-based query
        keyword_query = self._create_keyword_query(keywords)
        
        # Generate embedding cho keyword query
        query_embedding = self._generate_embedding(keyword_query)
        if not query_embedding:
            return []
        
        where_clause, where_params = self._build_where_clause(context.filters)
        
        results = self.pgvector_service.similarity_search(
            query_embedding=query_embedding,
            limit=context.max_results,
            where_clause=where_clause,
            where_params=where_params
        )
        
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                establishment_id=result["establishment_id"],
                name=result["metadata"].get("name", "Unknown"),
                relevance_score=result["similarity_score"] * 0.8,  # Weight thấp hơn semantic
                metadata=result["metadata"],
                explanation=f"Keyword match (score: {result['similarity_score']:.3f})"
            ))
        
        return search_results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords từ query"""
        # Remove common stop words
        stop_words = {"tôi", "muốn", "tìm", "kiếm", "ở", "tại", "với", "có", "một", "cái", "này"}
        words = query.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords
    
    def _create_keyword_query(self, keywords: List[str]) -> str:
        """Tạo query từ keywords"""
        return " ".join(keywords)
    
    def _combine_results(self, semantic_results: List[SearchResult], keyword_results: List[SearchResult]) -> List[SearchResult]:
        """Combine và rank results"""
        # Create a dict để track best score cho mỗi establishment
        combined = {}
        
        # Add semantic results
        for result in semantic_results:
            combined[result.establishment_id] = result
        
        # Add hoặc update với keyword results
        for result in keyword_results:
            if result.establishment_id in combined:
                # Nếu đã có, update score nếu keyword score cao hơn
                if result.relevance_score > combined[result.establishment_id].relevance_score:
                    combined[result.establishment_id].relevance_score = result.relevance_score
                    combined[result.establishment_id].explanation += f" + {result.explanation}"
            else:
                combined[result.establishment_id] = result
        
        # Sort by relevance score
        return sorted(combined.values(), key=lambda x: x.relevance_score, reverse=True)

class ContextualRetrievalStrategy(BaseRetrievalStrategy):
    """Chiến lược tìm kiếm contextual dựa trên conversation history"""
    
    def retrieve(self, context: RetrievalContext) -> List[SearchResult]:
        """Tìm kiếm contextual với conversation history"""
        try:
            # Build contextual query
            contextual_query = self._build_contextual_query(context)
            
            # Generate embedding cho contextual query
            query_embedding = self._generate_embedding(contextual_query)
            if not query_embedding:
                return []
            
            where_clause, where_params = self._build_where_clause(context.filters)
            
            results = self.pgvector_service.similarity_search(
                query_embedding=query_embedding,
                limit=context.max_results,
                where_clause=where_clause,
                where_params=where_params
            )
            
            search_results = []
            for result in results:
                if result.get("similarity_score", 0) >= context.similarity_threshold:
                    search_results.append(SearchResult(
                        establishment_id=result["establishment_id"],
                        name=result["metadata"].get("name", "Unknown"),
                        relevance_score=result["similarity_score"],
                        metadata=result["metadata"],
                        explanation=f"Contextual match (score: {result['similarity_score']:.3f})"
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in contextual retrieval: {e}")
            return []
    
    def _build_contextual_query(self, context: RetrievalContext) -> str:
        """Build contextual query từ conversation history"""
        query_parts = [context.query]
        
        # Thêm context từ user preferences
        if context.user_preferences:
            if context.user_preferences.get("budget_range"):
                query_parts.append(f"ngân sách {context.user_preferences['budget_range']}")
            if context.user_preferences.get("preferred_amenities"):
                amenities = context.user_preferences["preferred_amenities"]
                if isinstance(amenities, list):
                    query_parts.append(f"có {', '.join(amenities[:3])}")
        
        # Thêm context từ conversation history
        if context.conversation_history:
            recent_context = self._extract_recent_context(context.conversation_history)
            if recent_context:
                query_parts.append(recent_context)
        
        return " ".join(query_parts)
    
    def _extract_recent_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Extract context từ conversation history"""
        if not conversation_history:
            return ""
        
        # Lấy context từ 2-3 messages gần nhất
        recent_messages = conversation_history[-3:]
        context_parts = []
        
        for message in recent_messages:
            if message.get("type") == "user" and message.get("content"):
                content = message["content"].lower()
                # Extract key information
                if "khách sạn" in content:
                    context_parts.append("khách sạn")
                if "nhà hàng" in content:
                    context_parts.append("nhà hàng")
                if any(city in content for city in ["đà nẵng", "hồ chí minh", "hà nội"]):
                    for city in ["đà nẵng", "hồ chí minh", "hà nội"]:
                        if city in content:
                            context_parts.append(f"ở {city}")
                            break
        
        return " ".join(set(context_parts))  # Remove duplicates

def _build_where_clause(self, filters: Dict[str, Any]) -> tuple:
    """Build WHERE clause từ filters"""
    where_conditions = []
    where_params = []
    
    if not filters:
        return None, None
    
    # City filter
    if filters.get("city"):
        where_conditions.append("metadata->>'city' = %s")
        where_params.append(filters["city"])
    
    # Establishment type filter
    if filters.get("establishment_type"):
        where_conditions.append("metadata->>'type' = %s")
        where_params.append(filters["establishment_type"])
    
    # Price range filter
    if filters.get("max_price"):
        where_conditions.append("(metadata->>'price_range')::int <= %s")
        where_params.append(filters["max_price"])
    
    # Amenities filter
    if filters.get("amenities"):
        amenities = filters["amenities"]
        if isinstance(amenities, list) and amenities:
            amenity_conditions = []
            for amenity in amenities:
                amenity_conditions.append("metadata->>'amenities' ILIKE %s")
                where_params.append(f"%{amenity}%")
            where_conditions.append(f"({' OR '.join(amenity_conditions)})")
    
    if where_conditions:
        return " AND ".join(where_conditions), tuple(where_params)
    
    return None, None

# Monkey patch để thêm method vào BaseRetrievalStrategy
BaseRetrievalStrategy._build_where_clause = _build_where_clause
