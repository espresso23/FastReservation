# Hướng dẫn cài đặt pgvector

## Tổng quan
Dự án đã được chuyển đổi từ ChromaDB sang pgvector để đồng nhất với PostgreSQL. pgvector là một extension của PostgreSQL cho phép lưu trữ và tìm kiếm vector embeddings hiệu quả.

## Cài đặt pgvector extension

### 1. Cài đặt pgvector extension trong PostgreSQL

#### Trên Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql-16-pgvector
```

#### Trên macOS (với Homebrew):
```bash
brew install pgvector
```

#### Trên Windows:
Tải và cài đặt từ: https://github.com/pgvector/pgvector/releases

### 2. Kích hoạt extension trong database

Kết nối đến PostgreSQL database với quyền superuser và chạy:

```sql
-- Kích hoạt pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Chạy script setup

Chạy file `setup_pgvector.sql` để tạo bảng và index:

```bash
psql -U postgres -d fast_planner_db -f setup_pgvector.sql
```

## Cập nhật Dependencies

### Python dependencies
File `requirements.txt` đã được cập nhật với:
- `pgvector>=0.2.5` (thay thế cho `chromadb`)
- `numpy>=1.24.0` (hỗ trợ vector operations)

### Java dependencies
File `pom.xml` đã được cập nhật với:
```xml
<dependency>
    <groupId>com.pgvector</groupId>
    <artifactId>pgvector</artifactId>
    <version>0.1.4</version>
</dependency>
```

## Cấu trúc mới

### Bảng vector_embeddings
```sql
CREATE TABLE vector_embeddings (
    id SERIAL PRIMARY KEY,
    establishment_id VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Các tính năng chính:
- **Vector similarity search**: Tìm kiếm tương tự dựa trên cosine similarity
- **Metadata filtering**: Lọc kết quả theo city, type, amenities
- **Automatic indexing**: Index được tạo tự động cho hiệu suất tốt
- **JSONB metadata**: Lưu trữ metadata linh hoạt

## API Endpoints

Tất cả API endpoints vẫn giữ nguyên interface:
- `POST /generate-quiz`: Tạo quiz cho người dùng
- `POST /rag-search`: Tìm kiếm establishments
- `POST /add-establishment`: Thêm establishment vào vector store
- `POST /remove-establishment`: Xóa establishment khỏi vector store
- `GET /debug/vector/{id}`: Debug vector data
- `GET /health`: Health check

## Migration từ ChromaDB

### Dữ liệu cũ:
- Thư mục `chroma_db_gemini/` và `chroma_db_openai/` đã được xóa
- Dữ liệu vector cũ không được migrate tự động

### Khôi phục dữ liệu:
Để khôi phục dữ liệu vector, cần chạy lại các API `/add-establishment` cho tất cả establishments hiện có trong database.

## Troubleshooting

### Lỗi "extension vector does not exist":
```sql
-- Kiểm tra extension có được cài đặt không
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- Nếu có, kích hoạt extension
CREATE EXTENSION vector;
```

### Lỗi "relation vector_embeddings does not exist":
Chạy lại script `setup_pgvector.sql` với quyền phù hợp.

### Lỗi embedding dimension:
Đảm bảo embedding có đúng 1536 dimensions (OpenAI/Google embeddings).

## Performance Tips

1. **Index tuning**: Điều chỉnh `lists` parameter trong ivfflat index dựa trên số lượng vectors
2. **Batch operations**: Sử dụng batch insert cho nhiều embeddings cùng lúc
3. **Connection pooling**: Sử dụng connection pool cho PostgreSQL

## Monitoring

Kiểm tra hiệu suất:
```sql
-- Đếm số lượng embeddings
SELECT COUNT(*) FROM vector_embeddings;

-- Kiểm tra index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE tablename = 'vector_embeddings';
```
