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
import unicodedata
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
    """Gợi ý ảnh từ dữ liệu thật trong Chroma metadata (ưu tiên theo city)."""
    try:
        if vectorstore is None:
            return None
        # Lấy 12 cơ sở ở city nếu có
        city = (final_params or {}).get("city")
        where = {"city": city} if city else None
        coll = vectorstore._collection  # type: ignore
        ids = coll.get(where=where, include=["metadatas", "documents"], limit=12)
        metas = ids.get("metadatas") or []
        options: List[ImageOption] = []
        for m in metas:
            if not isinstance(m, dict):
                continue
            name = m.get("name") or m.get("id")
            img = m.get("image_url_main") or m.get("imageUrlMain")
            if not img:
                continue
            label = f"{name}"
            # Suy ra style nhẹ theo mô tả nếu có
            params = None
            if param_key == "style_vibe":
                params = {"style_vibe": (final_params.get("style_vibe") or "romantic")}
            options.append(ImageOption(label=label, image_url=img, value=name, params=params))
        return options or None
    except Exception:
        return None


def detect_brand_name(mixed_text: str, city: Optional[str]) -> Optional[str]:
    try:
        if vectorstore is None:
            return None
        coll = vectorstore._collection  # type: ignore
        where = {"city": city} if city else None
        data = coll.get(where=where, include=["metadatas"], limit=50)
        metas = data.get("metadatas") or []
        text_lc = (mixed_text or "").lower()
        best = None
        for m in metas:
            if not isinstance(m, dict):
                continue
            nm = (m.get("name") or "").strip()
            if not nm:
                continue
            if nm.lower() in text_lc:
                best = nm
                break
        return best
    except Exception:
        return None


# --- City inference helpers ---
def strip_accents(s: Optional[str]) -> str:
    if not s:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(s).strip()) if unicodedata.category(c) != 'Mn').lower()

# canonical -> display
CITY_DISPLAY = {
    "danang": "Đà Nẵng",
    "hanoi": "Hà Nội",
    "hochiminh": "Hồ Chí Minh",
    "nhatrang": "Nha Trang",
    "dalat": "Đà Lạt",
    "hue": "Huế",
    "cantho": "Cần Thơ",
}

# aliases -> canonical
CITY_ALIASES = {
    "da nang": "danang",
    "danang": "danang",
    "dn": "danang",
    "ha noi": "hanoi",
    "hanoi": "hanoi",
    "ho chi minh": "hochiminh",
    "tp ho chi minh": "hochiminh",
    "tphcm": "hochiminh",
    "hcm": "hochiminh",
    "sai gon": "hochiminh",
    "saigon": "hochiminh",
    "nha trang": "nhatrang",
    "nhatrang": "nhatrang",
    "da lat": "dalat",
    "dalat": "dalat",
}

def infer_city_from_text(text: str) -> Optional[str]:
    t = strip_accents(text)
    # tìm alias dài trước để tránh va chạm
    for alias in sorted(CITY_ALIASES.keys(), key=len, reverse=True):
        if alias in t:
            canonical = CITY_ALIASES[alias]
            return CITY_DISPLAY.get(canonical, canonical)
    return None


