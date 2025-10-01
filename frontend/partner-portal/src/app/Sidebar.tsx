import { NavLink } from 'react-router-dom'

const itemCls = ({ isActive }: { isActive: boolean }) =>
  `block px-4 py-2 rounded-md hover:bg-slate-100 ${isActive ? 'bg-slate-100 font-semibold' : ''}`

import { useAuth } from '../auth/AuthContext'

export default function Sidebar() {
  const { user } = useAuth()
  const isPartner = user?.role === 'PARTNER'
  return (
    <aside className="w-64 border-r border-slate-200 p-4 space-y-2">
      <div className="text-sm text-slate-500 px-2">Menu</div>
      {isPartner && <NavLink to="/" className={itemCls}>Cơ sở của tôi</NavLink>}
      {isPartner && <NavLink to="/establishments/new" className={itemCls}>Thêm cơ sở mới</NavLink>}
      {isPartner && <NavLink to="/types" className={itemCls}>Loại phòng/bàn</NavLink>}
      <NavLink to="/bookings" className={itemCls}>Booking</NavLink>
      <div className="text-sm text-slate-500 px-2 mt-4">User</div>
      <NavLink to="/user" className={itemCls}>Đặt chỗ (AI)</NavLink>
    </aside>
  )
}


