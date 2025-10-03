-- Script để cài đặt pgvector extension trong PostgreSQL
-- Chạy script này với quyền superuser

-- Cài đặt pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Tạo bảng vector_embeddings nếu chưa tồn tại
CREATE TABLE IF NOT EXISTS vector_embeddings (
    id SERIAL PRIMARY KEY,
    establishment_id VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536), -- OpenAI/Google embedding dimension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tạo index cho vector similarity search
CREATE INDEX IF NOT EXISTS vector_embeddings_embedding_idx 
ON vector_embeddings USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Tạo index cho establishment_id
CREATE INDEX IF NOT EXISTS vector_embeddings_establishment_id_idx 
ON vector_embeddings (establishment_id);

-- Tạo index cho metadata queries (sử dụng BTREE thay vì GIN cho TEXT)
CREATE INDEX IF NOT EXISTS vector_embeddings_metadata_city_idx 
ON vector_embeddings ((metadata->>'city'));

-- Hiển thị thông tin về bảng đã tạo
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename = 'vector_embeddings';

-- Hiển thị thông tin về các index
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'vector_embeddings';
