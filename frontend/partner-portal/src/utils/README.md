# 🛠️ Frontend Utilities

## 📋 Tổng quan

Các file utilities đã được tách ra từ `UserBookingPage.tsx` để tổ chức code tốt hơn và tái sử dụng dễ dàng.

## 📁 Cấu trúc thư mục

```
src/utils/
├── index.ts              # Export tất cả utilities
├── textProcessing.ts     # Xử lý text và parsing
├── agentApi.ts          # Agent API interactions
├── optionLabels.ts      # UI labels và options
├── validation.ts        # Validation functions
└── README.md           # Documentation này
```

## 🔧 Các modules

### 📝 `textProcessing.ts`

**Chức năng**: Xử lý text tiếng Việt và parsing parameters

**Exports chính**:
- `stripAccents()` - Loại bỏ dấu tiếng Việt
- `inferCityFromText()` - Suy luận thành phố từ text
- `inferEstablishmentType()` - Suy luận loại cơ sở
- `parsePriceFromText()` - Parse giá tiền
- `parseDateFromText()` - Parse ngày tháng
- `parseDurationFromText()` - Parse thời gian lưu trú
- `extractAmenitiesFromText()` - Trích xuất tiện ích
- `parseParametersFromPrompt()` - Parse tất cả parameters
- `humanizeParameterValue()` - Hiển thị giá trị thân thiện
- `getParameterLabel()` - Lấy label cho parameter

**Ví dụ sử dụng**:
```typescript
import { parseParametersFromPrompt, inferCityFromText } from '../utils'

const params = parseParametersFromPrompt('Tôi muốn đi Đà Nẵng 2 đêm, ngân sách 2 triệu')
// Output: { city: 'Đà Nẵng', duration: 2, max_price: 2000000 }

const city = inferCityFromText('Tôi muốn đi da nang')
// Output: 'Đà Nẵng'
```

### 🤖 `agentApi.ts`

**Chức năng**: Tương tác với Agent API và quản lý session

**Exports chính**:
- `callAgentChat()` - Gọi Agent Chat API
- `callAgentSearch()` - Gọi Agent Search API
- `convertAgentResultsToSuggestions()` - Chuyển đổi kết quả agent
- `checkAgentHealth()` - Kiểm tra agent health
- `getAgentStats()` - Lấy agent statistics
- `createSessionId()` - Tạo session ID
- `updateUserProfileFromAgent()` - Cập nhật user profile
- `buildAgentContext()` - Xây dựng context cho agent

**Types**:
- `AgentChatRequest`
- `AgentChatResponse`
- `SearchResultResponse`
- `AgentSearchRequest`
- `Suggestion`

**Ví dụ sử dụng**:
```typescript
import { callAgentChat, convertAgentResultsToSuggestions } from '../utils'

const response = await callAgentChat('Tôi muốn khách sạn Đà Nẵng', sessionId, userProfile, context)
const suggestions = convertAgentResultsToSuggestions(response.results)
```

### 🏷️ `optionLabels.ts`

**Chức năng**: Quản lý labels, options và UI helpers

**Exports chính**:
- `defaultOptions` - Các options mặc định
- `priceRangeOptions` - Các khoảng giá
- `getOptionLabel()` - Lấy label cho option
- `getEstablishmentTypeEmoji()` - Emoji cho loại cơ sở
- `getTravelCompanionEmoji()` - Emoji cho loại khách
- `getAmenityEmoji()` - Emoji cho tiện ích
- `formatPrice()` - Format giá tiền
- `getBudgetCategory()` - Phân loại ngân sách
- `getDurationCategory()` - Phân loại thời gian
- `getCityEmoji()` - Emoji cho thành phố
- `getRelevanceScoreColor()` - Màu cho relevance score
- `getRelevanceScoreLabel()` - Label cho relevance score

**Ví dụ sử dụng**:
```typescript
import { getOptionLabel, priceRangeOptions, getRelevanceScoreColor } from '../utils'

const label = getOptionLabel('establishment_type', 'HOTEL')
// Output: 'Khách sạn'

const priceOptions = priceRangeOptions
// Output: [{ label: '100k - 300k', value: 300000 }, ...]

const color = getRelevanceScoreColor(0.85)
// Output: 'text-green-600'
```

### ✅ `validation.ts`

**Chức năng**: Validation và sanitization

**Exports chính**:
- `isValidEmail()` - Validate email
- `isValidPhoneNumber()` - Validate số điện thoại VN
- `isValidDate()` - Validate ngày tháng
- `isFutureDate()` - Kiểm tra ngày tương lai
- `isValidDuration()` - Validate thời gian
- `isValidPrice()` - Validate giá tiền
- `isValidGuestCount()` - Validate số khách
- `isValidCity()` - Validate thành phố
- `isValidEstablishmentType()` - Validate loại cơ sở
- `isValidTravelCompanion()` - Validate loại khách
- `isValidAmenities()` - Validate tiện ích
- `isValidUserPrompt()` - Validate user prompt
- `validateBookingParams()` - Validate toàn bộ booking params
- `sanitizeInput()` - Sanitize user input
- `formatPhoneNumber()` - Format số điện thoại
- `isValidUrl()` - Validate URL
- `isValidImageUrl()` - Validate image URL

