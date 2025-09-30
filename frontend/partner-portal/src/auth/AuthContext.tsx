import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api from '../api/client'

export interface AuthUser { id: string; email: string; name?: string; role?: string }

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string, role: 'PARTNER' | 'CUSTOMER') => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem('authUser')
    return raw ? (JSON.parse(raw) as AuthUser) : null
  })
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('authToken'))

  useEffect(() => {
    api.interceptors.request.use((config) => {
      if (token) config.headers.Authorization = `Bearer ${token}`
      return config
    })
  }, [token])

  const login = async (email: string, password: string) => {
    const res = await api.post('/auth/login', { email, password })
    const t = res.data?.token || res.data?.accessToken
    if (t) {
      setToken(t)
      localStorage.setItem('authToken', t)
    }
    // Backend returns: { id, role, email }
    const id = res.data?.id
    if (id) {
      const u: AuthUser = { id: String(id), email: res.data?.email, role: res.data?.role }
      setUser(u)
      localStorage.setItem('authUser', JSON.stringify(u))
    }
  }

  const register = async (name: string, email: string, password: string, role: 'PARTNER' | 'CUSTOMER') => {
    // Backend expects { email, password, role }
    await api.post('/auth/register', { email, password, role })
    await login(email, password)
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('authToken')
    localStorage.removeItem('authUser')
  }

  const value = useMemo(() => ({ user, token, login, register, logout }), [user, token])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}


