import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import type { Establishment } from '../types'
import api from '../api/client'

export default function EstablishmentDetailPage() {
  const { id } = useParams()
  const [item, setItem] = useState<Establishment | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    if (!id) return
    api.get(`/partner/establishment/${id}`)
      .then((res) => { if (mounted) setItem(res.data) })
      .finally(() => { if (mounted) setLoading(false) })
    return () => { mounted = false }
  }, [id])

  if (loading) return <div>Đang tải...</div>
  if (!item) return <div>Không tìm thấy cơ sở.</div>

  const thumbs = item.imageUrlsGallery ?? []
  const amenities = item.amenitiesList ?? []

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold mb-1">{item.name}</h1>
      <div className="text-slate-600 mb-4">{item.city}{item.address ? ` • ${item.address}` : ''}</div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
        <div className="md:col-span-2">
          {item.imageUrlMain && (
            <img src={item.imageUrlMain} className="w-full h-80 object-cover rounded" />
          )}
          <div className="flex gap-2 mt-2 overflow-x-auto">
            {thumbs.map((u, i) => (
              <img key={i} src={u} className="w-24 h-24 object-cover rounded" />
            ))}
          </div>
        </div>
        <aside className="border rounded p-4 space-y-3 bg-white">
          <div className="font-semibold">Thông tin</div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-slate-500">Thành phố</div>
            <div>{item.city || '-'}</div>
            <div className="text-slate-500">Địa chỉ</div>
            <div>{item.address || '-'}</div>
            <div className="text-slate-500">Tình trạng tồn kho</div>
            <div>{item.hasInventory ? 'Có quản lý' : 'Không'}</div>
          </div>
          {amenities.length > 0 && (
            <div>
              <div className="text-sm font-medium mb-1">Tiện ích</div>
              <div className="flex flex-wrap gap-2">
                {amenities.map((a, idx) => (
                  <span key={idx} className="text-xs px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200">{a}</span>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>
      {(item.descriptionLong || item.description) && (
        <div className="mt-4">
          <div className="font-semibold mb-1">Giới thiệu</div>
          <p className="text-slate-700 whitespace-pre-line">{item.descriptionLong || item.description}</p>
        </div>
      )}
    </div>
  )
}


