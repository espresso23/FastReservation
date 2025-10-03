# -*- coding: utf-8 -*-
"""
City processing utilities
Xử lý các function liên quan đến thành phố và địa điểm
"""

from typing import Optional
from .text_utils import strip_accents

# canonical -> display
CITY_DISPLAY = {
    "danang": "Đà Nẵng",
    "hanoi": "Hà Nội", 
    "hochiminh": "Hồ Chí Minh",
    "nhatrang": "Nha Trang",
    "dalat": "Đà Lạt",
    "hue": "Huế",
    "cantho": "Cần Thơ",
}

# aliases -> canonical
CITY_ALIASES = {
    "da nang": "danang",
    "danang": "danang",
    "dn": "danang",
    "ha noi": "hanoi",
    "hanoi": "hanoi",
    "ho chi minh": "hochiminh",
    "tp ho chi minh": "hochiminh",
    "tphcm": "hochiminh",
    "hcm": "hochiminh",
    "sai gon": "hochiminh",
    "saigon": "hochiminh",
    "nha trang": "nhatrang",
    "nhatrang": "nhatrang",
    "da lat": "dalat",
    "dalat": "dalat",
    "hue": "hue",
    "can tho": "cantho",
    "cantho": "cantho",
}

def infer_city_from_text(text: str) -> Optional[str]:
    """
    Suy luận tên thành phố từ text input
    
    Args:
        text: Chuỗi text cần phân tích
        
    Returns:
        Tên thành phố đã chuẩn hóa hoặc None nếu không tìm thấy
    """
    t = strip_accents(text)
    
    # Tìm alias dài trước để tránh va chạm
    for alias in sorted(CITY_ALIASES.keys(), key=len, reverse=True):
        if alias in t:
            canonical = CITY_ALIASES[alias]
            return CITY_DISPLAY.get(canonical, canonical)
    
    return None

def normalize_city_name(city_name: str) -> Optional[str]:
    """
    Chuẩn hóa tên thành phố về dạng hiển thị
    
    Args:
        city_name: Tên thành phố cần chuẩn hóa
        
    Returns:
        Tên thành phố đã chuẩn hóa hoặc None
    """
    if not city_name:
        return None
        
    normalized = strip_accents(city_name)
    
    # Tìm trong aliases
    if normalized in CITY_ALIASES:
        canonical = CITY_ALIASES[normalized]
        return CITY_DISPLAY.get(canonical, canonical)
    
    # Tìm trong display names
    for display_name in CITY_DISPLAY.values():
        if strip_accents(display_name) == normalized:
            return display_name
    
    return city_name

def get_city_variants(city_name: str) -> set:
    """
    Lấy tất cả các biến thể của tên thành phố
    
    Args:
        city_name: Tên thành phố
        
    Returns:
        Set chứa tất cả các biến thể của tên thành phố
    """
    variants = {city_name}
    
    if not city_name:
        return variants
    
    normalized = strip_accents(city_name)
    
    # Thêm các biến thể từ aliases
    for alias, canonical in CITY_ALIASES.items():
        if strip_accents(alias) == normalized or strip_accents(CITY_DISPLAY.get(canonical, "")) == normalized:
            variants.add(alias)
            variants.add(CITY_DISPLAY.get(canonical, canonical))
            break
    
    # Thêm biến thể có dấu phổ biến
    if normalized == 'da nang':
        variants.update(['Đà Nẵng', 'Da Nang'])
    elif normalized == 'ha noi':
        variants.update(['Hà Nội', 'Ha Noi'])
    elif normalized in ('ho chi minh', 'tphcm', 'tp ho chi minh', 'sai gon'):
        variants.update(['Hồ Chí Minh', 'TP Hồ Chí Minh', 'TP. Hồ Chí Minh', 'Sai Gon'])
    
    return variants

def is_valid_city(city_name: str) -> bool:
    """
    Kiểm tra xem tên thành phố có hợp lệ không
    
    Args:
        city_name: Tên thành phố cần kiểm tra
        
    Returns:
        True nếu thành phố hợp lệ, False nếu không
    """
    if not city_name:
        return False
    
    normalized = strip_accents(city_name)
    
    # Kiểm tra trong aliases
    if normalized in CITY_ALIASES:
        return True
    
    # Kiểm tra trong display names
    for display_name in CITY_DISPLAY.values():
        if strip_accents(display_name) == normalized:
            return True
    
    return False
