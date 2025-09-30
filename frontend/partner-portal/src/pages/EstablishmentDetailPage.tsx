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

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold mb-4">{item.name}</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
        <aside className="border rounded p-4 space-y-2">
          <div className="font-semibold">Thông tin</div>
          <div className="text-sm text-slate-600">{item.city}</div>
          <div className="text-sm text-slate-600">{item.address}</div>
        </aside>
      </div>
      {item.description && (
        <p className="mt-4 text-slate-700">{item.description}</p>
      )}
    </div>
  )
}


