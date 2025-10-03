from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import os
import psycopg2 
from typing import Dict, Any, List, Optional
import logging
from dotenv import load_dotenv
import warnings
import unicodedata
from langchain_core._api import LangChainDeprecationWarning
from pgvector_service import PgVectorService
import sys
import os

# Import utils package directly from local ai-service folder
from utils import (
    strip_accents, normalize_params, apply_defaults,
    infer_city_from_text, detect_brand_name
)
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

# --- CẤU HÌNH ---
# Nạp biến môi trường từ file .env nếu có
load_dotenv()

# Cấu hình OpenAI API Key (nếu không có trong .env)
if not os.getenv("OPENAI_API_KEY"):
    # Thay thế bằng API key thực tế của bạn
    os.environ["OPENAI_API_KEY"] = "sk-your-openai-api-key-here"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

# *** CẤU HÌNH DB: Tách host và port để khớp với psycopg2 ***
db_host, db_port = "localhost", 5433 # PostgreSQL 18 port
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

# Khởi tạo LLM và Vector Store (có fallback)
llm = None
embeddings = None
pgvector_service = None
try:
    # Thử model mới (tắt retry để không bị chờ backoff khi hết quota)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, max_retries=0)
except Exception as e1:
    logging.warning("Primary model init failed (gpt-4o-mini): %s", getattr(e1, "message", str(e1)))
    try:
        # Fallback phổ biến, ổn định hơn
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0, max_retries=0)
    except Exception as e2:
        logging.error("Fallback model init failed (gpt-3.5-turbo): %s", getattr(e2, "message", str(e2)))
        llm = None

try:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    pgvector_service = PgVectorService(DB_CONFIG)
except Exception as e:
    logging.warning("Vector store/embeddings init failed: %s", getattr(e, "message", str(e)))
    embeddings = None
    pgvector_service = None


# --- DTOs (Pydantic Models) ---

class QuizRequest(BaseModel):
    # SỬA LỖI: Sử dụng alias để ánh xạ từ Java camelCase sang Python snake_case
    user_prompt: str = Field(..., alias="userPrompt")
    current_params: Dict[str, Any] = Field(..., alias="currentParams")

    class Config:
        # Cấu hình Pydantic để chấp nhận tên trường theo alias khi deserialize (input)
        populate_by_name = True


# Định nghĩa lại response model để phù hợp với Output Parser
class ImageOption(BaseModel):
    label: str
    image_url: str
    value: str
    params: Optional[Dict[str, Any]] = None


class QuizResponseModel(BaseModel):
    quiz_completed: bool = Field(description="True nếu tất cả 7 tham số cốt lõi đã có.")
    missing_quiz: Optional[str] = Field(None, description="Câu hỏi cần hỏi người dùng tiếp theo (Nếu quizCompleted là false).")
    key_to_collect: Optional[str] = Field(None, description="Tên tham số cần thu thập tiếp theo.")
    final_params: Dict[str, Any] = Field(description="Các tham số đã được cập nhật và chuẩn hóa.")
    image_options: Optional[List[ImageOption]] = Field(default=None, description="Các lựa chọn dạng thẻ ảnh cho câu hỏi hiện tại")

# Danh sách tham số cốt lõi (dùng cho cả fallback)
PARAM_ORDER = [
    "establishment_type",  # HOTEL | RESTAURANT (suy luận từ prompt nếu có)
    "city", "check_in_date", "travel_companion", "duration",
    "max_price", "amenities_priority"
]

FALLBACK_QUESTIONS = {
    "establishment_type": "Bạn muốn tìm Khách sạn (HOTEL) hay Nhà hàng (RESTAURANT)?",
    "city": "Bạn muốn đi ở thành phố nào?",
    "check_in_date": "Bạn dự định ngày bắt đầu chuyến đi là khi nào? (YYYY-MM-DD)",
    "travel_companion": "Bạn sẽ đi cùng ai? (single, couple, family, friends hoặc nhập số người)",
    "duration": "Thời lượng chuyến đi bao lâu? (số ngày)",
    "max_price": "Ngân sách tối đa của bạn là bao nhiêu (VND)?",
    "amenities_priority": "Bạn ưu tiên tiện ích nào? (ví dụ: hồ bơi, spa, bãi đậu xe)"
}

