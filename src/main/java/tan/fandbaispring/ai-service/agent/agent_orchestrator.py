# -*- coding: utf-8 -*-
"""
Agent Orchestrator - Điều phối workflow của các agents
"""

import time
from typing import Dict, Any, List, Optional
from .types import (
    AgentResponse, ConversationContext, ConversationState, 
    QueryIntent, SearchStrategy, UserProfile
)
from .rag_agent import RAGAgent
from .query_analyzer import QueryAnalyzer
import logging

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Orchestrator điều phối workflow của các agents"""
    
    def __init__(self, pgvector_service, embeddings):
        self.pgvector_service = pgvector_service
        self.embeddings = embeddings
        
        # Initialize main components
        self.rag_agent = RAGAgent(pgvector_service, embeddings)
        self.query_analyzer = QueryAnalyzer()
        
        # Conversation management
        self.active_conversations: Dict[str, ConversationContext] = {}
        
        # Configuration
        self.max_conversation_history = 10
        self.session_timeout = 3600  # 1 hour

    def process_user_message(
        self,
        message: str,
        session_id: str,
        user_profile: Optional[UserProfile] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Xử lý user message với conversation management
        
        Args:
            message: User message
            session_id: Session identifier
            user_profile: User profile
            context: Additional context
            
        Returns:
            AgentResponse
        """
        try:
            # Get or create conversation context
            conversation_context = self._get_or_create_conversation(
                session_id, user_profile
            )
            
            # Update conversation state
            conversation_context.current_query = message
            conversation_context.timestamp = time.time()
            
            # Analyze query
            query_analysis = self.query_analyzer.analyze(message, {
                "user_profile": user_profile.__dict__ if user_profile else {},
                "conversation_history": conversation_context.search_history[-3:]
            })
            
            # Determine next state
            next_state = self._determine_next_state(
                conversation_context, query_analysis
            )
            conversation_context.state = next_state
            
            # Process based on state
            response = self._process_by_state(
                conversation_context, query_analysis, context
            )
            
            # Update conversation history
            self._update_conversation_history(conversation_context, response)
            
            # Clean up old conversations
            self._cleanup_old_conversations()
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing user message: {e}")
            return AgentResponse(
                success=False,
                results=[],
                intent=QueryIntent.UNKNOWN,
                strategy_used=SearchStrategy.HYBRID,
                explanation=f"Lỗi khi xử lý tin nhắn: {str(e)}",
                suggestions=["Vui lòng thử lại"],
                confidence=0.0,
                processing_time=0.1,
                metadata={"error": str(e)}
            )

    def _get_or_create_conversation(
        self, 
        session_id: str, 
        user_profile: Optional[UserProfile]
    ) -> ConversationContext:
        """Lấy hoặc tạo conversation context"""
        if session_id in self.active_conversations:
            conversation = self.active_conversations[session_id]
            
            # Check if session is still valid
            if time.time() - conversation.timestamp > self.session_timeout:
                # Session expired, create new one
                del self.active_conversations[session_id]
                return self._create_new_conversation(session_id, user_profile)
            
            return conversation
        
        return self._create_new_conversation(session_id, user_profile)

    def _create_new_conversation(
        self, 
        session_id: str, 
        user_profile: Optional[UserProfile]
    ) -> ConversationContext:
        """Tạo conversation context mới"""
        if not user_profile:
            user_profile = UserProfile(
                preferences={},
                history=[],
                budget_range=None,
                preferred_cities=[],
                preferred_amenities=[],
                travel_companion=None
            )
        
        conversation = ConversationContext(
            state=ConversationState.INITIAL,
            user_profile=user_profile,
            current_query="",
            search_history=[],
            session_id=session_id,
            timestamp=time.time()
        )
        
        self.active_conversations[session_id] = conversation
        return conversation

    def _determine_next_state(
        self, 
        conversation: ConversationContext, 
        query_analysis
    ) -> ConversationState:
        """Xác định state tiếp theo của conversation"""
        current_state = conversation.state
        intent = query_analysis.intent
        confidence = query_analysis.confidence
        
        # State transition logic
        if current_state == ConversationState.INITIAL:
            if confidence > 0.6:
                return ConversationState.SEARCHING
            else:
                return ConversationState.COLLECTING_PREFERENCES
        
        elif current_state == ConversationState.COLLECTING_PREFERENCES:
            if confidence > 0.5:
                return ConversationState.SEARCHING
            else:
                return ConversationState.COLLECTING_PREFERENCES
        
        elif current_state == ConversationState.SEARCHING:
            if intent in [QueryIntent.COMPARE_ESTABLISHMENTS, QueryIntent.GET_DETAILS]:
                return ConversationState.REFINING
            elif intent == QueryIntent.BOOKING_INQUIRY:
                return ConversationState.CONFIRMING
            else:
                return ConversationState.SEARCHING
        
        elif current_state == ConversationState.REFINING:
            if intent == QueryIntent.BOOKING_INQUIRY:
                return ConversationState.CONFIRMING
            else:
                return ConversationState.REFINING
        
        elif current_state == ConversationState.CONFIRMING:
            return ConversationState.COMPLETED
        
        else:
            return ConversationState.SEARCHING

    def _process_by_state(
        self,
        conversation: ConversationContext,
        query_analysis,
        context: Optional[Dict[str, Any]]
    ) -> AgentResponse:
        """Xử lý dựa trên conversation state"""
        state = conversation.state
        
        if state == ConversationState.INITIAL:
            return self._handle_initial_state(conversation, query_analysis)
        
        elif state == ConversationState.COLLECTING_PREFERENCES:
            return self._handle_collecting_preferences(conversation, query_analysis)
        
        elif state == ConversationState.SEARCHING:
            return self._handle_searching_state(conversation, query_analysis, context)
        
        elif state == ConversationState.REFINING:
            return self._handle_refining_state(conversation, query_analysis, context)
        
        elif state == ConversationState.CONFIRMING:
            return self._handle_confirming_state(conversation, query_analysis, context)
        
        else:
            return self._handle_completed_state(conversation, query_analysis)

    def _handle_initial_state(
        self, 
        conversation: ConversationContext, 
        query_analysis
    ) -> AgentResponse:
        """Xử lý initial state"""
        return AgentResponse(
            success=True,
            results=[],
            intent=query_analysis.intent,
            strategy_used=SearchStrategy.HYBRID,
            explanation="Xin chào! Tôi có thể giúp bạn tìm kiếm khách sạn và nhà hàng. Bạn đang tìm kiếm gì hôm nay?",
            suggestions=[
                "Tìm khách sạn ở Đà Nẵng",
                "Gợi ý nhà hàng ngon",
                "So sánh các resort",
                "Kiểm tra giá phòng"
            ],
            confidence=1.0,
            processing_time=0.1,
            metadata={"state": "initial", "needs_more_info": True}
        )

    def _handle_collecting_preferences(
        self, 
        conversation: ConversationContext, 
        query_analysis
    ) -> AgentResponse:
        """Xử lý collecting preferences state"""
        suggestions = []
        explanation = "Để tôi có thể hỗ trợ tốt nhất, bạn có thể cung cấp thêm thông tin:"
        
        # Check what information is missing
        user_profile = conversation.user_profile
        
        if not user_profile.preferred_cities:
            suggestions.append("Bạn muốn tìm ở thành phố nào?")
        
        if not user_profile.budget_range:
            suggestions.append("Ngân sách của bạn là bao nhiêu?")
        
        if not user_profile.preferred_amenities:
            suggestions.append("Bạn có ưu tiên tiện ích nào không? (hồ bơi, spa, gym...)")
        
        if not user_profile.travel_companion:
            suggestions.append("Bạn đi một mình hay cùng ai?")
        
        return AgentResponse(
            success=True,
            results=[],
            intent=query_analysis.intent,
            strategy_used=SearchStrategy.HYBRID,
            explanation=explanation,
            suggestions=suggestions[:3],
            confidence=0.7,
            processing_time=0.1,
            metadata={"state": "collecting_preferences", "needs_more_info": True}
        )

    def _handle_searching_state(
        self,
        conversation: ConversationContext,
        query_analysis,
        context: Optional[Dict[str, Any]]
    ) -> AgentResponse:
        """Xử lý searching state"""
        # Build context for RAG agent
        rag_context = {
            "user_preferences": conversation.user_profile.__dict__,
            "conversation_history": conversation.search_history[-3:],
            "similarity_threshold": 0.6,
            "max_results": 8
        }
        
        if context:
            rag_context.update(context)
        
        # Process with RAG agent
        return self.rag_agent.process_query(
            query=conversation.current_query,
            context=rag_context
        )

    def _handle_refining_state(
        self,
        conversation: ConversationContext,
        query_analysis,
        context: Optional[Dict[str, Any]]
    ) -> AgentResponse:
        """Xử lý refining state"""
        # Similar to searching but with different parameters
        rag_context = {
            "user_preferences": conversation.user_profile.__dict__,
            "conversation_history": conversation.search_history[-3:],
            "similarity_threshold": 0.7,  # Higher threshold for refinement
            "max_results": 5
        }
        
        if context:
            rag_context.update(context)
        
        return self.rag_agent.process_query(
            query=conversation.current_query,
            context=rag_context
        )

    def _handle_confirming_state(
        self,
        conversation: ConversationContext,
        query_analysis,
        context: Optional[Dict[str, Any]]
    ) -> AgentResponse:
        """Xử lý confirming state"""
        return AgentResponse(
            success=True,
            results=[],
            intent=query_analysis.intent,
            strategy_used=SearchStrategy.HYBRID,
            explanation="Tôi hiểu bạn muốn đặt phòng. Để hoàn tất việc đặt phòng, bạn cần:",
            suggestions=[
                "Cung cấp thông tin liên hệ",
                "Chọn ngày check-in và check-out",
                "Xác nhận số lượng phòng và khách",
                "Chọn phương thức thanh toán"
            ],
            confidence=0.9,
            processing_time=0.1,
            metadata={"state": "confirming", "booking_flow": True}
        )

    def _handle_completed_state(
        self, 
        conversation: ConversationContext, 
        query_analysis
    ) -> AgentResponse:
        """Xử lý completed state"""
        return AgentResponse(
            success=True,
            results=[],
            intent=query_analysis.intent,
            strategy_used=SearchStrategy.HYBRID,
            explanation="Cảm ơn bạn đã sử dụng dịch vụ! Bạn có cần hỗ trợ gì thêm không?",
            suggestions=[
                "Tìm kiếm cơ sở khác",
                "Xem thông tin chi tiết",
                "Đặt phòng",
                "Bắt đầu cuộc trò chuyện mới"
            ],
            confidence=1.0,
            processing_time=0.1,
            metadata={"state": "completed", "ready_for_new_query": True}
        )

    def _update_conversation_history(
        self, 
        conversation: ConversationContext, 
        response: AgentResponse
    ):
        """Cập nhật conversation history"""
        # Add current search to history
        search_entry = {
            "query": conversation.current_query,
            "intent": response.intent.value,
            "strategy": response.strategy_used.value,
            "result_count": len(response.results),
            "confidence": response.confidence,
            "timestamp": time.time()
        }
        
        conversation.search_history.append(search_entry)
        
        # Limit history size
        if len(conversation.search_history) > self.max_conversation_history:
            conversation.search_history = conversation.search_history[-self.max_conversation_history:]

    def _cleanup_old_conversations(self):
        """Dọn dẹp các conversation cũ"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, conversation in self.active_conversations.items():
            if current_time - conversation.timestamp > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_conversations[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")

    def get_conversation_state(self, session_id: str) -> Optional[ConversationContext]:
        """Lấy trạng thái conversation"""
        return self.active_conversations.get(session_id)

    def update_user_profile(
        self, 
        session_id: str, 
        profile_updates: Dict[str, Any]
    ) -> bool:
        """Cập nhật user profile"""
        try:
            conversation = self.active_conversations.get(session_id)
            if not conversation:
                return False
            
            # Update profile
            for key, value in profile_updates.items():
                if hasattr(conversation.user_profile, key):
                    setattr(conversation.user_profile, key, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False

    def get_session_stats(self) -> Dict[str, Any]:
        """Lấy thống kê về các session"""
        return {
            "active_sessions": len(self.active_conversations),
            "session_timeout": self.session_timeout,
            "max_history": self.max_conversation_history,
            "conversation_states": {
                session_id: conv.state.value 
                for session_id, conv in self.active_conversations.items()
            }
        }

    def end_conversation(self, session_id: str) -> bool:
        """Kết thúc conversation"""
        try:
            if session_id in self.active_conversations:
                del self.active_conversations[session_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            return False
