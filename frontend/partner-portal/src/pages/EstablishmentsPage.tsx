import { useEffect, useMemo, useState } from 'react'
import { listMyEstablishments } from '../api/partner'
import type { Establishment } from '../types'
import EstablishmentCard from '../components/EstablishmentCard'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Plus, Building2 } from 'lucide-react'
import { Badge } from '../components/ui/badge'

export default function EstablishmentsPage() {
  const { user } = useAuth()
  const [items, setItems] = useState<Establishment[]>([])
  const [loading, setLoading] = useState(true)
  const [sortBy, setSortBy] = useState<'latest'|'name'>('latest')

  useEffect(() => {
    let mounted = true
    if (!user?.id) return
    listMyEstablishments(user.id)
      .then((data) => { if (mounted) setItems(data) })
      .finally(() => { if (mounted) setLoading(false) })
    return () => { mounted = false }
  }, [user?.id])

  const sortedItems = useMemo(() => {
    const arr = [...items]
    if (sortBy === 'name') {
      arr.sort((a,b)=> (a.name||'').localeCompare(b.name||''))
    }
    return arr
  }, [items, sortBy])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-2xl">Cơ sở của tôi</CardTitle>
          <CardDescription>Quản lý các cơ sở kinh doanh của bạn</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs">{items.length} cơ sở</Badge>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Sắp xếp</span>
              <select className="border rounded px-3 py-2 w-40" value={sortBy} onChange={(e)=>setSortBy(e.target.value as any)}>
                <option value="latest">Mới nhất</option>
                <option value="name">Theo tên</option>
              </select>
            </div>
          </div>
          <Button asChild className="focus-visible:ring-2 focus-visible:ring-slate-400">
            <Link to="/establishments/new">
              <Plus className="w-4 h-4 mr-2" />
              Thêm cơ sở mới
            </Link>
          </Button>
        </CardContent>
      </Card>

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
          {sortedItems.map((e, index) => (
            <div key={e.id} className="fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
              <EstablishmentCard item={e} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


