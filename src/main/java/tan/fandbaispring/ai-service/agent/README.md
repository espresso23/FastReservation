# Agent Package - Agentic RAG System

## Tổng quan

Package `agent` cung cấp hệ thống RAG thông minh với các agent chuyên biệt để xử lý các tác vụ tìm kiếm và gợi ý establishment một cách tự động và thông minh.

## Kiến trúc

```
agent/
├── __init__.py              # Package initialization
├── types.py                 # Data types và enums
├── query_analyzer.py        # Phân tích user query
├── retrieval_strategies.py  # Các chiến lược tìm kiếm
├── response_generator.py    # Tạo response thông minh
├── rag_agent.py            # Agent chính
├── agent_orchestrator.py   # Điều phối workflow
└── README.md               # Tài liệu này
```

## Các thành phần chính

### 1. RAGAgent (`rag_agent.py`)
Agent chính điều phối toàn bộ quá trình RAG:
- Phân tích query
- Lựa chọn strategy phù hợp
- Thực hiện retrieval
- Generate response

### 2. QueryAnalyzer (`query_analyzer.py`)
Phân tích và hiểu user query:
- Xác định intent (tìm kiếm, gợi ý, so sánh, đặt phòng...)
- Extract entities (thành phố, loại cơ sở, giá cả, amenities...)
- Tính confidence score
- Tạo suggestions

### 3. Retrieval Strategies (`retrieval_strategies.py`)
Các chiến lược tìm kiếm khác nhau:

#### SemanticRetrievalStrategy
- Tìm kiếm dựa trên semantic similarity thuần túy
- Phù hợp với query có intent rõ ràng và confidence cao

#### HybridRetrievalStrategy
- Kết hợp semantic và keyword matching
- Cân bằng giữa độ chính xác và coverage
- Chiến lược mặc định

#### ContextualRetrievalStrategy
- Tìm kiếm dựa trên conversation history
- Phù hợp với gợi ý và recommendation

### 4. ResponseGenerator (`response_generator.py`)
Tạo response thông minh từ search results:
- Response templates cho từng intent
- Tính toán confidence score
- Generate suggestions phù hợp
- Format output đẹp và dễ hiểu

### 5. AgentOrchestrator (`agent_orchestrator.py`)
Điều phối workflow của conversation:
- Quản lý conversation state
- User profile management
- Session management
- State transition logic

## Cách sử dụng

### Khởi tạo

```python
from agent import RAGAgent, AgentOrchestrator
from pgvector_service import PgVectorService

# Khởi tạo services
pgvector_service = PgVectorService(db_config)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Khởi tạo RAG Agent
rag_agent = RAGAgent(pgvector_service, embeddings)

# Hoặc sử dụng Orchestrator cho conversation management
orchestrator = AgentOrchestrator(pgvector_service, embeddings)
```

### Xử lý query đơn giản

```python
# Sử dụng RAG Agent trực tiếp
response = rag_agent.process_query(
    query="Tìm khách sạn ở Đà Nẵng với hồ bơi",
    context={
        "max_results": 5,
        "similarity_threshold": 0.7
    }
)

print(response.explanation)
print(f"Confidence: {response.confidence}")
```

### Xử lý conversation

```python
# Sử dụng Orchestrator cho conversation management
response = orchestrator.process_user_message(
    message="Tôi muốn tìm khách sạn ở Đà Nẵng",
    session_id="user123",
    user_profile=user_profile
)

# Tiếp tục conversation
response2 = orchestrator.process_user_message(
    message="Có hồ bơi không?",
    session_id="user123"
)
```

### Tích hợp với API endpoints

```python
@app.post("/agent/chat")
async def agent_chat(request: ChatRequest):
    response = orchestrator.process_user_message(
        message=request.message,
        session_id=request.session_id,
        user_profile=request.user_profile
    )
    
    return {
        "response": response.explanation,
        "results": [r.__dict__ for r in response.results],
        "suggestions": response.suggestions,
        "confidence": response.confidence
    }
```

## Query Intent Types

- `SEARCH_ESTABLISHMENTS`: Tìm kiếm cơ sở
- `GET_RECOMMENDATIONS`: Gợi ý
- `COMPARE_ESTABLISHMENTS`: So sánh
- `GET_DETAILS`: Lấy thông tin chi tiết
- `BOOKING_INQUIRY`: Hỏi về đặt phòng
- `PRICE_INQUIRY`: Hỏi về giá
- `AVAILABILITY_CHECK`: Kiểm tra phòng trống

## Search Strategies

- `SEMANTIC`: Semantic similarity thuần túy
- `HYBRID`: Kết hợp semantic + keyword
- `CONTEXTUAL`: Dựa trên conversation context

## Conversation States

- `INITIAL`: Bắt đầu conversation
- `COLLECTING_PREFERENCES`: Thu thập sở thích
- `SEARCHING`: Đang tìm kiếm
- `REFINING`: Tinh chỉnh kết quả
- `CONFIRMING`: Xác nhận đặt phòng
- `COMPLETED`: Hoàn thành

## Tùy chỉnh và mở rộng

### Thêm retrieval strategy mới

```python
class CustomRetrievalStrategy(BaseRetrievalStrategy):
    def retrieve(self, context: RetrievalContext) -> List[SearchResult]:
        # Implement custom logic
        pass

# Đăng ký strategy
rag_agent.retrieval_strategies[SearchStrategy.CUSTOM] = CustomRetrievalStrategy(pgvector_service, embeddings)
```

### Tùy chỉnh response template

```python
# Override method trong ResponseGenerator
def _generate_custom_response(self, results, context):
    return {
        "explanation": "Custom response",
        "metadata": {}
    }

response_generator.response_templates[QueryIntent.CUSTOM] = _generate_custom_response
```

## Lợi ích của Agentic RAG

1. **Thông minh hơn**: Hiểu được intent và context của user
2. **Linh hoạt**: Nhiều chiến lược tìm kiếm khác nhau
3. **Tương tác**: Conversation management và state tracking
4. **Tùy chỉnh**: Dễ dàng mở rộng và tùy chỉnh
5. **Hiệu quả**: Tự động lựa chọn strategy phù hợp

## Monitoring và Debug

```python
# Lấy thống kê
stats = rag_agent.get_stats()
print(f"Total establishments: {stats['total_establishments']}")

# Lấy conversation state
conversation = orchestrator.get_conversation_state("user123")
print(f"Current state: {conversation.state}")

# Lấy session stats
session_stats = orchestrator.get_session_stats()
print(f"Active sessions: {session_stats['active_sessions']}")
```

## Best Practices

1. **Sử dụng Orchestrator** cho applications có conversation flow
2. **Tùy chỉnh similarity threshold** dựa trên use case
3. **Monitor confidence scores** để cải thiện accuracy
4. **Sử dụng conversation history** để cải thiện context
5. **Implement feedback loop** để refine search results
