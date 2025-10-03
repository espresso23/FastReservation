# -*- coding: utf-8 -*-
"""
Price processing utilities
Xử lý các function liên quan đến giá cả và ngân sách
"""

import re
from typing import Optional, Tuple

def parse_price_from_text(text: str) -> Optional[int]:
    """
    Parse giá từ text với các format khác nhau
    
    Args:
        text: Chuỗi text chứa giá
        
    Returns:
        Giá đã parse (VND) hoặc None nếu không tìm thấy
    """
    if not text:
        return None
    
    # Chuẩn hoá dấu phẩy/chấm
    t_norm = text.lower().replace(",", ".").replace("đ", " đ ").replace("vnd", " vnd ")
    price: Optional[int] = None

    # 1) 1.2tr / 1.2 m / 1,2 triệu / 300k / 250 nghin
    m = re.search(r"(\d+(?:\.\d+)?)\s*(k|nghin|nghìn|ngan|ngàn|tr|triệu|trieu|m)\b", t_norm)
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        if unit in ("k", "nghin", "nghìn", "ngan", "ngàn"):
            price = int(round(val * 1_000))
        elif unit in ("tr", "triệu", "trieu", "m"):
            price = int(round(val * 1_000_000))
    else:
        # 2) 300.000 đ / 300000đ / 300000 vnd
        m2 = re.search(r"(\d{1,3}(?:[\.\s]\d{3})+|\d+)\s*(đ|vnd)\b", t_norm)
        if m2:
            num_str = m2.group(1).replace(".", "").replace(" ", "")
            try:
                price = int(num_str)
            except Exception:
                price = None

    return price if price and price > 0 else None

def format_price_for_display(price: int) -> str:
    """
    Format giá để hiển thị
    
    Args:
        price: Giá cần format (VND)
        
    Returns:
        Chuỗi giá đã format
    """
    if price >= 1_000_000:
        return f"{price // 1_000_000:,} triệu VND"
    elif price >= 1_000:
        return f"{price // 1_000:,}k VND"
    else:
        return f"{price:,} VND"

def format_price_for_api(price: int) -> int:
    """
    Format giá cho API (giữ nguyên số nguyên)
    
    Args:
        price: Giá cần format
        
    Returns:
        Giá đã format
    """
    return price

def parse_price_range(text: str) -> Optional[Tuple[int, int]]:
    """
    Parse khoảng giá từ text như "300k-500k", "1tr đến 2tr"
    
    Args:
        text: Chuỗi text chứa khoảng giá
        
    Returns:
        Tuple (min_price, max_price) hoặc None
    """
    if not text:
        return None
    
    # Tìm pattern khoảng giá
    range_patterns = [
        r"(\d+(?:\.\d+)?)\s*(k|tr|triệu|m)\s*[-đếnđến]\s*(\d+(?:\.\d+)?)\s*(k|tr|triệu|m)",
        r"từ\s*(\d+(?:\.\d+)?)\s*(k|tr|triệu|m)\s*đến\s*(\d+(?:\.\d+)?)\s*(k|tr|triệu|m)"
    ]
    
    for pattern in range_patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                val1 = float(match.group(1))
                unit1 = match.group(2)
                val2 = float(match.group(3))
                unit2 = match.group(4)
                
                min_price = _convert_to_vnd(val1, unit1)
                max_price = _convert_to_vnd(val2, unit2)
                
                if min_price and max_price and min_price <= max_price:
                    return min_price, max_price
            except Exception:
                continue
    
    return None

def _convert_to_vnd(value: float, unit: str) -> Optional[int]:
    """Convert value với unit thành VND"""
    if unit in ("k", "nghin", "nghìn", "ngan", "ngàn"):
        return int(round(value * 1_000))
    elif unit in ("tr", "triệu", "trieu", "m"):
        return int(round(value * 1_000_000))
    return None

def validate_price_range(min_price: int, max_price: int) -> bool:
    """
    Kiểm tra xem khoảng giá có hợp lệ không
    
    Args:
        min_price: Giá tối thiểu
        max_price: Giá tối đa
        
    Returns:
        True nếu hợp lệ, False nếu không
    """
    return (0 < min_price <= max_price <= 100_000_000)  # Max 100 triệu

def get_price_category(price: int) -> str:
    """
    Phân loại giá theo mức độ
    
    Args:
        price: Giá cần phân loại
        
    Returns:
        Category của giá
    """
    if price < 500_000:
        return "budget"
    elif price < 1_000_000:
        return "mid-range"
    elif price < 2_000_000:
        return "upscale"
    else:
        return "luxury"

def suggest_price_ranges(category: str) -> Tuple[int, int]:
    """
    Gợi ý khoảng giá theo category
    
    Args:
        category: Loại giá
        
    Returns:
        Tuple (min_price, max_price)
    """
    ranges = {
        "budget": (100_000, 500_000),
        "mid-range": (500_000, 1_000_000),
        "upscale": (1_000_000, 2_000_000),
        "luxury": (2_000_000, 5_000_000)
    }
    return ranges.get(category, (100_000, 1_000_000))

