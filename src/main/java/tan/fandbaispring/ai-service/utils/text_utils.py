# -*- coding: utf-8 -*-
"""
Text processing utilities
Xử lý các function liên quan đến text normalization và parameter processing
"""

import unicodedata
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

def strip_accents(s: Optional[str]) -> str:
    """
    Loại bỏ dấu tiếng Việt khỏi chuỗi
    
    Args:
        s: Chuỗi cần xử lý
        
    Returns:
        Chuỗi đã loại bỏ dấu và chuyển về lowercase
    """
    if not s:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(s).strip()) 
                   if unicodedata.category(c) != 'Mn').lower()

def normalize_params(final_params: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
    """
    Chuẩn hóa parameters: tách brand name, suy luận establishment type, city, ngày tháng, giá cả
    
    Args:
        final_params: Dictionary chứa các parameters hiện tại
        user_prompt: Prompt từ người dùng
        
    Returns:
        Dictionary đã được chuẩn hóa
    """
    params = dict(final_params or {})
    
    # Suy luận loại cơ sở từ prompt nếu có
    prompt_lc = (user_prompt or "").lower()
    if not params.get("establishment_type"):
        if any(k in prompt_lc for k in ["khach san","khách sạn","hotel"]):
            params["establishment_type"] = "HOTEL"
        elif any(k in prompt_lc for k in ["nha hang","nhà hàng","restaurant"]):
            params["establishment_type"] = "RESTAURANT"
    
    # Suy luận city nếu thiếu (accent-insensitive)
    if not params.get("city"):
        from .city_utils import infer_city_from_text
        guessed = infer_city_from_text(user_prompt or "")
        if guessed:
            params["city"] = guessed
    
    # Suy luận ngày/thời lượng từ prompt và đồng bộ hóa các trường liên quan
    _normalize_date_fields(params, user_prompt)
    
    # Suy luận ngân sách tối đa từ prompt
    _normalize_price_field(params, user_prompt)
    
    # Suy luận brand name nếu có
    from .brand_utils import detect_brand_name
    city = params.get("city")
    mixed = f"{user_prompt} {params.get('amenities_priority','')}"
    brand = detect_brand_name(mixed, city)
    if brand:
        params["brand_name"] = brand
    
    # Chuẩn hoá cờ xác nhận tiện ích về boolean
    if "_amenities_confirmed" in params:
        try:
            v = params.get("_amenities_confirmed")
            if isinstance(v, str):
                params["_amenities_confirmed"] = v.strip().lower() in ("true", "1", "yes")
            else:
                params["_amenities_confirmed"] = bool(v)
        except Exception:
            params["_amenities_confirmed"] = False
    
    return params

def _normalize_date_fields(params: Dict[str, Any], user_prompt: str):
    """Xử lý chuẩn hóa các trường ngày tháng"""
    try:
        text = (user_prompt or "")
        
        # 1) Bắt các ngày dạng YYYY-MM-DD
        date_strs = re.findall(r"(20\d{2}-\d{2}-\d{2})", text)
        parsed_dates: list = []
        for ds in date_strs:
            try:
                parsed_dates.append(datetime.strptime(ds, "%Y-%m-%d"))
            except Exception:
                pass
        
        # 2) Bắt số đêm/ngày từ prompt: "2 đêm/ngày"
        dur_match = re.search(r"(\d+)\s*(đêm|dem|ngày|ngay)", 
                             unicodedata.normalize('NFD', text).lower())
        prompt_nights: Optional[int] = None
        if dur_match:
            try:
                prompt_nights = int(dur_match.group(1))
            except Exception:
                prompt_nights = None

        # Đồng bộ từ params hiện có
        check_in = None
        check_out = None
        try:
            if params.get("check_in_date"):
                check_in = datetime.strptime(str(params.get("check_in_date")), "%Y-%m-%d")
        except Exception:
            check_in = None
        try:
            if params.get("check_out_date"):
                check_out = datetime.strptime(str(params.get("check_out_date")), "%Y-%m-%d")
        except Exception:
            check_out = None
            
        duration_nights = None
        try:
            if params.get("duration") is not None:
                duration_nights = int(str(params.get("duration")))
        except Exception:
            duration_nights = None

        # Ưu tiên: nếu bắt được 2 ngày trong prompt → thiết lập từ-to & duration
        if len(parsed_dates) >= 2:
            start = min(parsed_dates[0], parsed_dates[1])
            end = max(parsed_dates[0], parsed_dates[1])
            nights = max(1, (end - start).days)
            check_in = start
            check_out = end
            duration_nights = nights
        elif len(parsed_dates) == 1 and check_in is None:
            check_in = parsed_dates[0]

        # Nếu có check_in và prompt có số đêm → tính check_out
        if check_in is not None and prompt_nights and (check_out is None):
            duration_nights = prompt_nights if (duration_nights is None) else duration_nights
            if duration_nights is None or duration_nights <= 0:
                duration_nights = prompt_nights
            check_out = check_in + timedelta(days=duration_nights or 1)

        # Nếu có check_in và duration → tính check_out
        if check_in is not None and (duration_nights is not None) and check_out is None:
            check_out = check_in + timedelta(days=max(1, duration_nights))

        # Nếu có check_in và check_out nhưng thiếu duration → tính duration
        if check_in is not None and check_out is not None and (duration_nights is None or duration_nights <= 0):
            duration_nights = max(1, (check_out - check_in).days)

        # Ghi lại vào params dưới dạng ISO yyyy-MM-dd
        if check_in is not None:
            params["check_in_date"] = check_in.strftime("%Y-%m-%d")
        if check_out is not None:
            params["check_out_date"] = check_out.strftime("%Y-%m-%d")
        if duration_nights is not None and duration_nights > 0:
            params["duration"] = duration_nights
            
    except Exception:
        # Bỏ qua lỗi parse ngày để không chặn luồng
        pass

def _normalize_price_field(params: Dict[str, Any], user_prompt: str):
    """Xử lý chuẩn hóa trường giá cả"""
    try:
        if not params.get("max_price"):
            t = (user_prompt or "").lower()
            # Chuẩn hoá dấu phẩy/chấm
            t_norm = t.replace(",", ".").replace("đ", " đ ").replace("vnd", " vnd ")
            
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

            if price and price > 0:
                params["max_price"] = price
                
    except Exception:
        pass

def apply_defaults(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bổ sung giá trị ngầm định; suy luận num_guests từ travel_companion
    
    Args:
        params: Dictionary chứa các parameters
        
    Returns:
        Dictionary đã được bổ sung các giá trị mặc định
    """
    p = dict(params or {})
    
    # Suy luận num_guests từ travel_companion nếu chưa có
    if not p.get("num_guests") and p.get("travel_companion"):
        tc = str(p.get("travel_companion")).strip().lower()
        mapping = {"single": 1, "couple": 2, "family": 4, "friends": 3}
        try:
            p["num_guests"] = mapping.get(tc, int(float(tc)))
        except Exception:
            p["num_guests"] = mapping.get(tc)
    
    # Chuẩn hoá các giá trị khả dĩ của num_guests (single/couple -> số)
    if p.get("num_guests"):
        try:
            # Nếu là chuỗi đặc biệt, map sang số
            ng = str(p.get("num_guests")).strip().lower()
            mapping = {"single": 1, "couple": 2}
            if ng in mapping:
                p["num_guests"] = mapping[ng]
            else:
                p["num_guests"] = int(float(ng))
        except Exception:
            p["num_guests"] = 2  # mặc định an toàn
    
    return p
