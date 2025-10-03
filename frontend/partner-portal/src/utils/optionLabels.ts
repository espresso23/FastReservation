/**
 * Option labels and default options for UI components
 */

/**
 * Default options for different parameter types
 */
export const defaultOptions: Record<string, string[]> = {
  establishment_type: ['HOTEL', 'RESTAURANT'],
  travel_companion: ['single', 'couple', 'family', 'friends', 'team', 'business'],
  amenities_priority: [
    'Hồ bơi', 'Spa', 'Bãi đậu xe', 'Gym', 'Buffet sáng', 'Gần biển', 'Wifi', 'Lễ tân 24/7', 'Đưa đón sân bay',
    'Pet-friendly', 'Phòng gia đình', 'Không hút thuốc', 'Bồn tắm', 'View biển', 'View thành phố', 'Gần trung tâm',
    'Ban công', 'Cửa sổ', 'Giặt là', 'Thang máy', 'Romantic', 'Quiet', 'Lively', 'Luxury', 'Nature', 'Cozy', 'Modern', 'Classic'
  ],
  duration: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
  has_balcony: ['yes', 'no'],
  num_guests: ['single', 'couple', '3', '4', '5', '6', '7', '8', '9', '10']
}

/**
 * Price range options for quick selection
 */
export const priceRangeOptions = [
  { label: '100k - 300k', value: 300000 },
  { label: '500k - 1 triệu', value: 1000000 },
  { label: '1 - 2 triệu', value: 2000000 },
  { label: '2 - 3 triệu', value: 3000000 },
  { label: '3 - 5 triệu', value: 5000000 },
  { label: '5 triệu+', value: 10000000 }
]

/**
 * Get human-readable label for option value
 */
export const getOptionLabel = (key: string, value: string): string => {
  if (key === 'establishment_type') {
    if (value.toUpperCase() === 'HOTEL') return 'Khách sạn'
    if (value.toUpperCase() === 'RESTAURANT') return 'Nhà hàng'
  }
  
  if (key === 'travel_companion') {
    const m: Record<string, string> = { 
      single: 'Một mình', 
      couple: 'Cặp đôi', 
      family: 'Gia đình', 
      friends: 'Bạn bè',
      team: 'Nhóm',
      business: 'Công tác'
    }
    return m[value.toLowerCase()] || value
  }
  
  if (key === 'has_balcony') {
    if ((value || '').toLowerCase() === 'yes') return 'Có'
    if ((value || '').toLowerCase() === 'no') return 'Không'
  }
  
  return value
}

/**
 * Get emoji for establishment type
 */
export const getEstablishmentTypeEmoji = (type: string): string => {
  switch (type?.toUpperCase()) {
    case 'HOTEL': return '🏨'
    case 'RESTAURANT': return '🍽️'
    default: return '🏢'
  }
}

/**
 * Get emoji for travel companion
 */
export const getTravelCompanionEmoji = (companion: string): string => {
  switch (companion?.toLowerCase()) {
    case 'single': return '👤'
    case 'couple': return '👫'
    case 'family': return '👨‍👩‍👧‍👦'
    case 'friends': return '👥'
    case 'team': return '👨‍👨‍👦‍👦'
    case 'business': return '💼'
    default: return '👥'
  }
}

/**
 * Get emoji for amenity
 */
export const getAmenityEmoji = (amenity: string): string => {
  const amenityMap: Record<string, string> = {
    'Hồ bơi': '🏊‍♂️',
    'Spa': '🧘‍♀️',
    'Bãi đậu xe': '🚗',
    'Gym': '🏃‍♂️',
    'Buffet sáng': '🍳',
    'Gần biển': '🏖️',
    'Wifi': '📶',
    'Lễ tân 24/7': '🏨',
    'Đưa đón sân bay': '✈️',
    'Pet-friendly': '🐕',
    'Phòng gia đình': '👨‍👩‍👧‍👦',
    'Không hút thuốc': '🚭',
    'Bồn tắm': '🛁',
    'View biển': '🌊',
    'View thành phố': '🏙️',
    'Gần trung tâm': '🏛️',
    'Ban công': '🌿',
    'Cửa sổ': '🪟',
    'Giặt là': '👕',
    'Thang máy': '🛗',
    'Romantic': '💕',
    'Quiet': '🤫',
    'Lively': '🎉',
    'Luxury': '✨',
    'Nature': '🌿',
    'Cozy': '🏠',
    'Modern': '🏢',
    'Classic': '🏛️'
  }
  
  return amenityMap[amenity] || '✨'
}

/**
 * Format price for display
 */
export const formatPrice = (price: number): string => {
  if (price >= 1000000) {
    return `${(price / 1000000).toFixed(1)}M`
  } else if (price >= 1000) {
    return `${(price / 1000).toFixed(0)}K`
  }
  return price.toString()
}

/**
 * Get budget category from price
 */
export const getBudgetCategory = (price: number): string => {
  if (price < 500000) return 'Tiết kiệm'
  if (price < 1000000) return 'Bình dân'
  if (price < 2000000) return 'Trung bình'
  if (price < 5000000) return 'Cao cấp'
  return 'Luxury'
}

/**
 * Get duration category
 */
export const getDurationCategory = (duration: number): string => {
  if (duration === 1) return 'Một đêm'
  if (duration <= 3) return 'Ngắn ngày'
  if (duration <= 7) return 'Tuần'
  return 'Dài ngày'
}

/**
 * Get city emoji
 */
export const getCityEmoji = (city: string): string => {
  const cityMap: Record<string, string> = {
    'Đà Nẵng': '🏖️',
    'Hà Nội': '🏛️',
    'Hồ Chí Minh': '🌆',
    'Nha Trang': '🌊',
    'Đà Lạt': '🏔️',
    'Phú Quốc': '🏝️',
    'Hội An': '🏮',
    'Sa Pa': '⛰️',
    'Huế': '🏛️',
    'Cần Thơ': '🌾'
  }
  
  return cityMap[city] || '🏙️'
}

/**
 * Get relevance score color
 */
export const getRelevanceScoreColor = (score: number): string => {
  if (score >= 0.8) return 'text-green-600'
  if (score >= 0.6) return 'text-yellow-600'
  if (score >= 0.4) return 'text-orange-600'
  return 'text-red-600'
}

/**
 * Get relevance score label
 */
export const getRelevanceScoreLabel = (score: number): string => {
  if (score >= 0.8) return 'Rất phù hợp'
  if (score >= 0.6) return 'Phù hợp'
  if (score >= 0.4) return 'Khá phù hợp'
  return 'Ít phù hợp'
}
