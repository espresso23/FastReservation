import { useEffect, useMemo, useState } from 'react'
import { createType, listMyEstablishments, listTypes, uploadImage, updateType, deleteType } from '../api/partner'
import type { Establishment, UnitType } from '../types'
import { useAuth } from '../auth/AuthContext'
import { unitCodePresets } from '../constants/unitPresets'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'

export default function TypesPage() {
  const { user } = useAuth()
  const [establishments, setEstablishments] = useState<Establishment[]>([])
  const [selectedEst, setSelectedEst] = useState<string>('')
  const [types, setTypes] = useState<UnitType[]>([])
  const [presetCode, setPresetCode] = useState<string>('')
  const [requireDeposit, setRequireDeposit] = useState<boolean>(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)
	const [edit, setEdit] = useState<Record<number, Partial<UnitType>>>({})

  const [form, setForm] = useState<Omit<UnitType, 'id'>>({
    establishmentId: '',
    category: 'ROOM',
    code: '',
    name: '',
    capacity: 2,
    hasBalcony: false,
    basePrice: 0,
    depositAmount: 0,
    totalUnits: 1,
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

	function ensureEditRow(t: UnitType) {
		if (!t.id) return
		setEdit(prev => {
			if (prev[t.id!]) return prev
			return { ...prev, [t.id!]: { ...t } }
		})
	}

	async function onSaveRow(t: UnitType) {
		if (!t.id) return
		const payload = edit[t.id!] || {}
		const updated = await updateType(t.id!, payload)
		setTypes(list => list.map(x => x.id === t.id ? updated : x))
		setEdit(prev => ({ ...prev, [t.id!]: { ...updated } }))
	}

	function setField(tid: number, key: keyof UnitType, value: any) {
		setEdit(prev => ({ ...prev, [tid]: { ...(prev[tid]||{}), [key]: value } }))
	}

	async function addImage(t: UnitType, file: File) {
		if (!t.id) return
		const { url } = await uploadImage(file, 'unit_type')
		const imgs = [ ...((edit[t.id!]?.imageUrls) || t.imageUrls || []), url ]
		setField(t.id!, 'imageUrls', imgs)
	}

	function removeImage(t: UnitType, idx: number) {
		if (!t.id) return
		const arr = [ ...((edit[t.id!]?.imageUrls) || t.imageUrls || []) ]
		arr.splice(idx, 1)
		setField(t.id!, 'imageUrls', arr)
	}

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Loại phòng/bàn</h1>
      {/* Thanh chọn cơ sở tách riêng */}
      <Card className="mb-6">
        <CardContent className="p-3 flex flex-wrap items-center gap-3">
          <div className="text-sm text-slate-600">Chọn cơ sở</div>
          <select className="border rounded px-3 py-2" value={selectedEst} onChange={(e)=>setSelectedEst(e.target.value)}>
            <option value="">-- Chọn --</option>
            {establishments.map((e)=>(<option key={e.id} value={e.id}>{e.name}{e.address?` — ${e.address}`:''}</option>))}
          </select>
          {currentEst && <div className="text-sm text-slate-500">{currentEst.city}</div>}
        </CardContent>
      </Card>

      <div className="flex flex-col lg:flex-row gap-6 items-start mt-2 relative z-0">
        <Card className="w-full lg:w-1/2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Tạo loại mới</CardTitle>
            <CardDescription>Điền thông tin loại ROOM/TABLE</CardDescription>
          </CardHeader>
          <CardContent>
          {selectedEst && (
            <form onSubmit={onCreate} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <select className="border rounded px-3 py-2" value={form.category as any} onChange={(e)=>setForm({...form, category: e.target.value as any})}>
                  <option value="ROOM">ROOM</option>
                  <option value="TABLE">TABLE</option>
                </select>
                <div className="flex gap-2 flex-nowrap items-stretch min-w-0">
                  <Input className="flex-1 min-w-0" placeholder="Mã (VD: DLX)" value={form.code} onChange={(e)=>setForm({...form, code:e.target.value})} />
                  <select className="border rounded px-2 w-28 shrink-0" value={presetCode} onChange={(e)=>{
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
              <Input className="w-full" placeholder="Tên loại (VD: Phòng Deluxe)" value={form.name} onChange={(e)=>setForm({...form, name:e.target.value})} />
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
                      <Button
                        key={p.code}
                        type="button"
                        size="sm"
                        variant={presetCode===p.code? 'default':'outline'}
                        onClick={()=>{ setPresetCode(p.code); setForm(f=>({ ...f, category: p.category as any, code: p.code, name: p.name })) }}
                      >
                        {p.code}
                      </Button>
                    ))}
                </div>
              </div>
              {/* Hình ảnh (upload hoặc URL) */}
              <div className="space-y-2">
                <Label className="mb-1">Hình ảnh</Label>
                <div className="mb-2">
                  <Input type="file" accept="image/*" onChange={async (e:any)=>{
                    const f = e.target.files?.[0]
                    if (!f) return
                    const { url } = await uploadImage(f, 'unit_type')
                    setForm(prev => ({ ...prev, imageUrls: [ ...(prev.imageUrls||[]), url ] }))
                    e.currentTarget.value = ''
                  }} />
                </div>
                {(form.imageUrls && form.imageUrls.length>0) && (
                  <div className="grid grid-cols-4 gap-2">
                    {form.imageUrls.map((u,idx)=> (
                      <div key={idx} className="relative group rounded overflow-hidden">
                        <img src={u} className="w-full h-20 object-cover" />
                        <div className="absolute z-20 hidden group-hover:block left-full ml-2 top-0 w-64 h-40 bg-white shadow-xl rounded overflow-hidden">
                          <img src={u} className="w-full h-full object-cover" />
                        </div>
                        <Button type="button" variant="outline" size="icon" className="absolute top-1 right-1 h-5 w-5 text-[10px] hidden group-hover:flex items-center justify-center" onClick={()=>{
                          setForm(f=>({ ...f, imageUrls: (f.imageUrls||[]).filter((_,i)=>i!==idx) }))
                        }}>x</Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <Label className="mb-1">Sức chứa</Label>
                  <Input type="number" value={form.capacity as any} onChange={(e)=>setForm({...form, capacity:Number((e.target as any).value||0)})} />
                </div>
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!form.hasBalcony} onChange={(e)=>setForm({...form, hasBalcony:e.target.checked})} /> Ban công</label>
                </div>
                <div>
                  <Label className="mb-1">Tổng số phòng/bàn</Label>
                  <Input type="number" value={form.totalUnits as any} onChange={(e)=>setForm({...form, totalUnits:Number((e.target as any).value||0)})} />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  {form.category === 'ROOM' ? (
                    <>
                      <Label className="mb-1">Giá cơ bản (VND)</Label>
                      <Input type="number" value={form.basePrice as any} onChange={(e)=>setForm({...form, basePrice:Number((e.target as any).value||0)})} />
                    </>
                  ) : (
                    <>
                      <Label className="mb-1">Đặt cọc</Label>
                      <div className="flex items-center gap-2 mb-2">
                        <input id="requireDeposit" type="checkbox" className="accent-slate-900" checked={requireDeposit} onChange={(e)=>setRequireDeposit(e.target.checked)} />
                        <label htmlFor="requireDeposit" className="text-sm">Yêu cầu tiền cọc</label>
                      </div>
                      {requireDeposit && (
                        <>
                          <Label className="mb-1">Tiền cọc (VND)</Label>
                          <Input type="number" value={form.depositAmount as any} onChange={(e)=>setForm({...form, depositAmount:Number((e.target as any).value||0)})} />
                        </>
                      )}
                    </>
                  )}
                </div>
              </div>
                <Button type="submit" className="focus-visible:ring-2 focus-visible:ring-slate-400">Thêm loại</Button>
            </form>
          )}
          </CardContent>
        </Card>
        <Card className="w-full lg:w-1/2 min-h-[160px]">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Các loại đã tạo</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[60vh] overflow-auto pr-2">
              {types.map((t)=>(
              <Card key={t.id} className="p-3 flex flex-col">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-medium">{t.name} <span className="text-xs text-slate-500">({t.code})</span></div>
                    <div className="text-xs text-slate-600 mt-0.5">{t.category} • {t.capacity} người • {(establishments.find(e=>e.id===t.establishmentId)?.name) || t.establishmentId}</div>
                    <div className="mt-1 flex flex-wrap gap-2 text-xs">
                      <span className={`px-2 py-0.5 rounded-full border ${t.active ? 'bg-green-100 text-green-700 border-green-200':'bg-slate-100 text-slate-700 border-slate-200'}`}>{t.active ? 'Đang bán' : 'Tạm ẩn'}</span>
                      {t.hasBalcony && <span className="px-2 py-0.5 rounded-full border bg-slate-100 text-slate-700 border-slate-200">Ban công</span>}
                      {t.category==='ROOM' ? (
                        <span className="px-2 py-0.5 rounded-full border bg-slate-100 text-slate-700 border-slate-200">{t.basePrice?.toLocaleString()} đ</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full border bg-slate-100 text-slate-700 border-slate-200">Cọc: {t.depositAmount ? t.depositAmount.toLocaleString() + ' đ' : 'Không'}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm shrink-0">
                    <Button variant="outline" size="sm" onClick={()=>{ setExpandedId(expandedId===t.id?null:t.id); ensureEditRow(t) }}>
                      {expandedId===t.id ? 'Ẩn' : 'Sửa'}
                    </Button>
                    <Button variant="outline" size="sm" className="text-red-600" onClick={async()=>{
                      if (!confirm('Xóa loại này?')) return
                      await deleteType(t.id!)
                      setTypes(list=>list.filter(x=>x.id!==t.id))
                    }}>Xóa</Button>
                  </div>
                </div>
                {Array.isArray(t.imageUrls) && t.imageUrls.length>0 && (
                  <div className="mt-2 flex gap-2 overflow-x-auto">
                    {t.imageUrls.slice(0,4).map((u,idx)=>(
                      <div key={idx} className="relative group rounded overflow-hidden w-16 h-16">
                        <img src={u} className="w-full h-full object-cover" />
                        <div className="absolute z-20 hidden group-hover:block left-full ml-2 top-0 w-64 h-40 bg-white shadow-xl rounded overflow-hidden">
                          <img src={u} className="w-full h-full object-cover" />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {expandedId===t.id && (
                            <div className="mt-3 text-sm text-slate-700 grid grid-cols-2 gap-3">
								<div>
                                    <Label className="mb-1">Mã</Label>
                                    <Input value={(edit[t.id!]?.code ?? t.code) || ''}
                                        onChange={(e)=>setField(t.id!, 'code', e.target.value)} />
								</div>
								<div>
                                    <Label className="mb-1">Tên loại</Label>
                                    <Input value={(edit[t.id!]?.name ?? t.name) || ''}
                                        onChange={(e)=>setField(t.id!, 'name', e.target.value)} />
								</div>
								<div>
                                    <Label className="mb-1">Sức chứa</Label>
                                    <Input type="number" value={(edit[t.id!]?.capacity ?? t.capacity) as any}
                                        onChange={(e)=>setField(t.id!, 'capacity', Number((e.target as any).value||0))} />
								</div>
								<div className="flex items-end gap-2">
									<label className="text-sm flex items-center gap-2"><input type="checkbox" checked={!!(edit[t.id!]?.hasBalcony ?? t.hasBalcony)} onChange={(e)=>setField(t.id!, 'hasBalcony', e.target.checked)} /> Ban công</label>
									<label className="text-sm flex items-center gap-2 ml-4"><input type="checkbox" checked={!!(edit[t.id!]?.active ?? t.active)} onChange={(e)=>setField(t.id!, 'active', e.target.checked)} /> Active</label>
								</div>
								<div>
                                    <Label className="mb-1">Tổng số phòng/bàn</Label>
                                    <Input type="number" value={(edit[t.id!]?.totalUnits ?? t.totalUnits) as any}
                                        onChange={(e)=>setField(t.id!, 'totalUnits', Number((e.target as any).value||0))} />
								</div>
								{t.category==='ROOM' && (
									<div>
                                        <Label className="mb-1">Giá cơ bản (VND)</Label>
                                        <Input type="number" value={(edit[t.id!]?.basePrice ?? t.basePrice) as any}
                                            onChange={(e)=>setField(t.id!, 'basePrice', Number((e.target as any).value||0))} />
									</div>
								)}
								{t.category==='TABLE' && (
									<div>
                                        <Label className="mb-1">Tiền cọc (VND)</Label>
                                        <Input type="number" value={(edit[t.id!]?.depositAmount ?? t.depositAmount) as any}
                                            onChange={(e)=>setField(t.id!, 'depositAmount', Number((e.target as any).value||0))} />
									</div>
								)}
								<div className="col-span-2">
                                    <Label className="mb-1">Hình ảnh</Label>
                                    <div className="flex items-center gap-3 mb-2">
                                        <Input type="file" accept="image/*" onChange={async(e:any)=>{ const f=e.target.files?.[0]; if(!f) return; await addImage(t, f); }} />
                                        <Button variant="outline" size="sm" onClick={async()=>{ await onSaveRow(t) }}>Lưu thay đổi</Button>
                                    </div>
                                    {(((edit[t.id!]?.imageUrls) || t.imageUrls || []).length>0) ? (
                                        <div className="grid grid-cols-6 gap-2">
                                            {((edit[t.id!]?.imageUrls) || t.imageUrls || []).map((u,idx)=> (
                                                <div key={idx} className="relative group">
                                                    <img src={u} className="w-full h-20 object-cover rounded" />
                                                    <div className="absolute z-20 hidden group-hover:block left-full ml-2 top-0 w-64 h-40 bg-white shadow-xl rounded overflow-hidden">
                                                      <img src={u} className="w-full h-full object-cover" />
                                                    </div>
                                                    <Button type="button" variant="outline" size="icon" className="absolute top-1 right-1 h-5 w-5 text-[10px] hidden group-hover:flex items-center justify-center" onClick={()=>removeImage(t, idx)}>x</Button>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
										<div className="text-slate-500">Chưa có hình ảnh</div>
									)}
								</div>
							</div>
                )}
              </Card>
            ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


