import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import type { Establishment, UnitType } from '../types'
import { listTypes } from '../api/partner'
import api from '../api/client'

export default function EstablishmentDetailPage() {
  const { id } = useParams()
  const [item, setItem] = useState<Establishment | null>(null)
  const [loading, setLoading] = useState(true)
  const [types, setTypes] = useState<UnitType[]>([])

  useEffect(() => {
    let mounted = true
    if (!id) return
    api.get(`/partner/establishment/${id}`)
      .then((res) => { if (mounted) setItem(res.data) })
      .finally(() => { if (mounted) setLoading(false) })
    if (id) {
      listTypes(id).then((ts)=>{ if (mounted) setTypes(ts) })
    }
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
            <div className="w-full h-[360px] rounded overflow-hidden bg-slate-100">
              <img src={item.imageUrlMain} className="w-full h-full object-cover" />
            </div>
          )}
          <div className="flex gap-2 mt-2">
            {thumbs.map((u, i) => (
              <div key={i} className="relative group">
                <img src={u} className="w-24 h-24 object-cover rounded" />
                <div className="absolute z-20 hidden group-hover:block left-full ml-2 top-0 w-72 h-48 bg-white shadow-xl rounded overflow-hidden">
                  <img src={u} className="w-full h-auto object-contain" />
                </div>
              </div>
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

      <div className="mt-6">
        <div className="font-semibold mb-2">Các loại phòng/bàn</div>
        {types.length === 0 ? (
          <div className="text-slate-600 text-sm">Chưa có loại nào.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {types.map(t => (
              <div key={t.id} className="border rounded p-3 bg-white">
                <div className="flex items-center justify-between">
                  <div className="font-medium">{t.name} <span className="text-xs text-slate-500">({t.code})</span></div>
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${t.active ? 'bg-green-100 text-green-700 border-green-200':'bg-slate-100 text-slate-700 border-slate-200'}`}>{t.active ? 'Đang bán' : 'Tạm ẩn'}</span>
                </div>
                <div className="text-sm text-slate-600">Sức chứa: {t.capacity}{t.hasBalcony ? ' • Ban công' : ''}</div>
                <div className="text-sm">Giá cơ bản/Đặt cọc: {(t.basePrice||t.depositAmount||0).toLocaleString()} đ</div>
                {Array.isArray(t.imageUrls) && t.imageUrls.length>0 && (
                  <div className="mt-2 flex gap-2 overflow-x-auto">
                    {t.imageUrls.slice(0,4).map((u,idx)=>(
                      <img key={idx} src={u} className="w-20 h-20 object-cover rounded" />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}


