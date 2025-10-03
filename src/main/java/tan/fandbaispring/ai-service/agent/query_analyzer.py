# -*- coding: utf-8 -*-
"""
Query Analyzer - Phân tích và hiểu user query
"""

import re
from typing import Dict, Any, List, Optional
from .types import QueryIntent, QueryAnalysis, EstablishmentType
from utils import strip_accents, infer_city_from_text, parse_price_from_text

class QueryAnalyzer:
    """Phân tích user query để hiểu intent và extract entities"""
    
    def __init__(self):
        self.intent_keywords = {
            QueryIntent.SEARCH_ESTABLISHMENTS: [
                "tìm", "search", "tìm kiếm", "khách sạn", "nhà hàng", "hotel", "restaurant",
                "ở đâu", "chỗ nào", "địa điểm", "establishment"
            ],
            QueryIntent.GET_RECOMMENDATIONS: [
                "gợi ý", "recommend", "khuyên", "nên", "tốt nhất", "best", "top"
            ],
            QueryIntent.COMPARE_ESTABLISHMENTS: [
                "so sánh", "compare", "khác nhau", "difference", "hơn", "better"
            ],
            QueryIntent.GET_DETAILS: [
                "chi tiết", "details", "thông tin", "info", "như thế nào", "how"
            ],
            QueryIntent.BOOKING_INQUIRY: [
                "đặt", "book", "booking", "reservation", "phòng", "room"
            ],
            QueryIntent.PRICE_INQUIRY: [
                "giá", "price", "cost", "phí", "bao nhiêu", "how much"
            ],
            QueryIntent.AVAILABILITY_CHECK: [
                "còn phòng", "available", "trống", "free", "có không", "is there"
            ]
        }
        
        self.establishment_keywords = {
            EstablishmentType.HOTEL: ["khách sạn", "hotel", "resort", "lodge", "inn"],
            EstablishmentType.RESTAURANT: ["nhà hàng", "restaurant", "cafe", "quán", "bar"],
            EstablishmentType.SPA: ["spa", "massage", "wellness", "thẩm mỹ"],
            EstablishmentType.RESORT: ["resort", "khu nghỉ dưỡng", "resort"]
        }
        
        self.amenity_keywords = [
            "hồ bơi", "pool", "spa", "gym", "fitness", "wifi", "parking", "đỗ xe",
            "buffet", "breakfast", "restaurant", "nhà hàng", "bar", "quầy bar",
            "beach", "biển", "mountain", "núi", "city", "thành phố", "center", "trung tâm"
        ]

    def analyze(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryAnalysis:
        """
        Phân tích query để xác định intent và extract entities
        
        Args:
            query: User query
            context: Context bổ sung
            
        Returns:
            QueryAnalysis object
        """
        query_lower = query.lower().strip()
        
        # Xác định intent
        intent = self._detect_intent(query_lower)
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Extract parameters
        parameters = self._extract_parameters(query)
        
        # Tính confidence
        confidence = self._calculate_confidence(intent, entities, query_lower)
        
        # Tạo suggestions
        suggestions = self._generate_suggestions(intent, entities)
        
        return QueryAnalysis(
            intent=intent,
            entities=entities,
            parameters=parameters,
            confidence=confidence,
            suggestions=suggestions
        )

    def _detect_intent(self, query: str) -> QueryIntent:
        """Xác định intent của query"""
        intent_scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query:
                    score += 1
            intent_scores[intent] = score
        
        # Tìm intent có điểm cao nhất
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[best_intent] > 0:
                return best_intent
        
        return QueryIntent.UNKNOWN

    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities từ query"""
        entities = {
            "cities": [],
            "establishment_types": [],
            "amenities": [],
            "brands": [],
            "price_range": None,
            "dates": [],
            "duration": None
        }
        
        # Extract cities
        city = infer_city_from_text(query)
        if city:
            entities["cities"].append(city)
        
        # Extract establishment types
        query_lower = query.lower()
        for est_type, keywords in self.establishment_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    entities["establishment_types"].append(est_type.value)
                    break
        
        # Extract amenities
        for amenity in self.amenity_keywords:
            if amenity in query_lower:
                entities["amenities"].append(amenity)
        
        # Extract price range
        price = parse_price_from_text(query)
        if price:
            entities["price_range"] = price
        
        # Extract dates (YYYY-MM-DD pattern)
        date_pattern = r"\b(20\d{2}-\d{2}-\d{2})\b"
        dates = re.findall(date_pattern, query)
        entities["dates"] = dates
        
        # Extract duration
        duration_pattern = r"(\d+)\s*(đêm|dem|ngày|ngay|night|day)"
        duration_match = re.search(duration_pattern, query_lower)
        if duration_match:
            entities["duration"] = int(duration_match.group(1))
        
        return entities

    def _extract_parameters(self, query: str) -> Dict[str, Any]:
        """Extract parameters từ query"""
        parameters = {}
        
        # Travel companion
        companion_patterns = {
            "single": ["một mình", "alone", "solo"],
            "couple": ["cặp đôi", "couple", "hai người", "2 người"],
            "family": ["gia đình", "family", "trẻ em", "children"],
            "friends": ["bạn bè", "friends", "nhóm bạn"]
        }
        
        query_lower = query.lower()
        for companion, patterns in companion_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                parameters["travel_companion"] = companion
                break
        
        # Number of guests
        guest_pattern = r"(\d+)\s*(người|person|people|guests)"
        guest_match = re.search(guest_pattern, query_lower)
        if guest_match:
            parameters["num_guests"] = int(guest_match.group(1))
        
        # Star rating
        rating_pattern = r"(\d+)\s*(sao|star|stars)"
        rating_match = re.search(rating_pattern, query_lower)
        if rating_match:
            parameters["star_rating"] = int(rating_match.group(1))
        
        return parameters

    def _calculate_confidence(self, intent: QueryIntent, entities: Dict[str, Any], query: str) -> float:
        """Tính confidence score"""
        confidence = 0.0
        
        # Base confidence từ intent
        if intent != QueryIntent.UNKNOWN:
            confidence += 0.3
        
        # Confidence từ entities
        entity_count = sum(1 for v in entities.values() if v and len(str(v)) > 0)
        confidence += min(entity_count * 0.1, 0.4)
        
        # Confidence từ query length và specificity
        if len(query.split()) >= 3:
            confidence += 0.2
        
        # Confidence từ specific keywords
        specific_keywords = ["ở", "tại", "với", "có", "giá", "khoảng"]
        if any(keyword in query for keyword in specific_keywords):
            confidence += 0.1
        
        return min(confidence, 1.0)

    def _generate_suggestions(self, intent: QueryIntent, entities: Dict[str, Any]) -> List[str]:
        """Tạo suggestions dựa trên intent và entities"""
        suggestions = []
        
        if intent == QueryIntent.SEARCH_ESTABLISHMENTS:
            if not entities.get("cities"):
                suggestions.append("Bạn có thể chỉ định thành phố cụ thể không?")
            if not entities.get("establishment_types"):
                suggestions.append("Bạn muốn tìm khách sạn hay nhà hàng?")
            if not entities.get("amenities"):
                suggestions.append("Bạn có ưu tiên tiện ích nào không? (hồ bơi, spa, gym...)")
        
        elif intent == QueryIntent.GET_RECOMMENDATIONS:
            suggestions.append("Tôi có thể gợi ý dựa trên thành phố và ngân sách của bạn")
            suggestions.append("Bạn có thể cho biết thêm về sở thích của mình")
        
        elif intent == QueryIntent.BOOKING_INQUIRY:
            if not entities.get("dates"):
                suggestions.append("Bạn cần cung cấp ngày check-in và check-out")
            suggestions.append("Bạn muốn đặt bao nhiêu phòng?")
        
        return suggestions

    def refine_query(self, original_query: str, context: Dict[str, Any]) -> str:
        """
        Refine query dựa trên context
        
        Args:
            original_query: Query gốc
            context: Context bổ sung
            
        Returns:
            Refined query
        """
        refined_parts = [original_query]
        
        # Thêm city nếu có trong context nhưng không có trong query
        if context.get("city") and context["city"] not in original_query:
            refined_parts.append(f"ở {context['city']}")
        
        # Thêm establishment type
        if context.get("establishment_type") and context["establishment_type"] not in original_query.lower():
            est_type = context["establishment_type"]
            if est_type == "HOTEL":
                refined_parts.append("khách sạn")
            elif est_type == "RESTAURANT":
                refined_parts.append("nhà hàng")
        
        # Thêm amenities
        if context.get("amenities_priority"):
            amenities = context["amenities_priority"]
            if isinstance(amenities, str) and amenities not in original_query.lower():
                refined_parts.append(f"với {amenities}")
        
        return " ".join(refined_parts)
