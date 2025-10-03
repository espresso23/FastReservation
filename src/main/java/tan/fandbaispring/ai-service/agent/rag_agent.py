# -*- coding: utf-8 -*-
"""
RAG Agent - Agent chính cho Agentic RAG System
"""

import time
from typing import Dict, Any, List, Optional
from .types import RetrievalContext, AgentResponse, QueryIntent, SearchStrategy
from .query_analyzer import QueryAnalyzer
from .retrieval_strategies import (
    SemanticRetrievalStrategy,
    HybridRetrievalStrategy,
    ContextualRetrievalStrategy
)
from .response_generator import ResponseGenerator
import logging

logger = logging.getLogger(__name__)

class RAGAgent:
    """RAG Agent chính điều phối toàn bộ quá trình RAG"""
    
    def __init__(self, pgvector_service, embeddings):
        self.pgvector_service = pgvector_service
        self.embeddings = embeddings
        
        # Initialize components
        self.query_analyzer = QueryAnalyzer()
        self.response_generator = ResponseGenerator()
        
        # Initialize retrieval strategies
        self.retrieval_strategies = {
            SearchStrategy.SEMANTIC: SemanticRetrievalStrategy(pgvector_service, embeddings),
            SearchStrategy.HYBRID: HybridRetrievalStrategy(pgvector_service, embeddings),
            SearchStrategy.CONTEXTUAL: ContextualRetrievalStrategy(pgvector_service, embeddings)
        }
        
        # Default strategy
        self.default_strategy = SearchStrategy.HYBRID

    def process_query(
        self, 
        query: str,
        context: Optional[Dict[str, Any]] = None,
        strategy: Optional[SearchStrategy] = None
    ) -> AgentResponse:
        """
        Xử lý user query và trả về response
        
        Args:
            query: User query
            context: Context bổ sung
            strategy: Strategy tìm kiếm (optional)
            
        Returns:
            AgentResponse
        """
        start_time = time.time()
        
        try:
            # Step 1: Analyze query
            logger.info(f"Analyzing query: {query}")
            query_analysis = self.query_analyzer.analyze(query, context)
            
            # Step 2: Determine strategy
            if not strategy:
                strategy = self._determine_strategy(query_analysis, context)
            
            # Step 3: Build retrieval context
            retrieval_context = self._build_retrieval_context(
                query, query_analysis, context, strategy
            )
            
            # Step 4: Perform retrieval
            logger.info(f"Performing retrieval with strategy: {strategy.value}")
            search_results = self._perform_retrieval(retrieval_context)
            
            # Step 5: Generate response
            processing_time = time.time() - start_time
            response = self.response_generator.generate_response(
                results=search_results,
                intent=query_analysis.intent,
                strategy=strategy,
                processing_time=processing_time,
                context=context
            )
            
            logger.info(f"Query processed successfully in {processing_time:.3f}s")
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing query: {e}")
            
            return AgentResponse(
                success=False,
                results=[],
                intent=QueryIntent.UNKNOWN,
                strategy_used=strategy or self.default_strategy,
                explanation=f"Lỗi khi xử lý query: {str(e)}",
                suggestions=["Vui lòng thử lại với query khác"],
                confidence=0.0,
                processing_time=processing_time,
                metadata={"error": str(e)}
            )

    def _determine_strategy(self, query_analysis, context: Optional[Dict[str, Any]]) -> SearchStrategy:
        """Xác định strategy phù hợp dựa trên query analysis"""
        intent = query_analysis.intent
        confidence = query_analysis.confidence
        
        # Rule-based strategy selection
        if intent == QueryIntent.GET_RECOMMENDATIONS:
            return SearchStrategy.CONTEXTUAL
        
        elif intent == QueryIntent.COMPARE_ESTABLISHMENTS:
            return SearchStrategy.HYBRID
        
        elif intent in [QueryIntent.SEARCH_ESTABLISHMENTS, QueryIntent.GET_DETAILS]:
            if confidence > 0.7:
                return SearchStrategy.SEMANTIC
            else:
                return SearchStrategy.HYBRID
        
        elif intent in [QueryIntent.BOOKING_INQUIRY, QueryIntent.AVAILABILITY_CHECK]:
            return SearchStrategy.HYBRID
        
        else:
            return self.default_strategy

    def _build_retrieval_context(
        self,
        query: str,
        query_analysis,
        context: Optional[Dict[str, Any]],
        strategy: SearchStrategy
    ) -> RetrievalContext:
        """Build retrieval context từ query analysis và context"""
        
        # Extract filters từ query analysis
        filters = {}
        
        # City filter
        if query_analysis.entities.get("cities"):
            filters["city"] = query_analysis.entities["cities"][0]
        
        # Establishment type filter
        if query_analysis.entities.get("establishment_types"):
            filters["establishment_type"] = query_analysis.entities["establishment_types"][0]
        
        # Price filter
        if query_analysis.entities.get("price_range"):
            filters["max_price"] = query_analysis.entities["price_range"]
        
        # Amenities filter
        if query_analysis.entities.get("amenities"):
            filters["amenities"] = query_analysis.entities["amenities"]
        
        # Merge với context filters
        if context and context.get("filters"):
            filters.update(context["filters"])
        
        # User preferences
        user_preferences = context.get("user_preferences", {}) if context else {}
        
        # Conversation history
        conversation_history = context.get("conversation_history", []) if context else []
        
        # Similarity threshold
        similarity_threshold = context.get("similarity_threshold", 0.7) if context else 0.7
        
        # Max results
        max_results = context.get("max_results", 10) if context else 10
        
        return RetrievalContext(
            query=query,
            intent=query_analysis.intent,
            strategy=strategy,
            filters=filters,
            user_preferences=user_preferences,
            conversation_history=conversation_history,
            max_results=max_results,
            similarity_threshold=similarity_threshold
        )

    def _perform_retrieval(self, context: RetrievalContext) -> List:
        """Thực hiện retrieval với strategy được chọn"""
        strategy = self.retrieval_strategies.get(context.strategy)
        
        if not strategy:
            logger.warning(f"Strategy {context.strategy} not found, using default")
            strategy = self.retrieval_strategies[self.default_strategy]
        
        try:
            return strategy.retrieve(context)
        except Exception as e:
            logger.error(f"Error in retrieval with strategy {context.strategy}: {e}")
            return []

    def get_establishment_details(self, establishment_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết của establishment"""
        try:
            return self.pgvector_service.get_embedding_by_id(establishment_id)
        except Exception as e:
            logger.error(f"Error getting establishment details for {establishment_id}: {e}")
            return None

    def add_establishment(self, establishment_data: Dict[str, Any]) -> bool:
        """Thêm establishment mới vào vector database"""
        try:
            establishment_id = establishment_data.get("id")
            content = establishment_data.get("content", "")
            metadata = establishment_data.get("metadata", {})
            
            if not establishment_id or not content:
                logger.error("Missing required fields: id and content")
                return False
            
            # Generate embedding
            embedding = self.embeddings.embed_query(content)
            if not embedding:
                logger.error("Failed to generate embedding")
                return False
            
            # Add to vector database
            success = self.pgvector_service.add_embedding(
                establishment_id=establishment_id,
                content=content,
                metadata=metadata,
                embedding=embedding
            )
            
            if success:
                logger.info(f"Successfully added establishment {establishment_id}")
            else:
                logger.error(f"Failed to add establishment {establishment_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding establishment: {e}")
            return False

    def remove_establishment(self, establishment_id: str) -> bool:
        """Xóa establishment khỏi vector database"""
        try:
            success = self.pgvector_service.remove_embedding(establishment_id)
            
            if success:
                logger.info(f"Successfully removed establishment {establishment_id}")
            else:
                logger.error(f"Failed to remove establishment {establishment_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error removing establishment: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê về vector database"""
        try:
            count = self.pgvector_service.get_embedding_count()
            return {
                "total_establishments": count,
                "strategies_available": list(self.retrieval_strategies.keys()),
                "default_strategy": self.default_strategy.value
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "total_establishments": 0,
                "strategies_available": [],
                "default_strategy": self.default_strategy.value,
                "error": str(e)
            }

    def refine_search(
        self,
        original_query: str,
        feedback: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Refine search dựa trên feedback
        
        Args:
            original_query: Query gốc
            feedback: Feedback từ user
            context: Context bổ sung
            
        Returns:
            AgentResponse
        """
        try:
            # Analyze feedback
            if feedback.get("preferred_results"):
                # User thích kết quả nào đó, tìm similar
                preferred_id = feedback["preferred_results"][0]
                preferred_establishment = self.get_establishment_details(preferred_id)
                
                if preferred_establishment:
                    # Tìm similar establishments
                    content = preferred_establishment.get("content", "")
                    embedding = self.embeddings.embed_query(content)
                    
                    similar_results = self.pgvector_service.similarity_search(
                        query_embedding=embedding,
                        limit=5,
                        where_clause="establishment_id != %s",
                        where_params=(preferred_id,)
                    )
                    
                    # Convert to SearchResult format
                    search_results = []
                    for result in similar_results:
                        search_results.append({
                            "establishment_id": result["establishment_id"],
                            "name": result["metadata"].get("name", "Unknown"),
                            "relevance_score": result["similarity_score"],
                            "metadata": result["metadata"],
                            "explanation": f"Tương tự với {preferred_establishment.get('name', 'lựa chọn bạn thích')}"
                        })
                    
                    return AgentResponse(
                        success=True,
                        results=search_results,
                        intent=QueryIntent.SEARCH_ESTABLISHMENTS,
                        strategy_used=SearchStrategy.SEMANTIC,
                        explanation="Dựa trên lựa chọn bạn thích, đây là những cơ sở tương tự:",
                        suggestions=["Bạn có muốn xem thông tin chi tiết không?"],
                        confidence=0.8,
                        processing_time=0.1,
                        metadata={"refinement_type": "similar_to_preferred"}
                    )
            
            elif feedback.get("rejected_results"):
                # User không thích kết quả nào đó, exclude và tìm khác
                rejected_ids = feedback["rejected_results"]
                where_clause = " AND ".join([f"establishment_id != %s" for _ in rejected_ids])
                
                # Re-run search với exclusion
                return self.process_query(
                    query=original_query,
                    context={
                        **(context or {}),
                        "filters": {
                            **(context.get("filters", {}) if context else {}),
                            "exclude_ids": rejected_ids
                        }
                    }
                )
            
            else:
                # General feedback, re-analyze query
                return self.process_query(original_query, context)
                
        except Exception as e:
            logger.error(f"Error refining search: {e}")
            return AgentResponse(
                success=False,
                results=[],
                intent=QueryIntent.UNKNOWN,
                strategy_used=self.default_strategy,
                explanation=f"Lỗi khi refine search: {str(e)}",
                suggestions=["Vui lòng thử lại"],
                confidence=0.0,
                processing_time=0.1,
                metadata={"error": str(e)}
            )
