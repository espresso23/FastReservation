# Loại bỏ câu hỏi "Phong cách/không khí" (style_vibe)

## 🎯 Vấn đề đã giải quyết

Trước đây, AI vẫn hỏi "Bạn thích phong cách/không khí nào?" (style_vibe) mặc dù đã có ý định gộp nó vào amenities. Điều này gây ra:
- Câu hỏi thừa và không cần thiết
- Trải nghiệm không mượt mà
- User phải trả lời thêm câu hỏi về phong cách

## ✅ Giải pháp đã triển khai

### 1. **Backend (AI Service) - `ai_service_gemini.py`**

#### **Loại bỏ style_vibe khỏi PARAM_ORDER:**
```python
PARAM_ORDER = [
    "establishment_type",  # HOTEL | RESTAURANT
    "city", "check_in_date", "travel_companion", "duration",
    "max_price", "amenities_priority"  # Không có style_vibe
]
```

#### **Cập nhật normalize_params:**
```python
def normalize_params(final_params: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
    """Chuẩn hóa: tách brand name nếu phát hiện."""
    # ... existing code ...
    # Loại bỏ style_vibe nếu có (không cần nữa)
    if "style_vibe" in params:
        params.pop("style_vibe", None)
    return params
```

#### **Cập nhật RAG search:**
```python
# Trước: Tìm kiếm cơ sở ở {city} với phong cách {style}
# Sau: Tìm kiếm cơ sở ở {city}
query_text = (
    f"Tìm kiếm cơ sở ở {city_text}. "
    f"Cần tiện nghi phù hợp cho {companion} và ưu tiên các tiện ích: {amenities}. "
    f"Mô tả không gian và trải nghiệm."
)
```

#### **Cập nhật heuristic inference:**
```python
# Trước: final_params["style_vibe"] = "romantic"
# Sau: final_params["amenities_priority"] = "romantic"
if "lãng mạn" in prompt_lc and not final_params.get("amenities_priority"):
    final_params["amenities_priority"] = "romantic"
```

### 2. **Frontend - `UserBookingPage.tsx`**

#### **Cập nhật defaultOptions:**
```typescript
const defaultOptions: Record<string, string[]> = {
  establishment_type: ['HOTEL','RESTAURANT'],
  travel_companion: ['single','couple','family','friends','team','business'],
  amenities_priority: [
    'Hồ bơi','Spa','Bãi đậu xe','Gym','Buffet sáng','Gần biển','Wifi','Lễ tân 24/7','Đưa đón sân bay',
    'Pet-friendly','Phòng gia đình','Không hút thuốc','Bồn tắm','View biển','View thành phố','Gần trung tâm',
    'Ban công','Cửa sổ','Giặt là','Thang máy',
    // Thêm style options vào amenities
    'Romantic','Quiet','Lively','Luxury','Nature','Cozy','Modern','Classic'
  ],
  // Không có style_vibe nữa
}
```

#### **Loại bỏ style_vibe khỏi keyLabel:**
```typescript
const keyLabel = (k: string) => {
  switch (k) {
    case 'establishment_type': return 'Loại cơ sở';
    case 'city': return 'Thành phố';
    case 'check_in_date': return 'Ngày nhận';
    case 'duration': return 'Số đêm';
    case 'max_price': return 'Ngân sách tối đa (VND)';
    case 'travel_companion': return 'Đi cùng ai';
    case 'amenities_priority': return 'Tiện ích ưu tiên';
    case 'has_balcony': return 'Có ban công?';
    case 'num_guests': return 'Số người';
    // Không có case 'style_vibe' nữa
    default: return k || ''
  }
}
```

#### **Cập nhật broaden criteria:**
```typescript
if (action === 'any_style') {
  // Không cần xử lý style_vibe nữa
}
```

## 🎯 Kết quả

### **Trước khi sửa:**
```
AI: "Bạn thích phong cách/không khí nào? (ví dụ: lãng mạn, yên tĩnh, sôi động)"
User: [Phải chọn từ romantic, quiet, lively, luxury, nature, cozy, modern, classic]
```

### **Sau khi sửa:**
```
AI: "Bạn ưu tiên tiện ích gì? (ví dụ: Hồ bơi, Spa, Gym, Wifi, Romantic, Luxury...)"
User: [Chọn từ danh sách amenities bao gồm cả style options]
```

## 🔧 Lợi ích

1. **Giảm số câu hỏi**: Không còn câu hỏi thừa về phong cách
2. **Trải nghiệm mượt mà**: User chỉ cần trả lời về amenities
3. **Linh hoạt hơn**: Style options được gộp vào amenities
4. **Đơn giản hóa**: Một câu hỏi thay vì hai câu hỏi riêng biệt
5. **Tự nhiên hơn**: Amenities bao gồm cả phong cách và tiện ích

## 📊 So sánh

| Trước | Sau |
|-------|-----|
| 2 câu hỏi riêng biệt | 1 câu hỏi tổng hợp |
| "Phong cách/không khí" | Gộp vào "Tiện ích ưu tiên" |
| romantic, quiet, lively... | Hồ bơi, Spa, Romantic, Luxury... |
| Cần chọn style riêng | Chọn tất cả trong amenities |

## 🚀 Kết quả cuối cùng

- ✅ Không còn câu hỏi "Bạn thích phong cách/không khí nào?"
- ✅ Style options được gộp vào amenities
- ✅ Trải nghiệm đơn giản và mượt mà hơn
- ✅ User chỉ cần trả lời về tiện ích ưu tiên
- ✅ AI vẫn có thể hiểu được phong cách qua amenities

Bây giờ AI Booking Assistant sẽ không hỏi về phong cách nữa mà chỉ tập trung vào amenities, bao gồm cả style options! 🎉
