import { useEffect, useMemo, useState } from 'react'
import { createType, listMyEstablishments, listTypes } from '../api/partner'
import type { Establishment, UnitType } from '../types'
import { useAuth } from '../auth/AuthContext'
import { unitCodePresets } from '../constants/unitPresets'

export default function TypesPage() {
  const { user } = useAuth()
  const [establishments, setEstablishments] = useState<Establishment[]>([])
  const [selectedEst, setSelectedEst] = useState<string>('')
  const [types, setTypes] = useState<UnitType[]>([])
  const [presetCode, setPresetCode] = useState<string>('')
  const [requireDeposit, setRequireDeposit] = useState<boolean>(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const [form, setForm] = useState<Omit<UnitType, 'id'>>({
    establishmentId: '',
    category: 'ROOM',
    code: '',
    name: '',
    capacity: 2,
    hasBalcony: false,
    basePrice: 0,
    depositAmount: 0,
    imageUrls: [],
    active: true,
  } as any)

  useEffect(() => {
    if (!user?.id) return
    listMyEstablishments(user.id).then((list) => {
      setEstablishments(list)
      if (!selectedEst && list.length > 0) {
        setSelectedEst(list[0].id)
      }
    })
  }, [user?.id])

  useEffect(() => {
    if (!selectedEst) return
    listTypes(selectedEst).then(setTypes)
    setForm((f) => ({ ...f, establishmentId: selectedEst }))
  }, [selectedEst])

  const currentEst = useMemo(() => establishments.find(e => e.id === selectedEst), [establishments, selectedEst])

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    const payload: any = { ...form }
    if (form.category === 'ROOM') {
      payload.depositAmount = undefined
    } else {
      // TABLE: basePrice không dùng
      payload.basePrice = undefined
      if (!requireDeposit) payload.depositAmount = undefined
    }
    const created = await createType(payload)
    setTypes((t) => [created, ...t])
    setForm({ ...form, code: '', name: '', basePrice: 0 })
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Loại phòng/bàn</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label className="block text-sm mb-1">Chọn cơ sở</label>
          <select className="w-full border rounded px-3 py-2" value={selectedEst} onChange={(e)=>setSelectedEst(e.target.value)}>
            <option value="">-- Chọn --</option>
            {establishments.map((e)=>(<option key={e.id} value={e.id}>{e.name}</option>))}
          </select>
          {currentEst && <div className="text-sm text-slate-600 mt-1">{currentEst.city}</div>}

          {selectedEst && (
            <form onSubmit={onCreate} className="mt-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <select className="border rounded px-3 py-2" value={form.category as any} onChange={(e)=>setForm({...form, category: e.target.value as any})}>
                  <option value="ROOM">ROOM</option>
                  <option value="TABLE">TABLE</option>
                </select>
                <div className="flex gap-2">
                  <input className="flex-1 border rounded px-3 py-2" placeholder="Mã (VD: DLX)" value={form.code} onChange={(e)=>setForm({...form, code:e.target.value})} />
                  <select className="border rounded px-2" value={presetCode} onChange={(e)=>{
                    const code = e.target.value
                    setPresetCode(code)
                    const p = unitCodePresets.find(x=>x.code===code)
                    if (p) {
                      setForm(f=>({ ...f, category: p.category as any, code: p.code, name: p.name }))
                    }
                  }}>
                    <option value="">Gợi ý</option>
                    {unitCodePresets.map(p=> (
                      <option key={p.code} value={p.code}>{p.category}-{p.code}</option>
                    ))}
                  </select>
                </div>
              </div>
              <input className="w-full border rounded px-3 py-2" placeholder="Tên loại (VD: Phòng Deluxe)" value={form.name} onChange={(e)=>setForm({...form, name:e.target.value})} />
              <div className="text-xs text-slate-500">
                Chọn “Gợi ý” để tự điền mã và tên. Trường cần nhập: sức chứa, giá cơ bản; tuỳ chọn: ban công, hình ảnh.
                {presetCode && (
                  <div className="mt-1">
                    {(unitCodePresets.find(p=>p.code===presetCode)?.description) || ''}
                  </div>
                )}
              </div>

              <div className="mt-2">
                <div className="text-xs text-slate-500 mb-1">Hoặc chọn nhanh:</div>
                <div className="flex flex-wrap gap-2">
                  {unitCodePresets
                    .filter(p => p.category === (form.category as any))
                    .map(p => (
                      <button
                        key={p.code}
                        type="button"
                        className={`px-2 py-1 rounded border text-xs ${presetCode===p.code?'bg-slate-900 text-white border-slate-900':'border-slate-300'}`}
                        onClick={()=>{ setPresetCode(p.code); setForm(f=>({ ...f, category: p.category as any, code: p.code, name: p.name })) }}
                      >
                        {p.code}
                      </button>
                    ))}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-slate-600 mb-1">Sức chứa</label>
                  <input type="number" className="w-full border rounded px-3 py-2" value={form.capacity as any} onChange={(e)=>setForm({...form, capacity:Number(e.target.value||0)})} />
                </div>
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!form.hasBalcony} onChange={(e)=>setForm({...form, hasBalcony:e.target.checked})} /> Ban công</label>
                </div>
                <div>
                  {form.category === 'ROOM' ? (
                    <>
                      <label className="block text-xs text-slate-600 mb-1">Giá cơ bản (VND)</label>
                      <input type="number" className="w-full border rounded px-3 py-2" value={form.basePrice as any} onChange={(e)=>setForm({...form, basePrice:Number(e.target.value||0)})} />
                    </>
                  ) : (
                    <>
                      <label className="block text-xs text-slate-600 mb-1">Đặt cọc</label>
                      <div className="flex items-center gap-2 mb-2">
                        <input id="requireDeposit" type="checkbox" className="accent-slate-900" checked={requireDeposit} onChange={(e)=>setRequireDeposit(e.target.checked)} />
                        <label htmlFor="requireDeposit" className="text-sm">Yêu cầu tiền cọc</label>
                      </div>
                      {requireDeposit && (
                        <>
                          <label className="block text-xs text-slate-600 mb-1">Tiền cọc (VND)</label>
                          <input type="number" className="w-full border rounded px-3 py-2" value={form.depositAmount as any} onChange={(e)=>setForm({...form, depositAmount:Number(e.target.value||0)})} />
                        </>
                      )}
                    </>
                  )}
                </div>
              </div>
              <button className="px-4 py-2 rounded-md bg-slate-900 text-white">Thêm loại</button>
            </form>
          )}
        </div>
        <div className="md:col-span-2">
          <div className="text-sm text-slate-600 mb-2">Các loại đã tạo</div>
          <div className="space-y-2">
            {types.map((t)=>(
              <div key={t.id} className="border rounded p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{t.name} ({t.code})</div>
                    <div className="text-sm text-slate-600">{t.category} • Sức chứa {t.capacity} • Cơ sở: {t.establishmentId}</div>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    {t.category === 'ROOM' ? (
                      <span>{t.basePrice?.toLocaleString()} đ</span>
                    ) : (
                      <span>Đặt cọc: {t.depositAmount ? t.depositAmount.toLocaleString() + ' đ' : 'Không yêu cầu'}</span>
                    )}
                    <button className="px-2 py-1 border rounded" onClick={()=>setExpandedId(expandedId===t.id?null:t.id)}>
                      {expandedId===t.id ? 'Ẩn chi tiết' : 'Xem chi tiết'}
                    </button>
                  </div>
                </div>
                {expandedId===t.id && (
                  <div className="mt-3 text-sm text-slate-700 grid grid-cols-2 gap-3">
                    <div>Mã: {t.code}</div>
                    <div>Danh mục: {t.category}</div>
                    <div>Sức chứa: {t.capacity}</div>
                    <div>Ban công: {t.hasBalcony ? 'Có' : 'Không'}</div>
                    {t.category==='ROOM' && <div>Giá cơ bản: {t.basePrice?.toLocaleString()} đ</div>}
                    {t.category==='TABLE' && <div>Tiền cọc: {t.depositAmount ? t.depositAmount.toLocaleString() + ' đ' : 'Không'}</div>}
                    <div className="col-span-2">
                      <a href={`/variants?typeId=${t.id}`} className="text-blue-600">Quản lý biến thể cho loại này</a>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}


