import { Link, Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { useAuth } from '../auth/AuthContext'

export default function Layout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <header className="h-12 sticky top-0 z-30 bg-white/80 backdrop-blur border-b border-slate-200 px-6 flex items-center justify-between shadow-sm">
          <div className="font-semibold tracking-wide">Partner Portal</div>
          <HeaderRight />
        </header>
        <main className="px-8 py-6 w-full max-w-7xl mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function HeaderRight() {
  const { user, logout, token } = useAuth()
  if (!token && !user) return <Link to="/auth/login" className="text-sm text-blue-600">Đăng nhập</Link>
  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-[11px] font-semibold">
          {(user?.name || user?.email || 'U').slice(0,1).toUpperCase()}
        </div>
        <div className="leading-tight">
          <div className="font-medium">{user?.name || user?.email || 'Tài khoản'}</div>
          {user?.role && (
            <span className="inline-block text-[11px] px-2 py-[2px] rounded-full bg-slate-100 border border-slate-200 text-slate-700">
              {user.role}
            </span>
          )}
        </div>
      </div>
      <button onClick={logout} className="px-3 py-1 border rounded">Đăng xuất</button>
    </div>
  )
}


