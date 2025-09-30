export type UnitCategory = 'ROOM' | 'TABLE'

export interface Establishment {
  id: string
  name: string
  city?: string
  address?: string
  description?: string
  descriptionLong?: string
  imageUrlMain?: string
  imageUrlsGallery?: string[]
  hasInventory?: boolean
}

export interface EstablishmentCreationRequest {
  ownerId: string
  name: string
  type: string
  city?: string
  priceRangeVnd?: number
  starRating?: number
  descriptionLong?: string
  amenitiesList?: string[]
  hasInventory?: boolean
}

export interface UnitType {
  id: number
  establishmentId: string
  category: UnitCategory
  code: string
  name: string
  capacity: number
  hasBalcony?: boolean
  basePrice?: number
  depositAmount?: number
  imageUrls?: string[]
  active?: boolean
}

export interface UnitVariant {
  id: number
  typeId: number
  bedCount?: number
  bedType?: string
  hasWindow?: boolean
  view?: string
  extraPriceDelta?: number
}

export interface UnitAvailability {
  id: number
  variantId: number
  date: string
  totalUnits: number
  unitsBooked: number
  overridePrice?: number
  version?: number
}


