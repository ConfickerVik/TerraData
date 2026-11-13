import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from '../features/auth/useAuth'
import { AppLayout } from './layout/AppLayout'
import { AuthLayout } from './layout/AuthLayout'
import { AdminPage } from '../pages/AdminPage'
import { AnalyticsPage } from '../pages/AnalyticsPage'
import { ApiKeysPage } from '../pages/ApiKeysPage'
import { ConverterPage } from '../pages/ConverterPage'
import { DashboardPage } from '../pages/DashboardPage'
import { FiasPage } from '../pages/FiasPage'
import { LoginPage } from '../pages/LoginPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { NspdPage } from '../pages/NspdPage'
import { RegisterPage } from '../pages/RegisterPage'
import { RosreestrPage } from '../pages/RosreestrPage'
import { SudrfPage } from '../pages/SudrfPage'

function RequireAuth({ children }: { children: ReactNode }) {
  const { token, loading } = useAuth()

  if (loading) {
    return null
  }
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="rosreestr" element={<RosreestrPage />} />
        <Route path="converter" element={<ConverterPage />} />
        <Route path="nspd" element={<NspdPage />} />
        <Route path="fias" element={<FiasPage />} />
        <Route path="sudrf" element={<SudrfPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="api-keys" element={<ApiKeysPage />} />
        <Route path="admin" element={<AdminPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
