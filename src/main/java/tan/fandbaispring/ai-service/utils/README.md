# Utils Package

Package chứa các utility functions được tái sử dụng trong AI Service.

## Cấu trúc

```
utils/
├── __init__.py          # Package initialization và exports
├── text_utils.py        # Text processing utilities
├── city_utils.py        # City/địa điểm utilities  
├── date_utils.py        # Date/time utilities
├── price_utils.py       # Price/ngân sách utilities
├── brand_utils.py       # Brand/establishment utilities
└── README.md           # Tài liệu này
```

## Modules

### text_utils.py
- `strip_accents()`: Loại bỏ dấu tiếng Việt
- `normalize_params()`: Chuẩn hóa parameters từ user input
- `apply_defaults()`: Áp dụng giá trị mặc định cho parameters

### city_utils.py
- `infer_city_from_text()`: Suy luận thành phố từ text
- `normalize_city_name()`: Chuẩn hóa tên thành phố
- `get_city_variants()`: Lấy các biến thể của tên thành phố
- `is_valid_city()`: Kiểm tra tính hợp lệ của tên thành phố

### date_utils.py
- `parse_date_from_text()`: Parse ngày từ text
- `infer_duration_from_text()`: Suy luận thời lượng từ text
- `calculate_checkout_date()`: Tính ngày checkout
- `normalize_date_range()`: Chuẩn hóa khoảng ngày

### price_utils.py
- `parse_price_from_text()`: Parse giá từ text
- `format_price_for_display()`: Format giá để hiển thị
- `parse_price_range()`: Parse khoảng giá
- `get_price_category()`: Phân loại giá

### brand_utils.py
- `detect_brand_name()`: Phát hiện tên brand từ text
- `normalize_brand_name()`: Chuẩn hóa tên brand
- `extract_brand_keywords()`: Trích xuất từ khóa brand
- `suggest_brand_alternatives()`: Gợi ý brand thay thế

## Sử dụng

```python
from utils import strip_accents, normalize_params, infer_city_from_text

# Loại bỏ dấu
text = strip_accents("Đà Nẵng")  # "da nang"

# Chuẩn hóa parameters
params = normalize_params(current_params, user_prompt)

# Suy luận thành phố
city = infer_city_from_text("Tôi muốn đi Đà Nẵng")
```

## Lợi ích

1. **Tái sử dụng**: Các function có thể được sử dụng ở nhiều nơi
2. **Dễ bảo trì**: Code được tổ chức theo chức năng
3. **Testing**: Dễ dàng viết unit tests cho từng function
4. **Mở rộng**: Dễ dàng thêm function mới vào module tương ứng

