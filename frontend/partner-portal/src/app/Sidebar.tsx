import { NavLink } from 'react-router-dom'

const itemCls = ({ isActive }: { isActive: boolean }) =>
  `block px-4 py-2 rounded-md hover:bg-slate-100 ${isActive ? 'bg-slate-100 font-semibold' : ''}`

export default function Sidebar() {
  return (
    <aside className="w-64 border-r border-slate-200 p-4 space-y-2">
      <div className="text-sm text-slate-500 px-2">Menu</div>
      <NavLink to="/" className={itemCls}>Cơ sở của tôi</NavLink>
      <NavLink to="/establishments/new" className={itemCls}>Thêm cơ sở mới</NavLink>
      <NavLink to="/types" className={itemCls}>Loại phòng/bàn</NavLink>
      <NavLink to="/variants" className={itemCls}>Biến thể</NavLink>
      <NavLink to="/availability" className={itemCls}>Lịch khả dụng</NavLink>
    </aside>
  )
}


