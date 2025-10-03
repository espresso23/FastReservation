/**
 * Text processing utilities for natural language understanding
 */

/**
 * Remove accents and normalize Vietnamese text for better matching
 */
export const stripAccents = (text: string): string => {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // remove accents
    .replace(/đ/g, 'd').replace(/Đ/g, 'd')
    .replace(/[^a-zA-Z0-9\s]/g, ' ') // punctuation to spaces
    .replace(/\s+/g, ' ') // collapse
    .trim()
    .toLowerCase()
}

/**
 * Infer city from Vietnamese text
 */
export const inferCityFromText = (text: string): string | null => {
  const t = stripAccents(text)
  const pairs: [string, string][] = [
    ['da nang', 'Đà Nẵng'], ['danang', 'Đà Nẵng'], ['da-nang', 'Đà Nẵng'], ['da_nang', 'Đà Nẵng'], ['dn', 'Đà Nẵng'],
    ['ha noi', 'Hà Nội'], ['hanoi', 'Hà Nội'],
    ['ho chi minh', 'Hồ Chí Minh'], ['tphcm', 'Hồ Chí Minh'], ['hcm', 'Hồ Chí Minh'], ['sai gon', 'Hồ Chí Minh'], ['saigon', 'Hồ Chí Minh'],
    ['nha trang', 'Nha Trang'], ['nhatrang', 'Nha Trang'],
    ['da lat', 'Đà Lạt'], ['dalat', 'Đà Lạt'],
    ['phu quoc', 'Phú Quốc'], ['phuquoc', 'Phú Quốc'],
    ['hoi an', 'Hội An'], ['hoian', 'Hội An'],
    ['sapa', 'Sa Pa'], ['sa pa', 'Sa Pa'],
    ['hue', 'Huế'], ['hue', 'Huế'],
    ['can tho', 'Cần Thơ'], ['cantho', 'Cần Thơ']
  ]
  
  for (const [alias, disp] of pairs.sort((a, b) => b[0].length - a[0].length)) {
    if (t.includes(alias)) return disp
  }
  return null
}

/**
 * Infer establishment type from text
 */
export const inferEstablishmentType = (text: string): 'HOTEL' | 'RESTAURANT' | null => {
  const lc = stripAccents(text)
  if (lc.includes('khach san') || lc.includes('hotel') || lc.includes('resort')) return 'HOTEL'
  if (lc.includes('nha hang') || lc.includes('restaurant') || lc.includes('quan an')) return 'RESTAURANT'
  return null
}

/**
 * Parse price from Vietnamese text
 */
export const parsePriceFromText = (text: string): number | null => {
  try {
    const s2 = text.toLowerCase().replace(/,/g, '.')
    let price: number | null = null
    
    // Handle Vietnamese price units (k, nghìn, triệu, tr, m)
    let m1 = s2.match(/(\d+(?:\.\d+)?)\s*(k|nghin|nghìn|ngan|ngàn|tr|trieu|triệu|m)\b/)
    if (m1) {
      const val = parseFloat(m1[1])
      const unit = m1[2]
      if (['k', 'nghin', 'nghìn', 'ngan', 'ngàn'].includes(unit)) price = Math.round(val * 1000)
      else if (['tr', 'trieu', 'triệu'].includes(unit)) price = Math.round(val * 1000000)
      else if (unit === 'm') price = Math.round(val * 1000000) // million
    } else {
      // Handle direct VND format
      let m2 = s2.match(/(\d{1,3}(?:[\.\s]\d{3})+|\d+)\s*(đ|d|vnd)\b/)
      if (m2) {
        price = parseInt(m2[1].replace(/\./g, '').replace(/\s/g, ''))
      }
    }
    
    return price && price > 0 ? price : null
  } catch {
    return null
  }
}

/**
 * Parse date from text (YYYY-MM-DD format)
 */
export const parseDateFromText = (text: string): string | null => {
  const dateM = text.match(/(20\d{2}-\d{2}-\d{2})/)
  return dateM ? dateM[1] : null
}

