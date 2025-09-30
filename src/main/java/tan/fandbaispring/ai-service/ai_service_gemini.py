from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from chromadb import PersistentClient
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import os
import psycopg2 
from typing import Dict, Any, List, Optional
import logging
from dotenv import load_dotenv
import warnings
from langchain_core._api import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

# --- CẤU HÌNH ---
# Nạp biến môi trường từ file .env nếu có và ánh xạ KEY phù hợp
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    alt_key = os.getenv("GEMINI_API_KEY")
    if alt_key:
        os.environ["GOOGLE_API_KEY"] = alt_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

# *** SỬA LỖI DB_CONFIG: Tách host và port để khớp với psycopg2 ***
db_host, db_port = "localhost", 5432 # Mặc định
if ":" in "localhost:5432":
    db_host, db_port_str = "localhost:5432".split(":")
    db_port = int(db_port_str)

DB_CONFIG = {
    "host": db_host, 
    "port": db_port, # Thêm port
    "database": "fast_planner_db",
    "user": "postgres",
    "password": "root" 
}

CHROMA_PATH = "./chroma_db_gemini"

# Khởi tạo LLM và Vector Store (có fallback)
llm = None
embeddings = None
vectorstore = None
try:
    # Thử model mới
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
except Exception as e1:
    logging.warning("Primary model init failed (gemini-2.5-flash): %s", getattr(e1, "message", str(e1)))
    try:
        # Fallback phổ biến, ổn định hơn
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.0)
    except Exception as e2:
        logging.error("Fallback model init failed (gemini-1.5-flash): %s", getattr(e2, "message", str(e2)))
        llm = None

try:
    embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
    chroma_client = PersistentClient(path=CHROMA_PATH)
    vectorstore = Chroma(
        collection_name="fast_planner_establishments",
        embedding_function=embeddings,
        client=chroma_client
    )
except Exception as e:
    logging.warning("Vector store/embeddings init failed: %s", getattr(e, "message", str(e)))
    embeddings = None
    vectorstore = None


# --- DTOs (Pydantic Models) ---

class QuizRequest(BaseModel):
    # SỬA LỖI: Sử dụng alias để ánh xạ từ Java camelCase sang Python snake_case
    user_prompt: str = Field(..., alias="userPrompt")
    current_params: Dict[str, Any] = Field(..., alias="currentParams")

    class Config:
        # Cấu hình Pydantic để chấp nhận tên trường theo alias khi deserialize (input)
        populate_by_name = True


# Định nghĩa lại response model để phù hợp với Output Parser
class QuizResponseModel(BaseModel):
    quiz_completed: bool = Field(description="True nếu tất cả 7 tham số cốt lõi đã có.")
    missing_quiz: Optional[str] = Field(None, description="Câu hỏi cần hỏi người dùng tiếp theo (Nếu quizCompleted là false).")
    key_to_collect: Optional[str] = Field(None, description="Tên tham số cần thu thập tiếp theo.")
    final_params: Dict[str, Any] = Field(description="Các tham số đã được cập nhật và chuẩn hóa.")

# Danh sách tham số cốt lõi (dùng cho cả fallback)
PARAM_ORDER = [
    "city", "check_in_date", "style_vibe", "max_price",
    "travel_companion", "duration", "amenities_priority"
]

FALLBACK_QUESTIONS = {
    "city": "Bạn muốn đi ở thành phố nào?",
    "check_in_date": "Bạn dự định ngày bắt đầu chuyến đi là khi nào? (YYYY-MM-DD)",
    "style_vibe": "Bạn thích phong cách/không khí nào? (ví dụ: lãng mạn, yên tĩnh, sôi động)",
    "max_price": "Ngân sách tối đa của bạn là bao nhiêu (VND)?",
    "travel_companion": "Bạn đi cùng ai? (một mình, cặp đôi, gia đình, bạn bè)",
    "duration": "Thời lượng chuyến đi bao lâu? (số ngày)",
    "amenities_priority": "Bạn ưu tiên tiện ích nào? (ví dụ: hồ bơi, spa, bãi đậu xe)"
}

