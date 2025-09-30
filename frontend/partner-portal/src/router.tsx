import { createBrowserRouter } from 'react-router-dom'
import Layout from './app/Layout'
import EstablishmentsPage from './pages/EstablishmentsPage'
                import EstablishmentDetailPage from './pages/EstablishmentDetailPage'
import EstablishmentCreatePage from './pages/EstablishmentCreatePage'
import TypesPage from './pages/TypesPage'
import VariantsPage from './pages/VariantsPage'
import AvailabilityPage from './pages/AvailabilityPage'
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
          { path: '/variants', element: <VariantsPage /> },
          { path: '/availability', element: <AvailabilityPage /> },
        ],
      },
    ],
  },
])

export default router


