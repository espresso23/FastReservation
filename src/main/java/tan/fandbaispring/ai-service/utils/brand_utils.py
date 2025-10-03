# -*- coding: utf-8 -*-
"""
Brand processing utilities
Xử lý các function liên quan đến brand name và establishment detection
"""

from typing import Optional, Dict, Any
from .text_utils import strip_accents

def detect_brand_name(mixed_text: str, city: Optional[str], pgvector_service=None) -> Optional[str]:
    """
    Phát hiện tên brand/establishment từ text
    
    Args:
        mixed_text: Chuỗi text chứa tên brand
        city: Thành phố để filter
        pgvector_service: Service để query database
        
    Returns:
        Tên brand đã phát hiện hoặc None
    """
    try:
        if pgvector_service is None:
            return None
            
        where_clause = "metadata->>'city' = %s" if city else None
        where_params = (city,) if city else None
        
        results = pgvector_service.similarity_search(
            query_embedding=[0.0] * 1536,  # Dummy embedding cho metadata search
            limit=50,
            where_clause=where_clause,
            where_params=where_params
        )
        
        text_lc = (mixed_text or "").lower()
        best = None
        
        for result in results:
            metadata = result.get("metadata", {})
            nm = (metadata.get("name") or "").strip()
            if not nm:
                continue
            if nm.lower() in text_lc:
                best = nm
                break
                
        return best
    except Exception:
        return None

def normalize_brand_name(brand_name: str) -> str:
    """
    Chuẩn hóa tên brand
    
    Args:
        brand_name: Tên brand cần chuẩn hóa
        
    Returns:
        Tên brand đã chuẩn hóa
    """
    if not brand_name:
        return ""
    
    # Loại bỏ dấu và chuyển về lowercase
    normalized = strip_accents(brand_name)
    
    # Loại bỏ các ký tự đặc biệt thừa
    normalized = normalized.replace("_", " ").replace("-", " ")
    
    # Loại bỏ khoảng trắng thừa
    normalized = " ".join(normalized.split())
    
    return normalized

def extract_brand_keywords(text: str) -> list:
    """
    Trích xuất các từ khóa có thể là tên brand
    
    Args:
        text: Chuỗi text cần phân tích
        
    Returns:
        List các từ khóa có thể là brand
    """
    if not text:
        return []
    
    # Loại bỏ các từ không phải brand
    stop_words = {
        "khách sạn", "nhà hàng", "hotel", "restaurant", "resort", "spa",
        "có", "tại", "ở", "trong", "với", "và", "hoặc", "để", "cho"
    }
    
    words = text.lower().split()
    keywords = []
    
    for word in words:
        # Loại bỏ stop words và từ quá ngắn
        if len(word) > 2 and word not in stop_words:
            # Kiểm tra xem có phải từ có chữ cái không
            if any(c.isalpha() for c in word):
                keywords.append(word)
    
    return keywords[:5]  # Lấy tối đa 5 từ khóa

def match_brand_pattern(text: str, brand_patterns: Dict[str, list]) -> Optional[str]:
    """
    Match brand theo pattern
    
    Args:
        text: Chuỗi text cần match
        brand_patterns: Dictionary chứa các pattern của brand
        
    Returns:
        Tên brand match được hoặc None
    """
    text_lower = text.lower()
    
    for brand_name, patterns in brand_patterns.items():
        for pattern in patterns:
            if pattern.lower() in text_lower:
                return brand_name
    
    return None

def suggest_brand_alternatives(brand_name: str, city: Optional[str] = None) -> list:
    """
    Gợi ý các brand thay thế
    
    Args:
        brand_name: Tên brand hiện tại
        city: Thành phố để filter
        
    Returns:
        List các brand thay thế
    """
    # Dictionary chứa các brand phổ biến theo city
    city_brands = {
        "Đà Nẵng": ["InterContinental", "Novotel", "Pullman", "Sheraton", "Hyatt"],
        "Hồ Chí Minh": ["Park Hyatt", "Renaissance", "Sofitel", "Caravelle", "Rex"],
        "Hà Nội": ["Sofitel Legend", "InterContinental", "Hilton", "Sheraton", "Mövenpick"],
        "Nha Trang": ["Vinpearl", "Amiana", "InterContinental", "Sheraton", "Novotel"]
    }
    
    if city and city in city_brands:
        return city_brands[city]
    
    # Fallback brands
    return ["InterContinental", "Novotel", "Sheraton", "Hilton", "Hyatt"]

def is_brand_mentioned(text: str, brand_names: list) -> Optional[str]:
    """
    Kiểm tra xem có brand nào được mention trong text không
    
    Args:
        text: Chuỗi text cần kiểm tra
        brand_names: List tên các brand
        
    Returns:
        Tên brand được mention hoặc None
    """
    text_lower = text.lower()
    
    for brand in brand_names:
        if brand.lower() in text_lower:
            return brand
    
    return None