# Gợi ý lựa chọn cho FE (multiple choice)
FALLBACK_OPTIONS = {
    "travel_companion": ["single", "couple", "family", "friends"],
    "style_vibe": ["romantic", "quiet", "lively", "luxury", "nature"],
    "amenities_priority": ["Hồ bơi", "Spa", "Bãi đậu xe", "Gym", "Buffet sáng", "Gần biển"],
    "duration": ["1","2","3","4","5","6","7"],
    "has_balcony": ["yes","no"]
}


class SearchRequest(BaseModel):
    params: Dict[str, Any]

class SearchResult(BaseModel):
    establishment_id: str
    relevance_score: float

class AddEstablishmentRequest(BaseModel):
    id: str

# --- Hàm Hỗ trợ: Truy vấn DB (Lấy dữ liệu cho RAG) ---
def fetch_single_establishment(establishment_id: str) -> Optional[Dict[str, Any]]:
    """Truy vấn PostgreSQL để lấy data của một cơ sở mới."""
    conn = None
    data = None
    try:
        # DB_CONFIG đã được sửa để hoạt động với psycopg2
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cur = conn.cursor()
        try:
            cur.execute("SET search_path TO public;")
        except Exception:
            pass
        
        cur.execute("""
            SELECT 
                id, name, type, price_range_vnd, star_rating, owner_id, description_long, city, image_url_main
            FROM 
                establishment
            WHERE 
                id = %s;
        """, (establishment_id,))
        
        col_names = [desc[0] for desc in cur.description]
        row = cur.fetchone()
        if not row:
            logging.info("DB query returned 0 rows for id=%s", establishment_id)
        
        if row:
            data = dict(zip(col_names, row))
            # Lấy amenities từ bảng phụ (ElementCollection của JPA)
            amenities_raw: List[Any] = []
            try:
                # Thử tên bảng/column phổ biến do JPA sinh ra
                cur.execute("""
                    SELECT amenities_list FROM establishment_amenities_list WHERE establishment_id = %s
                """, (establishment_id,))
                rows = cur.fetchall()
                amenities_raw = [r[0] for r in rows]
            except Exception:
                try:
                    cur.execute("""
                        SELECT element FROM establishment_amenities_list WHERE establishment_id = %s
                    """, (establishment_id,))
                    rows = cur.fetchall()
                    amenities_raw = [r[0] for r in rows]
                except Exception:
                    logger.info("Amenities table not found with default names; skip amenities fetch")

            # Lọc None/empty và ép về string để tránh lỗi join
            amenities: List[str] = [str(x).strip() for x in amenities_raw if x is not None and str(x).strip()]
            data['amenities_list'] = ", ".join(amenities) if amenities else ''
            
        return data
    except Exception as error:
        logging.error("DB error in fetch_single_establishment: %s", error)
        return None
    finally:
        if conn is not None:
            conn.close()

