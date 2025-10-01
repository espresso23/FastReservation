# Hướng dẫn sử dụng Postman để thêm dữ liệu mẫu

## Bước 1: Import Collection vào Postman

1. Mở Postman
2. Click vào **Import** (góc trên bên trái)
3. Chọn **File** và browse đến file `postman_establishments_collection.json`
4. Click **Import**

## Bước 2: Thiết lập Environment (Tùy chọn)

1. Tạo Environment mới:
   - Click vào **Environments** tab
   - Click **Create Environment**
   - Đặt tên: `FandBAI Local`
   - Thêm variable:
     - Key: `base_url`
     - Value: `http://localhost:8080`
   - Click **Save**

2. Chọn Environment:
   - Click vào dropdown Environment (góc trên bên phải)
   - Chọn `FandBAI Local`

## Bước 3: Thêm dữ liệu establishments

### Cách 1: Chạy từng request riêng lẻ
1. Mở collection **"Add Sample Establishments"**
2. Chọn request đầu tiên (ví dụ: "1. Hotel Continental Saigon")
3. Click **Send**
4. Lặp lại cho các request khác

### Cách 2: Chạy tất cả requests cùng lúc
1. Click vào collection **"Add Sample Establishments"**
2. Click **Run collection**
3. Click **Run Add Sample Establishments**
4. Click **Run** để chạy tất cả requests

## Bước 4: Kiểm tra kết quả

Mỗi request sẽ trả về response với status code:
- **201 Created**: Thành công
- **400 Bad Request**: Lỗi dữ liệu
- **500 Internal Server Error**: Lỗi server

## Danh sách 15 establishments sẽ được thêm:

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

## Lưu ý quan trọng:

- **Tất cả establishments đều có `ownerId = "1"`**
- **Không cần upload ảnh** - bạn có thể cập nhật ảnh sau
- **Đảm bảo backend đang chạy** trên `http://localhost:8080`
- **Mỗi request sẽ tạo một establishment mới** trong database

## Troubleshooting:

### Lỗi 415 Unsupported Media Type:
- Đảm bảo Content-Type là `application/json`
- Kiểm tra request body format

### Lỗi Connection Refused:
- Kiểm tra backend có đang chạy không
- Kiểm tra URL trong environment variable

### Lỗi 500 Internal Server Error:
- Kiểm tra logs của backend
- Kiểm tra database connection

## Sau khi thêm xong:

1. Kiểm tra database để xác nhận dữ liệu đã được thêm
2. Test AI booking để xem establishments có xuất hiện trong suggestions không
3. Upload ảnh cho các establishments qua frontend hoặc API khác
