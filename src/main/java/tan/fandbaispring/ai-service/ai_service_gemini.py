# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
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

# Import utils and agent packages directly from local ai-service folder
try:
    from utils import (
        strip_accents, normalize_params, apply_defaults,
        infer_city_from_text, detect_brand_name
    )
    from agent import RAGAgent, AgentOrchestrator
    print("✅ Successfully imported utils and agent packages from ai-service")
except ImportError as e:
    print(f"Warning: Could not import utils/agent packages: {e}")
    print("Running without agent functionality...")
    
    # Fallback functions
    def strip_accents(text):
        return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8').lower()
    
    def normalize_params(params, user_prompt=""):
        return params or {}
    
    def apply_defaults(params):
        return params or {}
    
    def infer_city_from_text(text):
        return None
    
    def detect_brand_name(prompt, city, pgvector_service):
        return None
    
    # Mock agent classes
    class RAGAgent:
        def __init__(self, *args, **kwargs):
            pass
    
    class AgentOrchestrator:
        def __init__(self, *args, **kwargs):
            pass
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
db_host, db_port = "localhost", 5433 # PostgreSQL 18 port
if ":" in "localhost:5433":
    db_host, db_port_str = "localhost:5433".split(":")
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
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0, max_retries=0)
except Exception as e1:
    logging.warning("Primary model init failed (gemini-2.5-flash): %s", getattr(e1, "message", str(e1)))
    try:
        # Fallback phổ biến, ổn định hơn
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.0, max_retries=0)
    except Exception as e2:
        logging.error("Fallback model init failed (gemini-1.5-flash): %s", getattr(e2, "message", str(e2)))
        llm = None

try:
    embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
    pgvector_service = PgVectorService(DB_CONFIG)
except Exception as e:
    logging.warning("Vector store/embeddings init failed: %s", getattr(e, "message", str(e)))
    embeddings = None
    pgvector_service = None

# Khởi tạo Agent system
rag_agent = None
agent_orchestrator = None
if pgvector_service and embeddings:
    try:
        rag_agent = RAGAgent(pgvector_service, embeddings)
        agent_orchestrator = AgentOrchestrator(pgvector_service, embeddings)
        logging.info("Agent system initialized successfully")
    except Exception as e:
        logging.warning("Agent system init failed: %s", getattr(e, "message", str(e)))
        rag_agent = None
        agent_orchestrator = None


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
    options: Optional[List[str]] = Field(default=None, description="Các lựa chọn dạng text/tag cho câu hỏi hiện tại")


# Agent DTOs
class AgentChatRequest(BaseModel):
    message: str = Field(..., description="Tin nhắn từ user")
    session_id: str = Field(..., description="Session ID để quản lý conversation")
    user_profile: Optional[Dict[str, Any]] = Field(default=None, description="User profile và preferences")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context bổ sung")

class SearchResultResponse(BaseModel):
    establishment_id: str
    name: str
    relevance_score: float
    metadata: Dict[str, Any]
    explanation: str

class AgentChatResponse(BaseModel):
    success: bool
    results: List[SearchResultResponse]
    intent: str
    strategy_used: str
    explanation: str
    suggestions: List[str]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]

class AgentSearchRequest(BaseModel):
    query: str = Field(..., description="Query tìm kiếm")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context bổ sung")
    strategy: Optional[str] = Field(default=None, description="Strategy tìm kiếm (semantic, hybrid, contextual)")

class UserProfileRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences")
    budget_range: Optional[tuple] = Field(default=None, description="Budget range")
    preferred_cities: Optional[List[str]] = Field(default=None, description="Preferred cities")
    preferred_amenities: Optional[List[str]] = Field(default=None, description="Preferred amenities")
    travel_companion: Optional[str] = Field(default=None, description="Travel companion type")

# Danh sách tham số cốt lõi (dùng cho cả fallback)
PARAM_ORDER = [
    "establishment_type",  # HOTEL | RESTAURANT (suy luận từ prompt nếu có)
    "city", "check_in_date", "travel_companion", "duration",
    "max_price", "amenities_priority",
    "_amenities_confirmed"  # cờ xác nhận tiện ích (do FE gửi khi người dùng bấm Bỏ qua)
]

