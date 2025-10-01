# 📊 Dữ liệu mẫu Establishments

## 🎯 Mục đích
Tạo dữ liệu đa dạng các khách sạn và nhà hàng để test hệ thống booking AI và tìm kiếm.

## 📋 Danh sách Establishments

### 🏨 **Khách sạn (HOTEL)**

1. **Hotel Continental Saigon** - Hồ Chí Minh
   - ⭐ 5 sao, 2.5M VND
   - 🏊 Hồ bơi, Spa, Gym, Nhà hàng cao cấp

2. **InterContinental Hanoi Westlake** - Hà Nội  
   - ⭐ 5 sao, 3.2M VND
   - 🌊 View hồ Tây, Spa truyền thống Việt

3. **Furama Resort Danang** - Đà Nẵng
   - ⭐ 5 sao, 2.8M VND
   - 🏖️ Bãi biển riêng, Hồ bơi nhiều tầng

4. **Vinpearl Resort & Spa Phú Quốc** - Phú Quốc
   - ⭐ 5 sao, 3.5M VND
   - 🏝️ Resort đảo, Bãi biển cát trắng

5. **Hotel de l'Opera Hanoi** - Hà Nội
   - ⭐ 4 sao, 1.8M VND
   - 🎭 Phong cách Pháp cổ điển

6. **Khách sạn Rex Saigon** - Hồ Chí Minh
   - ⭐ 4 sao, 2.2M VND
   - 🏛️ Khách sạn lịch sử Sài Gòn

7. **Sofitel Legend Metropole Hanoi** - Hà Nội
   - ⭐ 5 sao, 4M VND
   - 👑 Khách sạn 5 sao lịch sử

8. **Vinpearl Resort Nha Trang** - Nha Trang
   - ⭐ 5 sao, 3M VND
   - 🏖️ Resort đảo Hòn Tre

### 🍽️ **Nhà hàng (RESTAURANT)**

1. **Nhà hàng Ngon Garden** - Hồ Chí Minh
   - ⭐ 4 sao, 800K VND
   - 🌿 Không gian xanh, Menu đa dạng

2. **Quán Ăn Ngon** - Hà Nội
   - ⭐ 4 sao, 600K VND
   - 🍜 Ẩm thực truyền thống Bắc Bộ

3. **Nhà hàng Hải Sản Biển Đông** - Đà Nẵng
   - ⭐ 4 sao, 1.2M VND
   - 🦐 Hải sản tươi ngon, View biển

4. **Nhà hàng Cửa Hàng** - Hội An
   - ⭐ 4 sao, 500K VND
   - 🏮 Ẩm thực truyền thống Quảng Nam

5. **Nhà hàng Sài Gòn Xưa** - Hồ Chí Minh
   - ⭐ 4 sao, 700K VND
   - 🥢 Ẩm thực Sài Gòn xưa

6. **Nhà hàng Hải Sản Cửa Lò** - Nghệ An
   - ⭐ 4 sao, 900K VND
   - 🦀 Hải sản biển Nghệ An

7. **Nhà hàng Ẩm Thực Huế** - Huế
   - ⭐ 4 sao, 550K VND
   - 🍲 Ẩm thực truyền thống Huế

## 🚀 Cách thêm dữ liệu

### **Phương pháp 1: Python Script (Khuyến nghị)**
```bash
# Cài đặt dependencies
pip install requests

# Chạy script
python add_sample_establishments.py
```

### **Phương pháp 2: Bash Script (Linux/Mac)**
```bash
# Cấp quyền thực thi
chmod +x add_establishments_curl.sh

# Chạy script
./add_establishments_curl.sh
```

### **Phương pháp 3: PowerShell (Windows)**
```powershell
# Chạy script
.\add_establishments.ps1
```

### **Phương pháp 4: Thủ công với Postman/Insomnia**
1. Import collection từ file JSON
2. Sử dụng endpoint: `POST /api/partner/establishments`
3. Điền thông tin theo format trong `sample_establishments_data.json`

## 📁 Cấu trúc dữ liệu

### **JSON Format:**
```json
{
  "name": "Tên cơ sở",
  "type": "HOTEL" | "RESTAURANT",
  "city": "Thành phố",
  "address": "Địa chỉ chi tiết",
  "priceRangeVnd": 2500000,
  "starRating": 5,
  "descriptionLong": "Mô tả chi tiết...",
  "amenitiesList": ["Tiện ích 1", "Tiện ích 2"],
  "hasInventory": true,
  "isAvailable": true
}
```

### **Multipart Form Data:**
- `data`: JSON string với thông tin cơ sở
- `mainFile`: Ảnh chính (dummy image)
- `galleryFiles`: Ảnh gallery (dummy images)

## 🎨 Thông tin ảnh

**Lưu ý:** Scripts sử dụng dummy images (1x1 pixel) để test. 
Sau khi thêm thành công, bạn có thể:

1. **Upload ảnh thật** qua frontend
2. **Sử dụng API update** để thay thế ảnh
3. **Upload trực tiếp** lên Cloudinary

## 🔧 Cấu hình

### **Environment Variables:**
```bash
# Backend URL
BASE_URL=http://localhost:8080/api

# Owner ID (Partner ID)
OWNER_ID=1
```

### **Database Requirements:**
- PostgreSQL đang chạy
- User với ID=1 và role=PARTNER đã tồn tại
- Backend Spring Boot đang chạy trên port 8080

## 📊 Kết quả mong đợi

Sau khi chạy thành công:
- ✅ 15 establishments được thêm vào database
- ✅ Ảnh được upload lên Cloudinary với folder structure
- ✅ Dữ liệu được index vào AI Vector Store
- ✅ Có thể tìm kiếm qua AI booking assistant

## 🧪 Test dữ liệu

### **Kiểm tra establishments:**
```bash
curl "http://localhost:8080/api/partner/establishments/1"
```

### **Test AI booking:**
```bash
curl -X POST "http://localhost:8080/api/booking/process" \
  -H "Content-Type: application/json" \
  -d '{"userPrompt": "Tôi muốn đặt khách sạn ở Hà Nội với giá dưới 2 triệu"}'
```

### **Test RAG search:**
```bash
curl -X POST "http://localhost:8000/rag-search" \
  -H "Content-Type: application/json" \
  -d '{"params": {"city": "Hà Nội", "max_price": 2000000}}'
```

## 🎯 Lợi ích

1. **Đa dạng dữ liệu**: 15 establishments ở 7 thành phố khác nhau
2. **Test AI**: Có thể test AI booking với nhiều scenario
3. **Demo sẵn sàng**: Dữ liệu phong phú để demo hệ thống
4. **Realistic data**: Thông tin thực tế, có thể sử dụng trong production

## 🚨 Lưu ý

- **Ảnh**: Scripts sử dụng dummy images, cần upload ảnh thật sau
- **Owner ID**: Đảm bảo user với ID=1 và role=PARTNER đã tồn tại
- **Cloudinary**: Cần cấu hình API keys trong `.env`
- **AI Service**: Cần chạy Python AI service để index dữ liệu

## 📞 Hỗ trợ

Nếu gặp lỗi:
1. Kiểm tra backend đang chạy
2. Kiểm tra database connection
3. Kiểm tra Cloudinary configuration
4. Kiểm tra AI service đang chạy