# Gợi ý lựa chọn cho FE (multiple choice)
FALLBACK_OPTIONS = {
    "establishment_type": ["HOTEL","RESTAURANT"],
    "travel_companion": ["single", "couple", "family", "friends"],
    "amenities_priority": ["Hồ bơi", "Spa", "Bãi đậu xe", "Gym", "Buffet sáng", "Gần biển"],
    "duration": ["1","2","3","4","5","6","7"],
    "has_balcony": ["yes","no"]
}


def image_options_from_real_data(param_key: str, final_params: Dict[str, Any]) -> Optional[List[ImageOption]]:
    """Gợi ý ảnh từ dữ liệu thật trong pgvector metadata (ưu tiên theo city)."""
    try:
        if pgvector_service is None:
            return None
        # Lấy 12 cơ sở ở city nếu có
        city = (final_params or {}).get("city")
        where_clause = "metadata->>'city' = %s" if city else None
        where_params = (city,) if city else None
        
        results = pgvector_service.similarity_search(
            query_embedding=[0.0] * 1536,  # Dummy embedding cho metadata search
            limit=12,
            where_clause=where_clause,
            where_params=where_params
        )
        
        options: List[ImageOption] = []
        for result in results:
            metadata = result.get("metadata", {})
            name = metadata.get("name") or metadata.get("id")
            img = metadata.get("image_url_main") or metadata.get("imageUrlMain")
            if not img:
                continue
            label = f"{name}"
            params = None
            options.append(ImageOption(label=label, image_url=img, value=name, params=params))
        return options or None
    except Exception:
        return None


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
        # Suy luận city và loại cơ sở từ prompt nếu thiếu
        if not final_params.get("city"):
            guessed_city = infer_city_from_text(req.user_prompt or "")
            if guessed_city:
                final_params["city"] = guessed_city
        if not final_params.get("establishment_type"):
            plc = (req.user_prompt or "").lower()
            if any(k in plc for k in ["khach san","khách sạn","hotel"]):
                final_params["establishment_type"] = "HOTEL"
            elif any(k in plc for k in ["nha hang","nhà hàng","restaurant"]):
                final_params["establishment_type"] = "RESTAURANT"
        # Heuristic nhỏ: nếu prompt chứa từ khóa, suy luận nhẹ
        prompt_lc = (req.user_prompt or "").lower()
        if "lãng mạn" in prompt_lc and not final_params.get("style_vibe"):
            final_params["style_vibe"] = "romantic"
        missing = next((k for k in PARAM_ORDER if not final_params.get(k)), None)
        if missing == 'amenities_priority':
            try:
                conn = psycopg2.connect(
                    host=DB_CONFIG['host'], port=DB_CONFIG['port'], database=DB_CONFIG['database'],
                    user=DB_CONFIG['user'], password=DB_CONFIG['password']
                )
                cur = conn.cursor()
                try:
                    cur.execute("SET search_path TO public;")
                except Exception:
                    pass
                where = []
                params = []
                if final_params.get('city'):
                    where.append("lower(city) = lower(%s)"); params.append(str(final_params['city']))
                if final_params.get('establishment_type'):
                    where.append("type = %s"); params.append(str(final_params['establishment_type']))
                sql = "SELECT id FROM establishment"
                if where:
                    sql += " WHERE " + " AND ".join(where)
                sql += " LIMIT 100"
                cur.execute(sql, tuple(params))
                ids = [r[0] for r in cur.fetchall()]
                amen = []
                if ids:
                    cur.execute("SELECT DISTINCT amenities_list FROM establishment_amenities_list WHERE establishment_id = ANY(%s)", (ids,))
                    amen = [str(r[0]).strip() for r in cur.fetchall() if r and r[0]]
                opts = sorted(list({a for a in amen if a}))
                if opts:
                    return {
                        "quiz_completed": False,
                        "missing_quiz": FALLBACK_QUESTIONS.get('amenities_priority', 'Bạn ưu tiên tiện ích nào?'),
                        "key_to_collect": 'amenities_priority',
                        "final_params": final_params,
                        "options": opts,
                        "image_options": None
                    }
            except Exception as _:
                pass
        if missing:
            # TẠM THỜI TẮT image_options → FE chỉ hiển thị TAGS/INPUT
            image_opts = None
            return {
                "quiz_completed": False,
                "missing_quiz": FALLBACK_QUESTIONS.get(missing, f"Vui lòng cung cấp '{missing}'"),
                "key_to_collect": missing,
                "final_params": final_params,
                "options": FALLBACK_OPTIONS.get(missing),
                "image_options": image_opts
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
        # Tiền xử lý: bổ sung city/type suy luận trước khi gửi vào LLM để tránh hỏi lại
        pre_params: Dict[str, Any] = dict(req.current_params or {})
        if not pre_params.get("city"):
            guessed_city = infer_city_from_text(req.user_prompt or "")
            if guessed_city:
                pre_params["city"] = guessed_city
        if not pre_params.get("establishment_type"):
            plc = (req.user_prompt or "").lower()
            if any(k in plc for k in ["khach san","khách sạn","hotel"]):
                pre_params["establishment_type"] = "HOTEL"
            elif any(k in plc for k in ["nha hang","nhà hàng","restaurant"]):
                pre_params["establishment_type"] = "RESTAURANT"

        result = chain.invoke({
            "param_order": ", ".join(PARAM_ORDER),
            "current_params": json.dumps(pre_params, ensure_ascii=False),
            "user_prompt": req.user_prompt,
            "format_instructions": parser.get_format_instructions()
        })

        # Chuẩn hóa + bổ sung mặc định để tránh hỏi lặp hoặc bất hợp lý
        # Gộp với pre_params để giữ các giá trị đã suy luận trước đó
        merged_after_llm = { **pre_params, **(result.get('final_params', {}) or {}) }
        normalized = normalize_params(merged_after_llm, req.user_prompt)
        normalized = apply_defaults(normalized)
        result['final_params'] = normalized

        # Tự quyết định thiếu gì dựa trên PARAM_ORDER (bỏ qua gợi ý của LLM như style_vibe)
        missing_key = next((k for k in PARAM_ORDER if not result['final_params'].get(k)), None)
        if missing_key == 'city' and result['final_params'].get('city') and not result['final_params'].get('establishment_type'):
            missing_key = 'establishment_type'
        if missing_key:
            result['quiz_completed'] = False
            result['key_to_collect'] = missing_key
            result['missing_quiz'] = FALLBACK_QUESTIONS.get(missing_key)
            result['options'] = FALLBACK_OPTIONS.get(missing_key)
            result['image_options'] = None
        else:
            result['quiz_completed'] = True
            result['key_to_collect'] = None
            result['missing_quiz'] = None
            result['options'] = None
            result['image_options'] = None
        
        return result
    except Exception as e:
        logging.error(f"LỖI GỌI LLM/Parser: {e}")
        # Cuối cùng vẫn có fallback để không chặn luồng FE
        final_params = dict(req.current_params or {})
        if not final_params.get("city"):
            guessed_city = infer_city_from_text(req.user_prompt or "")
            if guessed_city:
                final_params["city"] = guessed_city
        if not final_params.get("establishment_type"):
            plc = (req.user_prompt or "").lower()
            if any(k in plc for k in ["khach san","khách sạn","hotel"]):
                final_params["establishment_type"] = "HOTEL"
            elif any(k in plc for k in ["nha hang","nhà hàng","restaurant"]):
                final_params["establishment_type"] = "RESTAURANT"
        missing = next((k for k in PARAM_ORDER if not final_params.get(k)), None)
        if missing == 'city' and final_params.get('city') and not final_params.get('establishment_type'):
            missing = 'establishment_type'
        if missing:
            # TẮT image_options khi fallback
            image_opts = None
            return {
                "quiz_completed": False,
                "missing_quiz": FALLBACK_QUESTIONS.get(missing),
                "key_to_collect": missing,
                "final_params": final_params,
                "options": FALLBACK_OPTIONS.get(missing),
                "image_options": image_opts
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
    if not pgvector_service or not embeddings: 
        return []
        
    # Lấy các tham số đã thu thập
    companion = req.params.get("travel_companion", "tôi")
    city = req.params.get("city")  # có thể None
    amenities = req.params.get("amenities_priority", "tiện ích cơ bản")
    
    # Tạo Query mô tả chi tiết
    city_text = city or "địa điểm bất kỳ"
    query_text = (
        f"Tìm kiếm cơ sở ở {city_text}. "
        f"Cần tiện nghi phù hợp cho {companion} và ưu tiên các tiện ích: {amenities}. "
        f"Mô tả không gian và trải nghiệm."
    )
    
    # Tạo embedding cho query text
    try:
        query_embedding = embeddings.embed_query(query_text)
        results = pgvector_service.similarity_search(
            query_embedding=query_embedding,
            limit=30
        )
    except Exception as e:
        logger.error(f"Lỗi khi tạo embedding cho query: {e}")
        return []
    
    # Chuẩn hoá so sánh không dấu
    def strip_accents(s: Optional[str]) -> str:
        if not s:
            return ""
        return ''.join(c for c in unicodedata.normalize('NFD', str(s).strip()) if unicodedata.category(c) != 'Mn').lower()

    city_norm = strip_accents(city)
    amen_norm = strip_accents(amenities)

    # Khử trùng lặp theo establishment_id và hậu kiểm city/amenities
    best_by_id: Dict[str, float] = {}
    metas_by_id: Dict[str, Dict[str, Any]] = {}
    for result in results:
        meta = result.get('metadata', {})
        est_id = meta.get('id')
        if not est_id:
            continue
        # Hậu kiểm city (không dấu, không phân biệt hoa thường)
        if city_norm:
            meta_city = strip_accents(meta.get('city'))
            if meta_city != city_norm:
                continue
        # Hậu kiểm amenities nếu có
        if amenities:
            am_list = strip_accents(meta.get('amenities_list') or meta.get('amenities'))
            if amen_norm and amen_norm not in am_list:
                continue
        # Lấy điểm tốt hơn (similarity score cao hơn là tốt hơn)
        similarity_score = result.get('similarity_score', 0)
        prev = best_by_id.get(est_id)
        if prev is None or similarity_score > prev:
            best_by_id[est_id] = similarity_score
            metas_by_id[est_id] = meta

    suggestions = [SearchResult(establishment_id=eid, relevance_score=best_by_id[eid]) for eid in best_by_id.keys()]

    # Fallback: nếu sau hậu kiểm rỗng, nới lỏng điều kiện lần lượt
    if not suggestions:
        # 1) Bỏ lọc amenities nhưng giữ city
        best_by_id = {}
        for doc, score in results:
            meta = doc.metadata or {}
            est_id = meta.get('id')
            if not est_id:
                continue
            if city_norm and strip_accents(meta.get('city')) != city_norm:
                continue
            prev = best_by_id.get(est_id)
            if prev is None or score < prev:
                best_by_id[est_id] = score
        suggestions = [SearchResult(establishment_id=eid, relevance_score=best_by_id[eid]) for eid in best_by_id.keys()]

    if not suggestions:
        # 2) Bỏ tất cả hậu kiểm, trả top-N duy nhất
        seen = set()
        uniq = []
        for doc, score in results:
            est_id = (doc.metadata or {}).get('id')
            if not est_id or est_id in seen:
                continue
            seen.add(est_id)
            uniq.append(SearchResult(establishment_id=est_id, relevance_score=score))
            if len(uniq) >= 10:
                break
        suggestions = uniq

    # 3) Fallback bổ sung: nếu vẫn không có cơ sở ở đúng city chứa amenities, đọc trực tiếp metadata theo city (accent đúng)
    if city and amen_norm and pgvector_service is not None:
        try:
            # Thử cả city người dùng nhập và một số biến thể có dấu phổ biến
            city_variants = {city}
            if city_norm == 'da nang':
                city_variants.add('Đà Nẵng')
            if city_norm == 'ha noi':
                city_variants.add('Hà Nội')
            if city_norm in ('ho chi minh','tphcm','tp ho chi minh','sai gon'):
                city_variants.update({'Hồ Chí Minh','TP Hồ Chí Minh','TP. Hồ Chí Minh'})

            added = False
            for cv in city_variants:
                try:
                    results_fallback = pgvector_service.similarity_search(
                        query_embedding=[0.0] * 1536,  # Dummy embedding
                        limit=200,
                        where_clause="metadata->>'city' = %s",
                        where_params=(cv,)
                    )
                except Exception:
                    continue
                
                for result in results_fallback:
                    metadata = result.get('metadata', {})
                    est_id = metadata.get('id')
                    if not est_id:
                        continue
                    am = strip_accents(metadata.get('amenities_list') or metadata.get('amenities'))
                    if amen_norm in am:
                        # Thêm nếu chưa có trong suggestions
                        if all(s.establishment_id != est_id for s in suggestions):
                            suggestions.insert(0, SearchResult(establishment_id=est_id, relevance_score=0.25))
                            added = True
                if added:
                    break
        except Exception:
            pass
            
    return suggestions

# --- API 3: Cập nhật Vector Store ---
@app.post("/add-establishment")
async def add_establishment(req: AddEstablishmentRequest):
    # 0. Kiểm tra readiness của Vector Store
    logger.info("/add-establishment called with id=%s", req.id)
    if pgvector_service is None or embeddings is None:
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
        before = pgvector_service.get_embedding_count()
    except Exception:
        before = None
    logger.info("PgVector count before add: %s", before)

    # 3. Tạo Embeddings và thêm vào Vector Store
    try:
        # Tạo embedding cho content
        embedding = embeddings.embed_query(source_text)
        
        # Thêm vào pgvector
        success = pgvector_service.add_embedding(
            establishment_id=req.id,
            content=source_text,
            metadata=new_data,
            embedding=embedding
        )
        
        if success:
            try:
                after = pgvector_service.get_embedding_count()
                detail_after = pgvector_service.get_embedding_by_id(req.id)
                logger.info("PgVector detail after add: %s", detail_after)
            except Exception:
                after = None
                detail_after = None
            logger.info("Added to PgVector: id=%s, count after=%s", req.id, after)
            return {"status": "success", "message": f"Đã thêm {new_data['name']} vào Vector Store (OpenAI).", "pgvector_count": after, "pgvector_detail": detail_after }
        else:
            raise Exception("Failed to add embedding to PgVector")
            
    except Exception as e:
        logger.error("Error adding to PgVector: %s", getattr(e, 'message', str(e)))
        raise HTTPException(status_code=500, detail=f"Lỗi khi thêm vào PgVector: {e}")

# --- API 4: Xóa khỏi Vector Store ---
@app.post("/remove-establishment")
async def remove_establishment(req: AddEstablishmentRequest):
    logger.info("/remove-establishment called with id=%s", req.id)
    if pgvector_service is None:
        raise HTTPException(status_code=503, detail="Vector Store chưa được khởi tạo.")
    
    try:
        # Lấy thông tin trước khi xóa để log
        before_count = pgvector_service.get_embedding_count()
        
        # Xóa document khỏi PgVector
        success = pgvector_service.remove_embedding(req.id)
        
        if success:
            after_count = pgvector_service.get_embedding_count()
            
            logger.info("Removed from PgVector: id=%s, count before=%s, count after=%s", 
                       req.id, before_count, after_count)
            
            return {
                "status": "success", 
                "message": f"Đã xóa establishment {req.id} khỏi Vector Store (OpenAI).",
                "pgvector_count_before": before_count,
                "pgvector_count_after": after_count
            }
        else:
            raise Exception("Failed to remove embedding from PgVector")
        
    except Exception as e:
        logger.error("Error removing from PgVector: %s", getattr(e, 'message', str(e)))
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa khỏi PgVector: {e}")

# DEBUG: Truy vấn document đã lưu trong PgVector theo establishment id
@app.get("/debug/vector/{establishment_id}")
async def debug_vector(establishment_id: str):
    if pgvector_service is None:
        raise HTTPException(status_code=503, detail="Vector Store chưa sẵn sàng")
    try:
        data = pgvector_service.get_embedding_by_id(establishment_id)
        if data:
            content_preview = data.get('content', '')[:400] if data.get('content') else ''
            return {
                "found": 1, 
                "content_preview": content_preview, 
                "metadata": data.get('metadata', {}),
                "created_at": data.get('created_at'),
                "updated_at": data.get('updated_at')
            }
        else:
            return {"found": 0, "content_preview": "", "metadata": {}}
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
        "pgvector_initialized": pgvector_service is not None,
    }
    # Thử đếm số lượng bản ghi nếu có pgvector_service
    try:
        count = None
        if pgvector_service is not None:
            count = pgvector_service.get_embedding_count()
        ready["pgvector_count"] = count
    except Exception as e:
        ready["pgvector_count_error"] = getattr(e, "message", str(e))
    return ready

# CHẠY SERVER (đúng module):
#   uvicorn ai_service_openai:app --reload --port 8000