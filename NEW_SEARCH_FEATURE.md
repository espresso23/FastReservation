# Tính năng Tìm kiếm Mới - AI Booking Assistant

## 🎯 Vấn đề đã giải quyết

Trước đây, sau khi AI đưa ra kết quả booking, nếu user muốn tìm kiếm ở thành phố khác (ví dụ "tôi muốn đi hà nội"), hệ thống vẫn tiếp tục với cuộc trò chuyện cũ thay vì bắt đầu lại từ đầu.

## ✅ Giải pháp đã triển khai

### 1. **Auto Reset khi nhập yêu cầu mới**
- Khi user nhập yêu cầu mới sau khi quiz đã hoàn thành
- Hệ thống tự động reset tất cả state
- Bắt đầu lại từ đầu với yêu cầu mới

### 2. **Nút "Tìm kiếm mới"**
- Nút màu cam xuất hiện sau khi quiz hoàn thành
- Click để reset và bắt đầu tìm kiếm mới
- Thông báo rõ ràng cho user

### 3. **Thông báo thân thiện**
- AI thông báo: "Tôi hiểu bạn muốn tìm kiếm mới. Hãy để tôi hỗ trợ bạn!"
- Input field được clear sau khi reset
- Chat history được giữ lại để theo dõi

## 🔧 Cách hoạt động

### **Kịch bản 1: User nhập yêu cầu mới**
```
1. User: "Tôi muốn đi Đà Nẵng ngày 2025-10-10 2 đêm"
2. AI: [Quiz và đưa ra kết quả]
3. User: "Tôi muốn đi Hà Nội"
4. AI: "Tôi hiểu bạn muốn tìm kiếm mới. Hãy để tôi hỗ trợ bạn!"
5. AI: [Bắt đầu quiz mới cho Hà Nội]
```

### **Kịch bản 2: User click nút "Tìm kiếm mới"**
```
1. User: [Đã có kết quả booking]
2. User: [Click "Tìm kiếm mới"]
3. AI: "Tôi đã reset tìm kiếm. Hãy mô tả nhu cầu mới của bạn!"
4. User: "Tôi muốn đi Phú Quốc"
5. AI: [Bắt đầu quiz mới cho Phú Quốc]
```

## 📱 Giao diện người dùng

### **Sau khi quiz hoàn thành:**
```
┌─────────────────────────────────────┐
│ Tham số cuối                        │
│ [JSON parameters]                   │
│                                     │
│ [Thành phố] [Ngày] [Đêm] [Giá]     │
│                                     │
│ [Tìm gợi ý] [Tìm kiếm mới]         │
└─────────────────────────────────────┘
```

### **Khi user nhập yêu cầu mới:**
```
User: "Tôi muốn đi Hà Nội"
AI: "Tôi hiểu bạn muốn tìm kiếm mới. Hãy để tôi hỗ trợ bạn!"
AI: [Bắt đầu quiz mới]
```

## 🎯 Lợi ích

1. **Trải nghiệm mượt mà**: User không cần refresh trang
2. **Tự động reset**: Không cần thao tác thủ công
3. **Linh hoạt**: Có thể tìm kiếm nhiều lần liên tiếp
4. **Thông báo rõ ràng**: User biết hệ thống đã hiểu yêu cầu
5. **Giữ lịch sử**: Chat history được bảo toàn

## 🔍 Code Changes

### **File: `UserBookingPage.tsx`**

#### **1. Logic reset trong hàm `send`:**
```typescript
// Reset state if user is starting a new search (not auto-skip)
if (!override?.auto && pmt.trim() && quiz?.quiz_completed) {
  // User is starting a new search, reset everything
  setQuiz(null)
  setSuggestions(null)
  setCurrentParams({})
  setSelectedOpt('')
  setCustomOpt('')
  setSelectedAmenities([])
  setSelectedImages([])
  setMessages(prev => [...prev, 
    { role: 'user', text: pmt },
    { role: 'assistant', text: 'Tôi hiểu bạn muốn tìm kiếm mới. Hãy để tôi hỗ trợ bạn!' }
  ])
  setPrompt('') // Clear input field
  paramsToSend = {}
}
```

#### **2. Nút "Tìm kiếm mới":**
```typescript
<button 
  className="px-3 py-1 bg-orange-600 text-white rounded hover:bg-orange-700" 
  onClick={() => {
    setQuiz(null)
    setSuggestions(null)
    setCurrentParams({})
    setSelectedOpt('')
    setCustomOpt('')
    setSelectedAmenities([])
    setSelectedImages([])
    setMessages(prev => [...prev, { role: 'assistant', text: 'Tôi đã reset tìm kiếm. Hãy mô tả nhu cầu mới của bạn!' }])
  }}
>
  Tìm kiếm mới
</button>
```

## 🚀 Kết quả

- ✅ User có thể tìm kiếm nhiều lần liên tiếp
- ✅ Không cần refresh trang
- ✅ Trải nghiệm mượt mà và trực quan
- ✅ Thông báo rõ ràng cho user
- ✅ Giữ được lịch sử chat

Bây giờ AI Booking Assistant đã hoạt động như một chatbot thực sự, có thể xử lý nhiều yêu cầu tìm kiếm liên tiếp! 🎉
