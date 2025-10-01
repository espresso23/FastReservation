import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createEstablishment } from '../api/partner'
import type { EstablishmentCreationRequest } from '../types'
import { useAuth } from '../auth/AuthContext'
import { vnProvinces } from '../constants/vnProvinces'
import { popularAmenities } from '../constants/amenities'

export default function EstablishmentCreatePage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<EstablishmentCreationRequest>({
    ownerId: user?.id || '',
    name: '',
    type: 'HOTEL',
    city: '',
    address: '',
    hasInventory: true,
  })
  const [mainFile, setMainFile] = useState<File | null>(null)
  const [gallery, setGallery] = useState<File[]>([])
  const [amenities, setAmenities] = useState<string>('')
  const [amenitySet, setAmenitySet] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user?.id) return setError('Bạn cần đăng nhập')
    if (!mainFile) return setError('Chọn ảnh chính')
    setError(null); setLoading(true)
    try {
      const amenitiesList = Array.from(new Set([
        ...Array.from(amenitySet),
        ...amenities
        .split(',')
        .map(s => s.trim())
        .filter(Boolean)
      ]))
      const payload = { ...form, ownerId: user.id, amenitiesList }
      const created = await createEstablishment(payload, mainFile, gallery)
      navigate(`/establishments/${created.id}`)
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Tạo cơ sở thất bại')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-semibold mb-4">Thêm cơ sở mới</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        <input className="w-full border rounded px-3 py-2" placeholder="Tên cơ sở" value={form.name}
               onChange={(e)=>setForm({...form, name:e.target.value})} />
        <div className="grid grid-cols-2 gap-3">
          <select className="border rounded px-3 py-2" value={form.city}
                  onChange={(e)=>setForm({...form, city:e.target.value})}>
            <option value="">-- Chọn tỉnh/thành --</option>
            {vnProvinces.map((p)=>(
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <select className="border rounded px-3 py-2" value={form.type} onChange={(e)=>setForm({...form, type:e.target.value})}>
            <option value="HOTEL">HOTEL</option>
            <option value="RESTAURANT">RESTAURANT</option>
          </select>
        </div>
        <input className="w-full border rounded px-3 py-2" placeholder="Địa chỉ cụ thể" value={form.address}
               onChange={(e)=>setForm({...form, address:e.target.value})} />
        <input className="w-full border rounded px-3 py-2" placeholder="Tiện ích (phân tách bởi dấu phẩy, ví dụ: Wifi, Bãi đỗ xe, Máy lạnh)" value={amenities}
               onChange={(e)=>setAmenities(e.target.value)} />
        {/* Chọn nhanh tiện ích */}
        <div>
          <div className="text-sm font-medium mb-1">Tiện ích phổ biến</div>
          <div className="flex flex-wrap gap-2 mb-2">
            {popularAmenities.map(a => {
              const active = amenitySet.has(a)
              return (
                <button type="button" key={a}
                        className={`px-2 py-1 rounded border text-xs ${active? 'bg-slate-900 text-white border-slate-900' : 'border-slate-300'}`}
                        onClick={()=>{
                          setAmenitySet(prev => {
                            const next = new Set(Array.from(prev))
                            if (next.has(a)) next.delete(a); else next.add(a)
                            return next
                          })
                        }}>
                  {a}
                </button>
              )
            })}
          </div>
        </div>
        {/* Bỏ nhập khoảng giá và số sao khỏi form theo yêu cầu */}
        <textarea className="w-full border rounded px-3 py-2" rows={4} placeholder="Mô tả dài"
                  value={form.descriptionLong ?? ''}
                  onChange={(e)=>setForm({...form, descriptionLong:e.target.value})} />
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <label className="font-medium">Ảnh chính</label>
            <input type="file" accept="image/*" onChange={(e)=>setMainFile(e.target.files?.[0]||null)} />
          </div>
          <div className="rounded overflow-hidden bg-slate-100 w-[320px] h-[180px]">
            {mainFile && (
              <img src={URL.createObjectURL(mainFile)} className="w-full h-full object-cover" />
            )}
          </div>
          <div className="text-xs text-slate-500">Khuyến nghị tỉ lệ 16:9 (ví dụ 1280x720) để hiển thị đồng nhất.</div>
        </div>
        <div className="flex items-center gap-3">
          <label className="font-medium">Ảnh phụ</label>
          <input type="file" accept="image/*" multiple onChange={(e)=>setGallery(Array.from(e.target.files||[]))} />
        </div>
        {gallery.length>0 && (
          <div className="grid grid-cols-6 gap-2">
            {gallery.map((f,idx)=>(
              <div key={idx} className="rounded overflow-hidden w-24 h-24 bg-slate-100">
                <img src={URL.createObjectURL(f)} className="w-full h-full object-cover" />
              </div>
            ))}
          </div>
        )}
        {error && <div className="text-red-600 text-sm">{error}</div>}
        <button disabled={loading} className="px-4 py-2 rounded-md bg-slate-900 text-white disabled:opacity-60">{loading?'Đang tạo...':'Tạo cơ sở'}</button>
      </form>
    </div>
  )
}


