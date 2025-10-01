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
      const url = user?.role === 'PARTNER' ? `/partner/bookings/${user.id}` : `/booking/user/view/${user.id}`
      console.log('Loading bookings from:', url, 'for user:', user)
      const res = await api.get(url)
      console.log('Bookings response:', res.data)
      setItems(Array.isArray(res.data) ? res.data : [])
    } catch (error) {
      console.error('Error loading bookings:', error)
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [user?.id])

  const updateStatus = async (id: number, status: Booking['status']) => {
    if (user?.role !== 'PARTNER') return
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
      <h1 className="text-xl font-semibold mb-4">{user?.role==='PARTNER' ? 'Quản lý Booking' : 'Đặt chỗ của tôi'}</h1>
      {loading ? 'Đang tải...' : (
        <div className="space-y-2">
          {!Array.isArray(items) || items.length === 0 ? (
            <div className="text-slate-600">Chưa có booking nào.</div>
          ) : (
            items.map(b => (
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
              
            </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}


