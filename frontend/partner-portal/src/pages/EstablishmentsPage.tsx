import { useEffect, useState } from 'react'
import { listMyEstablishments } from '../api/partner'
import type { Establishment } from '../types'
import EstablishmentCard from '../components/EstablishmentCard'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardTitle } from '../components/ui/card'
import { Plus, Building2 } from 'lucide-react'

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Cơ sở của tôi</h1>
          <p className="text-slate-600 mt-1">Quản lý các cơ sở kinh doanh của bạn</p>
        </div>
        <Button asChild>
          <Link to="/establishments/new">
            <Plus className="w-4 h-4 mr-2" />
            Thêm cơ sở mới
          </Link>
        </Button>
      </div>

      {!Array.isArray(items) || items.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Building2 className="w-12 h-12 text-slate-400 mb-4" />
            <CardTitle className="text-lg text-slate-600 mb-2">Chưa có cơ sở nào</CardTitle>
            <CardDescription className="text-center mb-4">
              Bắt đầu bằng cách thêm cơ sở đầu tiên của bạn
            </CardDescription>
            <Button asChild>
              <Link to="/establishments/new">
                <Plus className="w-4 h-4 mr-2" />
                Thêm cơ sở mới
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-3 gap-6">
          {items.map((e, index) => (
            <div key={e.id} className="fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
              <EstablishmentCard item={e} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


