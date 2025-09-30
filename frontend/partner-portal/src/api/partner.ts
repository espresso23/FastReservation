import api from './client'
import type { Establishment, EstablishmentCreationRequest, UnitType } from '../types'

export async function listEstablishments(): Promise<Establishment[]> {
  const res = await api.get('/partner/establishments')
  const payload: any = res.data
  if (Array.isArray(payload)) return payload as Establishment[]
  if (payload && typeof payload === 'object') {
    if (Array.isArray(payload.content)) return payload.content as Establishment[]
    if (Array.isArray(payload.items)) return payload.items as Establishment[]
    if (Array.isArray(payload.establishments)) return payload.establishments as Establishment[]
    if (Array.isArray(payload.data)) return payload.data as Establishment[]
  }
  return []
}

export async function createEstablishment(data: EstablishmentCreationRequest, mainFile: File, galleryFiles: File[]) {
  const form = new FormData()
  form.append('data', new Blob([JSON.stringify(data)], { type: 'application/json' }))
  form.append('mainFile', mainFile)
  galleryFiles.forEach((f) => form.append('galleryFiles', f))
  const res = await api.post('/partner/establishments', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  return res.data as Establishment
}

export async function listMyEstablishments(ownerId: string) {
  const res = await api.get(`/partner/establishments/${ownerId}`)
  return Array.isArray(res.data) ? (res.data as Establishment[]) : []
}

export async function listTypes(establishmentId: string) {
  const res = await api.get(`/partner/types/${establishmentId}`)
  return Array.isArray(res.data) ? (res.data as UnitType[]) : []
}

export async function createType(input: Omit<UnitType, 'id'>) {
  const res = await api.post('/partner/types', input)
  return res.data as UnitType
}


