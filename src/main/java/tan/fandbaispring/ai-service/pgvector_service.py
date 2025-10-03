# -*- coding: utf-8 -*-
"""
PgVector Service - Thay thế cho ChromaDB
Sử dụng PostgreSQL với pgvector extension để lưu trữ và tìm kiếm vector embeddings
"""

import psycopg2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PgVectorService:
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection = None
        self._ensure_extension()
    
    def _get_connection(self):
        """Lấy kết nối database"""
        if self.connection is None or self.connection.closed:
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
        return self.connection
    
    def _ensure_extension(self):
        """Đảm bảo pgvector extension được cài đặt"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            logger.info("PgVector extension đã được đảm bảo")
        except Exception as e:
            logger.error(f"Lỗi khi tạo pgvector extension: {e}")
            raise
    
    def _ensure_table(self):
        """Đảm bảo bảng vector_embeddings tồn tại"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Tạo bảng nếu chưa tồn tại
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vector_embeddings (
                    id SERIAL PRIMARY KEY,
                    establishment_id VARCHAR(255) UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    embedding VECTOR(1536), -- OpenAI/Google embedding dimension
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Tạo index cho vector similarity search
            cur.execute("""
                CREATE INDEX IF NOT EXISTS vector_embeddings_embedding_idx 
                ON vector_embeddings USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100);
            """)
            
            # Tạo index cho establishment_id
            cur.execute("""
                CREATE INDEX IF NOT EXISTS vector_embeddings_establishment_id_idx 
                ON vector_embeddings (establishment_id);
            """)
            
            conn.commit()
            logger.info("Bảng vector_embeddings đã được đảm bảo")
        except Exception as e:
            logger.error(f"Lỗi khi tạo bảng vector_embeddings: {e}")
            raise
    
    def add_embedding(self, establishment_id: str, content: str, 
                     metadata: Dict[str, Any], embedding: List[float]) -> bool:
        """Thêm embedding mới vào database"""
        try:
            self._ensure_table()
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Chuyển đổi embedding thành numpy array để đảm bảo đúng format
            embedding_array = np.array(embedding, dtype=np.float32)
            
            # Sử dụng UPSERT (INSERT ... ON CONFLICT ... DO UPDATE)
            cur.execute("""
                INSERT INTO vector_embeddings 
                (establishment_id, content, metadata, embedding, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (establishment_id) 
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    updated_at = EXCLUDED.updated_at;
            """, (
                establishment_id, 
                content, 
                psycopg2.extras.Json(metadata),
                embedding_array.tolist(),
                datetime.now()
            ))
            
            conn.commit()
            logger.info(f"Đã thêm/cập nhật embedding cho establishment_id: {establishment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi thêm embedding: {e}")
            return False
    
    def remove_embedding(self, establishment_id: str) -> bool:
        """Xóa embedding khỏi database"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute(
                "DELETE FROM vector_embeddings WHERE establishment_id = %s",
                (establishment_id,)
            )
            
            deleted_count = cur.rowcount
            conn.commit()
            
            logger.info(f"Đã xóa {deleted_count} embedding cho establishment_id: {establishment_id}")
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Lỗi khi xóa embedding: {e}")
            return False
    
    def similarity_search(self, query_embedding: List[float], 
                         limit: int = 10, 
                         where_clause: Optional[str] = None,
                         where_params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Tìm kiếm tương tự dựa trên vector embedding"""
        try:
            self._ensure_table()
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Chuyển đổi query embedding thành numpy array
            query_array = np.array(query_embedding, dtype=np.float32)
            
            # Xây dựng query với cosine similarity
            base_query = """
                SELECT establishment_id, content, metadata, 
                       (1 - (embedding <=> %s)) as similarity_score
                FROM vector_embeddings
            """
            
            if where_clause:
                base_query += f" WHERE {where_clause}"
            
            base_query += """
                ORDER BY embedding <=> %s
                LIMIT %s;
            """
            
            # Thêm query embedding vào params (2 lần: một cho WHERE, một cho ORDER BY)
            params = [query_array.tolist()]
            if where_params:
                params.extend(where_params)
            params.extend([query_array.tolist(), limit])
            
            cur.execute(base_query, params)
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'establishment_id': row[0],
                    'content': row[1],
                    'metadata': row[2],
                    'similarity_score': float(row[3])
                })
            
            logger.info(f"Tìm thấy {len(results)} kết quả tương tự")
            return results
            
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm tương tự: {e}")
            return []
    
    def get_embedding_count(self) -> int:
        """Đếm số lượng embeddings trong database"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM vector_embeddings")
            count = cur.fetchone()[0]
            
            return count
            
        except Exception as e:
            logger.error(f"Lỗi khi đếm embeddings: {e}")
            return 0
    
    def get_embedding_by_id(self, establishment_id: str) -> Optional[Dict[str, Any]]:
        """Lấy embedding theo establishment_id"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT establishment_id, content, metadata, embedding, created_at, updated_at
                FROM vector_embeddings 
                WHERE establishment_id = %s
            """, (establishment_id,))
            
            row = cur.fetchone()
            if row:
                return {
                    'establishment_id': row[0],
                    'content': row[1],
                    'metadata': row[2],
                    'embedding': row[3],
                    'created_at': row[4],
                    'updated_at': row[5]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy embedding theo ID: {e}")
            return None
    
    def close(self):
        """Đóng kết nối database"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Đã đóng kết nối PgVector database")
