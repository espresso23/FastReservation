# AI Service Setup Guide

## 🎯 Tổng quan

AI Service là Python FastAPI service cung cấp AI quiz và RAG search cho hệ thống booking. Có 2 phiên bản:

- **Gemini AI Service** (`ai_service_gemini.py`) - Sử dụng Google Gemini API
- **OpenAI AI Service** (`ai_service_openai.py`) - Sử dụng OpenAI API

## 🚀 Cách chạy nhanh

### **Windows:**
```bash
# Chạy script tự động
start_ai_service.bat
```

### **Linux/Mac:**
```bash
# Cấp quyền và chạy
chmod +x start_ai_service.sh
./start_ai_service.sh
```

### **Manual (Tất cả hệ điều hành):**
```bash
# 1. Cài đặt dependencies
python install_dependencies.py

# 2. Tạo file .env từ template
cp env_example.txt .env
# Chỉnh sửa .env với API keys của bạn

# 3. Chạy service
python run_gemini.py    # Cho Gemini
# hoặc
python run_openai.py    # Cho OpenAI
```

## 📋 Yêu cầu hệ thống

- **Python 3.8+**
- **PostgreSQL** (đã chạy với database `fast_planner_db`)
- **API Keys:**
  - Google Gemini API key (cho Gemini service)
  - OpenAI API key (cho OpenAI service)

## 🔧 Cài đặt chi tiết

### **1. Cài đặt Python dependencies:**
```bash
pip install -r requirements.txt
```

### **2. Cấu hình environment:**
```bash
# Copy template
cp env_example.txt .env

# Chỉnh sửa .env file
nano .env  # hoặc notepad .env trên Windows
```

### **3. Điền API keys vào .env:**
```env
# Google Gemini API Key
GOOGLE_API_KEY=your_gemini_api_key_here

# OpenAI API Key (cho ai_service_openai.py)
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fast_planner_db
DB_USER=postgres
DB_PASSWORD=root
```

## 🌐 Chạy service

### **Gemini AI Service:**
```bash
python run_gemini.py
```

### **OpenAI AI Service:**
```bash
python run_openai.py
```

### **Manual với uvicorn:**
```bash
# Gemini
uvicorn ai_service_gemini:app --host 0.0.0.0 --port 8000 --reload

# OpenAI
uvicorn ai_service_openai:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Endpoints

Service sẽ chạy trên `http://localhost:8000` với các endpoints:

### **Core APIs:**
- `POST /generate-quiz` - Tạo AI quiz
- `POST /rag-search` - Tìm kiếm RAG
- `POST /add-establishment` - Thêm establishment vào vector store
- `POST /remove-establishment` - Xóa establishment khỏi vector store

### **Debug APIs:**
- `GET /health` - Health check
- `GET /debug/vector/{establishment_id}` - Debug vector store
- `GET /debug/db/{establishment_id}` - Debug database

### **Documentation:**
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## 🔍 Kiểm tra service

### **1. Health Check:**
```bash
curl http://localhost:8000/health
```

### **2. Test API:**
```bash
# Test quiz generation
curl -X POST "http://localhost:8000/generate-quiz" \
  -H "Content-Type: application/json" \
  -d '{"user_prompt": "Tôi muốn đi Đà Nẵng ngày 2025-10-10 2 đêm"}'
```

### **3. Check documentation:**
Mở browser: `http://localhost:8000/docs`

## 🐛 Troubleshooting

### **Lỗi thường gặp:**

#### **1. "Module not found" errors:**
```bash
# Cài đặt lại dependencies
python install_dependencies.py
```

#### **2. "API key not found" errors:**
```bash
# Kiểm tra file .env
cat .env  # Linux/Mac
type .env  # Windows
```

#### **3. "Database connection failed":**
- Đảm bảo PostgreSQL đang chạy
- Kiểm tra thông tin database trong `.env`
- Test connection: `psql -h localhost -U postgres -d fast_planner_db`

#### **4. "Port 8000 already in use":**
```bash
# Tìm process sử dụng port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# Kill process hoặc đổi port
```

### **Logs và Debug:**
```bash
# Chạy với verbose logging
uvicorn ai_service_gemini:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

## 🔄 Tích hợp với Spring Boot

AI Service cần chạy song song với Spring Boot:

1. **Start PostgreSQL** (port 5432)
2. **Start AI Service** (port 8000)
3. **Start Spring Boot** (port 8080)
4. **Start Frontend** (port 5173)

### **URLs:**
- Spring Boot: `http://localhost:8080`
- AI Service: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## 📝 Notes

- AI Service sử dụng ChromaDB để lưu vector embeddings
- Vector store được lưu trong `./chroma_db_gemini` hoặc `./chroma_db_openai`
- Service tự động tạo vector store nếu chưa có
- Có thể chạy cả 2 service cùng lúc trên port khác nhau

## 🎯 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] PostgreSQL running
- [ ] API keys obtained (Gemini/OpenAI)
- [ ] `.env` file configured
- [ ] Dependencies installed
- [ ] Service running on port 8000
- [ ] Health check passed
- [ ] Spring Boot integration working
