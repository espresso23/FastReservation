# -*- coding: utf-8 -*-
"""
Response Generator - Tạo response thông minh từ kết quả tìm kiếm
"""

from typing import Dict, Any, List, Optional
from .types import AgentResponse, SearchResult, QueryIntent, SearchStrategy
import logging

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """Generator response thông minh từ search results"""
    
    def __init__(self):
        self.response_templates = {
            QueryIntent.SEARCH_ESTABLISHMENTS: self._generate_search_response,
            QueryIntent.GET_RECOMMENDATIONS: self._generate_recommendation_response,
            QueryIntent.COMPARE_ESTABLISHMENTS: self._generate_compare_response,
            QueryIntent.GET_DETAILS: self._generate_details_response,
            QueryIntent.BOOKING_INQUIRY: self._generate_booking_response,
            QueryIntent.PRICE_INQUIRY: self._generate_price_response,
            QueryIntent.AVAILABILITY_CHECK: self._generate_availability_response
        }

    def generate_response(
        self, 
        results: List[SearchResult],
        intent: QueryIntent,
        strategy: SearchStrategy,
        processing_time: float,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Generate response từ search results
        
        Args:
            results: Danh sách search results
            intent: Intent của query
            strategy: Strategy được sử dụng
            processing_time: Thời gian xử lý
            context: Context bổ sung
            
        Returns:
            AgentResponse object
        """
        try:
            # Generate response dựa trên intent
            generator_func = self.response_templates.get(intent, self._generate_default_response)
            response_content = generator_func(results, context or {})
            
            # Calculate confidence
            confidence = self._calculate_confidence(results, intent)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(results, intent, context or {})
            
            return AgentResponse(
                success=len(results) > 0,
                results=results,
                intent=intent,
                strategy_used=strategy,
                explanation=response_content["explanation"],
                suggestions=suggestions,
                confidence=confidence,
                processing_time=processing_time,
                metadata=response_content.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return AgentResponse(
                success=False,
                results=[],
                intent=intent,
                strategy_used=strategy,
                explanation=f"Lỗi khi tạo response: {str(e)}",
                suggestions=["Vui lòng thử lại với query khác"],
                confidence=0.0,
                processing_time=processing_time,
                metadata={}
            )

    def _generate_search_response(self, results: List[SearchResult], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response cho search establishments"""
        if not results:
            return {
                "explanation": "Không tìm thấy cơ sở nào phù hợp với yêu cầu của bạn. Bạn có thể thử mở rộng tiêu chí tìm kiếm.",
                "metadata": {"result_count": 0}
            }
        
        result_count = len(results)
        city = context.get("city", "không xác định")
        
        explanation = f"Tôi đã tìm thấy {result_count} cơ sở phù hợp ở {city}:\n\n"
        
        for i, result in enumerate(results[:5], 1):  # Chỉ hiển thị top 5
            name = result.name
            score = result.relevance_score
            metadata = result.metadata
            
            explanation += f"{i}. **{name}** (Độ phù hợp: {score:.1%})\n"
            
            # Thêm thông tin bổ sung
            if metadata.get("price_range"):
                explanation += f"   💰 Giá: {metadata['price_range']}\n"
            
            if metadata.get("rating"):
                explanation += f"   ⭐ Đánh giá: {metadata['rating']}/5\n"
            
            if metadata.get("amenities"):
                amenities = metadata["amenities"]
                if isinstance(amenities, list):
                    explanation += f"   🏨 Tiện ích: {', '.join(amenities[:3])}\n"
            
            explanation += f"   📍 Địa chỉ: {metadata.get('address', 'Không có thông tin')}\n\n"
        
        if result_count > 5:
            explanation += f"... và {result_count - 5} cơ sở khác."
        
        return {
            "explanation": explanation,
            "metadata": {
                "result_count": result_count,
                "top_score": results[0].relevance_score if results else 0,
                "average_score": sum(r.relevance_score for r in results) / len(results) if results else 0
            }
        }

    def _generate_recommendation_response(self, results: List[SearchResult], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response cho get recommendations"""
        if not results:
            return {
                "explanation": "Tôi chưa thể đưa ra gợi ý cụ thể. Bạn có thể cung cấp thêm thông tin về sở thích và ngân sách không?",
                "metadata": {"result_count": 0}
            }
        
        result_count = len(results)
        city = context.get("city", "không xác định")
        
        explanation = f"Dựa trên sở thích của bạn, tôi gợi ý {result_count} cơ sở tốt nhất ở {city}:\n\n"
        
        # Top 3 recommendations
        for i, result in enumerate(results[:3], 1):
            name = result.name
            score = result.relevance_score
            metadata = result.metadata
            
            explanation += f"🥇 **{name}** - Lựa chọn hàng đầu ({score:.1%})\n"
            explanation += f"   {metadata.get('description', 'Mô tả không có sẵn')[:100]}...\n\n"
        
        if result_count > 3:
            explanation += f"Ngoài ra, bạn cũng có thể xem xét {result_count - 3} lựa chọn khác."
        
        return {
            "explanation": explanation,
            "metadata": {
                "result_count": result_count,
                "recommendation_type": "top_rated",
                "confidence_level": "high" if result_count >= 3 else "medium"
            }
        }

    def _generate_compare_response(self, results: List[SearchResult], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response cho compare establishments"""
        if len(results) < 2:
            return {
                "explanation": "Để so sánh, tôi cần ít nhất 2 cơ sở. Bạn có thể chỉ định cụ thể cơ sở nào muốn so sánh không?",
                "metadata": {"result_count": len(results)}
            }
        
        explanation = "Đây là bảng so sánh chi tiết:\n\n"
        explanation += "| Tiêu chí | " + " | ".join([r.name for r in results[:3]]) + " |\n"
        explanation += "|----------|" + "|".join(["---" for _ in results[:3]]) + "|\n"
        
        # Compare các tiêu chí chính
        criteria = ["rating", "price_range", "amenities", "location"]
        
        for criterion in criteria:
            explanation += f"| {criterion.title()} | "
            for result in results[:3]:
                value = result.metadata.get(criterion, "N/A")
                if isinstance(value, list):
                    value = ", ".join(value[:2]) if value else "N/A"
                explanation += f"{value} | "
            explanation += "\n"
        
        explanation += f"\n**Kết luận:** Dựa trên điểm số phù hợp, {results[0].name} có vẻ phù hợp nhất với yêu cầu của bạn."
        
        return {
            "explanation": explanation,
            "metadata": {
                "result_count": len(results),
                "comparison_criteria": criteria,
                "top_choice": results[0].name if results else None
            }
        }

    def _generate_details_response(self, results: List[SearchResult], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response cho get details"""
        if not results:
            return {
                "explanation": "Không tìm thấy thông tin chi tiết. Bạn có thể cung cấp tên cụ thể của cơ sở không?",
                "metadata": {"result_count": 0}
            }
        
        result = results[0]  # Lấy result đầu tiên
        metadata = result.metadata
        
        explanation = f"**{result.name}** - Thông tin chi tiết:\n\n"
        
        # Basic info
        if metadata.get("address"):
            explanation += f"📍 **Địa chỉ:** {metadata['address']}\n"
        
        if metadata.get("phone"):
            explanation += f"📞 **Điện thoại:** {metadata['phone']}\n"
        
        if metadata.get("website"):
            explanation += f"🌐 **Website:** {metadata['website']}\n"
        
        # Rating và reviews
        if metadata.get("rating"):
            explanation += f"⭐ **Đánh giá:** {metadata['rating']}/5\n"
        
        if metadata.get("review_count"):
            explanation += f"📝 **Số lượt đánh giá:** {metadata['review_count']}\n"
        
        # Price range
        if metadata.get("price_range"):
            explanation += f"💰 **Khoảng giá:** {metadata['price_range']}\n"
        
        # Amenities
        if metadata.get("amenities"):
            amenities = metadata["amenities"]
            if isinstance(amenities, list) and amenities:
                explanation += f"🏨 **Tiện ích:** {', '.join(amenities)}\n"
        
        # Description
        if metadata.get("description"):
            explanation += f"\n📋 **Mô tả:** {metadata['description']}\n"
        
        return {
            "explanation": explanation,
            "metadata": {
                "result_count": 1,
                "establishment_name": result.name,
                "has_full_info": bool(metadata.get("address") and metadata.get("phone"))
            }
        }

    def _generate_booking_response(self, results: List[SearchResult], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response cho booking inquiry"""
        if not results:
            return {
                "explanation": "Không tìm thấy cơ sở phù hợp để đặt phòng. Bạn có thể thử tìm kiếm với tiêu chí khác không?",
                "metadata": {"result_count": 0}
            }
        
        result = results[0]
        metadata = result.metadata
        
        explanation = f"**{result.name}** - Thông tin đặt phòng:\n\n"
        
        # Availability
        if metadata.get("availability"):
            explanation += f"✅ **Tình trạng:** {metadata['availability']}\n"
        else:
            explanation += "📞 **Để kiểm tra phòng trống, vui lòng liên hệ trực tiếp:**\n"
        
        # Contact info
        if metadata.get("phone"):
            explanation += f"   📞 {metadata['phone']}\n"
        
        if metadata.get("email"):
            explanation += f"   📧 {metadata['email']}\n"
        
        # Price info
        if metadata.get("price_range"):
            explanation += f"\n💰 **Khoảng giá:** {metadata['price_range']}\n"
        
        # Booking instructions
        explanation += "\n📋 **Hướng dẫn đặt phòng:**\n"
        explanation += "1. Liên hệ trực tiếp để kiểm tra phòng trống\n"
        explanation += "2. Xác nhận giá và điều kiện\n"
        explanation += "3. Cung cấp thông tin cá nhân\n"
        explanation += "4. Thanh toán theo hướng dẫn\n"
        
        return {
            "explanation": explanation,
            "metadata": {
                "result_count": 1,
                "has_contact_info": bool(metadata.get("phone") or metadata.get("email")),
                "booking_ready": bool(metadata.get("availability"))
            }
        }

    def _generate_price_response(self, results: List[SearchResult], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response cho price inquiry"""
        if not results:
            return {
                "explanation": "Không tìm thấy thông tin giá. Bạn có thể cung cấp tên cụ thể của cơ sở không?",
                "metadata": {"result_count": 0}
            }
        
        explanation = "**Thông tin giá:**\n\n"
        
        for result in results[:3]:
            name = result.name
            metadata = result.metadata
            
            explanation += f"🏨 **{name}**\n"
            
            if metadata.get("price_range"):
                explanation += f"   💰 {metadata['price_range']}\n"
            else:
                explanation += "   💰 Giá chưa cập nhật\n"
            
            if metadata.get("rating"):
                explanation += f"   ⭐ {metadata['rating']}/5\n"
            
            explanation += "\n"
        
        explanation += "💡 **Lưu ý:** Giá có thể thay đổi tùy theo thời điểm và loại phòng. Vui lòng liên hệ trực tiếp để có thông tin chính xác nhất."
        
        return {
            "explanation": explanation,
            "metadata": {
                "result_count": len(results),
                "price_info_available": any(r.metadata.get("price_range") for r in results)
            }
        }

    def _generate_availability_response(self, results: List[SearchResult], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response cho availability check"""
        if not results:
            return {
                "explanation": "Không tìm thấy thông tin về tình trạng phòng. Bạn có thể cung cấp tên cụ thể của cơ sở không?",
                "metadata": {"result_count": 0}
            }
        
        explanation = "**Tình trạng phòng:**\n\n"
        
        for result in results[:3]:
            name = result.name
            metadata = result.metadata
            
            explanation += f"🏨 **{name}**\n"
            
            if metadata.get("availability"):
                explanation += f"   ✅ {metadata['availability']}\n"
            else:
                explanation += "   📞 Cần liên hệ để kiểm tra\n"
            
            if metadata.get("phone"):
                explanation += f"   📞 {metadata['phone']}\n"
            
            explanation += "\n"
        
        explanation += "💡 **Gợi ý:** Để có thông tin chính xác nhất, bạn nên liên hệ trực tiếp với cơ sở."
        
        return {
            "explanation": explanation,
            "metadata": {
                "result_count": len(results),
                "availability_info_available": any(r.metadata.get("availability") for r in results)
            }
        }

    def _generate_default_response(self, results: List[SearchResult], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate default response"""
        if not results:
            return {
                "explanation": "Tôi chưa hiểu rõ yêu cầu của bạn. Bạn có thể diễn đạt cụ thể hơn không?",
                "metadata": {"result_count": 0}
            }
        
        return {
            "explanation": f"Tôi đã tìm thấy {len(results)} kết quả phù hợp với yêu cầu của bạn.",
            "metadata": {"result_count": len(results)}
        }

    def _calculate_confidence(self, results: List[SearchResult], intent: QueryIntent) -> float:
        """Calculate confidence score"""
        if not results:
            return 0.0
        
        # Base confidence từ số lượng results
        base_confidence = min(len(results) / 5.0, 0.6)
        
        # Confidence từ relevance scores
        if results:
            avg_score = sum(r.relevance_score for r in results) / len(results)
            score_confidence = avg_score * 0.4
        
            return min(base_confidence + score_confidence, 1.0)
        
        return base_confidence

    def _generate_suggestions(self, results: List[SearchResult], intent: QueryIntent, context: Dict[str, Any]) -> List[str]:
        """Generate suggestions dựa trên results và context"""
        suggestions = []
        
        if not results:
            suggestions.append("Bạn có thể thử mở rộng tiêu chí tìm kiếm")
            suggestions.append("Hãy cung cấp thêm thông tin về sở thích của bạn")
            suggestions.append("Thử tìm kiếm với từ khóa khác")
        else:
            if len(results) == 1:
                suggestions.append("Bạn có muốn xem thông tin chi tiết không?")
                suggestions.append("Tôi có thể giúp bạn so sánh với các lựa chọn khác")
            elif len(results) < 5:
                suggestions.append("Bạn có muốn xem thêm lựa chọn không?")
                suggestions.append("Tôi có thể gợi ý các cơ sở tương tự")
            
            suggestions.append("Bạn có cần hỗ trợ đặt phòng không?")
            suggestions.append("Tôi có thể cung cấp thông tin liên hệ")
        
        return suggestions[:3]  # Chỉ trả về 3 suggestions
