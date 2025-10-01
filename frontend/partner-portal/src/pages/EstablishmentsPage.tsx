import { useEffect, useState } from 'react'
import { listMyEstablishments } from '../api/partner'
import type { Establishment } from '../types'
import EstablishmentCard from '../components/EstablishmentCard'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function EstablishmentsPage() {
  const { user } = useAuth()
  const [items, setItems] = useState<Establishment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    if (!user?.id) return
    listMyEstablishments(user.id)
      .then((data) => { if (mounted) setItems(data) })
      .finally(() => { if (mounted) setLoading(false) })
    return () => { mounted = false }
  }, [user?.id])

  if (loading) return <div>Đang tải...</div>

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Cơ sở của tôi</h1>
      {!Array.isArray(items) || items.length === 0 ? (
        <div className="text-slate-600">Chưa có cơ sở nào. <Link className="text-blue-600" to="/establishments/new">Thêm cơ sở mới</Link></div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((e) => (
            <EstablishmentCard key={e.id} item={e} />
          ))}
        </div>
      )}
    </div>
  )
}


