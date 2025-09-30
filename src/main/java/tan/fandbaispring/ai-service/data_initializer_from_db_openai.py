import pandas as pd
import psycopg2
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings  # Hoặc dùng model embedding của Gemini
import os

# --- Cấu hình DB (Cần khớp với Spring Boot) ---
DB_HOST = "localhost"
DB_NAME = "fast_planner_db"
DB_USER = "postgres"
DB_PASS = "root"  # Thay thế bằng mật khẩu thực tế


# Đảm bảo khóa API OpenAI đã được thiết lập trong biến môi trường
# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"

def fetch_data_from_postgres():
    """Kết nối PostgreSQL và lấy dữ liệu cần thiết cho RAG."""
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()

        # CHỈ LẤY CÁC CỘT CẦN THIẾT
        cur.execute("""
            SELECT 
                id, name, type, price_range_vnd, star_rating, owner_id,
                description_long, amenities_list
            FROM establishment;
        """)

        col_names = [desc[0] for desc in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=col_names)

        # Xử lý amenities_list từ định dạng DB sang chuỗi
        df['amenities_list'] = df['amenities_list'].apply(
            lambda x: ', '.join(x) if isinstance(x, list) else str(x)
        )
        return df
    except Exception as error:
        print(f"❌ Lỗi DB: {error}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            conn.close()


def initialize_vector_store():
    df = fetch_data_from_postgres()
    if df.empty: return

    # 1. Chuẩn hóa dữ liệu cho source_text RAG
    df['source_text'] = df.apply(
        lambda row: (
            f"ID: {row['id']}, Tên: {row['name']}, Loại: {row['type']}, Giá: {row['price_range_vnd']}, "
            f"Sao: {row['star_rating']}, Tiện ích: {row['amenities_list']}. "
            f"Mô tả chi tiết: {row['description_long']}"
        ), axis=1
    )

    # 2. Định nghĩa Metadata (chứa các trường lọc)
    metadatas = df.drop(columns=['description_long', 'source_text', 'amenities_list']).to_dict('records')
    texts = df['source_text'].tolist()

    # 3. Tạo Vector Store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_texts(
        texts=texts, embedding=embeddings, metadatas=metadatas,
        collection_name="fast_planner_establishments",
        persist_directory="./chroma_db"
    )
    vectorstore.persist()
    print("✅ Vector Store đã được tạo/cập nhật thành công.")


if __name__ == "__main__':
    initialize_vector_store()