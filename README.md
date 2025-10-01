# FandBAI Spring - AI-Powered Booking Platform

## 📋 Tổng quan dự án

**FandBAI Spring** là một nền tảng đặt chỗ thông minh được tích hợp AI, cho phép người dùng đặt phòng khách sạn và bàn nhà hàng thông qua giao diện trò chuyện tự nhiên. Hệ thống sử dụng AI để hiểu yêu cầu của người dùng và đưa ra gợi ý phù hợp nhất.

## 🚀 Tính năng chính

### 🤖 AI Booking Assistant
- **Trò chuyện tự nhiên**: Giao diện chat giống ChatGPT để tương tác với người dùng
- **RAG (Retrieval-Augmented Generation)**: Tìm kiếm thông minh dựa trên cơ sở dữ liệu
- **Quiz thông minh**: Thu thập thông tin người dùng qua các câu hỏi tương tác
- **Gợi ý cá nhân hóa**: Đề xuất phù hợp dựa trên sở thích và yêu cầu

### 🏢 Quản lý cơ sở (Partner Portal)
- **Tạo và quản lý cơ sở**: Thêm khách sạn/nhà hàng với thông tin chi tiết
- **Quản lý loại phòng/bàn**: Tạo và cấu hình các loại phòng, bàn với giá và tiện ích
- **Upload hình ảnh**: Quản lý hình ảnh chính và thư viện ảnh
- **Quản lý booking**: Xem và cập nhật trạng thái đặt chỗ

### 👤 Trải nghiệm người dùng
- **Đăng ký/Đăng nhập**: Hệ thống phân quyền CUSTOMER/PARTNER
- **Tìm kiếm thông minh**: Lọc theo thành phố, giá, tiện ích, ngày
- **Xem chi tiết**: Thông tin đầy đủ về cơ sở và loại phòng/bàn
- **Đặt chỗ dễ dàng**: Quy trình đặt chỗ đơn giản và trực quan

## 🏗️ Kiến trúc hệ thống

### Backend (Spring Boot)
- **Framework**: Spring Boot 3.5.6 với Java 21
- **Database**: PostgreSQL với JPA/Hibernate
- **Security**: Spring Security cho authentication
- **Image Storage**: Cloudinary cho quản lý hình ảnh
- **AI Integration**: REST API kết nối với Python AI service

### Frontend (React + Vite)
- **Framework**: React 19 với TypeScript
- **Styling**: Tailwind CSS với animations mượt mà
- **Routing**: React Router DOM
- **State Management**: React Context API
- **UI/UX**: Giao diện hiện đại với Notion-like animations

### AI Service (Python + FastAPI)
- **LLM**: Google Gemini API cho xử lý ngôn ngữ tự nhiên
- **Vector Store**: ChromaDB cho RAG search
- **Framework**: FastAPI với LangChain
- **Features**: Quiz generation, RAG search, parameter extraction

## 🛠️ Công nghệ sử dụng

### Backend Stack
- **Java 21** - Ngôn ngữ lập trình chính
- **Spring Boot 3.5.6** - Framework backend
- **Spring Data JPA** - ORM cho database
- **Spring Security** - Authentication & Authorization
- **PostgreSQL** - Database chính
- **Lombok** - Giảm boilerplate code
- **Maven** - Build tool
- **Cloudinary** - Cloud image storage

### Frontend Stack
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool và dev server
- **Tailwind CSS 4** - Utility-first CSS framework
- **React Router DOM** - Client-side routing
- **Axios** - HTTP client
- **Heroicons** - Icon library

### AI & ML Stack
- **Python 3.x** - AI service
- **FastAPI** - Python web framework
- **LangChain** - LLM framework
- **Google Gemini API** - Large Language Model
- **ChromaDB** - Vector database cho RAG
- **PostgreSQL** - Metadata storage

## 📁 Cấu trúc dự án

```
FandBAISpring/
├── src/main/java/tan/fandbaispring/
│   ├── controller/          # REST API controllers
│   ├── model/              # JPA entities
│   ├── dto/                # Data Transfer Objects
│   ├── repository/         # JPA repositories
│   ├── service/            # Business logic
│   ├── ai-service/         # Python AI service
│   └── cloud/              # Cloudinary configuration
├── frontend/partner-portal/
│   ├── src/
│   │   ├── pages/          # React pages
│   │   ├── components/     # Reusable components
│   │   ├── api/            # API client
│   │   ├── auth/           # Authentication
│   │   └── constants/      # Static data
│   └── public/             # Static assets
└── src/main/resources/
    └── application.properties
```

## 🚀 Hướng dẫn cài đặt

### Yêu cầu hệ thống
- **Java 21+**
- **Node.js 18+**
- **Python 3.8+**
- **PostgreSQL 12+**
- **Maven 3.6+**

