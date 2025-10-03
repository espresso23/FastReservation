import { useState } from 'react'
import { ArrowPathIcon } from '@heroicons/react/24/solid'
import { confirmBooking, processBooking } from '../api/user'
import type { QuizResponse, Suggestion } from '../api/user'
import { Button } from '../components/ui/button'
import { DatePicker } from '../components/ui/calendar'
import { Input } from '../components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Avatar, AvatarFallback } from '../components/ui/avatar'
import { Label } from '../components/ui/label'
import { Send, Bot, User, Sparkles } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'

// Import utilities
import {
  // Agent API
  callAgentChat,
  convertAgentResultsToSuggestions,
  createSessionId,
  updateUserProfileFromAgent,
  buildAgentContext,
  type AgentChatRequest,
  
  // Text processing
  parseParametersFromPrompt,
  humanizeParameterValue,
  getParameterLabel,
  
  // Option labels
  defaultOptions,
  priceRangeOptions,
  getOptionLabel,
  getRelevanceScoreColor,
  getRelevanceScoreLabel,
  
  // Validation (for future use)
  // validateBookingParams,
  // sanitizeInput
} from '../utils'

export default function UserBookingPage() {
  const { user } = useAuth()
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

  // Agent system state
  const [sessionId] = useState(createSessionId)
  const [userProfile, setUserProfile] = useState<AgentChatRequest['user_profile']>({
    preferences: {},
    history: [],
    preferred_cities: [],
    preferred_amenities: [],
    travel_companion: undefined
  })
  const [agentMode, setAgentMode] = useState<'quiz' | 'agent'>('quiz') // Toggle between old quiz and new agent

  type ChatMessage = { role: 'assistant' | 'user', text: string, timestamp?: Date }
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', text: 'Xin chào! Tôi là trợ lý AI thông minh. Hãy mô tả nhu cầu đặt chỗ của bạn, tôi sẽ tìm kiếm và đề xuất những lựa chọn tốt nhất.', timestamp: new Date() }
  ])
  // Ghi nhớ các key đã hỏi để giảm hỏi lặp
  const [askedKeys, setAskedKeys] = useState<Set<string>>(new Set())



  const send = async (override?: { params?: Record<string, any>, prompt?: string, auto?: boolean, mode?: 'quiz' | 'agent' }) => {
    setLoading(true); setMsg(null)
    try {
      const pmt = (override?.prompt ?? prompt) || ''
      let paramsToSend = override?.params ?? currentParams
      let userMsgAppended = false
      const useMode = override?.mode || agentMode

      // Agent mode - direct conversation
      if (useMode === 'agent') {
        if (pmt.trim() && !userMsgAppended) {
          setMessages(prev => [...prev, { role: 'user', text: pmt.trim(), timestamp: new Date() }])
          userMsgAppended = true
        }

        try {
          const agentResponse = await callAgentChat(pmt, sessionId, userProfile, buildAgentContext(paramsToSend))
          
          if (agentResponse.success && agentResponse.results.length > 0) {
            // Convert agent results to suggestions
            const convertedSuggestions = convertAgentResultsToSuggestions(agentResponse.results)
            setSuggestions(convertedSuggestions)
            setQuiz(null)
            
            // Add agent response to chat
            setMessages(prev => [
              ...prev,
              { 
                role: 'assistant', 
                text: agentResponse.explanation || `Tôi đã tìm thấy ${agentResponse.results.length} lựa chọn phù hợp với yêu cầu của bạn.`,
                timestamp: new Date()
              }
            ])
          } else {
            // No results or unsuccessful
            setSuggestions([])
            setQuiz(null)
            setMessages(prev => [
              ...prev,
              { 
                role: 'assistant', 
                text: agentResponse.explanation || 'Tôi chưa tìm thấy kết quả phù hợp. Bạn có thể thử mô tả chi tiết hơn hoặc nới lỏng một số tiêu chí.',
                timestamp: new Date()
              }
            ])
          }

          // Update user profile if agent provided insights
          if (agentResponse.metadata?.user_insights) {
            setUserProfile(prev => updateUserProfileFromAgent(prev, agentResponse.metadata))
          }

          return
        } catch (error) {
          console.error('Agent API error:', error)
          // Fallback to quiz mode on agent error
          setMessages(prev => [
            ...prev,
            { 
              role: 'assistant', 
              text: 'Hệ thống AI đang gặp sự cố. Tôi sẽ chuyển sang chế độ hỏi đáp truyền thống để hỗ trợ bạn.',
              timestamp: new Date()
            }
          ])
          setAgentMode('quiz')
        }
      }
      
      // Reset state if user is starting a new search (not auto-skip)
      if (!override?.auto && pmt.trim() && ((quiz && quiz.quiz_completed) || (suggestions && suggestions.length >= 0))) {
        // User is starting a new search, reset everything
        setQuiz(null)
        setSuggestions(null)
        setCurrentParams({})
        setSelectedOpt('')
        setCustomOpt('')
        setSelectedAmenities([])
        setSelectedImages([])
        setMessages(prev => [...prev, 
          { role: 'user', text: pmt },
          { role: 'assistant', text: 'Tôi hiểu bạn muốn tìm kiếm mới. Hãy để tôi hỗ trợ bạn!' }
        ])
        userMsgAppended = true
        setPrompt('') // Clear input field
        paramsToSend = {}
      } else if (!override?.auto && pmt.trim()) {
        // Add user message to chat for normal interactions
        setMessages(prev => [...prev, { role: 'user', text: pmt }])
        userMsgAppended = true
      }
      // Parse immediately at the very first prompt
      const parsed = parseParametersFromPrompt(pmt)
      if (Object.keys(parsed).length) {
        paramsToSend = { ...paramsToSend, ...parsed }
        setCurrentParams(prev => ({ ...prev, ...parsed }))
      }
      // Tránh nhân đôi tin nhắn người dùng
      if (pmt.trim() && !userMsgAppended) {
        setMessages(prev => [...prev, { role: 'user', text: pmt.trim() }])
      }
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
        // FE fallback: nếu đã có amenities nhưng chưa xác nhận, cưỡng chế hỏi 1 lần để tránh bị bỏ qua
        const needAmenConfirm = !!mergedParams.amenities_priority && !mergedParams._amenities_confirmed && (
          res.quiz_completed || (res.key_to_collect && res.key_to_collect !== 'amenities_priority')
        )
        if (needAmenConfirm) {
          setQuiz({
            quiz_completed: false,
            key_to_collect: 'amenities_priority'
          } as any)
          setMessages(prev => [...prev, { role: 'assistant', text: 'Bạn có muốn chọn thêm tiện ích không? (bạn có thể bỏ qua nếu đủ)' }])
          return
        }
        // Auto-skip nếu server hỏi lại trường đã có trong mergedParams (giảm hỏi lặp)
        if (!res.quiz_completed && res.key_to_collect) {
          const k = res.key_to_collect as string
          const val = (mergedParams as any)[k]
          // Đừng auto-skip khi đang ở bước tiện ích và chưa xác nhận xong
          const awaitingAmenitiesConfirm = (k === 'amenities_priority') && !(mergedParams as any)._amenities_confirmed
          if (!awaitingAmenitiesConfirm && val !== undefined && val !== null && String(val).trim() !== '') {
            setTimeout(() => { send({ params: mergedParams, prompt: '', auto: true }) }, 0)
            return
          }
          // nếu key đã hỏi trước đó và không có giá trị mới, tránh lặp vô hạn
          if (askedKeys.has(k)) {
            // Đã hỏi rồi mà vẫn thiếu -> dừng auto để người dùng nhập, tránh loop
            // Không auto gọi lại.
          } else {
            setAskedKeys(prev => new Set(prev).add(k))
          }
        }
        setSuggestions(null)
        setSelectedOpt('')
        setCustomOpt('')
        // Không xoá lựa chọn tiện ích tạm thời khi vẫn còn ở bước tiện ích
        if (res.key_to_collect !== 'amenities_priority') {
          setSelectedAmenities([])
        }
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
        userId: user?.id ? Number(user.id) : 1,
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


  const renderInputForKey = (k?: string) => {
    if (!k) return null
    if (k === 'check_in_date') {
      // Khi đang ở bước quiz hỏi ngày, luôn cho phép chọn khoảng ngày (đến & đi)
      const isQuizStep = !!quiz && !quiz.quiz_completed
      const hasStart = !!currentParams.check_in_date
      const allowRange = isQuizStep && !currentParams.check_out_date
      return (
        <div className="w-full">
          <DatePicker
            value={hasStart && customOpt ? new Date(customOpt) : undefined}
            onChange={(d:any)=>{
              if (d && d.from && d.to) {
                // range được chọn: set check_in_date và duration
                const from = d.from as Date
                const to = d.to as Date
                const isoFrom = new Date(from.getTime()-from.getTimezoneOffset()*60000).toISOString().slice(0,10)
                const dayMs = 24*60*60*1000
                const nights = Math.max(1, Math.round((to.getTime()-from.getTime())/dayMs))
                setCustomOpt(isoFrom)
                setCurrentParams(prev => ({ ...prev, check_in_date: isoFrom, duration: nights }))
              } else if (d instanceof Date) {
                const iso = new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10)
                setCustomOpt(iso)
              }
            }}
            trigger="icon"
            ariaLabel="Chọn ngày"
            range={allowRange || !hasStart}
          />
        </div>
      )
    }
    if (k === 'duration' || k === 'max_price' || k === 'num_guests') return (
      <Input type="number" className="h-10" value={customOpt} onChange={(e:any)=>setCustomOpt(e.target.value)} />
    )
    if (k === 'travel_companion') return (
      <Input type="number" className="h-10" placeholder="Nhập số người (vd: 2)" value={customOpt} onChange={(e:any)=>setCustomOpt(e.target.value)} />
    )
    if (k === 'city') return (
      <Input type="text" className="h-10" placeholder="Nhập tên thành phố (ví dụ: Đà Nẵng)" value={customOpt} onChange={(e:any)=>setCustomOpt(e.target.value)} />
    )
    return null
  }

  const answerAndNext = async () => {
    const k = quiz?.key_to_collect
    if (!k) return
    let val = ''
    if (k === 'amenities_priority') {
      if (selectedAmenities.length === 0) return
      // Merge với các tiện ích đã có để tránh ghi đè (unique, giữ thứ tự: cũ trước, mới sau)
      const existingRaw = String(currentParams.amenities_priority || '')
      const existingList = existingRaw
        .split(',')
        .map(s => s.trim())
        .filter(Boolean)
      const addList = selectedAmenities.map(s => s.trim()).filter(Boolean)
      const seen = new Set<string>()
      const mergedList: string[] = []
      for (const x of [...existingList, ...addList]) {
        const key = x.toLowerCase()
        if (!seen.has(key)) { seen.add(key); mergedList.push(x) }
      }
      val = mergedList.join(', ')
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
      // Cho phép nhập tay cho travel_companion/city
      if ((k === 'travel_companion' || k==='city') && customOpt.trim()) {
      val = customOpt.trim()
    } else {
      if (!selectedOpt.trim()) return
      val = selectedOpt.trim()
      }
    }

    // Tạo params kế tiếp; nếu người dùng vừa gửi tiện ích thì coi như đã xác nhận (_amenities_confirmed=true)
    const extra: Record<string, any> = {}
    if (k === 'amenities_priority') {
      extra._amenities_confirmed = true
    }
    const nextParams = { ...currentParams, ...extra, [k]: k==='duration'||k==='max_price' ? Number(val) : val }
    setCurrentParams(nextParams)
    // Tùy biến câu trả lời hiển thị cho bước ngày: nêu rõ ngày đến và số đêm
    let userText = `Tôi chọn ${getParameterLabel(k)}: ${humanizeParameterValue(k, val)}`
    if (k === 'check_in_date') {
      const nights = Number(nextParams.duration || 0)
      if (!isNaN(nights) && nights > 0) {
        userText = `Tôi chọn ngày đến: ${nextParams.check_in_date} và ở lại ${nights} đêm`
      }
    }
    setPrompt('')
    await send({ params: nextParams, prompt: userText })
  }

  // Zero-result relax actions
  const relaxAndSearch = async (action: 'more_budget'|'drop_amenities'|'shift_date') => {
    const np = { ...currentParams }
    if (action === 'more_budget') {
      const cur = Number(np.max_price || 0)
      np.max_price = cur > 0 ? Math.round(cur * 1.2) : 1000000
    }
    if (action === 'drop_amenities') {
      delete np.amenities_priority
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
    <div className="h-screen flex flex-col bg-white overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 p-6 border-b border-gray-200 bg-white">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Trợ lý đặt chỗ AI</h1>
          <p className="text-gray-600 text-sm">Hãy mô tả nhu cầu của bạn, tôi sẽ giúp bạn tìm chỗ phù hợp nhất</p>
          
          {/* Mode Toggle */}
          <div className="mt-4 flex justify-center">
            <div className="bg-gray-100 rounded-lg p-1 flex gap-1">
              <Button
                variant={agentMode === 'quiz' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => {
                  setAgentMode('quiz')
                  // Reset state when switching modes
                  setQuiz(null)
                  setSuggestions(null)
                  setCurrentParams({})
                  setSelectedOpt('')
                  setCustomOpt('')
                  setSelectedAmenities([])
                  setSelectedImages([])
                  setMessages(prev => [...prev, { 
                    role: 'assistant', 
                    text: 'Đã chuyển sang chế độ hỏi đáp. Tôi sẽ hỏi bạn từng bước để hiểu rõ nhu cầu.',
                    timestamp: new Date()
                  }])
                }}
                className={`px-4 py-2 text-sm ${agentMode === 'quiz' ? 'bg-white shadow-sm' : 'hover:bg-gray-50'}`}
              >
                📋 Chế độ Quiz
              </Button>
              <Button
                variant={agentMode === 'agent' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => {
                  setAgentMode('agent')
                  // Reset state when switching modes
                  setQuiz(null)
                  setSuggestions(null)
                  setCurrentParams({})
                  setSelectedOpt('')
                  setCustomOpt('')
                  setSelectedAmenities([])
                  setSelectedImages([])
                  setMessages(prev => [...prev, { 
                    role: 'assistant', 
                    text: 'Đã chuyển sang chế độ AI thông minh. Bạn có thể nói chuyện tự nhiên, tôi sẽ hiểu và tìm kiếm ngay.',
                    timestamp: new Date()
                  }])
                }}
                className={`px-4 py-2 text-sm ${agentMode === 'agent' ? 'bg-white shadow-sm' : 'hover:bg-gray-50'}`}
              >
                🤖 AI Thông minh
              </Button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Chat window - fixed height, only this area scrolls */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <Card className="flex-1 m-6 overflow-hidden border border-gray-200 shadow-sm">
          <CardContent className="p-0 h-full">
            <div className="h-full overflow-y-auto p-4 space-y-4 bg-gray-50" aria-live="polite" aria-relevant="additions" role="log">
            {messages.map((m,idx)=> (
              <div key={idx} className={`flex items-end gap-3 ${m.role==='user'?'justify-end':''} transition-all duration-300 ease-out`}>
                {m.role==='assistant' && (
                  <Avatar className="w-8 h-8 shrink-0">
                    <AvatarFallback className="bg-gray-100 text-gray-600 border border-gray-200">
                      <Bot className="w-4 h-4" />
                    </AvatarFallback>
                  </Avatar>
                )}
                <div className={`${m.role==='user'?'bg-gray-900 text-white':'bg-white text-gray-900 border border-gray-200'} px-4 py-3 rounded-2xl max-w-[80%] shadow-sm transition-all duration-300 ease-out`}>
                  {m.text}
                </div>
                {m.role==='user' && (
                  <Avatar className="w-8 h-8 shrink-0">
                    <AvatarFallback className="bg-gray-900 text-white">
                      <User className="w-4 h-4" />
                    </AvatarFallback>
                  </Avatar>
                )}
              </div>
            ))}
            {/* When a quiz step comes, render choices as chips/images in the chat */}
            {quiz && !quiz.quiz_completed && (
              <div className="flex items-start gap-3 transition-all duration-300 ease-out">
                <Avatar className="w-8 h-8 shrink-0">
                  <AvatarFallback className="bg-gray-100 text-gray-600 border border-gray-200">
                    <Bot className="w-4 h-4" />
                  </AvatarFallback>
                </Avatar>
                <Card className="w-full border border-gray-200 shadow-sm transition-all duration-300 ease-out">
                  <CardContent className="p-4 bg-white">
                    {/* Heading */}
                    <div className="mb-4">
                      <CardTitle className="text-lg text-gray-900 mb-1">{getParameterLabel(quiz.key_to_collect)}</CardTitle>
                      <CardDescription className="text-gray-600">Chọn một trong các gợi ý bên dưới hoặc nhập thủ công.</CardDescription>
                    </div>
                    {/* Options as images */}
                    {quiz.image_options && quiz.image_options.length > 0 && (
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                        {quiz.image_options.map((opt,i)=> {
                          const on = selectedImages.some(x=>x.url===opt.image_url)
                          return (
                          <Button key={i} variant={on ? "default" : "outline"} className="p-0 h-auto flex flex-col border-gray-200 transition-all duration-300 ease-out" onClick={()=>{
                            setSelectedOpt(opt.value); setCustomOpt(opt.value);
                            setSelectedImages(prev => on ? prev.filter(x=>x.url!==opt.image_url) : [...prev, { url: opt.image_url, label: opt.label, params: (opt as any).params }])
                          }}>
                            <div className="aspect-video bg-gray-100 overflow-hidden rounded-t-md">
                              <img src={opt.image_url} alt={opt.label} className="w-full h-full object-cover transition-transform duration-300 ease-out group-hover:scale-[1.02]" />
                            </div>
                            <div className="p-2 text-xs font-medium text-gray-700">{opt.label}</div>
                          </Button>
                          )
                        })}
                      </div>
                    )}
                    {/* Options as selectable chips (single-select) */}
                    {/* Chỉ hiển thị chips khi BE cung cấp options rõ ràng hoặc key travel_companion (có preset) */}
                    {!quiz.image_options && quiz.key_to_collect !== 'amenities_priority' && (
                      <div className="flex flex-wrap gap-2 mb-4">
                        {(
                          (Array.isArray(quiz.options) && quiz.options.length>0)
                            ? quiz.options
                            : (
                                quiz.key_to_collect==='travel_companion'
                                  ? defaultOptions['travel_companion']
                                  : (quiz.key_to_collect==='establishment_type' ? defaultOptions['establishment_type'] : [])
                              )
                        ).map((o,i)=> (
                          <Button key={i} variant={selectedOpt===o ? "default" : "outline"} size="sm" className="border-gray-200 transition-all duration-200 ease-out focus-visible:ring-2 focus-visible:ring-gray-300" onClick={()=>{ 
                            setSelectedOpt(o); 
                            if ((quiz.key_to_collect as string) === 'travel_companion') {
                              const lc = (o||'').toLowerCase();
                              const mapped = lc==='single' ? '1' : lc==='couple' ? '2' : o;
                              setCustomOpt(mapped);
                            } else {
                              setCustomOpt(o);
                            }
                          }}>
                            {getOptionLabel(quiz.key_to_collect as string, o)}
                          </Button>
                        ))}
                      </div>
                    )}
                    {/* Quick price chips for max_price */}
                    {quiz.key_to_collect === 'max_price' && (
                      <div className="flex flex-wrap gap-2 mb-4">
                        {priceRangeOptions.map((p, i) => (
                          <Button
                            key={`pr-${i}`}
                            variant={Number(customOpt)===p.value ? 'default' : 'outline'}
                            size="sm"
                            className="border-gray-200"
                            onClick={() => { setSelectedOpt(String(p.value)); setCustomOpt(String(p.value)); }}
                          >
                            {p.label}
                          </Button>
                        ))}
                      </div>
                    )}
                    {/* Amenities as multi-select tags */}
                    {quiz.key_to_collect === 'amenities_priority' && (
                      <div className="flex flex-wrap gap-2 mb-4">
                        {((quiz.options && quiz.options.length>0) ? quiz.options : (defaultOptions['amenities_priority']||[])).map((o,i)=> {
                          const on = selectedAmenities.includes(o)
                          return (
                            <Button
                              key={i}
                              aria-pressed={on}
                              variant={on ? "default" : "outline"}
                              size="sm"
                              className={`${on ? 'ring-2 ring-gray-300 shadow-sm scale-[1.02]' : 'hover:bg-gray-50'} border-gray-200 transition-all duration-200 ease-out active:scale-95 focus-visible:ring-2 focus-visible:ring-gray-300`}
                              onClick={()=>{
                              setSelectedAmenities(prev => on ? prev.filter(x=>x!==o) : [...prev, o])
                              }}
                            >
                              {o}
                            </Button>
                          )
                        })}
                      </div>
                    )}
                {/* Inputs only for date/price/duration */}
                {renderInputForKey(quiz.key_to_collect)}
                    {/* Submit / Skip buttons */}
                    <div className="flex justify-end gap-2">
                      {quiz.key_to_collect === 'amenities_priority' && (currentParams.amenities_priority || (quiz.missing_quiz && quiz.missing_quiz.includes('chọn thêm')) ) && (
                        <Button variant="outline" className="border-gray-200 transition-colors duration-200" onClick={()=>{
                          const np = { ...currentParams, _amenities_confirmed: true }
                          setCurrentParams(np)
                          send({ params: np, prompt: 'Bỏ qua chọn thêm tiện ích', auto: true })
                        }}>Bỏ qua</Button>
                      )}
                      <Button onClick={answerAndNext} disabled={loading} size="sm" className="bg-gray-900 hover:bg-gray-800 text-white transition-colors duration-200">
                        <Send className="w-4 h-4 mr-2" />
                        Gửi
                      </Button>
                    </div>
                    {/* Collected params summary as inline chips */}
                    <div className="mt-4 flex flex-wrap gap-2">
                      {Object.entries(currentParams).map(([k,v])=> (
                        <Badge key={k} variant="secondary" className="text-xs bg-gray-100 text-gray-700 border border-gray-200">
                          {getParameterLabel(k)}: {humanizeParameterValue(k, String(v))}
                        </Badge>
                      ))}
                    </div>
                    {/* Selected thumbnails history */}
                    {selectedImages.length>0 && (
                      <div className="mt-4 flex gap-2">
                        {selectedImages.map((it,idx)=>(
                          <img key={idx} src={it.url} alt={it.label} className="w-16 h-16 object-cover rounded-md border border-gray-200" />
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
            {/* Typing indicator moved below quiz to avoid covering */}
            {loading && (!quiz || !quiz.quiz_completed) && (
              <div className="flex items-end gap-3 transition-all duration-300 ease-out">
                <Avatar className="w-8 h-8 shrink-0">
                  <AvatarFallback className="bg-gray-100 text-gray-600 border border-gray-200">
                    <Bot className="w-4 h-4" />
                  </AvatarFallback>
                </Avatar>
                <div className="bg-white text-gray-900 border border-gray-200 px-4 py-3 rounded-2xl shadow-sm inline-flex items-center gap-2 transition-all duration-300 ease-out">
                  <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:-0.2s]"></span>
                  <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></span>
                  <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0.2s]"></span>
                </div>
              </div>
            )}

          {/* Suggestions as assistant bubble inside chat - show up to 3 cards, responsive */}
          {suggestions && (
            <div className="flex items-start gap-2 transition-all duration-300 ease-out">
              <div className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-[10px] font-medium text-gray-700 shrink-0">AI</div>
              <div className="bg-white border border-gray-200 px-3 py-2 rounded-2xl w-full">
                <div className="text-sm font-medium text-gray-900 mb-2">
                  {suggestions.length > 0 ? `Mình có ${suggestions.length} gợi ý dành cho bạn:` : 'Chưa tìm thấy kết quả phù hợp.'}
                </div>
                
                {/* Agent mode info */}
                {agentMode === 'agent' && suggestions.length > 0 && (suggestions[0] as any).relevanceScore && (
                  <div className="mb-2 flex gap-2 text-xs text-gray-500">
                    <Badge variant="outline" className={`text-xs ${getRelevanceScoreColor((suggestions[0] as any).relevanceScore)}`}>
                      {getRelevanceScoreLabel((suggestions[0] as any).relevanceScore)}: {Math.round((suggestions[0] as any).relevanceScore * 100)}%
                    </Badge>
                  </div>
                )}
                {suggestions.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {suggestions.slice(0,3).map(s => (
                      <Card key={s.establishmentId + (s.itemType||'')} className="overflow-hidden border border-gray-200 shadow-sm transition-all duration-300 ease-out">
                        {s.itemImageUrl || s.imageUrlMain ? (
                          <div className="aspect-video bg-gray-100 overflow-hidden">
                            <img src={s.itemImageUrl || s.imageUrlMain!} alt={s.establishmentName} className="w-full h-full object-cover transition-transform duration-300 ease-out hover:scale-[1.02]" />
                          </div>
                        ) : null}
                        <CardContent className="p-3">
                          <div className="font-medium text-gray-900">{s.establishmentName}</div>
                          <div className="text-sm text-gray-600">{s.city}</div>
                          <div className="mt-1 text-sm text-gray-700">Loại: <span className="font-medium">{s.itemType || s.floorArea}</span></div>
                          <div className="text-sm text-gray-900">Giá: {s.finalPrice?.toLocaleString()} đ</div>
                          <div className="text-xs text-gray-600">Còn: {s.unitsAvailable}</div>
                          
                          {/* Agent explanation */}
                          {(s as any).explanation && agentMode === 'agent' && (
                            <div className="mt-2 text-xs text-gray-500 italic border-l-2 border-gray-200 pl-2">
                              {(s as any).explanation}
                            </div>
                          )}
                          
                          <div className="mt-2 flex items-center gap-2">
                            <Button size="sm" className="bg-gray-900 hover:bg-gray-800 text-white transition-colors duration-200" onClick={()=>book(s)} disabled={loading}>Book ngay</Button>
                            <Button size="sm" variant="outline" className="border-gray-200 transition-colors duration-200" asChild>
                              <a href={`/establishments/${s.establishmentId}`} target="_blank" rel="noreferrer">Xem chi tiết</a>
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : null}
                {suggestions.length > 0 ? (
                  <div className="mt-3 text-sm">
                    <div className="text-gray-700 mb-2">Bạn có muốn xem gợi ý khác hoặc tinh chỉnh tiêu chí?</div>
                    <div className="flex flex-wrap gap-2">
                      <Button size="sm" variant="outline" className="border-gray-200 transition-colors duration-200" onClick={moreSuggestions}>Gợi ý khác</Button>
                      <Button size="sm" variant="outline" className="border-gray-200 transition-colors duration-200" onClick={()=>relaxAndSearch('more_budget')}>Tăng ngân sách +20%</Button>
                      <Button size="sm" variant="outline" className="border-gray-200 transition-colors duration-200" onClick={()=>relaxAndSearch('drop_amenities')}>Bỏ lọc tiện ích</Button>
                      <Button size="sm" variant="outline" className="border-gray-200 transition-colors duration-200" onClick={()=>relaxAndSearch('shift_date')}>Lùi/ngày khác</Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-700">
                    Hãy nới tiêu chí tìm kiếm một chút nhé:
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Button size="sm" variant="outline" className="border-gray-200 transition-colors duration-200" onClick={()=>relaxAndSearch('more_budget')}>Tăng ngân sách +20%</Button>
                      <Button size="sm" variant="outline" className="border-gray-200 transition-colors duration-200" onClick={()=>relaxAndSearch('drop_amenities')}>Bỏ lọc tiện ích</Button>
                      <Button size="sm" variant="outline" className="border-gray-200 transition-colors duration-200" onClick={()=>relaxAndSearch('shift_date')}>Lùi/ngày khác</Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          </div>
        </CardContent>
      </Card>
      </div>

      {/* Input bar: hiển thị khi ở agent mode hoặc quiz completed */}
      {(agentMode === 'agent' || !quiz || quiz.quiz_completed) && (
        <div className="flex-shrink-0 p-6 border-t border-gray-200 bg-white">
          <div className="relative max-w-3xl mx-auto">
            <Input
              className="w-full h-12 rounded-full px-4 pr-14 shadow-sm border-gray-200 focus:border-gray-400"
              placeholder={agentMode === 'agent' 
                ? "Nói chuyện tự nhiên với AI (ví dụ: 'Tôi muốn đi Đà Nẵng 2 đêm, có hồ bơi, ngân sách 2 triệu')" 
                : "Nhập yêu cầu của bạn..."
              }
              value={prompt}
              onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setPrompt(e.target.value)}
              onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>)=>{ if (e.key==='Enter' && !e.shiftKey && !loading) { e.preventDefault(); send() } }}
            />
            <Button
              className="absolute right-2 inset-y-0 my-auto h-10 w-10 rounded-full bg-gray-900 hover:bg-gray-800 text-white"
              onClick={()=>send()}
              disabled={loading}
              size="sm"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <div className="mt-2 flex items-center gap-2">
            {loading && <ArrowPathIcon className="w-4 h-4 animate-spin text-gray-500" />}
            {msg && <span className="text-green-700">{msg}</span>}
          </div>
        </div>
      )}

      {quiz && quiz.quiz_completed && (
        <div className="flex-shrink-0 p-6 border-t border-gray-200 bg-white">
          <Card className="border border-gray-200">
            <CardHeader>
              <CardTitle className="text-lg text-gray-900">Tham số tìm kiếm</CardTitle>
              <CardDescription className="text-gray-600">Điều chỉnh các tham số nếu cần thiết</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 bg-white">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <Label htmlFor="city">Thành phố</Label>
                <Input 
                  id="city"
                  placeholder="Thành phố" 
                  value={currentParams.city||''} 
                  onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setCurrentParams({ ...currentParams, city: e.target.value })} 
                />
              </div>
              <div>
                <Label htmlFor="check_in_date">Ngày check-in</Label>
              <DatePicker
                  id="check_in_date"
                value={currentParams.check_in_date ? new Date(currentParams.check_in_date) : undefined}
                range={false}
                onChange={(d)=>{
                  const dd = d as Date | undefined
                  setCurrentParams({ ...currentParams, check_in_date: dd ? dd.toISOString().slice(0,10) : '' })
                }}
                />
              </div>
              <div>
                <Label htmlFor="duration">Số đêm</Label>
                <Input 
                  id="duration"
                  type="number" 
                  placeholder="Số đêm" 
                  value={currentParams.duration||''} 
                  onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setCurrentParams({ ...currentParams, duration: Number(e.target.value||0) })} 
                />
              </div>
              <div>
                <Label htmlFor="max_price">Ngân sách tối đa</Label>
                <Input 
                  id="max_price"
                  type="number" 
                  placeholder="Ngân sách tối đa" 
                  value={currentParams.max_price||''} 
                  onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setCurrentParams({ ...currentParams, max_price: Number(e.target.value||0) })} 
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={()=>{ setPrompt(''); send({ params: currentParams, prompt: '' }) }} disabled={loading} className="bg-gray-900 hover:bg-gray-800 text-white">
                <Sparkles className="w-4 h-4 mr-2" />
                Tìm gợi ý
              </Button>
              <Button 
                variant="outline"
                className="border-gray-200"
                onClick={() => {
                  setQuiz(null)
                  setSuggestions(null)
                  setCurrentParams({})
                  setSelectedOpt('')
                  setCustomOpt('')
                  setSelectedAmenities([])
                  setSelectedImages([])
                  setMessages(prev => [...prev, { role: 'assistant', text: 'Tôi đã reset tìm kiếm. Hãy mô tả nhu cầu mới của bạn!' }])
                }}
              >
                Tìm kiếm mới
              </Button>
            </div>
            </CardContent>
          </Card>
        </div>
      )}

      
    </div>
  )
}


