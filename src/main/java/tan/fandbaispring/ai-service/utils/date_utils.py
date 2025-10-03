# -*- coding: utf-8 -*-
"""
Date processing utilities
Xử lý các function liên quan đến ngày tháng và thời gian
"""

import re
import unicodedata
from typing import Optional, List, Tuple
from datetime import datetime, timedelta

def parse_date_from_text(text: str) -> List[datetime]:
    """
    Parse các ngày từ text dạng YYYY-MM-DD
    
    Args:
        text: Chuỗi text chứa ngày tháng
        
    Returns:
        List các datetime đã parse được
    """
    date_strs = re.findall(r"(20\d{2}-\d{2}-\d{2})", text)
    parsed_dates: List[datetime] = []
    
    for ds in date_strs:
        try:
            parsed_dates.append(datetime.strptime(ds, "%Y-%m-%d"))
        except Exception:
            pass
    
    return parsed_dates

def infer_duration_from_text(text: str) -> Optional[int]:
    """
    Suy luận số đêm/ngày từ text
    
    Args:
        text: Chuỗi text cần phân tích
        
    Returns:
        Số đêm/ngày hoặc None nếu không tìm thấy
    """
    # Bắt số đêm/ngày từ prompt: "2 đêm/ngày"
    dur_match = re.search(r"(\d+)\s*(đêm|dem|ngày|ngay)", 
                         unicodedata.normalize('NFD', text).lower())
    
    if dur_match:
        try:
            return int(dur_match.group(1))
        except Exception:
            pass
    
    return None

def calculate_checkout_date(checkin_date: datetime, duration_nights: int) -> datetime:
    """
    Tính ngày checkout từ ngày checkin và số đêm
    
    Args:
        checkin_date: Ngày checkin
        duration_nights: Số đêm ở
        
    Returns:
        Ngày checkout
    """
    return checkin_date + timedelta(days=max(1, duration_nights))

def calculate_duration_nights(checkin_date: datetime, checkout_date: datetime) -> int:
    """
    Tính số đêm từ ngày checkin và checkout
    
    Args:
        checkin_date: Ngày checkin
        checkout_date: Ngày checkout
        
    Returns:
        Số đêm
    """
    return max(1, (checkout_date - checkin_date).days)

def normalize_date_range(checkin_date: Optional[datetime], 
                        checkout_date: Optional[datetime], 
                        duration_nights: Optional[int]) -> Tuple[Optional[datetime], Optional[datetime], Optional[int]]:
    """
    Chuẩn hóa và đồng bộ các trường ngày tháng
    
    Args:
        checkin_date: Ngày checkin
        checkout_date: Ngày checkout  
        duration_nights: Số đêm
        
    Returns:
        Tuple (checkin_date, checkout_date, duration_nights) đã được chuẩn hóa
    """
    # Nếu có checkin và duration nhưng thiếu checkout → tính checkout
    if checkin_date is not None and (duration_nights is not None) and checkout_date is None:
        checkout_date = calculate_checkout_date(checkin_date, duration_nights)
    
    # Nếu có checkin và checkout nhưng thiếu duration → tính duration
    if checkin_date is not None and checkout_date is not None and (duration_nights is None or duration_nights <= 0):
        duration_nights = calculate_duration_nights(checkin_date, checkout_date)
    
    return checkin_date, checkout_date, duration_nights

def format_date_for_display(date: datetime) -> str:
    """
    Format ngày để hiển thị
    
    Args:
        date: Ngày cần format
        
    Returns:
        Chuỗi ngày đã format
    """
    return date.strftime("%d/%m/%Y")

def format_date_for_api(date: datetime) -> str:
    """
    Format ngày cho API (ISO format)
    
    Args:
        date: Ngày cần format
        
    Returns:
        Chuỗi ngày theo format ISO
    """
    return date.strftime("%Y-%m-%d")

def parse_relative_date(text: str, reference_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse ngày tương đối như "hôm nay", "ngày mai", "tuần sau"
    
    Args:
        text: Chuỗi text chứa ngày tương đối
        reference_date: Ngày tham chiếu (mặc định là hôm nay)
        
    Returns:
        Ngày đã parse hoặc None
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    text_lower = text.lower().strip()
    
    if text_lower in ["hôm nay", "hom nay", "today"]:
        return reference_date
    elif text_lower in ["ngày mai", "ngay mai", "tomorrow"]:
        return reference_date + timedelta(days=1)
    elif text_lower in ["ngày kia", "ngay kia"]:
        return reference_date + timedelta(days=2)
    elif "tuần sau" in text_lower or "tuan sau" in text_lower:
        return reference_date + timedelta(weeks=1)
    elif "tháng sau" in text_lower or "thang sau" in text_lower:
        # Tháng sau (approximate)
        return reference_date + timedelta(days=30)
    
    return None

def is_valid_date_range(checkin_date: datetime, checkout_date: datetime) -> bool:
    """
    Kiểm tra xem khoảng ngày có hợp lệ không
    
    Args:
        checkin_date: Ngày checkin
        checkout_date: Ngày checkout
        
    Returns:
        True nếu hợp lệ, False nếu không
    """
    return checkout_date > checkin_date and (checkout_date - checkin_date).days <= 365

