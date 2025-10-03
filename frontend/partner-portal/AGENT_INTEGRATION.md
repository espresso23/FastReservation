# 🤖 Agentic RAG Integration với Frontend

## 📋 Tổng quan

Frontend `UserBookingPage.tsx` đã được cập nhật để tích hợp với hệ thống Agentic RAG, cho phép người dùng chọn giữa hai chế độ:

1. **📋 Chế độ Quiz**: Hỏi đáp từng bước truyền thống
2. **🤖 AI Thông minh**: Trò chuyện tự nhiên với Agent

## 🔄 Chế độ hoạt động

### 📋 Chế độ Quiz (Truyền thống)
- Hỏi từng tham số một cách có hệ thống
- Người dùng chọn từ các options được cung cấp
- Phù hợp cho người dùng muốn kiểm soát chi tiết

### 🤖 Chế độ AI Thông minh (Agent)
- Trò chuyện tự nhiên với AI
- AI tự động phân tích và tìm kiếm
- Hiển thị confidence score và explanation
- Phù hợp cho trải nghiệm nhanh chóng

## 🛠️ Tính năng mới

### 🔀 Mode Toggle
- Button chuyển đổi giữa hai chế độ
- Reset state khi chuyển mode
- Thông báo rõ ràng về chế độ hiện tại

### 🎯 Agent Integration
- Gọi API `/agent/chat` cho conversation
- Gọi API `/agent/search` cho tìm kiếm trực tiếp
- Xử lý lỗi và fallback tự động

### 📊 Enhanced UI
- Hiển thị relevance score
- Hiển thị explanation từ AI
- Placeholder text thông minh theo mode
- Timestamp cho messages

## 🔧 API Endpoints sử dụng

### Agent Chat
```typescript
POST http://localhost:8000/agent/chat
{
  "message": "Tôi muốn đi Đà Nẵng 2 đêm",
  "session_id": "session_123",
  "user_profile": {
    "preferences": {},
    "preferred_cities": ["Đà Nẵng"],
    "travel_companion": "couple"
  },
  "context": {}
}
```

### Agent Search
```typescript
POST http://localhost:8000/agent/search
{
  "query": "khách sạn Đà Nẵng có hồ bơi",
  "strategy": "semantic"
}
```

## 📱 User Experience

### 🤖 Agent Mode
1. Người dùng nhập yêu cầu tự nhiên
2. AI phân tích và tìm kiếm
3. Hiển thị kết quả với explanation
4. Có thể tiếp tục trò chuyện để refine

### 📋 Quiz Mode
1. AI hỏi từng tham số cụ thể
2. Người dùng chọn từ options
3. Tích lũy thông tin từng bước
4. Tìm kiếm khi đủ thông tin

## 🎨 UI Components

### Mode Toggle
```tsx
<div className="bg-gray-100 rounded-lg p-1 flex gap-1">
  <Button variant={agentMode === 'quiz' ? 'default' : 'ghost'}>
    📋 Chế độ Quiz
  </Button>
  <Button variant={agentMode === 'agent' ? 'default' : 'ghost'}>
    🤖 AI Thông minh
  </Button>
</div>
```

### Agent Info Display
```tsx
{agentMode === 'agent' && suggestions.length > 0 && (
  <Badge variant="outline">
    Độ phù hợp: {Math.round(relevanceScore * 100)}%
  </Badge>
)}
```

### Explanation Display
```tsx
{(s as any).explanation && agentMode === 'agent' && (
  <div className="text-xs text-gray-500 italic border-l-2 border-gray-200 pl-2">
    {(s as any).explanation}
  </div>
)}
```

## 🔄 State Management

### Agent State
```typescript
const [agentMode, setAgentMode] = useState<'quiz' | 'agent'>('quiz')
const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
const [userProfile, setUserProfile] = useState<AgentChatRequest['user_profile']>({
  preferences: {},
  history: [],
  preferred_cities: [],
  preferred_amenities: [],
  travel_companion: undefined
})
```

### Message State
```typescript
type ChatMessage = { 
  role: 'assistant' | 'user', 
  text: string, 
  timestamp?: Date 
}
```

## 🚀 Cách sử dụng

### 1. Khởi động AI Service
```bash
cd src/main/java/tan/fandbaispring/ai-service
python run_gemini.py
```

### 2. Khởi động Frontend
```bash
cd frontend/partner-portal
npm run dev
```

### 3. Truy cập trang
- Mở http://localhost:3000/user-booking
- Chọn chế độ phù hợp
- Bắt đầu trò chuyện với AI

## 🎯 Lợi ích

### 👥 Cho người dùng
- **Linh hoạt**: Chọn chế độ phù hợp
- **Nhanh chóng**: Agent mode cho kết quả nhanh
- **Chi tiết**: Quiz mode cho kiểm soát đầy đủ
- **Thông minh**: AI hiểu ngữ cảnh và học từ interaction

### 👨‍💻 Cho developer
- **Tương thích**: Hoạt động với cả quiz và agent
- **Mở rộng**: Dễ dàng thêm tính năng mới
- **Robust**: Xử lý lỗi và fallback tốt
- **Type-safe**: TypeScript với type definitions đầy đủ

## 🔮 Tương lai

### Tính năng có thể thêm
- Voice input/output
- Multi-language support
- Advanced filtering
- Recommendation history
- Social sharing
- Real-time availability updates

### Optimization
- Caching cho agent responses
- Lazy loading cho images
- Progressive enhancement
- Offline support