# --- API 1: Conditional Quiz Generation (Sử dụng LLM Suy luận) ---
@app.post("/generate-quiz", response_model=QuizResponseModel)
async def generate_quiz(req: QuizRequest):
    # Fallback nếu LLM chưa sẵn sàng: logic quyết định tối thiểu, KHÔNG trả 503
    if not llm:
        final_params = dict(req.current_params or {})
        # Heuristic nhỏ: nếu prompt chứa từ khóa, suy luận nhẹ
        prompt_lc = (req.user_prompt or "").lower()
        if "lãng mạn" in prompt_lc and not final_params.get("style_vibe"):
            final_params["style_vibe"] = "romantic"
        missing = next((k for k in PARAM_ORDER if not final_params.get(k)), None)
        if missing:
            return {
                "quiz_completed": False,
                "missing_quiz": FALLBACK_QUESTIONS.get(missing, f"Vui lòng cung cấp '{missing}'"),
                "key_to_collect": missing,
                "final_params": final_params,
                "options": FALLBACK_OPTIONS.get(missing)
            }
        return {
            "quiz_completed": True,
            "missing_quiz": None,
            "key_to_collect": None,
            "final_params": final_params
        }

    # Sử dụng LangChain JsonOutputParser
    parser = JsonOutputParser(pydantic_object=QuizResponseModel)

    # Prompt cho LLM (tránh chèn trực tiếp JSON/Schema vào template để không bị bắt nhầm biến)
    template = """
    Bạn là trợ lý AI đặt chỗ. Nhiệm vụ của bạn là thu thập 7 tham số sau: {param_order}.
    
    Quy tắc:
    1. Phân tích 'user_prompt' và 'current_params' để suy luận và cập nhật các tham số có thể.
    2. Sau khi cập nhật, kiểm tra xem còn thiếu tham số nào KHÔNG?
    3. Nếu TẤT CẢ số tham số đã đầy đủ, đặt 'quiz_completed': true và trả về 'final_params'.
    4. Nếu còn thiếu, xác định tham số còn thiếu ƯU TIÊN nhất (theo thứ tự: {param_order}).
    5. Đặt 'quiz_completed': false, 'key_to_collect': tham số thiếu đó, và tạo 'missing_quiz': MỘT câu hỏi ngắn gọn.
    6. Đảm bảo 'max_price' là số nguyên (VND); 'duration' là số nguyên (ngày).
    
    Tham số hiện tại: {current_params}
    Yêu cầu mới nhất của người dùng: "{user_prompt}"
    
    Định dạng đầu ra phải là JSON.
    JSON SCHEMA: {format_instructions}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Bạn là một AI phân tích ngôn ngữ tự nhiên và chuyển đổi ý định người dùng thành các tham số đặt chỗ. Chỉ trả lời bằng JSON."),
        ("human", template)
    ])
    chain = prompt | llm | parser

    try:
        result = chain.invoke({
            "param_order": ", ".join(PARAM_ORDER),
            "current_params": json.dumps(req.current_params, ensure_ascii=False),
            "user_prompt": req.user_prompt,
            "format_instructions": parser.get_format_instructions()
        })

        if not result.get('quiz_completed'):
            for key in PARAM_ORDER:
                if not result.get('final_params', {}).get(key):
                    result['key_to_collect'] = key
                    if not result.get('missing_quiz'):
                        result['missing_quiz'] = FALLBACK_QUESTIONS.get(key)
                    result['options'] = FALLBACK_OPTIONS.get(key)
                    break

        return result
    except Exception as e:
        logging.error(f"LỖI GỌI LLM/Parser: {e}")
        # Cuối cùng vẫn có fallback để không chặn luồng FE
        final_params = dict(req.current_params or {})
        missing = next((k for k in PARAM_ORDER if not final_params.get(k)), None)
        if missing:
            return {
                "quiz_completed": False,
                "missing_quiz": FALLBACK_QUESTIONS.get(missing),
                "key_to_collect": missing,
                "final_params": final_params,
                "options": FALLBACK_OPTIONS.get(missing)
            }
        return {
            "quiz_completed": True,
            "missing_quiz": None,
            "key_to_collect": None,
            "final_params": final_params
        }


# --- API 2: RAG Search ---
@app.post("/rag-search", response_model=List[SearchResult])
async def rag_search(req: SearchRequest):
    if not vectorstore:
        return []

    # Lấy các tham số đã thu thập
    style = req.params.get("style_vibe", "phù hợp")
    companion = req.params.get("travel_companion", "tôi")
    city = req.params.get("city")  # có thể None
    amenities = req.params.get("amenities_priority", "tiện ích cơ bản")

    # Tạo Query mô tả chi tiết
    city_text = city or "địa điểm bất kỳ"
    query_text = (
        f"Tìm kiếm cơ sở ở {city_text} với phong cách {style}. "
        f"Cần tiện nghi phù hợp cho {companion} và ưu tiên các tiện ích: {amenities}. "
        f"Mô tả không gian và trải nghiệm."
    )

    # Áp dụng filter theo city nếu có để tăng độ chính xác
    search_kwargs = {"k": 10}
    if city:
        search_kwargs["filter"] = {"city": city}

    results = vectorstore.similarity_search_with_score(query=query_text, **search_kwargs)
    
    suggestions = []
    for doc, score in results:
        # Lấy ID và Score để Spring Boot lọc tiếp
        suggestions.append(SearchResult(establishment_id=doc.metadata.get('id'), relevance_score=score))
            
    return suggestions

# --- API 3: Cập nhật Vector Store ---
@app.post("/add-establishment")
async def add_establishment(req: AddEstablishmentRequest):
    # 0. Kiểm tra readiness của Vector Store
    logger.info("/add-establishment called with id=%s", req.id)
    if vectorstore is None or embeddings is None:
        raise HTTPException(status_code=503, detail="Vector Store chưa được khởi tạo (thiếu embeddings/API key).")

    # 1. Lấy dữ liệu mới nhất từ PostgreSQL
    new_data = fetch_single_establishment(req.id) 

    if not new_data:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu trong DB để cập nhật RAG.")

    # 2. Chuẩn hóa thành source_text
    city = new_data.get('city', '')
    amenities = new_data.get('amenities_list', '')
    source_text = (
        f"ID: {new_data['id']}, Tên: {new_data['name']}, Thành phố: {city}, Loại: {new_data['type']}, "
        f"Giá: {new_data.get('price_range_vnd')}, Sao: {new_data.get('star_rating')}. "
        f"Tiện ích: {amenities}. "
        f"Mô tả chi tiết: {new_data['description_long']}"
    )
    long_desc = (new_data.get('description_long') or '')
    logger.info("Fetched establishment name=%s, city=%s, len(description)=%s", new_data.get('name'), city, len(long_desc))
    logger.info("Description snippet: %s", long_desc[:300].replace("\n", " "))
    logger.info("Source_text snippet: %s", source_text[:300].replace("\n", " "))
    try:
        before = vectorstore._collection.count()  # type: ignore
    except Exception:
        before = None
    logger.info("Chroma count before add: %s", before)

    # 3. Tạo Embeddings và thêm vào Vector Store
    try:
        vectorstore.add_texts(
            texts=[source_text],
            metadatas=[new_data]
        )
        try:
            after = vectorstore._collection.count()  # type: ignore
            detail_after = vectorstore._collection.get(  # type: ignore
                where={"id": req.id},
                include=["documents","metadatas"]
            )
            logger.info("Chroma detail after add: %s", detail_after)
        except Exception:
            after = None
        logger.info("Added to Chroma: id=%s, count after=%s", req.id, after)
        return {"status": "success", "message": f"Đã thêm {new_data['name']} vào Vector Store (Gemini).", "chroma_count": after, "chroma_detail": detail_after }
    except Exception as e:
        logger.error("Error adding to ChromaDB: %s", getattr(e, 'message', str(e)))
        raise HTTPException(status_code=500, detail=f"Lỗi khi thêm vào ChromaDB: {e}")

# DEBUG: Truy vấn document đã lưu trong Chroma theo establishment id
@app.get("/debug/vector/{establishment_id}")
async def debug_vector(establishment_id: str):
    if vectorstore is None:
        raise HTTPException(status_code=503, detail="Vector Store chưa sẵn sàng")
    try:
        data = vectorstore._collection.get(  # type: ignore
            where={"id": establishment_id},
            include=["documents","metadatas"]
        )
        # Chuẩn hoá phản hồi gọn, chỉ trả về phần đầu document để xem nhanh
        docs = data.get("documents") or []
        metas = data.get("metadatas") or []
        preview = [ (d[:400] if isinstance(d,str) else d) for d in docs ]
        return {"found": len(docs), "documents_preview": preview, "metadatas": metas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug read error: {e}")

# DEBUG: Kiểm tra trực tiếp bản ghi trong Postgres theo id
@app.get("/debug/db/{establishment_id}")
async def debug_db(establishment_id: str):
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cur = conn.cursor()
        try:
            cur.execute("SET search_path TO public;")
        except Exception:
            pass
        cur.execute("SELECT COUNT(*) FROM establishment WHERE id = %s", (establishment_id,))
        cnt = cur.fetchone()[0]
        sample = None
        if cnt:
            cur.execute("SELECT id, name, city FROM establishment WHERE id = %s", (establishment_id,))
            r = cur.fetchone()
            sample = {"id": r[0], "name": r[1], "city": r[2]}
        return {"db_host": DB_CONFIG['host'], "db": DB_CONFIG['database'], "row_count": cnt, "sample": sample}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug DB error: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass



@app.get("/health")
async def health():
    ready = {
        "llm_initialized": llm is not None,
        "embeddings_initialized": embeddings is not None,
        "vectorstore_initialized": vectorstore is not None,
    }
    # Thử đếm số lượng bản ghi nếu có vectorstore
    try:
        count = None
        if vectorstore is not None:
            count = vectorstore._collection.count()  # type: ignore
        ready["chroma_count"] = count
    except Exception as e:
        ready["chroma_count_error"] = getattr(e, "message", str(e))
    return ready

# CHẠY SERVER (đúng module):
#   uvicorn ai_service_gemini:app --reload --port 8000