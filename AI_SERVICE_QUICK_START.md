# 🚀 AI Service Quick Start Guide

## 📋 Tổng quan

AI Service là Python FastAPI service cung cấp AI quiz và RAG search cho hệ thống booking. Đã tạo đầy đủ scripts và hướng dẫn để chạy dễ dàng.

## 🎯 Cách chạy nhanh nhất

### **Windows:**
```bash
# Chạy tất cả services cùng lúc
start_all_services.bat

# Hoặc chạy AI service riêng
cd src\main\java\tan\fandbaispring\ai-service
start_ai_service.bat
```

### **Linux/Mac:**
```bash
# Chạy tất cả services cùng lúc
chmod +x start_all_services.sh
./start_all_services.sh

# Hoặc chạy AI service riêng
cd src/main/java/tan/fandbaispring/ai-service
chmod +x start_ai_service.sh
./start_ai_service.sh
```

## 📁 Files đã tạo

### **AI Service Files:**
- `requirements.txt` - Python dependencies
- `env_example.txt` - Environment template
- `run_gemini.py` - Chạy Gemini service
- `run_openai.py` - Chạy OpenAI service
- `install_dependencies.py` - Cài đặt dependencies
- `test_service.py` - Test service
- `start_ai_service.bat` - Windows startup script
- `start_ai_service.sh` - Linux/Mac startup script
- `start_ai_service.ps1` - PowerShell startup script
- `README_AI_SERVICE.md` - Hướng dẫn chi tiết

### **All Services Scripts:**
- `start_all_services.bat` - Windows: Start all services
- `start_all_services.sh` - Linux/Mac: Start all services

## 🔧 Setup từ đầu

### **1. Cài đặt Python dependencies:**
```bash
cd src/main/java/tan/fandbaispring/ai-service
python install_dependencies.py
```

### **2. Cấu hình API keys:**
```bash
# Copy template
cp env_example.txt .env

# Chỉnh sửa .env với API keys của bạn
nano .env  # Linux/Mac
notepad .env  # Windows
```

### **3. Điền API keys:**
```env
# Google Gemini API Key (cho Gemini service)
GOOGLE_API_KEY=your_gemini_api_key_here

# OpenAI API Key (cho OpenAI service)
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fast_planner_db
DB_USER=postgres
DB_PASSWORD=root
```

## 🚀 Chạy service

### **Option 1: Chạy tất cả services (Recommended)**
```bash
# Windows
start_all_services.bat

# Linux/Mac
./start_all_services.sh
```

### **Option 2: Chạy AI service riêng**
```bash
cd src/main/java/tan/fandbaispring/ai-service

# Windows
start_ai_service.bat

# Linux/Mac
./start_ai_service.sh

# PowerShell
./start_ai_service.ps1
```

### **Option 3: Manual**
```bash
cd src/main/java/tan/fandbaispring/ai-service

# Gemini service
python run_gemini.py

# OpenAI service
python run_openai.py
```

## 🧪 Test service

```bash
cd src/main/java/tan/fandbaispring/ai-service
python test_service.py
```

## 📱 Service URLs

Sau khi chạy, các services sẽ có sẵn tại:

- **Frontend**: http://localhost:5173
- **Spring Boot**: http://localhost:8080
- **AI Service**: http://localhost:8000
- **AI Documentation**: http://localhost:8000/docs
- **AI Health Check**: http://localhost:8000/health

## 🔍 Kiểm tra hoạt động

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

#### **1. "Python not found":**
```bash
# Cài đặt Python 3.8+ từ https://python.org
# Đảm bảo Python được thêm vào PATH
```

#### **2. "API key not found":**
```bash
# Kiểm tra file .env
cat .env  # Linux/Mac
type .env  # Windows
```

#### **3. "Database connection failed":**
```bash
# Đảm bảo PostgreSQL đang chạy
# Kiểm tra thông tin database trong .env
```

#### **4. "Port 8000 already in use":**
```bash
# Tìm và kill process sử dụng port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac
```

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

## 🚀 Ready to go!

Sau khi setup xong, chạy:
```bash
start_all_services.bat  # Windows
./start_all_services.sh  # Linux/Mac
```

Và truy cập http://localhost:5173 để sử dụng hệ thống! 🎉