### 1. Clone repository
```bash
git clone <repository-url>
cd FandBAISpring
```

### 2. Cấu hình Database
```sql
-- Tạo database PostgreSQL
CREATE DATABASE fast_planner_db;
```

### 3. Cấu hình Backend
```bash
# Cập nhật application.properties với thông tin database
spring.datasource.url=jdbc:postgresql://localhost:5432/fast_planner_db
spring.datasource.username=your_username
spring.datasource.password=your_password

# Cấu hình Cloudinary
cloudinary.cloud_name=your_cloud_name
cloudinary.api_key=your_api_key
cloudinary.api_secret=your_api_secret
```

### 4. Chạy Backend
```bash
# Build và chạy Spring Boot
mvn clean install
mvn spring-boot:run
```

### 5. Cấu hình AI Service
```bash
# Cài đặt Python dependencies
cd src/main/java/tan/fandbaispring/ai-service
pip install -r requirements.txt

# Cấu hình Gemini API key
export GEMINI_API_KEY=your_gemini_api_key

# Chạy AI service
python ai_service_gemini.py
```

### 6. Chạy Frontend
```bash
# Cài đặt dependencies
cd frontend/partner-portal
npm install

# Chạy development server
npm run dev
```

## 🔧 Cấu hình môi trường

### Environment Variables
```bash
# Database
DB_URL=jdbc:postgresql://localhost:5432/fast_planner_db
DB_USERNAME=postgres
DB_PASSWORD=root

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# AI Service
GEMINI_API_KEY=your_gemini_api_key
PYTHON_AI_SERVICE_URL=http://localhost:8000
```

### Ports mặc định
- **Backend**: http://localhost:8080
- **Frontend**: http://localhost:5173
- **AI Service**: http://localhost:8000
- **Database**: localhost:5432

## 📊 API Documentation

### 🔐 Authentication Endpoints
| Method | Endpoint | Mô tả | Vai trò |
|--------|----------|-------|---------|
| `POST` | `/api/auth/register` | Đăng ký tài khoản mới với role (CUSTOMER/PARTNER) | Tạo tài khoản người dùng |
| `POST` | `/api/auth/login` | Đăng nhập và nhận thông tin user (id, role, email) | Xác thực người dùng |

### 🏢 Partner Management Endpoints
| Method | Endpoint | Mô tả | Vai trò |
|--------|----------|-------|---------|
| `GET` | `/api/partner/establishments/{ownerId}` | Lấy danh sách cơ sở của partner | Quản lý cơ sở |
| `POST` | `/api/partner/establishments` | Tạo cơ sở mới (khách sạn/nhà hàng) | Thêm cơ sở |
| `GET` | `/api/partner/establishments/{id}` | Chi tiết thông tin cơ sở | Xem chi tiết |
| `PUT` | `/api/partner/establishments/{id}` | Cập nhật thông tin cơ sở | Chỉnh sửa cơ sở |
| `POST` | `/api/partner/upload-image` | Upload hình ảnh lên Cloudinary | Quản lý media |

### 🏠 Unit Type Management Endpoints
| Method | Endpoint | Mô tả | Vai trò |
|--------|----------|-------|---------|
| `GET` | `/api/partner/types/{establishmentId}` | Lấy danh sách loại phòng/bàn | Quản lý loại |
| `POST` | `/api/partner/types` | Tạo loại phòng/bàn mới | Thêm loại |
| `PUT` | `/api/partner/types/{typeId}` | Cập nhật thông tin loại | Chỉnh sửa loại |
| `DELETE` | `/api/partner/types/{typeId}` | Xóa loại phòng/bàn | Xóa loại |

### 📅 Booking Management Endpoints
| Method | Endpoint | Mô tả | Vai trò |
|--------|----------|-------|---------|
| `GET` | `/api/partner/bookings/{ownerId}` | Lấy danh sách booking của partner | Quản lý booking |
| `GET` | `/api/booking/user/view/{userId}` | Lấy booking của user | Xem booking cá nhân |

### 🤖 AI-Powered Booking Endpoints
| Method | Endpoint | Mô tả | Vai trò |
|--------|----------|-------|---------|
| `POST` | `/api/booking/process` | Xử lý AI quiz và tìm kiếm gợi ý | AI booking flow |
| `POST` | `/api/booking/confirm` | Xác nhận đặt chỗ cuối cùng | Hoàn tất booking |