def normalize_params(final_params: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
    """Chuẩn hóa: gộp style_vibe vào amenities_priority; tách brand name nếu phát hiện."""
    params = dict(final_params or {})
    city = params.get("city")
    mixed = f"{user_prompt} {params.get('amenities_priority','')} {params.get('style_vibe','')}"
    # Suy luận loại cơ sở từ prompt nếu có
    prompt_lc = (user_prompt or "").lower()
    if not params.get("establishment_type"):
        if any(k in prompt_lc for k in ["khach san","khách sạn","hotel"]):
            params["establishment_type"] = "HOTEL"
        elif any(k in prompt_lc for k in ["nha hang","nhà hàng","restaurant"]):
            params["establishment_type"] = "RESTAURANT"
    # Suy luận city nếu thiếu (accent-insensitive)
    if not params.get("city"):
        guessed = infer_city_from_text(user_prompt or "")
        if guessed:
            params["city"] = guessed
    brand = detect_brand_name(mixed, city)
    if brand:
        params["brand_name"] = brand
    # Gộp style_vibe vào amenities_priority
    try:
        style = str(params.get("style_vibe") or "").strip()
        if style:
            am = str(params.get("amenities_priority") or "").strip()
            if am:
                if style.lower() not in am.lower():
                    params["amenities_priority"] = f"{am}, {style}"
            else:
                params["amenities_priority"] = style
        # Loại bỏ style_vibe sau khi gộp để toàn hệ thống chỉ dùng amenities_priority
        if "style_vibe" in params:
            params.pop("style_vibe", None)
    except Exception:
        pass
    return params


def apply_defaults(params: Dict[str, Any]) -> Dict[str, Any]:
    """Bổ sung giá trị ngầm định; suy luận num_guests từ travel_companion hoặc số nhập tự do."""
    p = dict(params or {})
    # Suy luận num_guests từ travel_companion nếu chưa có
    if not p.get("num_guests") and p.get("travel_companion"):
        tc = str(p.get("travel_companion")).strip().lower()
        mapping = {"single": 1, "couple": 2, "family": 4, "friends": 3}
        try:
            p["num_guests"] = mapping.get(tc, int(float(tc)))
        except Exception:
            p["num_guests"] = mapping.get(tc)
    # Chuẩn hoá các giá trị khả dĩ của num_guests (single/couple -> số)
    if p.get("num_guests"):
        try:
            # Nếu là chuỗi đặc biệt, map sang số
            ng = str(p.get("num_guests")).strip().lower()
            mapping = {"single": 1, "couple": 2}
            if ng in mapping:
                p["num_guests"] = mapping[ng]
            else:
                p["num_guests"] = int(float(ng))
        except Exception:
            p["num_guests"] = 2  # mặc định an toàn
    return p


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
    
    # Truy vấn k lớn hơn; filter city sẽ được hậu kiểm để tránh lệch dấu/biến thể
    search_kwargs = {"k": 30}
    results = vectorstore.similarity_search_with_score(query=query_text, **search_kwargs)
    
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
    for doc, score in results:
        meta = doc.metadata or {}
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
        # Lấy điểm tốt hơn (score nhỏ hơn coi là tốt hơn)
        prev = best_by_id.get(est_id)
        if prev is None or score < prev:
            best_by_id[est_id] = score
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
    if city and amen_norm and vectorstore is not None:
        try:
            coll = vectorstore._collection  # type: ignore
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
                    data = coll.get(where={"city": cv}, include=["metadatas"], limit=200)
                except Exception:
                    continue
                metas = data.get('metadatas') or []
                for m in metas:
                    if not isinstance(m, dict):
                        continue
                    est_id = m.get('id')
                    if not est_id:
                        continue
                    am = strip_accents(m.get('amenities_list') or m.get('amenities'))
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

# --- API 4: Xóa khỏi Vector Store ---
@app.post("/remove-establishment")
async def remove_establishment(req: AddEstablishmentRequest):
    logger.info("/remove-establishment called with id=%s", req.id)
    if vectorstore is None:
        raise HTTPException(status_code=503, detail="Vector Store chưa được khởi tạo.")
    
    try:
        # Lấy thông tin trước khi xóa để log
        before_count = vectorstore._collection.count()  # type: ignore
        
        # Xóa document khỏi ChromaDB
        vectorstore._collection.delete(where={"id": req.id})  # type: ignore
        
        after_count = vectorstore._collection.count()  # type: ignore
        
        logger.info("Removed from Chroma: id=%s, count before=%s, count after=%s", 
                   req.id, before_count, after_count)
        
        return {
            "status": "success", 
            "message": f"Đã xóa establishment {req.id} khỏi Vector Store (Gemini).",
            "chroma_count_before": before_count,
            "chroma_count_after": after_count
        }
        
    except Exception as e:
        logger.error("Error removing from ChromaDB: %s", getattr(e, 'message', str(e)))
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa khỏi ChromaDB: {e}")

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