/**
 * Parse duration from Vietnamese text
 */
export const parseDurationFromText = (text: string): number | null => {
  const s = stripAccents(text)
  const durM = s.match(/(\d+)\s*(dem|dems|ngay|ngày)/)
  return durM ? Number(durM[1]) : null
}

/**
 * Extract amenities from text
 */
export const extractAmenitiesFromText = (text: string): string[] => {
  const s = stripAccents(text)
  const amens: string[] = []
  
  const amenityMap: Record<string, string> = {
    'gym': 'Gym',
    'ho boi': 'Hồ bơi', 'hoboi': 'Hồ bơi', 'pool': 'Hồ bơi',
    'spa': 'Spa',
    'bai do xe': 'Bãi đậu xe', 'giu xe': 'Bãi đậu xe', 'parking': 'Bãi đậu xe',
    'gan bien': 'Gần biển', 'ganbien': 'Gần biển', 'beach': 'Gần biển',
    'buffet sang': 'Buffet sáng',
    'wifi': 'Wifi',
    'le tan': 'Lễ tân 24/7',
    'dua don': 'Đưa đón sân bay',
    'pet friendly': 'Pet-friendly',
    'phong gia dinh': 'Phòng gia đình',
    'khong hut thuoc': 'Không hút thuốc',
    'bon tam': 'Bồn tắm',
    'view bien': 'View biển',
    'view thanh pho': 'View thành phố',
    'gan trung tam': 'Gần trung tâm',
    'ban cong': 'Ban công',
    'cua so': 'Cửa sổ',
    'giat la': 'Giặt là',
    'thang may': 'Thang máy'
  }
  
  for (const [key, value] of Object.entries(amenityMap)) {
    if (s.includes(key)) amens.push(value)
  }
  
  return amens
}

/**
 * Parse all parameters from user prompt
 */
export const parseParametersFromPrompt = (text: string): Record<string, any> => {
  const out: Record<string, any> = {}
  
  // City
  const city = inferCityFromText(text)
  if (city) out.city = city
  
  // Date
  const date = parseDateFromText(text)
  if (date) out.check_in_date = date
  
  // Duration
  const duration = parseDurationFromText(text)
  if (duration) out.duration = duration
  
  // Price
  const price = parsePriceFromText(text)
  if (price) out.max_price = price
  
  // Amenities
  const amenities = extractAmenitiesFromText(text)
  if (amenities.length > 0) out.amenities_priority = amenities.join(', ')
  
  // Balcony
  const s = stripAccents(text)
  if (s.includes('ban cong')) out.has_balcony = 'yes'
  
  // Establishment type
  const type = inferEstablishmentType(text)
  if (type) out.establishment_type = type
  
  return out
}

/**
 * Humanize parameter values for display
 */
export const humanizeParameterValue = (key: string, value: string): string => {
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
  
  if (key === 'num_guests') {
    const vv = (value || '').toLowerCase()
    if (vv === 'single') return '1 người'
    if (vv === 'couple') return '2 người'
    const n = Number(vv)
    if (!isNaN(n) && n > 0) return `${n} người`
  }
  
  if (key === 'has_balcony') {
    if ((value || '').toLowerCase() === 'yes') return 'Có'
    if ((value || '').toLowerCase() === 'no') return 'Không'
  }
  
  return value
}

/**
 * Get label for parameter key
 */
export const getParameterLabel = (key?: string): string => {
  switch (key) {
    case 'establishment_type': return 'Loại cơ sở'
    case 'city': return 'Thành phố'
    case 'check_in_date': return 'Ngày nhận'
    case 'duration': return 'Số đêm'
    case 'max_price': return 'Ngân sách tối đa (VND)'
    case 'travel_companion': return 'Đi cùng ai'
    case 'amenities_priority': return 'Tiện ích ưu tiên'
    case 'has_balcony': return 'Có ban công?'
    case 'num_guests': return 'Số người'
    default: return key || ''
  }
}
