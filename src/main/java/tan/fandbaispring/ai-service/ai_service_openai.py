from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import json
import os

# import psycopg2 # Cần nếu muốn Python tự query DB khi add-establishment
# (Chạy server này bằng: uvicorn ai_service:app --reload --port 8000)


app = FastAPI()

# Khởi tạo LLM và Vector Store (Giả định đã chạy data_initializer_from_db_openai.py)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)  # Hoặc dùng ChatGemini
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(
    collection_name="fast_planner_establishments",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)
print("✅ Python Service: LLM và Vector Store đã sẵn sàng.")


# --- DTOs ---
class QuizRequest(BaseModel):
    user_prompt: str
    current_params: dict


class QuizResponse(BaseModel):
    quiz_completed: bool
    missing_quiz: str = None
    key_to_collect: str = None
    final_params: dict = None


class SearchRequest(BaseModel):
    params: dict


class SearchResult(BaseModel):
    establishment_id: str
    relevance_score: float


class AddEstablishmentRequest(BaseModel):
    id: str  # Spring Boot gửi ID của Establishment mới


# --- API 1: Conditional Quiz Generation ---
@app.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(req: QuizRequest):
    required_params = {
        "check_in_date": "Ngày nhận phòng/đặt bàn", "duration": "Số đêm/Thời gian dự kiến",
        "max_price": "Ngân sách tối đa (Ví dụ: 3000000 VND)", "style": "Phong cách/Không gian (Luxury, Lãng mạn)"
    }
    missing_params = {key: desc for key, desc in required_params.items() if
                      key not in req.current_params or not req.current_params[key]}

    if not missing_params:
        return QuizResponse(quiz_completed=True, final_params=req.current_params)

    next_param_key = list(missing_params.keys())[0]

    system_prompt = f"""
    Bạn là trợ lý đặt chỗ. Các thông tin đã có: {json.dumps(req.current_params)}.
    Thông tin cần thu thập: '{missing_params[next_param_key]}'.
    Hãy đặt MỘT câu hỏi tương tác ngắn gọn, không thêm lời dẫn, để lấy thông tin đó.
    """
    response = llm.invoke(system_prompt).content

    return QuizResponse(
        quiz_completed=False, missing_quiz=response, key_to_collect=next_param_key
    )


# --- API 2: RAG Search ---
@app.post("/rag-search")
async def rag_search(req: SearchRequest):
    style = req.params.get("style", "tìm kiếm tổng quát")
    query_text = f"Tìm kiếm cơ sở ở Đà Nẵng có phong cách {style} phù hợp cho {req.params.get('duration', 'ngắn')}"

    results = vectorstore.similarity_search_with_score(query=query_text, k=5)

    suggestions = []
    for doc, score in results:
        suggestions.append(SearchResult(establishment_id=doc.metadata.get('id'), relevance_score=score).model_dump())

    return suggestions


# --- API 3: Cập nhật Vector Store khi Đối tác thêm mới ---
@app.post("/add-establishment")
async def add_establishment(req: AddEstablishmentRequest):
    # LƯU Ý: Triển khai logic truy vấn PostgreSQL ở đây
    # Giả định: Hàm fetch_single_establishment(req.id) trả về dict data của cơ sở mới
    # Dùng psycopg2 để SELECT * từ bảng 'establishment'

    # MÔ PHỎNG: Lấy data từ DB và tạo embedding
    new_data = {"id": req.id, "name": "Cơ sở mới", "price_range_vnd": 2000000,
                "description_long": "Mô tả của cơ sở mới thêm."}
    source_text = f"ID: {new_data['id']}, Tên: {new_data['name']}. Mô tả: {new_data['description_long']}"

    try:
        vectorstore.add_texts(
            texts=[source_text],
            metadatas=[new_data],
            embedding=embeddings
        )
        vectorstore.persist()
        return {"status": "success", "message": f"Đã thêm {new_data['name']} vào Vector Store."}
    except Exception as e:
        return {"status": "error", "message": f"Lỗi khi thêm vào ChromaDB: {e}"}