### 🔍 AI Service Endpoints (Python)
| Method | Endpoint | Mô tả | Vai trò |
|--------|----------|-------|---------|
| `POST` | `/ai/quiz` | Tạo quiz AI tương tác | Thu thập thông tin |
| `POST` | `/ai/rag-search` | Tìm kiếm thông minh với RAG | Tìm gợi ý phù hợp |
| `POST` | `/add-establishment` | Thêm cơ sở vào vector store | Cập nhật AI knowledge |
| `GET` | `/health` | Kiểm tra trạng thái AI service | Health monitoring |
| `GET` | `/debug/db/{id}` | Debug database connection | Troubleshooting |
| `GET` | `/debug/vector/{id}` | Debug vector store | Troubleshooting |

### 📊 Search & Availability Endpoints
| Method | Endpoint | Mô tả | Vai trò |
|--------|----------|-------|---------|
| `GET` | `/api/availability` | Kiểm tra tình trạng phòng/bàn | Check availability |
| `POST` | `/api/search` | Tìm kiếm cơ sở theo tiêu chí | Search functionality |

## 🔧 API Usage Examples

### Authentication Flow
```bash
# 1. Đăng ký tài khoản
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "partner@example.com",
    "password": "123456",
    "role": "PARTNER"
  }'

# 2. Đăng nhập (trả về id, role, email - không có JWT token)
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "partner@example.com",
    "password": "123456"
  }'
```

### Partner Management
```bash
# Tạo cơ sở mới (không cần Authorization header)
curl -X POST http://localhost:8080/api/partner/establishments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Khách sạn ABC",
    "type": "HOTEL",
    "city": "Hồ Chí Minh",
    "address": "123 Nguyễn Huệ, Q1",
    "description": "Khách sạn 5 sao tại trung tâm",
    "amenities": ["WiFi", "Pool", "Gym", "Spa"]
  }'

# Lấy danh sách cơ sở (không cần Authorization header)
curl -X GET http://localhost:8080/api/partner/establishments/1
```

### AI Booking Flow
```bash
# Bắt đầu AI quiz
curl -X POST http://localhost:8080/api/booking/process \
  -H "Content-Type: application/json" \
  -d '{
    "userPrompt": "Tôi muốn đặt phòng khách sạn ở Đà Nẵng cho 2 người, ngày 15/12",
    "currentParams": {}
  }'

# Xác nhận booking
curl -X POST http://localhost:8080/api/booking/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "establishmentId": "123",
    "itemType": "Deluxe Room",
    "startDate": "2024-12-15",
    "duration": 2,
    "totalPrice": 1500000,
    "userId": 1
  }'
```

### AI Service Integration
```bash
# Kiểm tra trạng thái AI service
curl -X GET http://localhost:8000/health

# Thêm cơ sở vào vector store
curl -X POST http://localhost:8000/add-establishment \
  -H "Content-Type: application/json" \
  -d '{
    "establishment_id": "123",
    "name": "Khách sạn ABC",
    "city": "Hồ Chí Minh",
    "amenities": ["WiFi", "Pool", "Gym"]
  }'
```

## 📋 Request/Response Formats

### Authentication Response
```json
{
  "message": "Đăng nhập thành công.",
  "id": 1,
  "email": "partner@example.com",
  "role": "PARTNER"
}
```

### AI Quiz Response
```json
{
  "quiz_completed": false,
  "key_to_collect": "city",
  "question": "Bạn muốn đặt chỗ ở thành phố nào?",
  "options": ["Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Nha Trang"],
  "current_params": {
    "establishment_type": "HOTEL",
    "num_guests": 2
  },
  "image_options": null
}
```

### Booking Suggestion Response
```json
{
  "suggestions": [
    {
      "establishment_id": "123",
      "establishment_name": "Khách sạn ABC",
      "city": "Đà Nẵng",
      "item_type": "Deluxe Room",
      "item_image_url": "https://res.cloudinary.com/...",
      "price": 1500000,
      "availability": true,
      "amenities": ["WiFi", "Pool", "Gym"]
    }
  ],
  "total_found": 5,
  "search_criteria": {
    "city": "Đà Nẵng",
    "num_guests": 2,
    "check_in_date": "2024-12-15"
  }
}
```

### Error Response
```json
{
  "message": "Không tìm thấy cơ sở phù hợp"
}
```

## 🔒 Bảo mật

- **Simple Authentication**: Sử dụng password cố định "123456" cho demo
- **Role-based Access**: Phân quyền CUSTOMER/PARTNER
- **No JWT**: Không sử dụng JWT token, chỉ trả về thông tin user
- **Open API**: Tất cả endpoints đều public (SecurityConfig cho phép tất cả)

## 🎯 Tính năng nổi bật

### 1. AI-Powered Booking Flow
- **Conversational UI**: Giao diện chat tự nhiên như ChatGPT
- **Smart Parameter Extraction**: Tự động trích xuất thông tin từ câu hỏi
- **Contextual Suggestions**: Gợi ý dựa trên ngữ cảnh và lịch sử
- **Multi-step Quiz**: Thu thập thông tin qua các bước tương tác

