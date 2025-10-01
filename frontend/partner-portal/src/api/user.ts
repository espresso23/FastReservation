import api from './client'

export type QuizRequest = {
  userPrompt: string
  currentParams: Record<string, any>
}

export type QuizResponse = {
  quiz_completed: boolean
  missing_quiz?: string
  key_to_collect?: string
  final_params?: Record<string, any>
  options?: string[]
  image_options?: { label: string; image_url: string; value: string }[]
}

export type Suggestion = {
  establishmentId: string
  establishmentName: string
  city?: string
  starRating?: number
  imageUrlMain?: string
  imageUrlsGallery?: string[]
  itemType?: string
  floorArea?: string
  unitsAvailable?: number
  finalPrice?: number
  itemImageUrl?: string
}

export async function processBooking(data: QuizRequest): Promise<QuizResponse | Suggestion[]> {
  const res = await api.post('/booking/process', data)
  return res.data
}

export async function confirmBooking(payload: any) {
  const res = await api.post('/booking/confirm-payment', payload)
  return res.data
}

// Xem danh sách booking của một khách hàng
export async function getUserBookings(userId: number) {
  const res = await api.get(`/booking/user/view/${userId}`)
  return Array.isArray(res.data) ? res.data : []
}


