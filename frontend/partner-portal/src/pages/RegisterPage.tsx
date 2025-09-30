import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<'PARTNER' | 'CUSTOMER'>('PARTNER')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null); setLoading(true)
    try {
      await register(name, email, password, role)
      navigate('/', { replace: true })
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Đăng kí thất bại')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto">
      <h1 className="text-xl font-semibold mb-4">Đăng kí</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        <input className="w-full border rounded px-3 py-2" placeholder="Họ tên" value={name} onChange={(e)=>setName(e.target.value)} />
        <input className="w-full border rounded px-3 py-2" placeholder="Email" value={email} onChange={(e)=>setEmail(e.target.value)} />
        <input type="password" className="w-full border rounded px-3 py-2" placeholder="Mật khẩu" value={password} onChange={(e)=>setPassword(e.target.value)} />
        <div className="flex gap-3 text-sm">
          <label className="flex items-center gap-2">
            <input type="radio" className="accent-slate-900" checked={role==='PARTNER'} onChange={()=>setRole('PARTNER')} />
            PARTNER
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" className="accent-slate-900" checked={role==='CUSTOMER'} onChange={()=>setRole('CUSTOMER')} />
            CUSTOMER
          </label>
        </div>
        {error && <div className="text-red-600 text-sm">{error}</div>}
        <button disabled={loading} className="w-full px-4 py-2 rounded-md bg-slate-900 text-white disabled:opacity-60">{loading?'Đang xử lý...':'Đăng kí'}</button>
      </form>
      <div className="text-sm mt-3">Đã có tài khoản? <Link className="text-blue-600" to="/auth/login">Đăng nhập</Link></div>
    </div>
  )
}