### 2. Advanced Search & Filtering
- **RAG Search**: Tìm kiếm thông minh dựa trên vector embeddings
- **Fuzzy Matching**: Tìm kiếm mờ cho tên thành phố và tiện ích
- **Alias Mapping**: Xử lý các tên gọi khác nhau của cùng một địa điểm
- **Fallback Mechanisms**: Cơ chế dự phòng khi AI không khả dụng

### 3. Rich Media Management
- **Cloudinary Integration**: Upload và quản lý hình ảnh trên cloud
- **Image Preview**: Xem trước hình ảnh khi hover
- **Responsive Images**: Tối ưu hiển thị trên các thiết bị khác nhau
- **Gallery Management**: Quản lý thư viện ảnh cho cơ sở

### 4. Modern UI/UX
- **Notion-like Animations**: Hiệu ứng mượt mà và chuyên nghiệp
- **Responsive Design**: Tương thích với mọi kích thước màn hình
- **Dark/Light Theme**: Hỗ trợ chế độ sáng/tối
- **Smooth Transitions**: Chuyển đổi mượt mà giữa các trang

## 🔒 Bảo mật

- **JWT Authentication**: Xác thực token-based
- **Role-based Access**: Phân quyền CUSTOMER/PARTNER
- **CORS Configuration**: Cấu hình cross-origin requests
- **Input Validation**: Kiểm tra dữ liệu đầu vào
- **SQL Injection Protection**: Bảo vệ khỏi SQL injection
## 🔧 Environment Variables

Tạo file `.env` trong thư mục gốc với các biến sau:

```bash
# Database
DB_URL=jdbc:postgresql://localhost:5432/fast_planner_db
DB_USERNAME=postgres
DB_PASSWORD=your_password

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# AI Service
PYTHON_AI_SERVICE_URL=http://localhost:8000
GEMINI_API_KEY=your_gemini_api_key

```

## 🧪 Testing

### Backend Testing
```bash
# Chạy unit tests
mvn test

# Chạy integration tests
mvn verify
```

### Frontend Testing
```bash
# Chạy tests
npm test

# Chạy linting
npm run lint
```

## 📈 Performance

- **Database Indexing**: Tối ưu truy vấn database
- **Caching**: Cache kết quả tìm kiếm
- **Lazy Loading**: Tải dữ liệu theo yêu cầu
- **Image Optimization**: Tối ưu hình ảnh
- **API Rate Limiting**: Giới hạn tần suất gọi API

## 🚧 Roadmap

### Đã hoàn thành ✅
- [x] Backend API với Spring Boot
- [x] Frontend React với TypeScript
- [x] AI Service với Gemini API
- [x] Database schema và relationships
- [x] Authentication & Authorization
- [x] Image upload với Cloudinary
- [x] AI-powered booking flow
- [x] Partner portal cho quản lý
- [x] Responsive UI với Tailwind CSS

### Đang phát triển 🚧
- [ ] **Payment Integration**: Tích hợp thanh toán (Stripe, PayPal, VNPay)
- [ ] **Email Notifications**: Gửi email xác nhận và thông báo
- [ ] **Real-time Updates**: WebSocket cho cập nhật real-time
- [ ] **Mobile App**: Ứng dụng di động với React Native

### Kế hoạch tương lai 📋
- [ ] **Advanced Analytics**: Dashboard phân tích dữ liệu
- [ ] **Multi-language Support**: Hỗ trợ đa ngôn ngữ
- [ ] **API Rate Limiting**: Giới hạn tần suất gọi API
- [ ] **Microservices Architecture**: Chuyển sang kiến trúc microservices
- [ ] **Kubernetes Deployment**: Triển khai trên Kubernetes
- [ ] **CI/CD Pipeline**: Tự động hóa build và deploy

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request


## 👥 Tác giả

- **Tên**: Espresso23
- **Email**: [phamlequoctan@gamil.com]
- **GitHub**: [@espresso23]

## 🙏 Acknowledgments

- Spring Boot team cho framework tuyệt vời
- React team cho UI library mạnh mẽ
- Google Gemini team cho AI capabilities
- Tailwind CSS team cho utility-first CSS
- PostgreSQL team cho database engine

---

**Lưu ý**: Dự án này đang trong giai đoạn phát triển. Một số tính năng có thể chưa hoàn thiện. Vui lòng báo cáo bug hoặc đề xuất tính năng mới qua Issues.

## 📞 Hỗ trợ

Nếu bạn gặp vấn đề hoặc có câu hỏi, vui lòng:
- Tạo issue trên GitHub

*Được phát triển với ❤️ bởi team FandBAI*