def effective_param_order(final_params: Dict[str, Any]) -> list[str]:
    try:
        est_type = (final_params or {}).get("establishment_type")
        order = list(PARAM_ORDER)
        if str(est_type).upper() == "RESTAURANT":
            # Nhà hàng: không hỏi số đêm
            order = [k for k in order if k != "duration"]
        return order
    except Exception:
        return list(PARAM_ORDER)

FALLBACK_QUESTIONS = {
    "establishment_type": "Bạn muốn tìm loại cơ sở nào?",
    "city": "Bạn muốn đi ở thành phố nào?",
    "check_in_date": "Ngày bạn muốn bắt đầu chuyến đi là khi nào?",
    "travel_companion": "Bạn sẽ đi cùng ai?",
    "duration": "Bạn muốn ở bao nhiêu đêm?",
    "max_price": "Ngân sách tối đa cho một đêm là bao nhiêu?",
    "amenities_priority": "Bạn ưu tiên tiện ích nào?"
}

# Gợi ý lựa chọn thông minh cho FE (multiple choice)
FALLBACK_OPTIONS = {
    "establishment_type": ["🏨 Khách sạn", "🍽️ Nhà hàng"],
    "city": ["🏖️ Đà Nẵng", "🏛️ Hà Nội", "🌆 TP.HCM", "🏔️ Đà Lạt", "🌊 Nha Trang", "🏛️ Huế"],
    "travel_companion": ["👤 Một mình", "👫 Cặp đôi", "👨‍👩‍👧‍👦 Gia đình", "👥 Bạn bè"],
    "duration": ["1 đêm", "2 đêm", "3 đêm", "4 đêm", "5 đêm", "1 tuần"],
    "max_price": ["💰 500K-1M", "💰 1M-2M", "💰 2M-3M", "💰 3M-5M", "💰 5M+"],
    "amenities_priority": ["🏊‍♂️ Hồ bơi", "🧘‍♀️ Spa", "🏃‍♂️ Gym", "🍽️ Nhà hàng", "🚗 Bãi đậu xe", "🏖️ Gần biển", "🍳 Buffet sáng"]
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
    name: str

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
    # Chỉ dùng LLM; nếu chưa sẵn sàng thì báo lỗi
    if not llm:
        raise HTTPException(status_code=503, detail="LLM chưa được khởi tạo")
    
    # Sử dụng LangChain JsonOutputParser
    parser = JsonOutputParser(pydantic_object=QuizResponseModel)

    # Prompt cho LLM (tránh chèn trực tiếp JSON/Schema vào template để không bị bắt nhầm biến)
    template = """
    Bạn là trợ lý AI đặt chỗ thông minh. Nhiệm vụ của bạn là thu thập thông tin đặt chỗ một cách tự nhiên và hiệu quả.
    
    QUY TẮC THU THẬP THÔNG TIN:
    1. Phân tích 'user_prompt' và 'current_params' để suy luận và cập nhật các tham số có thể.
    2. Ưu tiên thu thập theo thứ tự: {param_order}
    3. Tạo câu hỏi ngắn gọn, thân thiện và dễ hiểu
    4. Cung cấp options phù hợp để user dễ chọn
    5. Tránh hỏi lại thông tin đã có
    
    THÔNG MINH TRONG CÂU HỎI:
    - Nếu user nói "khách sạn" → establishment_type = "HOTEL"
    - Nếu user nói "nhà hàng" → establishment_type = "RESTAURANT"  
    - Nếu user nói "Đà Nẵng" → city = "Đà Nẵng"
    - Nếu user nói "cặp đôi" → travel_companion = "couple"
    - Nếu user nói "2 triệu" → max_price = 2000000
    
    XỬ LÝ ĐẶC BIỆT:
    - Nếu còn thiếu tham số: đặt quiz_completed = false, tạo câu hỏi cho tham số thiếu
    - Nếu đủ tham số: đặt quiz_completed = true, trả về final_params
    - Đảm bảo max_price là số nguyên (VND), duration là số nguyên (ngày)
    
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

        # Không xử lý hoặc chấp nhận bất kỳ khóa 'style' nào từ LLM

        # Tự quyết định thiếu gì dựa trên PARAM_ORDER
        ord2 = effective_param_order(result['final_params'])
        # Xác định thiếu thực sự (coi như có nếu không rỗng sau chuẩn hoá)
        missing_key_default = None
        for k in ord2:
            v = result['final_params'].get(k)
            if v is None:
                missing_key_default = k; break
            if isinstance(v, str) and not v.strip():
                missing_key_default = k; break
        # Cho phép hỏi THÊM tiện ích đúng một lần nếu đã có giá trị nhưng chưa xác nhận
        missing_key = missing_key_default
        try:
            fp = result.get('final_params') or {}
            has_amen = bool(fp.get('amenities_priority'))
            amen_confirmed = bool(fp.get('_amenities_confirmed'))
            if missing_key_default is None and has_amen and not amen_confirmed:
                missing_key = 'amenities_priority'
        except Exception:
            pass
        # Ưu tiên cho phép người dùng CHỌN THÊM tiện ích một lần nữa nếu chưa xác nhận
        try:
            fp = result.get('final_params') or {}
            has_amen = bool(fp.get('amenities_priority'))
            amenities_confirmed = bool(fp.get('_amenities_confirmed'))
            if has_amen and not amenities_confirmed:
                missing_key = 'amenities_priority'
        except Exception:
            pass
        # Nếu người dùng chỉ nêu city nhưng chưa rõ loại cơ sở -> ưu tiên hỏi establishment_type trước
        if missing_key == 'city' and result['final_params'].get('city') and not result['final_params'].get('establishment_type'):
            missing_key = 'establishment_type'
        if missing_key:
            result['quiz_completed'] = False
            result['key_to_collect'] = missing_key
            if missing_key == 'amenities_priority' and (result.get('final_params') or {}).get('amenities_priority'):
                result['missing_quiz'] = 'Bạn có muốn chọn thêm tiện ích không? (bạn có thể bỏ qua nếu đủ)'
            else:
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
        raise HTTPException(status_code=502, detail=f"Lỗi LLM hoặc Parser: {e}")


# --- API 2: RAG Search ---
@app.post("/rag-search", response_model=List[SearchResult])
async def rag_search(req: SearchRequest):
    if not pgvector_service or not embeddings:
        raise HTTPException(status_code=503, detail="Vector Store chưa được khởi tạo")
        
    # Lấy các tham số đã thu thập
    companion = req.params.get("travel_companion")
    city = req.params.get("city")  # có thể None
    amenities = req.params.get("amenities_priority", "tiện ích cơ bản")
    est_type = req.params.get("establishment_type") or req.params.get("type")
    check_in_date = req.params.get("check_in_date")
    check_out_date = req.params.get("check_out_date")
    duration = req.params.get("duration")
    
    # Tạo Query mô tả chi tiết
    city_text = city or "địa điểm bất kỳ"
    # Chuẩn hoá amenities: chấp nhận cả mảng hoặc chuỗi
    if isinstance(amenities, list):
        amenities_list = [str(a) for a in amenities if a is not None and str(a).strip()]
        amenities_text = ", ".join(amenities_list) if amenities_list else "tiện ích cơ bản"
    else:
        amenities_text = str(amenities) if amenities is not None else "tiện ích cơ bản"

    # Chỉ dùng city + amenities (+ type nếu có) cho truy vấn vector
    type_text = f" Loại: {str(est_type).upper()}." if est_type else ""
    query_text = (
        f"Tìm kiếm cơ sở ở {city_text}.{type_text} "
        f"Ưu tiên các tiện ích: {amenities_text}. "
        f"Mô tả không gian và trải nghiệm."
    )
    
    # Tạo embedding cho query text
    try:
        query_embedding = embeddings.embed_query(query_text)
        results = pgvector_service.similarity_search(
            query_embedding=query_embedding,
            limit=100
        )
    except Exception as e:
        logger.error(f"Lỗi khi tạo embedding cho query: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi tạo embedding")
    
    # Chuẩn hoá so sánh không dấu
    def strip_accents(s: Optional[str]) -> str:
        if not s:
            return ""
        return ''.join(c for c in unicodedata.normalize('NFD', str(s).strip()) if unicodedata.category(c) != 'Mn').lower()

    city_norm = strip_accents(city)
    # Chuẩn hoá tiện ích để so khớp: hỗ trợ mảng -> match bất kỳ tiện ích nào
    amen_norm_list: List[str] = []
    if isinstance(amenities, list):
        try:
            amen_norm_list = [strip_accents(a) for a in amenities if a is not None]
        except Exception:
            amen_norm_list = []
    else:
        amen_norm_single = strip_accents(amenities)
        if amen_norm_single:
            amen_norm_list = [amen_norm_single]

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
            if amen_norm_list:
                # match nếu BẤT KỲ tiện ích nào trong danh sách xuất hiện trong metadata
                if not any(an in am_list for an in amen_norm_list):
                    continue
        # Hậu kiểm type nếu có
        if est_type:
            try:
                meta_type = str(meta.get('type') or '').strip().upper()
                want_type = str(est_type).strip().upper()
                if not meta_type or meta_type != want_type:
                    continue
            except Exception:
                continue
        # Lấy điểm tốt hơn (similarity score cao hơn là tốt hơn)
        similarity_score = result.get('similarity_score', 0)
        prev = best_by_id.get(est_id)
        if prev is None or similarity_score > prev:
            best_by_id[est_id] = similarity_score
            metas_by_id[est_id] = meta

    suggestions = [SearchResult(establishment_id=eid, name=str((metas_by_id.get(eid) or {}).get('name') or '')) for eid in best_by_id.keys()]

    # Hậu kiểm thêm: lọc theo khả dụng dựa trên travel_companion (số khách) và ngày, nếu cung cấp
    def infer_num_guests(companion_val: Optional[str]) -> Optional[int]:
        if not companion_val:
            return None
        try:
            tc = str(companion_val).strip().lower()
            mapping = {"single": 1, "couple": 2, "family": 4, "friends": 3}
            return mapping.get(tc, int(float(tc)))
        except Exception:
            return None

    num_guests = infer_num_guests(companion)

    # Chuẩn hoá ngày nếu có
    start_dt = None
    end_dt = None
    try:
        if check_in_date:
            from datetime import datetime, timedelta
            start_dt = datetime.strptime(str(check_in_date), "%Y-%m-%d")
            if check_out_date:
                end_dt = datetime.strptime(str(check_out_date), "%Y-%m-%d")
            elif duration:
                try:
                    dur = int(str(duration))
                    end_dt = start_dt + timedelta(days=max(1, dur))
                except Exception:
                    end_dt = None
    except Exception:
        start_dt = None
        end_dt = None

    if num_guests is not None:
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

            def establishment_has_capacity(est_id: str) -> bool:
                # Cố gắng kiểm tra theo nhiều tên cột khả dĩ để tránh phụ thuộc schema cứng
                candidate_cols = [
                    "max_guests", "maxGuests", "capacity", "base_capacity", "baseCapacity"
                ]
                for col in candidate_cols:
                    try:
                        cur.execute(f"SELECT id FROM unit_type WHERE establishment_id = %s AND {col} >= %s LIMIT 1", (est_id, num_guests))
                        if cur.fetchone():
                            return True
                    except Exception:
                        continue
                # Nếu không dò được theo cột, coi như không lọc
                return True

            def establishment_has_availability(est_id: str) -> bool:
                if start_dt is None or end_dt is None:
                    return True
                # Thử các tên cột phổ biến
                date_col = "date"
                avail_col_candidates = ["available", "available_count", "available_units", "availableRooms"]
                try:
                    # Lấy các unit_type đủ sức chứa
                    cur.execute("SELECT id FROM unit_type WHERE establishment_id = %s", (est_id,))
                    unit_ids = [r[0] for r in cur.fetchall()]
                    if not unit_ids:
                        return False
                    for avail_col in avail_col_candidates:
                        try:
                            cur.execute(
                                f"SELECT COUNT(*) FROM unit_availability WHERE unit_type_id = ANY(%s) AND {date_col} >= %s AND {date_col} < %s AND {avail_col} > 0",
                                (unit_ids, start_dt, end_dt)
                            )
                            cnt = cur.fetchone()[0]
                            if cnt and cnt > 0:
                                return True
                        except Exception:
                            continue
                    # Nếu không query được cột nào, không chặn kết quả
                    return True
                except Exception:
                    return True

            filtered = []
            for s in suggestions:
                try:
                    if establishment_has_capacity(s.establishment_id) and establishment_has_availability(s.establishment_id):
                        filtered.append(s)
                except Exception:
                    filtered.append(s)
            suggestions = filtered
        except Exception:
            # Nếu lỗi DB, giữ nguyên danh sách
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # Không dùng fallback nới lỏng; trả đúng những gì VectorStore tìm thấy sau hậu kiểm
            
    # Trả về đúng 3 cơ sở điểm tốt nhất (score nhỏ hơn là tốt hơn)
    # Giữ nguyên thứ tự tốt nhất dựa trên score đã chọn trước đó; cắt còn 3
    suggestions = suggestions[:3]
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
            return {"status": "success", "message": f"Đã thêm {new_data['name']} vào Vector Store (Gemini).", "pgvector_count": after, "pgvector_detail": detail_after }
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
                "message": f"Đã xóa establishment {req.id} khỏi Vector Store (Gemini).",
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



# Agent endpoints
@app.post("/agent/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest):
    """Chat với Agent system"""
    if not agent_orchestrator:
        raise HTTPException(status_code=503, detail="Agent system not initialized")
    
    try:
        from agent.types import UserProfile
        
        # Convert user_profile to UserProfile object if provided
        user_profile = None
        if request.user_profile:
            user_profile = UserProfile(
                preferences=request.user_profile.get("preferences", {}),
                history=request.user_profile.get("history", []),
                budget_range=request.user_profile.get("budget_range"),
                preferred_cities=request.user_profile.get("preferred_cities", []),
                preferred_amenities=request.user_profile.get("preferred_amenities", []),
                travel_companion=request.user_profile.get("travel_companion")
            )
        
        # Process message with orchestrator
        response = agent_orchestrator.process_user_message(
            message=request.message,
            session_id=request.session_id,
            user_profile=user_profile,
            context=request.context
        )
        
        # Convert SearchResult objects to dicts
        results_data = []
        for result in response.results:
            results_data.append(SearchResultResponse(
                establishment_id=result.establishment_id,
                name=result.name,
                relevance_score=result.relevance_score,
                metadata=result.metadata,
                explanation=result.explanation
            ))
        
        return AgentChatResponse(
            success=response.success,
            results=results_data,
            intent=response.intent.value,
            strategy_used=response.strategy_used.value,
            explanation=response.explanation,
            suggestions=response.suggestions,
            confidence=response.confidence,
            processing_time=response.processing_time,
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"Error in agent chat: {e}")
        raise HTTPException(status_code=500, detail=f"Agent chat error: {str(e)}")

@app.post("/agent/search", response_model=AgentChatResponse)
async def agent_search(request: AgentSearchRequest):
    """Tìm kiếm trực tiếp với RAG Agent"""
    if not rag_agent:
        raise HTTPException(status_code=503, detail="RAG Agent not initialized")
    
    try:
        from agent.types import SearchStrategy
        
        # Determine strategy
        strategy = None
        if request.strategy:
            try:
                strategy = SearchStrategy(request.strategy.lower())
            except ValueError:
                strategy = None
        
        # Process query with RAG agent
        response = rag_agent.process_query(
            query=request.query,
            context=request.context,
            strategy=strategy
        )
        
        # Convert SearchResult objects to dicts
        results_data = []
        for result in response.results:
            results_data.append(SearchResultResponse(
                establishment_id=result.establishment_id,
                name=result.name,
                relevance_score=result.relevance_score,
                metadata=result.metadata,
                explanation=result.explanation
            ))
        
        return AgentChatResponse(
            success=response.success,
            results=results_data,
            intent=response.intent.value,
            strategy_used=response.strategy_used.value,
            explanation=response.explanation,
            suggestions=response.suggestions,
            confidence=response.confidence,
            processing_time=response.processing_time,
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"Error in agent search: {e}")
        raise HTTPException(status_code=500, detail=f"Agent search error: {str(e)}")

@app.post("/agent/profile")
async def update_user_profile(request: UserProfileRequest):
    """Cập nhật user profile"""
    if not agent_orchestrator:
        raise HTTPException(status_code=503, detail="Agent system not initialized")
    
    try:
        # Prepare profile updates
        profile_updates = {}
        if request.preferences is not None:
            profile_updates["preferences"] = request.preferences
        if request.budget_range is not None:
            profile_updates["budget_range"] = request.budget_range
        if request.preferred_cities is not None:
            profile_updates["preferred_cities"] = request.preferred_cities
        if request.preferred_amenities is not None:
            profile_updates["preferred_amenities"] = request.preferred_amenities
        if request.travel_companion is not None:
            profile_updates["travel_companion"] = request.travel_companion
        
        # Update profile
        success = agent_orchestrator.update_user_profile(
            session_id=request.session_id,
            profile_updates=profile_updates
        )
        
        return {"success": success, "message": "Profile updated successfully" if success else "Failed to update profile"}
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail=f"Profile update error: {str(e)}")

@app.get("/agent/stats")
async def get_agent_stats():
    """Lấy thống kê về Agent system"""
    stats = {}
    
    try:
        # RAG Agent stats
        if rag_agent:
            stats["rag_agent"] = rag_agent.get_stats()
        else:
            stats["rag_agent"] = {"error": "RAG Agent not initialized"}
        
        # Orchestrator stats
        if agent_orchestrator:
            stats["orchestrator"] = agent_orchestrator.get_session_stats()
        else:
            stats["orchestrator"] = {"error": "Agent Orchestrator not initialized"}
        
        # System status
        stats["system"] = {
            "rag_agent_initialized": rag_agent is not None,
            "orchestrator_initialized": agent_orchestrator is not None,
            "embeddings_initialized": embeddings is not None,
            "pgvector_initialized": pgvector_service is not None
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@app.get("/agent/conversation/{session_id}")
async def get_conversation_state(session_id: str):
    """Lấy trạng thái conversation"""
    if not agent_orchestrator:
        raise HTTPException(status_code=503, detail="Agent system not initialized")
    
    try:
        conversation = agent_orchestrator.get_conversation_state(session_id)
        
        if not conversation:
            return {"session_id": session_id, "exists": False}
        
        return {
            "session_id": session_id,
            "exists": True,
            "state": conversation.state.value,
            "current_query": conversation.current_query,
            "search_history_count": len(conversation.search_history),
            "user_profile": {
                "preferred_cities": conversation.user_profile.preferred_cities,
                "preferred_amenities": conversation.user_profile.preferred_amenities,
                "travel_companion": conversation.user_profile.travel_companion,
                "budget_range": conversation.user_profile.budget_range
            },
            "timestamp": conversation.timestamp
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation state: {e}")
        raise HTTPException(status_code=500, detail=f"Conversation state error: {str(e)}")

@app.delete("/agent/conversation/{session_id}")
async def end_conversation(session_id: str):
    """Kết thúc conversation"""
    if not agent_orchestrator:
        raise HTTPException(status_code=503, detail="Agent system not initialized")
    
    try:
        success = agent_orchestrator.end_conversation(session_id)
        return {"success": success, "message": "Conversation ended" if success else "Conversation not found"}
        
    except Exception as e:
        logger.error(f"Error ending conversation: {e}")
        raise HTTPException(status_code=500, detail=f"End conversation error: {str(e)}")

@app.get("/health")
async def health():
    ready = {
        "llm_initialized": llm is not None,
        "embeddings_initialized": embeddings is not None,
        "pgvector_initialized": pgvector_service is not None,
        "rag_agent_initialized": rag_agent is not None,
        "agent_orchestrator_initialized": agent_orchestrator is not None,
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
#   uvicorn ai_service_gemini:app --reload --port 8000