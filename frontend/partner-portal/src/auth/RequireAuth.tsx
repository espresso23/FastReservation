import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function RequireAuth() {
  const { token, user } = useAuth()
  const location = useLocation()
  if (!token && !user) return <Navigate to="/auth/login" replace state={{ from: location }} />
  return <Outlet />
}


