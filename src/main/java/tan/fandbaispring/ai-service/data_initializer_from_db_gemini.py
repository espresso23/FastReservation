import pandas as pd
import psycopg2 # Cần thiết để kết nối PostgreSQL
import os
import time
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings # Sử dụng Gemini Embeddings

# --- CẤU HÌNH ---
DB_HOST = "localhost:5432" # Bỏ port trong host nếu dùng psycopg2
DB_NAME = "fast_planner_db"
DB_USER = "postgres"
DB_PASS = "root" # Mật khẩu của bạn

CHROMA_PATH = "./chroma_db_gemini"
EMBEDDING_MODEL = "text-embedding-004"

# Đảm bảo khóa API GEMINI đã được thiết lập
# KHÔNG NÊN hardcode key trong file. Tốt nhất nên dùng os.environ.get("GEMINI_API_KEY")
os.environ["GEMINI_API_KEY"] = "AIzaSyAVlInLQvqqmiEwmXn1fmtMRcfNQpytgRY"

# --- Hàm Lấy dữ liệu từ DB (ĐÃ THÊM LOGIC) ---
def fetch_data_from_postgres():
    """Truy vấn PostgreSQL để lấy toàn bộ dữ liệu Establishment."""
    print("⏳ Đang kết nối và lấy dữ liệu từ PostgreSQL...")
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()
        
        # Lấy TẤT CẢ các cột cần thiết cho Metadata và Source Text
        cur.execute("""
            SELECT 
                id, name, type, price_range_vnd, star_rating, owner_id, description_long, amenities_list, has_inventory
            FROM 
                establishment;
        """)
        
        col_names = [desc[0] for desc in cur.description]
        data = cur.fetchall()
        
        print(f"✅ Lấy thành công {len(data)} bản ghi từ DB.")
        
        df = pd.DataFrame(data, columns=col_names)
        
        # Xử lý list/array (amenities_list) thành chuỗi để dễ nhúng
        df['amenities_list'] = df['amenities_list'].apply(
             lambda x: ', '.join(x) if isinstance(x, list) else str(x)
        )
        
        return df
    except Exception as error:
        print(f"❌ Lỗi khi làm việc với PostgreSQL: {error}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            conn.close()

# --- Hàm Khởi tạo/Cập nhật Vector Store ---
def initialize_vector_store():
    df = fetch_data_from_postgres()
    if df.empty: 
        print("Không có dữ liệu để tạo Vector Store.")
        return

    # 1. Chuẩn hóa dữ liệu cho RAG (Source Text)
    df['source_text'] = df.apply(
        lambda row: (
            f"ID: {row['id']}, Tên: {row['name']}, Loại: {row['type']}, Giá: {row['price_range_vnd']}, "
            f"Sao: {row['star_rating']}, Tiện ích: {row['amenities_list']}. "
            f"Mô tả chi tiết: {row['description_long']}"
        ), axis=1
    )

    # 2. Định nghĩa Metadata và Text
    # Bỏ các cột TEXT dài khỏi metadata
    metadatas = df.drop(columns=['description_long', 'source_text', 'amenities_list']).to_dict('records')
    texts = df['source_text'].tolist()

    # 3. Tạo Vector Store với GEMINI EMBEDDINGS
    print(f"⏳ Đang tạo {len(texts)} Vector Embeddings (Gemini) và lưu vào ChromaDB...")
    start_time = time.time()
    
    # Sử dụng mô hình text-embedding-004 cho Embedding
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL) 

    vectorstore = Chroma.from_texts(
        texts=texts, 
        embedding=embeddings, 
        metadatas=metadatas,
        collection_name="fast_planner_establishments",
        persist_directory=CHROMA_PATH
    )
    vectorstore.persist()
    end_time = time.time()
    print(f"✅ Vector Store (Gemini) đã được tạo/cập nhật thành công trong {end_time - start_time:.2f} giây.")


if __name__ == '__main__':
    initialize_vector_store()