**Ví dụ sử dụng**:
```typescript
import { validateBookingParams, sanitizeInput } from '../utils'

const validation = validateBookingParams({
  city: 'Đà Nẵng',
  check_in_date: '2025-12-01',
  duration: 2,
  max_price: 2000000
})

if (!validation.isValid) {
  console.log('Errors:', validation.errors)
}

const cleanInput = sanitizeInput('<script>alert("xss")</script>Hello')
// Output: 'Hello'
```

### 📦 `index.ts`

**Chức năng**: Export tất cả utilities và types

**Exports**:
- Tất cả functions từ các modules trên
- Re-export các types quan trọng

**Ví dụ sử dụng**:
```typescript
import {
  parseParametersFromPrompt,
  callAgentChat,
  getOptionLabel,
  validateBookingParams
} from '../utils'
```

## 🎯 Lợi ích

### 👨‍💻 Cho Developer

**🔧 Tái sử dụng**: 
- Các functions có thể dùng ở nhiều component khác
- Không cần copy-paste code

**📚 Dễ bảo trì**:
- Code được tổ chức theo chức năng
- Dễ dàng tìm và sửa bugs
- Dễ dàng thêm tính năng mới

**🧪 Dễ test**:
- Các functions độc lập, dễ unit test
- Logic tách biệt khỏi UI

**📖 Dễ đọc**:
- `UserBookingPage.tsx` giờ ngắn gọn hơn
- Mỗi file có trách nhiệm rõ ràng

### 🎨 Cho UI/UX

**🎯 Consistency**:
- Labels và options thống nhất
- Validation rules đồng nhất
- Format hiển thị nhất quán

**⚡ Performance**:
- Code splitting tự nhiên
- Tree shaking hiệu quả
- Lazy loading dễ dàng

**🔄 Maintainability**:
- Thay đổi logic không ảnh hưởng UI
- Cập nhật API không ảnh hưởng parsing
- Thêm validation không ảnh hưởng hiển thị

## 🚀 Cách sử dụng

### 1. Import cần thiết

```typescript
import {
  parseParametersFromPrompt,
  callAgentChat,
  getOptionLabel,
  defaultOptions
} from '../utils'
```

### 2. Sử dụng trong component

```typescript
const MyComponent = () => {
  const [params, setParams] = useState({})
  
  const handleUserInput = (text: string) => {
    const parsed = parseParametersFromPrompt(text)
    setParams(prev => ({ ...prev, ...parsed }))
  }
  
  return (
    <div>
      {defaultOptions.establishment_type.map(type => (
        <Button key={type}>
          {getOptionLabel('establishment_type', type)}
        </Button>
      ))}
    </div>
  )
}
```

### 3. Extend utilities

```typescript
// Thêm function mới vào textProcessing.ts
export const parseCustomParam = (text: string): string | null => {
  // Implementation
}

// Hoặc tạo module mới
// src/utils/customProcessing.ts
export const myCustomFunction = () => {
  // Implementation
}
```

## 🔮 Roadmap

### Tính năng có thể thêm

**🌐 Internationalization**:
- `i18n.ts` - Đa ngôn ngữ
- `localeUtils.ts` - Xử lý locale

**📊 Analytics**:
- `analytics.ts` - Tracking events
- `metrics.ts` - Performance metrics

**🎨 Theme**:
- `themeUtils.ts` - Theme helpers
- `colorUtils.ts` - Color processing

**📱 Device**:
- `deviceUtils.ts` - Device detection
- `responsiveUtils.ts` - Responsive helpers

### Optimization

**⚡ Performance**:
- Memoization cho expensive functions
- Lazy loading cho heavy utilities
- Caching cho API calls

**🔒 Security**:
- Input sanitization nâng cao
- XSS protection
- CSRF protection

**🧪 Testing**:
- Unit tests cho tất cả functions
- Integration tests cho API calls
- E2E tests cho user flows

## 📝 Best Practices

### 1. Import chỉ cần thiết

```typescript
// ✅ Good
import { parseParametersFromPrompt } from '../utils'

// ❌ Bad
import * as utils from '../utils'
```

### 2. Sử dụng types

```typescript
// ✅ Good
import type { AgentChatRequest } from '../utils'

const request: AgentChatRequest = {
  message: 'Hello',
  session_id: '123'
}

// ❌ Bad
const request = {
  message: 'Hello',
  session_id: '123'
}
```

### 3. Error handling

```typescript
// ✅ Good
try {
  const response = await callAgentChat(message, sessionId)
  // Handle success
} catch (error) {
  console.error('Agent API error:', error)
  // Handle error
}

// ❌ Bad
const response = await callAgentChat(message, sessionId) // No error handling
```

### 4. Validation

```typescript
// ✅ Good
const validation = validateBookingParams(params)
if (!validation.isValid) {
  setErrors(validation.errors)
  return
}

// ❌ Bad
// Assume params are valid without validation
```

**🎉 Với cấu trúc utilities mới, code frontend trở nên sạch sẽ, dễ bảo trì và có thể tái sử dụng hiệu quả!**
