import { createContext, useContext, useEffect, useState } from 'react'
import { authApi, TOKEN_KEY } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [mfaRequired, setMfaRequired] = useState(false)
  const [pendingMfaToken, setPendingMfaToken] = useState(null)

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setLoading(false)
      return
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setLoading(false))
  }, [])

  async function login(email, password) {
    const data = await authApi.login({ email, password })
    if (data.mfa_required) {
      setMfaRequired(true)
      setPendingMfaToken(data.mfa_pending_token)
      return { mfaRequired: true }
    }
    localStorage.setItem(TOKEN_KEY, data.access_token)
    const me = await authApi.me()
    setUser(me)
    return { mfaRequired: false }
  }

  async function verifyMfa(code) {
    const data = await authApi.mfaVerify({ mfa_pending_token: pendingMfaToken, code })
    localStorage.setItem(TOKEN_KEY, data.access_token)
    const me = await authApi.me()
    setUser(me)
    setMfaRequired(false)
    setPendingMfaToken(null)
  }

  async function register(name, email, password) {
    return authApi.register({ name, email, password })
  }

  async function resendVerification(email) {
    return authApi.resendVerification(email)
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
    setMfaRequired(false)
    setPendingMfaToken(null)
  }

  async function refreshUser() {
    const me = await authApi.me()
    setUser(me)
    return me
  }

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    mfaRequired,
    login,
    verifyMfa,
    register,
    resendVerification,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
