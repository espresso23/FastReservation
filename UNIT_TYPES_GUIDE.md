# Hướng dẫn thêm UnitType cho Establishments

## 🎯 Tổng quan

Đã thêm thành công **44 UnitType** cho **15 establishments** bao gồm:

### 🏨 Hotels (8 establishments):
- **Hotel Continental Saigon**: 3 room types (Standard, Deluxe, Suite)
- **InterContinental Hanoi Westlake**: 3 room types (Standard, Deluxe, Presidential Suite)
- **Furama Resort Danang**: 3 room types (Garden View, Ocean View, Family)
- **Vinpearl Resort Phu Quoc**: 3 room types (Standard Villa, Deluxe Villa, Presidential Villa)
- **Hotel de l'Opera Hanoi**: 2 room types (Classic, Deluxe)
- **Rex Hotel Saigon**: 3 room types (Standard, Deluxe, Executive Suite)
- **Sofitel Legend Metropole Hanoi**: 3 room types (Classic, Deluxe, Legend Suite)
- **Vinpearl Resort Nha Trang**: 3 room types (Standard, Deluxe, Family)

### 🍽️ Restaurants (7 establishments):
- **Ngon Garden Restaurant**: 3 table types (T2, T4, T8)
- **Quan An Ngon**: 3 table types (T2, T4, T6)
- **Bien Dong Seafood Restaurant**: 3 table types (Sea View T2, T4, Private Dining)
- **Cua Hang Restaurant**: 3 table types (Traditional T2, T4, Family T8)
- **Sai Gon Xua Restaurant**: 3 table types (Vintage T2, T4, T6)
- **Bien Dong Seafood Cua Lo**: 3 table types (Beach T2, T4, Beach Pavilion)
- **Am Thuc Hue Restaurant**: 3 table types (Hue Style T2, T4, T6)

## 📊 Chi tiết UnitType

### 🏨 Room Types (Hotels):
- **Standard Room**: Phòng tiêu chuẩn, 2 người, không ban công
- **Deluxe Room**: Phòng cao cấp, 2 người, có ban công
- **Suite**: Phòng suite, 4-8 người, có ban công
- **Family Room**: Phòng gia đình, 4 người, có ban công
- **Villa**: Biệt thự, 2-8 người, có ban công

### 🍽️ Table Types (Restaurants):
- **Table for 2**: Bàn 2 người
- **Table for 4**: Bàn 4 người  
- **Table for 6**: Bàn 6 người
- **Table for 8**: Bàn 8 người
- **Private Dining**: Phòng riêng 10 người
- **Beach Pavilion**: Lều bãi biển 8 người

## 🔧 Cách sử dụng

### 1. Kiểm tra UnitType đã được thêm:
```bash
# Lấy danh sách UnitType của một establishment
GET /api/partner/types/{establishmentId}
```

### 2. Thêm UnitType mới (nếu cần):
```bash
POST /api/partner/types
Content-Type: application/json

{
  "establishmentId": "establishment-id-here",
  "category": "ROOM" | "TABLE",
  "code": "STD",
  "name": "Standard Room",
  "capacity": 2,
  "hasBalcony": false,
  "basePrice": 2500000,  // For ROOM
  "depositAmount": 200000,  // For TABLE
  "totalUnits": 50,
  "active": true
}
```

### 3. Cập nhật UnitType:
```bash
PUT /api/partner/types/{typeId}
Content-Type: application/json

{
  "name": "Updated Name",
  "basePrice": 3000000,
  "totalUnits": 60
}
```

### 4. Xóa UnitType:
```bash
DELETE /api/partner/types/{typeId}
```

## 📋 Dữ liệu mẫu

### Room Types (Hotels):
- **Standard**: 1.8M - 4M VND, 2 người
- **Deluxe**: 2.5M - 5.5M VND, 2 người, có ban công
- **Suite**: 4.5M - 12M VND, 4-8 người, có ban công
- **Family**: 4.5M - 5.5M VND, 4 người, có ban công
- **Villa**: 3.5M - 10M VND, 2-8 người, có ban công

### Table Types (Restaurants):
- **T2**: 100K - 300K VND deposit, 2 người
- **T4**: 200K - 500K VND deposit, 4 người
- **T6**: 350K - 450K VND deposit, 6 người
- **T8**: 400K - 800K VND deposit, 8 người
- **Private**: 1M VND deposit, 10 người

## 🎯 Lợi ích

1. **Đa dạng lựa chọn**: Khách hàng có nhiều loại phòng/bàn để chọn
2. **Giá cả linh hoạt**: Từ phòng tiêu chuẩn đến suite cao cấp
3. **Quản lý khả dụng**: Theo dõi số lượng phòng/bàn còn trống
4. **Tích hợp AI**: AI có thể đề xuất phù hợp với ngân sách và nhu cầu
5. **Booking system**: Hỗ trợ đặt phòng/bàn theo loại cụ thể

## 🔍 Kiểm tra kết quả

### 1. Kiểm tra trong database:
```sql
SELECT e.name, ut.name, ut.category, ut.base_price, ut.deposit_amount, ut.total_units 
FROM establishment e 
JOIN unit_type ut ON e.id = ut.establishment_id 
ORDER BY e.name, ut.category, ut.base_price;
```

### 2. Kiểm tra qua API:
```bash
# Lấy tất cả establishments
GET /api/partner/establishments

# Lấy UnitType của một establishment
GET /api/partner/types/{establishmentId}
```

### 3. Kiểm tra AI booking:
- Thử đặt phòng qua AI booking
- Kiểm tra suggestions có hiển thị đúng loại phòng/bàn
- Kiểm tra giá cả và thông tin chi tiết

## 🚀 Bước tiếp theo

1. **Upload ảnh**: Thêm ảnh cho các UnitType
2. **Test booking**: Thử đặt phòng/bàn qua AI
3. **Tối ưu**: Điều chỉnh giá và số lượng theo nhu cầu thực tế
4. **Monitor**: Theo dõi booking và cập nhật khả dụng
