import type { UnitCategory } from '../types'

export type UnitCodePreset = {
  category: UnitCategory
  code: string
  name: string
  description: string
  fieldsHint: string
}

export const unitCodePresets: UnitCodePreset[] = [
  // ROOM presets
  {
    category: 'ROOM',
    code: 'STD',
    name: 'Standard Room',
    description: 'Phòng tiêu chuẩn 1-2 khách, tiện nghi cơ bản.',
    fieldsHint: 'capacity=2, basePrice, hasBalcony?, imageUrls',
  },
  {
    category: 'ROOM',
    code: 'DLX',
    name: 'Deluxe Room',
    description: 'Phòng Deluxe rộng hơn, view đẹp hơn Standard.',
    fieldsHint: 'capacity=2-3, basePrice, hasBalcony?, imageUrls',
  },
  {
    category: 'ROOM',
    code: 'SUI',
    name: 'Suite',
    description: 'Phòng Suite cao cấp, phòng khách riêng.',
    fieldsHint: 'capacity=2-4, basePrice, hasBalcony?, imageUrls',
  },
  {
    category: 'ROOM',
    code: 'FAM',
    name: 'Family Room',
    description: 'Phòng gia đình, phù hợp nhóm 3-5 người.',
    fieldsHint: 'capacity=4-5, basePrice, hasBalcony?, imageUrls',
  },
  // TABLE presets
  {
    category: 'TABLE',
    code: 'T2',
    name: 'Bàn 2 người',
    description: 'Bàn nhỏ cho 2 khách, phù hợp cặp đôi.',
    fieldsHint: 'capacity=2, basePrice (mặc định 0 nếu không cần)',
  },
  {
    category: 'TABLE',
    code: 'T4',
    name: 'Bàn 4 người',
    description: 'Bàn trung bình cho nhóm 4 khách.',
    fieldsHint: 'capacity=4, basePrice',
  },
  {
    category: 'TABLE',
    code: 'T8',
    name: 'Bàn 8 người',
    description: 'Bàn lớn cho nhóm 6-8 khách hoặc tiệc nhỏ.',
    fieldsHint: 'capacity=8, basePrice',
  },
]


