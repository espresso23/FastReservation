# -*- coding: utf-8 -*-
"""
Data types và enums cho Agent package
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

class QueryIntent(Enum):
    """Các loại intent của user query"""
    SEARCH_ESTABLISHMENTS = "search_establishments"
    GET_RECOMMENDATIONS = "get_recommendations"
    COMPARE_ESTABLISHMENTS = "compare_establishments"
    GET_DETAILS = "get_details"
    BOOKING_INQUIRY = "booking_inquiry"
    PRICE_INQUIRY = "price_inquiry"
    AVAILABILITY_CHECK = "availability_check"
    UNKNOWN = "unknown"

class SearchStrategy(Enum):
    """Các chiến lược tìm kiếm"""
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    CONTEXTUAL = "contextual"
    FILTER_BASED = "filter_based"

class EstablishmentType(Enum):
    """Loại cơ sở"""
    HOTEL = "HOTEL"
    RESTAURANT = "RESTAURANT"
    ALL = "ALL"

@dataclass
class RetrievalContext:
    """Context cho việc retrieval"""
    query: str
    intent: QueryIntent
    strategy: SearchStrategy
    filters: Dict[str, Any]
    user_preferences: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    max_results: int = 10
    similarity_threshold: float = 0.7

@dataclass
class SearchResult:
    """Kết quả tìm kiếm"""
    establishment_id: str
    name: str
    relevance_score: float
    metadata: Dict[str, Any]
    explanation: str

@dataclass
class AgentResponse:
    """Response từ agent"""
    success: bool
    results: List[SearchResult]
    intent: QueryIntent
    strategy_used: SearchStrategy
    explanation: str
    suggestions: List[str]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]

@dataclass
class QueryAnalysis:
    """Phân tích query"""
    intent: QueryIntent
    entities: Dict[str, Any]
    parameters: Dict[str, Any]
    confidence: float
    suggestions: List[str]

@dataclass
class EstablishmentProfile:
    """Profile của establishment"""
    id: str
    name: str
    type: EstablishmentType
    city: str
    price_range: Optional[tuple]
    amenities: List[str]
    description: str
    rating: Optional[float]
    image_urls: List[str]
    availability: Dict[str, Any]

@dataclass
class UserProfile:
    """Profile của user"""
    preferences: Dict[str, Any]
    history: List[Dict[str, Any]]
    budget_range: Optional[tuple]
    preferred_cities: List[str]
    preferred_amenities: List[str]
    travel_companion: Optional[str]

class ConversationState(Enum):
    """Trạng thái cuộc hội thoại"""
    INITIAL = "initial"
    COLLECTING_PREFERENCES = "collecting_preferences"
    SEARCHING = "searching"
    REFINING = "refining"
    CONFIRMING = "confirming"
    COMPLETED = "completed"

@dataclass
class ConversationContext:
    """Context của cuộc hội thoại"""
    state: ConversationState
    user_profile: UserProfile
    current_query: str
    search_history: List[RetrievalContext]
    session_id: str
    timestamp: datetime
