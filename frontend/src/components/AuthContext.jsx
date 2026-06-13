import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('financeai_token'))
  const [username, setUsername] = useState(localStorage.getItem('financeai_username'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const savedToken = localStorage.getItem('financeai_token')
    const savedUsername = localStorage.getItem('financeai_username')
    if (savedToken && savedUsername) {
      setToken(savedToken)
      setUsername(savedUsername)
    } else {
      setToken(null)
      setUsername(null)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response && error.response.status === 401) {
          logout()
        }
        return Promise.reject(error)
      }
    )
    return () => {
      api.interceptors.response.eject(interceptor)
    }
  }, [])

  const login = (userToken, userVal) => {
    localStorage.setItem('financeai_token', userToken)
    localStorage.setItem('financeai_username', userVal)
    setToken(userToken)
    setUsername(userVal)
  }

  const logout = () => {
    localStorage.removeItem('financeai_token')
    localStorage.removeItem('financeai_username')
    setToken(null)
    setUsername(null)
  }

  return (
    <AuthContext.Provider value={{ token, username, login, logout, loading, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
