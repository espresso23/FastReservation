import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../auth/AuthContext'

type Booking = {
  id: number
  userId: number
  establishmentId: string
  partnerId: string
  startDate: string
  duration: number
  totalPriceVnd: number
  status: 'PENDING_PAYMENT' | 'CONFIRMED' | 'CANCELLED'
  bookedItemType?: string
  bookedFloorArea?: string
}

export default function BookingsPage() {
  const { user } = useAuth()
  const [items, setItems] = useState<Booking[]>([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    if (!user?.id) return
    setLoading(true)
    try {
      const res = await api.get(`/partner/bookings/${user.id}`)
      setItems(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [user?.id])

  const updateStatus = async (id: number, status: Booking['status']) => {
    await api.post(`/partner/bookings/${id}/status`, { status })
    await load()
  }

  const formatDate = (d: string) => new Date(d).toISOString().slice(0,10)
  const addDays = (d: string, n: number) => {
    const dt = new Date(d)
    dt.setDate(dt.getDate() + (n || 0))
    return dt.toISOString().slice(0,10)
  }

  const badge = (status: Booking['status']) => {
    switch (status) {
      case 'CONFIRMED': return 'bg-green-100 text-green-800 border-green-200'
      case 'CANCELLED': return 'bg-red-100 text-red-800 border-red-200'
      default: return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Quản lý Booking</h1>
      {loading ? 'Đang tải...' : (
        <div className="space-y-2">
          {items.map(b => (
            <div key={b.id} className={`border rounded p-3 flex items-center justify-between` }>
              <div className="text-sm">
                <div className="font-medium flex items-center gap-2">
                  <span>#{b.id}</span>
                  <span>•</span>
                  <span>{b.bookedItemType || '-'}</span>
                  <span>•</span>
                  <span>{formatDate(b.startDate)} → {addDays(b.startDate, b.duration)}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${badge(b.status)}`}>{b.status}</span>
                </div>
                <div className="text-slate-600">Tổng: {b.totalPriceVnd?.toLocaleString()} đ • Thời lượng: {b.duration} đêm</div>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <button className="px-2 py-1 border rounded" disabled={b.status==='CONFIRMED'} onClick={()=>updateStatus(b.id, 'CONFIRMED')}>Xác nhận</button>
                <button className="px-2 py-1 border rounded" disabled={b.status==='PENDING_PAYMENT'} onClick={()=>updateStatus(b.id, 'PENDING_PAYMENT')}>Pending</button>
                <button className="px-2 py-1 border rounded" disabled={b.status==='CANCELLED'} onClick={()=>updateStatus(b.id, 'CANCELLED')}>Hủy</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


