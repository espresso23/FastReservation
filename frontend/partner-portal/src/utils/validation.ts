/**
 * Validation utilities for form inputs and user data
 */

/**
 * Validate email format
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validate phone number format (Vietnamese)
 */
export const isValidPhoneNumber = (phone: string): boolean => {
  const phoneRegex = /^(\+84|84|0)[1-9][0-9]{8,9}$/
  return phoneRegex.test(phone.replace(/\s/g, ''))
}

/**
 * Validate date format (YYYY-MM-DD)
 */
export const isValidDate = (date: string): boolean => {
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/
  if (!dateRegex.test(date)) return false
  
  const dateObj = new Date(date)
  return dateObj instanceof Date && !isNaN(dateObj.getTime())
}

/**
 * Validate that date is not in the past
 */
export const isFutureDate = (date: string): boolean => {
  const dateObj = new Date(date)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return dateObj >= today
}

/**
 * Validate duration (positive integer)
 */
export const isValidDuration = (duration: number): boolean => {
  return Number.isInteger(duration) && duration > 0 && duration <= 365
}

/**
 * Validate price (positive number)
 */
export const isValidPrice = (price: number): boolean => {
  return Number.isFinite(price) && price > 0 && price <= 1000000000 // Max 1 billion VND
}

/**
 * Validate number of guests
 */
export const isValidGuestCount = (guests: number): boolean => {
  return Number.isInteger(guests) && guests > 0 && guests <= 50
}

/**
 * Validate city name (non-empty string)
 */
export const isValidCity = (city: string): boolean => {
  return typeof city === 'string' && city.trim().length > 0 && city.trim().length <= 100
}

/**
 * Validate establishment type
 */
export const isValidEstablishmentType = (type: string): boolean => {
  const validTypes = ['HOTEL', 'RESTAURANT']
  return validTypes.includes(type.toUpperCase())
}

/**
 * Validate travel companion type
 */
export const isValidTravelCompanion = (companion: string): boolean => {
  const validTypes = ['single', 'couple', 'family', 'friends', 'team', 'business']
  return validTypes.includes(companion.toLowerCase())
}

/**
 * Validate amenities list
 */
export const isValidAmenities = (amenities: string | string[]): boolean => {
  if (typeof amenities === 'string') {
    return amenities.trim().length > 0 && amenities.length <= 1000
  }
  if (Array.isArray(amenities)) {
    return amenities.length > 0 && amenities.length <= 20 && 
           amenities.every(amenity => typeof amenity === 'string' && amenity.trim().length > 0)
  }
  return false
}

/**
 * Validate user prompt (non-empty, reasonable length)
 */
export const isValidUserPrompt = (prompt: string): boolean => {
  return typeof prompt === 'string' && 
         prompt.trim().length > 0 && 
         prompt.trim().length <= 1000
}

/**
 * Validate session ID format
 */
export const isValidSessionId = (sessionId: string): boolean => {
  const sessionRegex = /^session_\d+_[a-z0-9]+$/
  return sessionRegex.test(sessionId)
}

/**
 * Validate establishment ID format
 */
export const isValidEstablishmentId = (id: string): boolean => {
  return typeof id === 'string' && 
         id.trim().length > 0 && 
         id.trim().length <= 50 &&
         /^[a-zA-Z0-9_-]+$/.test(id)
}

/**
 * Comprehensive validation for booking parameters
 */
export const validateBookingParams = (params: Record<string, any>): {
  isValid: boolean
  errors: string[]
} => {
  const errors: string[] = []

  // Validate required fields
  if (!params.city || !isValidCity(params.city)) {
    errors.push('Thành phố không hợp lệ')
  }

  if (!params.check_in_date || !isValidDate(params.check_in_date) || !isFutureDate(params.check_in_date)) {
    errors.push('Ngày check-in không hợp lệ hoặc đã qua')
  }

  if (!params.duration || !isValidDuration(params.duration)) {
    errors.push('Số đêm không hợp lệ')
  }

  // Validate optional fields
  if (params.max_price && !isValidPrice(params.max_price)) {
    errors.push('Ngân sách không hợp lệ')
  }

  if (params.num_guests && !isValidGuestCount(params.num_guests)) {
    errors.push('Số khách không hợp lệ')
  }

  if (params.establishment_type && !isValidEstablishmentType(params.establishment_type)) {
    errors.push('Loại cơ sở không hợp lệ')
  }

  if (params.travel_companion && !isValidTravelCompanion(params.travel_companion)) {
    errors.push('Loại khách hàng không hợp lệ')
  }

  if (params.amenities_priority && !isValidAmenities(params.amenities_priority)) {
    errors.push('Danh sách tiện ích không hợp lệ')
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Sanitize user input
 */
export const sanitizeInput = (input: string): string => {
  return input
    .trim()
    .replace(/[<>]/g, '') // Remove potential HTML tags
    .replace(/['"]/g, '') // Remove quotes
    .substring(0, 1000) // Limit length
}

/**
 * Sanitize establishment name
 */
export const sanitizeEstablishmentName = (name: string): string => {
  return name
    .trim()
    .replace(/[<>'"&]/g, '') // Remove potentially dangerous characters
    .substring(0, 100) // Limit length
}

/**
 * Validate and format phone number
 */
export const formatPhoneNumber = (phone: string): string => {
  const cleaned = phone.replace(/\D/g, '') // Remove non-digits
  
  if (cleaned.startsWith('84')) {
    return `+${cleaned}`
  } else if (cleaned.startsWith('0')) {
    return `+84${cleaned.substring(1)}`
  } else if (cleaned.length === 9) {
    return `+84${cleaned}`
  }
  
  return phone // Return original if can't format
}

/**
 * Validate URL format
 */
export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * Validate image URL (basic check)
 */
export const isValidImageUrl = (url: string): boolean => {
  if (!isValidUrl(url)) return false
  
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
  const lowerUrl = url.toLowerCase()
  
  return imageExtensions.some(ext => lowerUrl.includes(ext)) || 
         lowerUrl.includes('cloudinary') || 
         lowerUrl.includes('amazonaws')
}
