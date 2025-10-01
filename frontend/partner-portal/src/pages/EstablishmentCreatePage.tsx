import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createEstablishment } from '../api/partner'
import type { EstablishmentCreationRequest } from '../types'
import { useAuth } from '../auth/AuthContext'
import { vnProvinces } from '../constants/vnProvinces'
import { popularAmenities } from '../constants/amenities'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Card, CardContent } from '../components/ui/card'

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
    <div className="max-w-3xl">
      <h1 className="text-2xl font-semibold mb-4">Thêm cơ sở mới</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <Input placeholder="Tên cơ sở" value={form.name}
               onChange={(e)=>setForm({...form, name:e.target.value})} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label className="mb-1 block">Tỉnh/Thành</Label>
            <select className="w-full border rounded px-3 py-2" value={form.city}
                    onChange={(e)=>setForm({...form, city:e.target.value})}>
              <option value="">-- Chọn tỉnh/thành --</option>
              {vnProvinces.map((p)=>(
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div>
            <Label className="mb-1 block">Loại</Label>
            <select className="w-full border rounded px-3 py-2" value={form.type} onChange={(e)=>setForm({...form, type:e.target.value})}>
              <option value="HOTEL">HOTEL</option>
              <option value="RESTAURANT">RESTAURANT</option>
            </select>
          </div>
        </div>
        <Input placeholder="Địa chỉ cụ thể" value={form.address}
               onChange={(e)=>setForm({...form, address:e.target.value})} />
        <Input placeholder="Tiện ích (phân tách bởi dấu phẩy)" value={amenities}
               onChange={(e)=>setAmenities(e.target.value)} />
        <div>
          <div className="text-sm font-medium mb-2">Tiện ích phổ biến</div>
          <div className="flex flex-wrap gap-2">
            {popularAmenities.map(a => {
              const active = amenitySet.has(a)
              return (
                <Button
                  type="button"
                  key={a}
                  variant={active? 'default':'outline'}
                  size="sm"
                  className="transition-all duration-150"
                  onClick={()=>{
                    setAmenitySet(prev => {
                      const next = new Set(Array.from(prev))
                      if (next.has(a)) next.delete(a); else next.add(a)
                      return next
                    })
                  }}
                >
                  {a}
                </Button>
              )
            })}
          </div>
        </div>
        <Card>
          <CardContent className="py-4 space-y-3">
            <div className="space-y-2">
              <Label>Ảnh chính</Label>
              <div className="flex items-center gap-3">
                <input id="main-file" type="file" accept="image/*" className="sr-only" onChange={(e)=>setMainFile(e.target.files?.[0]||null)} />
                <Label htmlFor="main-file">
                  <Button type="button" asChild={false} className="cursor-pointer">Chọn ảnh</Button>
                </Label>
                {mainFile && <span className="text-sm text-slate-600 truncate max-w-[240px]">{mainFile.name}</span>}
              </div>
              <div className="rounded overflow-hidden bg-slate-100 w-[320px] h-[180px]">
                {mainFile && (
                  <img src={URL.createObjectURL(mainFile)} className="w-full h-full object-cover" />
                )}
              </div>
              <div className="text-xs text-slate-500">Khuyến nghị tỉ lệ 16:9 (ví dụ 1280x720).</div>
            </div>
            <div className="space-y-2">
              <Label>Ảnh phụ</Label>
              <div className="flex items-center gap-3">
                <input id="gallery-files" type="file" accept="image/*" multiple className="sr-only" onChange={(e)=>setGallery(Array.from(e.target.files||[]))} />
                <Label htmlFor="gallery-files">
                  <Button type="button" asChild={false} className="cursor-pointer" variant="outline">Chọn ảnh</Button>
                </Label>
                {gallery.length>0 && <span className="text-sm text-slate-600">{gallery.length} ảnh đã chọn</span>}
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
            </div>
          </CardContent>
        </Card>
        {error && <div className="text-red-600 text-sm">{error}</div>}
        <Button disabled={loading} className="bg-slate-900 hover:bg-slate-800 text-white">{loading?'Đang tạo...':'Tạo cơ sở'}</Button>
      </form>
    </div>
  )
}


