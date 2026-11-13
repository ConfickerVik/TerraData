import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { UNAUTHORIZED_EVENT } from '../../api/client'
import { clearAccessToken, getAccessToken, setAccessToken } from '../../api/token'
import type { UserOut } from '../../api/types'
import * as authApi from './authApi'

interface AuthContextValue {
  user: UserOut | null
  token: string | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, password: string, email?: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getAccessToken())
  const [user, setUser] = useState<UserOut | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  const logout = useCallback(() => {
    clearAccessToken()
    setToken(null)
    setUser(null)
  }, [])

  // При старте, если токен есть, подтягиваем профиль пользователя.
  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    let cancelled = false
    authApi
      .getMe()
      .then((me) => {
        if (!cancelled) setUser(me)
      })
      .catch(() => {
        if (!cancelled) logout()
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token, logout])

  // Глобальная реакция на 401 от API.
  useEffect(() => {
    const handler = () => logout()
    window.addEventListener(UNAUTHORIZED_EVENT, handler)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handler)
  }, [logout])

  const login = useCallback(async (username: string, password: string) => {
    const res = await authApi.login({ username, password })
    setAccessToken(res.access_token)
    setToken(res.access_token)
  }, [])

  const register = useCallback(
    async (username: string, password: string, email?: string) => {
      await authApi.register({ username, password, email: email ?? null })
    },
    [],
  )

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, loading, login, register, logout }),
    [user, token, loading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
