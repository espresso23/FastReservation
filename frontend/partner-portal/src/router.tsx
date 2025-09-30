import { createBrowserRouter } from 'react-router-dom'
import Layout from './app/Layout'
import EstablishmentsPage from './pages/EstablishmentsPage'
                import EstablishmentDetailPage from './pages/EstablishmentDetailPage'
import EstablishmentCreatePage from './pages/EstablishmentCreatePage'
import TypesPage from './pages/TypesPage'
import BookingsPage from './pages/BookingsPage'
import UserBookingPage from './pages/UserBookingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import { AuthProvider } from './auth/AuthContext'
import RequireAuth from './auth/RequireAuth'

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <AuthProvider>
        <Layout />
      </AuthProvider>
    ),
    children: [
      { path: '/auth/login', element: <LoginPage /> },
      { path: '/auth/register', element: <RegisterPage /> },
      {
        element: <RequireAuth />,
        children: [
          { path: '/', element: <EstablishmentsPage /> },
          { path: '/establishments/new', element: <EstablishmentCreatePage /> },
          { path: '/establishments/:id', element: <EstablishmentDetailPage /> },
          { path: '/types', element: <TypesPage /> },
          { path: '/bookings', element: <BookingsPage /> },
          { path: '/user', element: <UserBookingPage /> },
        ],
      },
    ],
  },
])

export default router


