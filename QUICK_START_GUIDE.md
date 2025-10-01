# Hướng dẫn nhanh - Thêm dữ liệu mẫu bằng Postman

## 🚀 Cách 1: Sử dụng Postman Collection (Khuyến nghị)

### Bước 1: Import Collection
1. Mở Postman
2. Click **Import** → chọn file `postman_establishments_collection.json`
3. Collection sẽ được import với 15 requests

### Bước 2: Thiết lập Environment
1. Tạo Environment mới:
   - Name: `FandBAI Local`
   - Variable: `base_url` = `http://localhost:8080`
2. Chọn Environment này

### Bước 3: Chạy Collection
1. Click vào collection **"Add Sample Establishments"**
2. Click **Run collection**
3. Click **Run** để chạy tất cả 15 requests

## 🚀 Cách 2: Copy-paste JSON đơn giản

### Bước 1: Tạo request mới
- Method: `POST`
- URL: `http://localhost:8080/api/partner/establishments/simple`
- Headers: `Content-Type: application/json`

### Bước 2: Copy JSON data
Copy một trong các JSON từ file `establishments_data_simple.json` vào Body

### Bước 3: Send request
Click **Send** và kiểm tra response

## 📊 Dữ liệu sẽ được thêm:

### Hotels (8):
1. Hotel Continental Saigon - Ho Chi Minh
2. InterContinental Hanoi Westlake - Hanoi  
3. Furama Resort Danang - Danang
4. Vinpearl Resort Phu Quoc - Phu Quoc
5. Hotel de l'Opera Hanoi - Hanoi
6. Rex Hotel Saigon - Ho Chi Minh
7. Sofitel Legend Metropole Hanoi - Hanoi
8. Vinpearl Resort Nha Trang - Nha Trang

### Restaurants (7):
1. Ngon Garden Restaurant - Ho Chi Minh
2. Quan An Ngon - Hanoi
3. Bien Dong Seafood Restaurant - Danang
4. Cua Hang Restaurant - Hoi An
5. Sai Gon Xua Restaurant - Ho Chi Minh
6. Bien Dong Seafood Cua Lo - Nghe An
7. Am Thuc Hue Restaurant - Hue

## ✅ Kiểm tra kết quả:

### Response thành công (201):
```json
{
  "id": "uuid-here",
  "name": "Hotel Name",
  "ownerId": "1",
  "type": "HOTEL",
  "city": "Ho Chi Minh",
  "address": "123 Street",
  "descriptionLong": "Description...",
  "amenitiesList": ["Free WiFi", "Parking"],
  "hasInventory": true,
  "available": true
}
```

### Lỗi thường gặp:
- **400 Bad Request**: JSON format sai
- **500 Internal Server Error**: Lỗi server
- **403 Forbidden**: ownerId không hợp lệ

## 🔧 Troubleshooting:

### Lỗi "Content-Type not supported":
- Đảm bảo sử dụng endpoint `/api/partner/establishments/simple`
- Không sử dụng endpoint `/api/partner/establishments` (cần multipart)

### Lỗi "ownerId không hợp lệ":
- Đảm bảo user với ID "1" tồn tại và có role PARTNER
- Tạo user trước: `POST /api/auth/register` với role PARTNER

### Lỗi JSON parse:
- Kiểm tra JSON format
- Đảm bảo tất cả strings có dấu ngoặc kép
- Không có trailing commas

## 📝 Lưu ý quan trọng:

- **Tất cả establishments có `ownerId = "1"`**
- **Không cần upload ảnh** - có thể thêm sau
- **Backend phải đang chạy** trên port 8080
- **Mỗi request tạo một establishment mới**

## 🎯 Sau khi thêm xong:

1. Kiểm tra database để xác nhận dữ liệu
2. Test AI booking để xem establishments xuất hiện trong suggestions
3. Upload ảnh cho establishments qua frontend hoặc API khác
