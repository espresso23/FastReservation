import { useState } from 'react'
import { PaperAirplaneIcon, ArrowPathIcon } from '@heroicons/react/24/solid'
import { confirmBooking, processBooking } from '../api/user'
import type { QuizResponse, Suggestion } from '../api/user'

export default function UserBookingPage() {
  const [prompt, setPrompt] = useState('Tôi muốn đi Đà Nẵng ngày 2025-10-10 2 đêm, có phòng gym')
  const [currentParams, setCurrentParams] = useState<Record<string, any>>({})
  const [quiz, setQuiz] = useState<QuizResponse | null>(null)
  const [suggestions, setSuggestions] = useState<Suggestion[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const [selectedOpt, setSelectedOpt] = useState<string>('')
  const [customOpt, setCustomOpt] = useState<string>('')
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([])
  const [selectedImages, setSelectedImages] = useState<{url:string,label:string,params?:Record<string,any>}[]>([])

  type ChatMessage = { role: 'assistant' | 'user', text: string }
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', text: 'Xin chào! Hãy mô tả ngắn gọn nhu cầu đặt chỗ của bạn.' }
  ])

  // Fallback tag choices nếu BE không gửi options
  const defaultOptions: Record<string, string[]> = {
    establishment_type: ['HOTEL','RESTAURANT'],
    travel_companion: ['single','couple','family','friends','team','business'],
    style_vibe: ['romantic','quiet','lively','luxury','nature','cozy','modern','classic'],
    amenities_priority: [
      'Hồ bơi','Spa','Bãi đậu xe','Gym','Buffet sáng','Gần biển','Wifi','Lễ tân 24/7','Đưa đón sân bay',
      'Pet-friendly','Phòng gia đình','Không hút thuốc','Bồn tắm','View biển','View thành phố','Gần trung tâm',
      'Ban công','Cửa sổ','Giặt là','Thang máy'
    ],
    duration: ['1','2','3','4','5','6','7','8','9','10'],
    has_balcony: ['yes','no'],
    num_guests: ['single','couple','3','4','5','6','7','8','9','10']
  }

  const send = async (override?: { params?: Record<string, any>, prompt?: string, auto?: boolean }) => {
    setLoading(true); setMsg(null)
    try {
      const pmt = (override?.prompt ?? prompt) || ''
      let paramsToSend = override?.params ?? currentParams
      // Client-side quick inference to avoid re-asking basic facts
      const strip = (s:string) => (
        s
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '') // remove accents
          .replace(/đ/g, 'd').replace(/Đ/g, 'd')
          .replace(/[^a-zA-Z0-9\s]/g, ' ') // punctuation to spaces
          .replace(/\s+/g, ' ') // collapse
          .trim()
          .toLowerCase()
      )
      const inferCity = (text:string): string | null => {
        const t = strip(text)
        const pairs: [string, string][] = [
          ['da nang','Đà Nẵng'], ['danang','Đà Nẵng'], ['da-nang','Đà Nẵng'], ['da_nang','Đà Nẵng'], ['dn','Đà Nẵng'],
          ['ha noi','Hà Nội'], ['hanoi','Hà Nội'],
          ['ho chi minh','Hồ Chí Minh'], ['tphcm','Hồ Chí Minh'], ['hcm','Hồ Chí Minh'], ['sai gon','Hồ Chí Minh'], ['saigon','Hồ Chí Minh'],
          ['nha trang','Nha Trang'], ['nhatrang','Nha Trang'],
          ['da lat','Đà Lạt'], ['dalat','Đà Lạt']
        ]
        for (const [alias, disp] of pairs.sort((a,b)=>b[0].length-a[0].length)) {
          if (t.includes(alias)) return disp
        }
        return null
      }
      const inferType = (text:string): 'HOTEL'|'RESTAURANT'|null => {
        const lc = strip(text)
        if (lc.includes('khach san') || lc.includes('hotel')) return 'HOTEL'
        if (lc.includes('nha hang') || lc.includes('restaurant')) return 'RESTAURANT'
        return null
      }
      const parseFromPrompt = (text: string): Record<string, any> => {
        const out: Record<string, any> = {}
        const city = inferCity(text); if (city) out.city = city
        // YYYY-MM-DD
        const dateM = text.match(/(20\d{2}-\d{2}-\d{2})/)
        if (dateM) out.check_in_date = dateM[1]
        // duration: "2 đêm" or "2 ngay"
        const s = strip(text)
        const durM = s.match(/(\d+)\s*(dem|dems|ngay)/)
        if (durM) out.duration = Number(durM[1])
        // amenities and balcony
        const amens: string[] = []
        if (s.includes('gym')) amens.push('Gym')
        if (s.includes('ho boi') || s.includes('hoboi') || s.includes('pool')) amens.push('Hồ bơi')
        if (s.includes('spa')) amens.push('Spa')
        if (s.includes('bai do xe') || s.includes('giu xe') || s.includes('parking')) amens.push('Bãi đậu xe')
        if (s.includes('gan bien') || s.includes('ganbien') || s.includes('beach')) amens.push('Gần biển')
        if (amens.length) out.amenities_priority = amens.join(', ')
        if (s.includes('ban cong')) out.has_balcony = 'yes'
        const t = inferType(text); if (t) out.establishment_type = t
        return out
      }
      // Parse immediately at the very first prompt
      const parsed = parseFromPrompt(pmt)
      if (Object.keys(parsed).length) {
        paramsToSend = { ...paramsToSend, ...parsed }
        setCurrentParams(prev => ({ ...prev, ...parsed }))
      }
      // Fill city/type if missing
      const localCity = (!paramsToSend.city) ? inferCity(pmt) : null
      const localType = (!paramsToSend.establishment_type) ? inferType(pmt) : null
      if (localCity || localType) paramsToSend = { ...paramsToSend }
      if (localCity) paramsToSend.city = localCity
      if (localType) paramsToSend.establishment_type = localType
      // Ghi message user
      if (pmt.trim()) setMessages(prev => [...prev, { role: 'user', text: pmt.trim() }])
      const res = await processBooking({ userPrompt: pmt, currentParams: paramsToSend })
      if (Array.isArray(res)) {
        setSuggestions(res)
        setQuiz(null)
        setMessages(prev => [
          ...prev,
          { role: 'assistant', text: res.length > 0 ? `Mình đã có ${res.length} gợi ý phù hợp, bạn chọn để đặt nhé.` : 'Chưa tìm thấy kết quả phù hợp, bạn có muốn nới tiêu chí không?' }
        ])
      } else {
        setQuiz(res)
        // Đồng bộ tham số: ưu tiên paramsToSend (đã infer localCity/localType) rồi merge final_params từ server
        const mergedParams = { ...paramsToSend, ...(res.final_params || {}) }
        setCurrentParams(mergedParams)
        // Auto-skip if server still asks for a field we already inferred locally
        if (!res.quiz_completed && res.key_to_collect) {
          const k = res.key_to_collect
          if ((k === 'city' && mergedParams.city) || (k === 'establishment_type' && mergedParams.establishment_type)) {
            setTimeout(() => { send({ params: mergedParams, prompt: '', auto: true }) }, 0)
            return
          }
        }
        setSuggestions(null)
        setSelectedOpt('')
        setCustomOpt('')
        setSelectedAmenities([])
        setSelectedImages([])
        if (!res.quiz_completed && res.missing_quiz) {
          setMessages(prev => [...prev, { role: 'assistant', text: res.missing_quiz! }])
        } else if (res.quiz_completed && !override?.auto) {
          const merged = { ...paramsToSend, ...(res.final_params || {}) }
          setTimeout(() => { send({ params: merged, prompt: '', auto: true }) }, 0)
        }
      }
    } finally { setLoading(false) }
  }

  const book = async (s: Suggestion) => {
    setLoading(true); setMsg(null)
    try {
      const payload = {
        userId: 1,
        establishmentId: s.establishmentId,
        bookedItemType: s.itemType || s.floorArea || 'TYPE',
        startDate: currentParams.check_in_date || new Date().toISOString().slice(0,10),
        duration: Number(currentParams.duration || 1),
        totalPriceVnd: s.finalPrice || 0,
        bookedFloorArea: s.floorArea,
        numGuests: Number(currentParams.num_guests || 1)
      }
      await confirmBooking(payload)
      setMsg('Đặt chỗ thành công!')
    } catch (e:any) {
      setMsg(e?.response?.data?.message || 'Đặt chỗ thất bại')
    } finally { setLoading(false) }
  }

  const keyLabel = (k?: string) => {
    switch (k) {
      case 'establishment_type': return 'Loại cơ sở';
      case 'city': return 'Thành phố';
      case 'check_in_date': return 'Ngày nhận';
      case 'duration': return 'Số đêm';
      case 'max_price': return 'Ngân sách tối đa (VND)';
      case 'style_vibe': return 'Phong cách/không gian';
      case 'travel_companion': return 'Đi cùng ai';
      case 'amenities_priority': return 'Tiện ích ưu tiên';
      case 'has_balcony': return 'Có ban công?';
      case 'num_guests': return 'Số người';
      default: return k || ''
    }
  }

  const optionLabel = (key: string, v: string) => {
    if (key === 'establishment_type') {
      if (v.toUpperCase() === 'HOTEL') return 'Khách sạn'
      if (v.toUpperCase() === 'RESTAURANT') return 'Nhà hàng'
    }
    if (key === 'travel_companion') {
      const m: Record<string,string> = { single: 'Một mình', couple: 'Cặp đôi', family: 'Gia đình', friends: 'Bạn bè' }
      return m[v.toLowerCase()] || v
    }
    if (key === 'has_balcony') {
      if ((v || '').toLowerCase() === 'yes') return 'Có'
      if ((v || '').toLowerCase() === 'no') return 'Không'
    }
    return v
  }

  const humanizeValue = (k: string, v: string) => {
    if (k === 'establishment_type') {
      return optionLabel(k, v)
    }
    if (k === 'num_guests') {
      const vv = (v || '').toLowerCase()
      if (vv === 'single') return '1 người'
      if (vv === 'couple') return '2 người'
      const n = Number(vv)
      if (!isNaN(n) && n > 0) return `${n} người`
    }
    if (k === 'has_balcony') {
      if ((v || '').toLowerCase() === 'yes') return 'Có'
      if ((v || '').toLowerCase() === 'no') return 'Không'
    }
    return v
  }

  const renderInputForKey = (k?: string) => {
    if (!k) return null
    if (k === 'check_in_date') return (
      <input type="date" className="border rounded px-2 py-1" value={customOpt} onChange={(e)=>setCustomOpt(e.target.value)} />
    )
    if (k === 'duration' || k === 'max_price' || k === 'num_guests') return (
      <input type="number" className="border rounded px-2 py-1" value={customOpt} onChange={(e)=>setCustomOpt(e.target.value)} />
    )
    return null
  }

  const answerAndNext = async () => {
    const k = quiz?.key_to_collect
    if (!k) return
    let val = ''
    if (k === 'amenities_priority') {
      if (selectedAmenities.length === 0) return
      val = selectedAmenities.join(', ')
    } else if (quiz?.image_options && quiz.image_options.length > 0) {
      // Multi-select images: merge params inferred from selected images
      if (selectedImages.length === 0) return
      const mergedParams: Record<string, any> = {}
      selectedImages.forEach(it => {
        if (it.params) Object.assign(mergedParams, it.params)
      })
      setCurrentParams(prev => ({ ...prev, ...mergedParams }))
      val = selectedImages.map(it=>it.label).join(', ')
    } else if (k === 'duration' || k === 'max_price' || k === 'check_in_date') {
      if (!customOpt.trim()) return
      val = customOpt.trim()
    } else {
      if (!selectedOpt.trim()) return
      val = selectedOpt.trim()
    }

    const nextParams = { ...currentParams, [k]: k==='duration'||k==='max_price' ? Number(val) : val }
    setCurrentParams(nextParams)
    const userText = `Tôi chọn ${keyLabel(k)}: ${humanizeValue(k, val)}`
    setPrompt('')
    await send({ params: nextParams, prompt: userText })
  }

  // Zero-result relax actions
  const relaxAndSearch = async (action: 'more_budget'|'drop_amenities'|'any_style'|'shift_date') => {
    const np = { ...currentParams }
    if (action === 'more_budget') {
      const cur = Number(np.max_price || 0)
      np.max_price = cur > 0 ? Math.round(cur * 1.2) : 1000000
    }
    if (action === 'drop_amenities') {
      delete np.amenities_priority
    }
    if (action === 'any_style') {
      delete np.style_vibe
    }
    if (action === 'shift_date') {
      try {
        const d = new Date(np.check_in_date)
        d.setDate(d.getDate() + 1)
        np.check_in_date = d.toISOString().slice(0,10)
      } catch {}
    }
    setCurrentParams(np)
    await send({ params: np, prompt: 'Hãy mở rộng tiêu chí giúp mình' })
  }

  const moreSuggestions = async () => {
    await send({ params: currentParams, prompt: 'Cho mình gợi ý khác', auto: true })
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Trợ lý đặt chỗ</h1>
      {/* Chat window */}
      <div className="rounded-2xl border bg-white/90 backdrop-blur card p-4 h-[560px] overflow-auto shadow-sm">
        <div className="space-y-3">
          {messages.map((m,idx)=> (
            <div key={idx} className={`flex items-end gap-2 ${m.role==='user'?'justify-end':''} chat-anim`}>
              {m.role==='assistant' && (
                <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-[10px] font-medium text-slate-700 shrink-0">AI</div>
              )}
              <div className={`${m.role==='user'?'bg-slate-900 text-white':'bg-slate-100 text-slate-900'} px-3 py-2 rounded-2xl max-w-[78%] shadow-sm transition-all duration-300`}>{m.text}</div>
              {m.role==='user' && (
                <div className="w-7 h-7 rounded-full bg-slate-900 text-white flex items-center justify-center text-[10px] font-medium shrink-0">U</div>
              )}
            </div>
          ))}
          {/* Typing indicator */}
          {loading && (!quiz || !quiz.quiz_completed) && (
            <div className="flex items-end gap-2 chat-anim">
              <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-[10px] font-medium text-slate-700 shrink-0">AI</div>
              <div className="bg-slate-100 text-slate-900 px-3 py-2 rounded-2xl shadow-sm inline-flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.2s]"></span>
                <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce"></span>
                <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:0.2s]"></span>
              </div>
            </div>
          )}
          {/* When a quiz step comes, render choices as chips/images in the chat */}
          {quiz && !quiz.quiz_completed && (
            <div className="flex items-start gap-2 chat-anim">
              <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-[10px] font-medium text-slate-700 shrink-0">AI</div>
              <div className="bg-slate-50 border px-3 py-2 rounded-2xl w-full relative">
                {/* Heading */}
                <div className="mb-2">
                  <div className="text-sm font-medium text-slate-800">{keyLabel(quiz.key_to_collect)}</div>
                  <div className="text-xs text-slate-500">Chọn một trong các gợi ý bên dưới hoặc nhập thủ công.</div>
                </div>
                {/* Options as images */}
                {quiz.image_options && quiz.image_options.length > 0 && (
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {quiz.image_options.map((opt,i)=> {
                      const on = selectedImages.some(x=>x.url===opt.image_url)
                      return (
                      <button key={i} type="button" onClick={()=>{
                        setSelectedOpt(opt.value); setCustomOpt(opt.value);
                        setSelectedImages(prev => on ? prev.filter(x=>x.url!==opt.image_url) : [...prev, { url: opt.image_url, label: opt.label, params: (opt as any).params }])
                      }} className={`group border rounded overflow-hidden text-left ${on? 'ring-2 ring-slate-900' : ''}`}>
                        <div className="aspect-video bg-slate-100 overflow-hidden">
                          <img src={opt.image_url} alt={opt.label} className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform" />
                        </div>
                        <div className="p-2 text-sm">{opt.label}</div>
                      </button>
                      )
                    })}
                  </div>
                )}
                {/* Options as selectable chips (single-select) */}
                {!quiz.image_options && quiz.key_to_collect !== 'amenities_priority' && (
                  <div className="flex flex-wrap gap-2">
                    {(quiz.options && quiz.options.length>0 ? quiz.options : (defaultOptions[quiz.key_to_collect as string]||[])).map((o,i)=> (
                      <button key={i} type="button" onClick={()=>{ setSelectedOpt(o); setCustomOpt(o); }} className={`inline-flex items-center gap-1.5 px-3 py-1.5 border rounded-full text-sm chip shadow-sm ${selectedOpt===o?'bg-slate-900 text-white border-slate-900':'bg-white hover:bg-slate-50'}`}>{optionLabel(quiz.key_to_collect as string, o)}</button>
                    ))}
                  </div>
                )}
                {/* Amenities as multi-select tags */}
                {quiz.key_to_collect === 'amenities_priority' && (
                  <div className="flex flex-wrap gap-2">
                    {((quiz.options && quiz.options.length>0) ? quiz.options : (defaultOptions['amenities_priority']||[])).map((o,i)=> {
                      const on = selectedAmenities.includes(o)
                      return (
                        <button key={i} type="button" onClick={()=>{
                          setSelectedAmenities(prev => on ? prev.filter(x=>x!==o) : [...prev, o])
                        }} className={`inline-flex items-center gap-1.5 px-3 py-1.5 border rounded-full text-sm chip shadow-sm ${on?'bg-slate-900 text-white border-slate-900':'bg-white hover:bg-slate-50'}`}>{o}</button>
                      )
                    })}
                  </div>
                )}
                {/* Inputs only for date/price/duration */}
                {renderInputForKey(quiz.key_to_collect)}
                {/* Submit button pinned bottom-right */}
                <button className="absolute right-2 bottom-2 h-9 w-9 rounded-full bg-slate-900 text-white flex items-center justify-center hover:brightness-110 transition disabled:opacity-50" onClick={answerAndNext} disabled={loading} title="Gửi">
                  <PaperAirplaneIcon className="w-4 h-4" />
                </button>
                {/* Collected params summary as inline chips */}
                <div className="mt-3 flex flex-wrap gap-2 text-xs pr-12">
                  {Object.entries(currentParams).map(([k,v])=> (
                    <span key={k} className="px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200 chip shadow-sm">{keyLabel(k)}: {String(v)}</span>
                  ))}
                </div>
                {/* Selected thumbnails history */}
                {selectedImages.length>0 && (
                  <div className="mt-3 flex gap-2">
                    {selectedImages.map((it,idx)=>(
                      <img key={idx} src={it.url} alt={it.label} className="w-16 h-16 object-cover rounded" />
                    ))}
                  </div>
                )}
              </div>
              <div className="w-7 h-7" />
            </div>
          )}

          {/* Suggestions as assistant bubble inside chat */}
          {suggestions && (
            <div className="flex items-start gap-2 chat-anim">
              <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-[10px] font-medium text-slate-700 shrink-0">AI</div>
              <div className="bg-slate-50 border px-3 py-2 rounded-2xl w-full">
                <div className="text-sm font-medium text-slate-800 mb-2">
                  {suggestions.length > 0 ? `Mình có ${suggestions.length} gợi ý dành cho bạn:` : 'Chưa tìm thấy kết quả phù hợp.'}
                </div>
                {suggestions.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {suggestions.map(s => (
                      <div key={s.establishmentId + (s.itemType||'')} className="border rounded overflow-hidden bg-white card">
                        {s.itemImageUrl || s.imageUrlMain ? (
                          <div className="aspect-video bg-slate-100">
                            <img src={s.itemImageUrl || s.imageUrlMain!} className="w-full h-full object-cover" />
                          </div>
                        ) : null}
                        <div className="p-3">
                          <div className="font-medium">{s.establishmentName}</div>
                          <div className="text-sm text-slate-600">{s.city}</div>
                          <div className="mt-1 text-sm">Loại: <span className="font-medium">{s.itemType || s.floorArea}</span></div>
                          <div className="text-sm">Giá: {s.finalPrice?.toLocaleString()} đ</div>
                          <div className="text-xs text-slate-600">Còn: {s.unitsAvailable}</div>
                          <div className="mt-2 flex items-center gap-2">
                            <button className="px-3 py-1 border rounded" onClick={()=>book(s)} disabled={loading}>Book ngay</button>
                            <a className="px-3 py-1 border rounded" href={`/establishments/${s.establishmentId}`} target="_blank" rel="noreferrer">Xem chi tiết</a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}
                {suggestions.length > 0 ? (
                  <div className="mt-3 text-sm">
                    <div className="text-slate-700 mb-2">Bạn có muốn xem gợi ý khác hoặc tinh chỉnh tiêu chí?</div>
                    <div className="flex flex-wrap gap-2">
                      <button className="px-3 py-1.5 border rounded-full" onClick={moreSuggestions}>Gợi ý khác</button>
                      <button className="px-3 py-1.5 border rounded-full" onClick={()=>relaxAndSearch('more_budget')}>Tăng ngân sách +20%</button>
                      <button className="px-3 py-1.5 border rounded-full" onClick={()=>relaxAndSearch('drop_amenities')}>Bỏ lọc tiện ích</button>
                      <button className="px-3 py-1.5 border rounded-full" onClick={()=>relaxAndSearch('shift_date')}>Lùi/ngày khác</button>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-slate-700">
                    Hãy nới tiêu chí tìm kiếm một chút nhé:
                    <div className="mt-2 flex flex-wrap gap-2">
                      <button className="px-2 py-1 border rounded-full" onClick={()=>relaxAndSearch('more_budget')}>Tăng ngân sách +20%</button>
                      <button className="px-2 py-1 border rounded-full" onClick={()=>relaxAndSearch('drop_amenities')}>Bỏ lọc tiện ích</button>
                      <button className="px-2 py-1 border rounded-full" onClick={()=>relaxAndSearch('any_style')}>Bất kỳ phong cách</button>
                      <button className="px-2 py-1 border rounded-full" onClick={()=>relaxAndSearch('shift_date')}>Lùi/ngày khác</button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input bar: chỉ hiển thị khi chưa vào quiz, hoặc quiz đã hoàn thành */}
      {(!quiz || quiz.quiz_completed) && (
        <div className="mt-3">
          <div className="relative">
            <input
              className="w-full border rounded-full px-4 py-3 pr-12 shadow-sm"
              placeholder="Nhập yêu cầu..."
              value={prompt}
              onChange={(e)=>setPrompt(e.target.value)}
              onKeyDown={(e)=>{ if (e.key==='Enter' && !e.shiftKey && !loading) { e.preventDefault(); send() } }}
            />
            <button
              className="absolute right-1.5 top-1/2 -translate-y-1/2 h-9 w-9 rounded-full bg-slate-900 text-white flex items-center justify-center hover:brightness-110 transition disabled:opacity-50"
              onClick={()=>send()}
              disabled={loading}
              title="Gửi"
            >
              <PaperAirplaneIcon className="w-4 h-4" />
            </button>
          </div>
          <div className="mt-2 flex items-center gap-2">
            {loading && <ArrowPathIcon className="w-4 h-4 animate-spin text-slate-500" />}
            {msg && <span className="text-green-700">{msg}</span>}
          </div>
        </div>
      )}

      {quiz && quiz.quiz_completed && (
        <div className="mt-4 rounded-2xl border p-3 bg-white">
          <div className="font-medium mb-2">Tham số cuối</div>
          <pre className="text-xs bg-slate-50 p-2 rounded overflow-auto">{JSON.stringify(quiz.final_params, null, 2)}</pre>
          <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
            <input className="border rounded px-2 py-1" placeholder="Thành phố" value={currentParams.city||''} onChange={(e)=>setCurrentParams({ ...currentParams, city: e.target.value })} />
            <input type="date" className="border rounded px-2 py-1" value={currentParams.check_in_date||''} onChange={(e)=>setCurrentParams({ ...currentParams, check_in_date: e.target.value })} />
            <input type="number" className="border rounded px-2 py-1" placeholder="Số đêm" value={currentParams.duration||''} onChange={(e)=>setCurrentParams({ ...currentParams, duration: Number(e.target.value||0) })} />
            <input type="number" className="border rounded px-2 py-1" placeholder="Ngân sách tối đa" value={currentParams.max_price||''} onChange={(e)=>setCurrentParams({ ...currentParams, max_price: Number(e.target.value||0) })} />
          </div>
          <div className="mt-2">
            <button className="px-3 py-1 border rounded" onClick={()=>{ setPrompt(''); send({ params: currentParams, prompt: '' }) }} disabled={loading}>Tìm gợi ý</button>
          </div>
        </div>
      )}

      
    </div>
  )
}


